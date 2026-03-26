import base64
import re
import threading
import logging
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration, ApiClient, MessagingApi, 
    MessagingApiBlob, ReplyMessageRequest, TextMessage
)
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent
from linebot.v3.exceptions import InvalidSignatureError
import os
from dotenv import load_dotenv
from typing import List
from urllib.parse import urlparse
from collections import defaultdict

# 匯入自定義模組
from models import ScamDetectionRecord, UserHistory, LeaderboardEntry, CreateTeamRequest, JoinTeamRequest
from database import add_detection_record, get_user_history, get_leaderboard, create_table_if_not_exists, create_team_tables_if_not_exist, get_report_count, dynamodb
from bedrock_service import analyze_scam_content
from team_service import TeamService
from mass_report_service import process_mass_report
from app_logging import setup_logging
from security import RateLimiter, validate_line_channel_access_token

setup_logging()
logger = logging.getLogger(__name__)

# 載入環境變數
load_dotenv()

# 初始化 DynamoDB table
logger.info("Checking primary DynamoDB table")
create_table_if_not_exists()
logger.info("Checking team collaboration DynamoDB tables")
create_team_tables_if_not_exist()

# 初始化 FastAPI
app = FastAPI(title="FLAC Linebot - Scam Detection System")

# 掛載靜態檔案
app.mount("/static", StaticFiles(directory="static"), name="static")

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = validate_line_channel_access_token(
    os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LIFF_URL_TEAM_MANAGEMENT = os.getenv("LIFF_URL_TEAM_MANAGEMENT", "https://liff.line.me/2009609029-RlBZuNs2")

if not CHANNEL_ACCESS_TOKEN or not CHANNEL_SECRET:
    raise ValueError("請確保 .env 檔案中已設定 LINE_CHANNEL_ACCESS_TOKEN 與 LINE_CHANNEL_SECRET")

configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)

# 初始化團隊服務
team_service = TeamService()

# ==================== 靜態網頁路由 ====================

@app.get("/")
async def root():
    """首頁 - 重導向到 index.html"""
    return FileResponse("static/index.html")

@app.get("/index.html")
async def index():
    """個人儀表板"""
    return FileResponse("static/index.html")

@app.get("/leaderboard.html")
async def leaderboard_page():
    """個人排行榜頁面"""
    return FileResponse("static/leaderboard.html")

@app.get("/team.html")
async def team_page():
    """團隊管理頁面"""
    return FileResponse("static/team.html")

@app.get("/team-leaderboard.html")
async def team_leaderboard_page():
    """團隊排行榜頁面"""
    return FileResponse("static/team-leaderboard.html")

@app.get("/trends.html")
async def trends_page():
    """詐騙趨勢地圖頁面"""
    return FileResponse("static/trends.html")

# ==================== API 路由 ====================

@app.get("/api/history/{user_id}", response_model=List[UserHistory])
async def get_history(user_id: str):
    """取得使用者的詐騙偵測歷史記錄"""
    try:
        history = get_user_history(user_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法取得歷史記錄: {str(e)}")

@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard_api():
    """取得全球排行榜"""
    try:
        leaderboard = get_leaderboard()
        return leaderboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"無法取得排行榜: {str(e)}")

# ==================== Team Collaboration API ====================

@app.post("/api/teams/join")
async def join_team(request: JoinTeamRequest):
    """加入團隊
    
    Request Body:
    {
        "team_id": "550e8400-e29b-41d4-a716-446655440000",
        "member_uid": "U9876543210",
        "signature": "abc123..."
    }
    
    Response:
    {
        "success": true,
        "team_name": "防詐先鋒隊",
        "member_count": 5
    }
    """
    # 驗證必要參數
    if not request.team_id or not request.member_uid or not request.signature:
        raise HTTPException(status_code=400, detail="缺少必要參數")
    
    try:
        # 呼叫 TeamService 加入團隊（內部會驗證簽章）
        success = team_service.join_team(
            team_id=request.team_id,
            member_uid=request.member_uid,
            signature=request.signature
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="加入團隊失敗")
        
        # 取得團隊資訊以回傳團隊名稱與成員數
        team_info = team_service.get_team_info(request.team_id)
        
        if not team_info:
            # 理論上不應該發生（加入成功但查不到團隊）
            raise HTTPException(status_code=500, detail="無法取得團隊資訊")
        
        return {
            "success": True,
            "team_name": team_info.team_name,
            "member_count": team_info.member_count
        }
        
    except ValueError as e:
        # 處理業務邏輯錯誤
        error_msg = str(e)
        
        # 根據錯誤訊息回傳適當的 HTTP 狀態碼
        if "無效的邀請連結" in error_msg or "簽章驗證失敗" in error_msg:
            raise HTTPException(status_code=403, detail=error_msg)
        elif "團隊不存在或已解散" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        elif "您已經是團隊成員" in error_msg or "您已加入其他團隊" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    except HTTPException:
        # 重新拋出 HTTPException，不要被下面的 Exception 捕獲
        raise
    
    except Exception as e:
        # 處理其他未預期的錯誤
        print(f"加入團隊失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"加入團隊失敗: {str(e)}")

@app.post("/api/teams/create")
async def create_team(request: CreateTeamRequest):
    """建立團隊
    
    Request Body:
    {
        "leader_uid": "U1234567890",
        "team_name": "防詐先鋒隊"
    }
    
    Response:
    {
        "team_id": "550e8400-e29b-41d4-a716-446655440000",
        "team_name": "防詐先鋒隊",
        "invite_url": "https://liff.line.me/xxx?team_id=xxx&signature=xxx"
    }
    """
    # 驗證團隊名稱
    team_name = request.team_name.strip()
    
    if not team_name:
        raise HTTPException(status_code=400, detail="團隊名稱不可為空")
    
    if len(team_name) > 30:
        raise HTTPException(status_code=400, detail="團隊名稱不可超過 30 字元")
    
    try:
        # 建立團隊
        team = team_service.create_team(
            leader_uid=request.leader_uid,
            team_name=team_name
        )
        
        # 產生邀請連結
        invite_url = team_service.invite_member(
            team_id=team.team_id,
            inviter_uid=request.leader_uid
        )
        
        return {
            "team_id": team.team_id,
            "team_name": team.team_name,
            "invite_url": invite_url
        }
        
    except ValueError as e:
        # 處理業務邏輯錯誤（例如：使用者已是隊長）
        error_msg = str(e)
        if "已經是隊長" in error_msg:
            raise HTTPException(status_code=409, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail=error_msg)
    
    except HTTPException:
        # 重新拋出 HTTPException，不要被下面的 Exception 捕獲
        raise
    
    except Exception as e:
        # 處理其他未預期的錯誤
        print(f"建立團隊失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"建立團隊失敗: {str(e)}")

@app.get("/api/teams/{team_id}/invite")
async def get_invite_url(team_id: str, inviter_uid: str):
    """取得團隊邀請 URL
    
    Query Parameters:
    - inviter_uid: 邀請者的 LINE UID
    
    Response:
    {
        "invite_url": "https://liff.line.me/xxx?team_id=xxx&signature=xxx"
    }
    """
    try:
        # 驗證團隊是否存在
        team_info = team_service.get_team_info(team_id)
        if not team_info:
            raise HTTPException(status_code=404, detail="團隊不存在或已解散")
        
        # 產生邀請連結
        invite_url = team_service.invite_member(
            team_id=team_id,
            inviter_uid=inviter_uid
        )
        
        return {
            "invite_url": invite_url
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"產生邀請連結失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"產生邀請連結失敗: {str(e)}")

@app.get("/api/teams/{team_id}")
async def get_team(team_id: str):
    """取得團隊資訊
    
    Response:
    {
        "team_id": "550e8400-e29b-41d4-a716-446655440000",
        "team_name": "防詐先鋒隊",
        "leader_uid": "U1234567890",
        "total_points": 1250,
        "member_count": 5,
        "created_at": "2024-01-15T10:30:00Z"
    }
    """
    try:
        team_info = team_service.get_team_info(team_id)
        
        if not team_info:
            raise HTTPException(status_code=404, detail="團隊不存在或已解散")
        
        return {
            "team_id": team_info.team_id,
            "team_name": team_info.team_name,
            "leader_uid": team_info.leader_uid,
            "total_points": team_info.total_points,
            "member_count": team_info.member_count,
            "created_at": team_info.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"查詢團隊資訊失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢團隊資訊失敗: {str(e)}")

@app.get("/api/users/{user_id}/team")
async def get_user_team(user_id: str):
    """查詢使用者所屬團隊
    
    Response:
    {
        "has_team": true,
        "team_id": "550e8400-e29b-41d4-a716-446655440000",
        "team_name": "防詐先鋒隊",
        "is_leader": false
    }
    """
    try:
        # 使用 LineUidIndex GSI 查詢使用者所屬團隊
        team_members_table = team_service.team_members_table
        response = team_members_table.query(
            IndexName='LineUidIndex',
            KeyConditionExpression='line_uid = :uid',
            ExpressionAttributeValues={':uid': user_id},
            Limit=1
        )
        
        items = response.get('Items', [])
        
        if not items:
            # 使用者不屬於任何團隊
            return {
                "has_team": False,
                "team_id": None,
                "team_name": None,
                "is_leader": False
            }
        
        # 取得團隊資訊
        member_data = items[0]
        team_id = member_data['team_id']
        is_leader = member_data.get('is_leader', False)
        
        team_info = team_service.get_team_info(team_id)
        
        if not team_info:
            return {
                "has_team": False,
                "team_id": None,
                "team_name": None,
                "is_leader": False
            }
        
        return {
            "has_team": True,
            "team_id": team_info.team_id,
            "team_name": team_info.team_name,
            "is_leader": is_leader
        }
        
    except Exception as e:
        print(f"查詢使用者團隊失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢使用者團隊失敗: {str(e)}")

@app.get("/api/teams/{team_id}/members")
async def get_team_members(team_id: str):
    """取得團隊成員清單
    
    Response:
    {
        "members": [
            {
                "line_uid": "U1234567890",
                "contribution_points": 450,
                "report_count": 15,
                "is_leader": true,
                "joined_at": "2024-01-15T10:30:00Z"
            }
        ]
    }
    """
    try:
        # 先檢查團隊是否存在
        team_info = team_service.get_team_info(team_id)
        if not team_info:
            raise HTTPException(status_code=404, detail="團隊不存在或已解散")
        
        # 取得成員清單
        members = team_service.get_team_members(team_id)
        
        # 轉換為回應格式
        members_data = [
            {
                "line_uid": member.line_uid,
                "contribution_points": member.contribution_points,
                "report_count": member.report_count,
                "is_leader": member.is_leader,
                "joined_at": member.joined_at.isoformat()
            }
            for member in members
        ]
        
        return {"members": members_data}
        
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"查詢團隊成員失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢團隊成員失敗: {str(e)}")

@app.get("/api/leaderboard/teams")
async def get_team_leaderboard():
    """取得團隊排行榜
    
    Response:
    {
        "teams": [
            {
                "rank": 1,
                "team_id": "550e8400-e29b-41d4-a716-446655440000",
                "team_name": "防詐先鋒隊",
                "total_points": 2500,
                "report_count": 85,
                "member_count": 8
            }
        ]
    }
    """
    try:
        # 從 Teams 表掃描所有團隊
        teams_table = team_service.teams_table
        response = teams_table.scan()
        items = response.get('Items', [])
        
        # 處理分頁（如果資料超過 1MB）
        while 'LastEvaluatedKey' in response:
            response = teams_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # 轉換 Decimal 為 int
        items = team_service._convert_decimal_to_int(items)
        
        # 依 total_points 降序排序
        items.sort(key=lambda x: x.get('total_points', 0), reverse=True)
        
        # 取前 10 名並加上排名
        top_teams = items[:10]
        
        # 為了取得 report_count，需要查詢 ScamReports 表
        # 但為了效能考量，這裡先設為 0（可以後續優化）
        teams_data = [
            {
                "rank": idx + 1,
                "team_id": team['team_id'],
                "team_name": team['team_name'],
                "total_points": team.get('total_points', 0),
                "report_count": 0,  # TODO: 從 ScamReports 表統計
                "member_count": team.get('member_count', 0)
            }
            for idx, team in enumerate(top_teams)
        ]
        
        return {"teams": teams_data}
        
    except Exception as e:
        print(f"查詢團隊排行榜失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢團隊排行榜失敗: {str(e)}")

# ==================== Scam Trends API ====================

@app.get("/api/trends/domains")
async def get_domain_trends():
    """取得詐騙網域趨勢統計
    
    Response:
    {
        "domains": [
            {
                "rank": 1,
                "domain": "scam-site.com",
                "report_count": 45,
                "avg_risk_score": 9.2
            }
        ]
    }
    """
    try:
        # 從 ScamReports 表掃描所有通報
        from database import dynamodb
        reports_table = dynamodb.Table('ScamReports')
        
        response = reports_table.scan()
        items = response.get('Items', [])
        
        # 處理分頁（如果資料超過 1MB）
        while 'LastEvaluatedKey' in response:
            response = reports_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        
        # 統計每個網域的通報次數與風險評分
        domain_stats = defaultdict(lambda: {'count': 0, 'total_risk': 0})
        
        for item in items:
            url = item.get('url', '')
            risk_score = int(item.get('risk_score', 0))
            
            # 提取網域名稱
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # 移除 www. 前綴
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                if domain:  # 只統計有效網域
                    domain_stats[domain]['count'] += 1
                    domain_stats[domain]['total_risk'] += risk_score
            except Exception as e:
                print(f"解析 URL 失敗: {url}, 錯誤: {str(e)}")
                continue
        
        # 計算平均風險評分並排序
        domains_data = []
        for domain, stats in domain_stats.items():
            avg_risk = round(stats['total_risk'] / stats['count'], 1)
            domains_data.append({
                'domain': domain,
                'report_count': stats['count'],
                'avg_risk_score': avg_risk
            })
        
        # 依通報次數降序排序，取前 20 名
        domains_data.sort(key=lambda x: x['report_count'], reverse=True)
        top_domains = domains_data[:20]
        
        # 加上排名
        for idx, domain in enumerate(top_domains):
            domain['rank'] = idx + 1
        
        return {"domains": top_domains}
        
    except Exception as e:
        print(f"查詢詐騙趨勢失敗: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查詢詐騙趨勢失敗: {str(e)}")

# ==================== LINE Bot Webhook ====================

@app.post("/callback")
async def callback(request: Request):
    """LINE Bot Webhook 接收端點"""
    signature = request.headers.get("X-Line-Signature")
    body = await request.body()
    body_str = body.decode("utf-8")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        print("簽章驗證失敗，請檢查 CHANNEL_SECRET")
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"

# ==================== LINE Bot 訊息處理 ====================

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    """處理文字訊息（整合團隊積分）"""
    user_text = event.message.text
    user_id = event.source.user_id

    if not rate_limiter.allow_request(user_id):
        reply_message(
            event.reply_token,
            "⏳ 通報過於頻繁，請稍候再試。每位使用者每分鐘最多可提交 10 次通報。"
        )
        logger.warning("Rate limit exceeded: user_id=%s", user_id)
        return
    
    # 偵測網址
    urls = re.findall(r'https?://[^\s]+', user_text)
    msg_type = "url" if urls else "text"
    
    print(f"[收到訊息] User: {user_id}, Type: {msg_type}, Content: {user_text[:50]}...")
    
    # 使用 Bedrock 分析詐騙風險
    analysis_result = analyze_scam_content(user_text)
    
    # 儲存到資料庫
    record = ScamDetectionRecord(
        user_id=user_id,
        input_content=user_text,
        risk_score=analysis_result['risk_score'],
        category=analysis_result['category'],
        analysis=analysis_result['analysis'],
        expert_warning=analysis_result['expert_warning']
    )
    add_detection_record(record)
    
    # 新增：團隊積分計算（僅當訊息包含 URL 時）
    team_result = None
    mass_report_context = None
    if urls:
        team_result = update_team_points_for_report(
            reporter_uid=user_id,
            url=urls[0],  # 取第一個 URL
            risk_score=analysis_result['risk_score'],
            category=analysis_result['category']
        )
        mass_report_context = build_mass_report_context(
            reporter_uid=user_id,
            url=urls[0],
            risk_score=analysis_result['risk_score'],
            category=analysis_result['category'],
            team_result=team_result
        )
    
    # 修改回覆訊息，加入團隊積分資訊
    if team_result and team_result.get('points_earned', 0) > 0:
        reply_text = format_reply_with_team_points(analysis_result, team_result)
    else:
        reply_text = format_reply_message(analysis_result)
    
    reply_message(event.reply_token, reply_text)

    if mass_report_context:
        trigger_mass_report_check(**mass_report_context)

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image(event):
    """處理圖片訊息"""
    user_id = event.source.user_id
    
    with ApiClient(configuration) as api_client:
        line_bot_blob = MessagingApiBlob(api_client)
        image_content = line_bot_blob.get_message_content(event.message.id)
        
        # 轉換為 Base64
        base64_image = base64.b64encode(image_content).decode('utf-8')
        
        print(f"[收到圖片] User: {user_id}, Base64 長度: {len(base64_image)}")
        
        # TODO: 未來可以加入圖片 OCR 或視覺分析
        # 目前先回覆已接收
        reply_message(event.reply_token, "✅ 已接收圖片！\n\n目前系統專注於文字詐騙分析，圖片分析功能即將推出。")

# ==================== 輔助函數 ====================

def save_scam_report(reporter_uid: str, url: str, normalized_url: str, risk_score: int, category: str) -> dict:
    """為非團隊使用者寫入 ScamReports 記錄。"""
    scam_reports_table = dynamodb.Table('ScamReports')
    now = datetime.now()
    report_id = f"{reporter_uid}#{now.isoformat()}"

    scam_reports_table.put_item(
        Item={
            'report_id': report_id,
            'url': url,
            'normalized_url': normalized_url,
            'reporter_uid': reporter_uid,
            'team_id': None,
            'risk_score': risk_score,
            'category': category,
            'multiplier_applied': False,
            'points_earned': 0,
            'reported_at': now.isoformat()
        }
    )

    return {
        'success': True,
        'points_earned': 0,
        'is_duplicate': False,
        'multiplier_applied': False,
        'normalized_url': normalized_url,
        'report_id': report_id,
        'message': '成功通報，已記錄至系統'
    }


def build_mass_report_context(reporter_uid: str, url: str, risk_score: int, category: str, team_result: dict | None) -> dict | None:
    """建立大量通報檢查所需的上下文。"""
    normalized_url = team_result.get('normalized_url') if team_result else None

    if team_result and normalized_url and team_result.get('report_id') and not team_result.get('is_duplicate'):
        return {'normalized_url': normalized_url}

    if team_result and team_result.get('is_duplicate'):
        return None

    if team_result:
        return None

    from points_calculator import PointsCalculator

    calculator = PointsCalculator()
    normalized_url = calculator.normalize_url(url)
    save_scam_report(
        reporter_uid=reporter_uid,
        url=url,
        normalized_url=normalized_url,
        risk_score=risk_score,
        category=category
    )
    return {'normalized_url': normalized_url}


def trigger_mass_report_check(normalized_url: str) -> None:
    """非阻塞觸發大量通報檢查。"""
    current_report_count = get_report_count(normalized_url)

    def _run_mass_report() -> None:
        try:
            result = process_mass_report(
                normalized_url=normalized_url,
                current_report_count=current_report_count
            )
            logger.info("Mass report background processing completed: result=%s", result)
        except Exception as e:
            logger.exception("Mass report background processing failed: error=%s", e)

    threading.Thread(target=_run_mass_report, daemon=True).start()

def update_team_points_for_report(reporter_uid: str, url: str, risk_score: int, category: str) -> dict:
    """
    查詢使用者所屬團隊並更新團隊積分
    
    Args:
        reporter_uid: 通報者的 LINE UID
        url: 通報的 URL
        risk_score: 風險評分
        category: 詐騙類別
        
    Returns:
        dict: 積分更新結果，若使用者不屬於任何團隊則回傳 None
    """
    from points_calculator import PointsCalculator
    
    try:
        # 查詢使用者所屬團隊（使用 LineUidIndex GSI）
        team_members_table = team_service.team_members_table
        response = team_members_table.query(
            IndexName='LineUidIndex',
            KeyConditionExpression='line_uid = :uid',
            ExpressionAttributeValues={':uid': reporter_uid},
            Limit=1
        )
        
        items = response.get('Items', [])
        
        if not items:
            # 使用者不屬於任何團隊，不更新積分
            print(f"[團隊積分] User {reporter_uid} 不屬於任何團隊")
            return None
        
        # 取得團隊 ID
        team_id = items[0]['team_id']
        print(f"[團隊積分] User {reporter_uid} 屬於團隊 {team_id}")
        
        # 呼叫 PointsCalculator 更新積分
        calculator = PointsCalculator()
        result = calculator.update_team_points(
            team_id=team_id,
            member_uid=reporter_uid,
            url=url,
            risk_score=risk_score,
            category=category
        )
        
        print(f"[團隊積分] 更新結果: {result}")
        
        # 檢查每日任務完成狀態（僅在積分更新成功時檢查）
        if result and result.get('success'):
            quest_result = calculator.check_daily_quest(team_id=team_id)
            print(f"[每日任務] 檢測結果: {quest_result}")
            
            # 將任務結果附加到 result 中，供回覆訊息使用
            result['quest_result'] = quest_result
        
        return result
        
    except Exception as e:
        # 積分更新失敗不應影響主流程，記錄錯誤但繼續
        print(f"[團隊積分] 更新失敗: {str(e)}")
        return None

def reply_message(token: str, text: str):
    """回覆 LINE 訊息"""
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=token,
                messages=[TextMessage(text=text)]
            )
        )

def format_reply_message(analysis: dict) -> str:
    """格式化回覆訊息"""
    score = analysis['risk_score']
    category = analysis['category']
    warning = analysis['expert_warning']
    
    # 風險等級表情符號
    if score >= 7:
        emoji = "🚨"
        level = "高風險"
    elif score >= 4:
        emoji = "⚠️"
        level = "中風險"
    else:
        emoji = "✅"
        level = "低風險"
    
    reply = f"""{emoji} 防詐風險評估報告

風險評分：{score}/10 ({level})
詐騙類別：{category}

💡 專員警示：
{warning}

📊 查看完整分析記錄，請點選下方選單「我的儀表板」

🏆 團隊功能：
• 建立團隊與好友一起通報詐騙
• 累積團隊積分爭奪排行榜
👉 {LIFF_URL_TEAM_MANAGEMENT}
"""
    
    return reply

def format_reply_with_team_points(analysis: dict, team_result: dict) -> str:
    """
    格式化包含團隊積分資訊的回覆訊息
    
    Args:
        analysis: Bedrock AI 分析結果
        team_result: 團隊積分更新結果
        
    Returns:
        str: 格式化的回覆訊息
    """
    score = analysis['risk_score']
    category = analysis['category']
    warning = analysis['expert_warning']
    
    # 風險等級表情符號
    if score >= 7:
        emoji = "🚨"
        level = "高風險"
    elif score >= 4:
        emoji = "⚠️"
        level = "中風險"
    else:
        emoji = "✅"
        level = "低風險"
    
    # 基本回覆訊息
    reply = f"""{emoji} 防詐風險評估報告

風險評分：{score}/10 ({level})
詐騙類別：{category}

💡 專員警示：
{warning}
"""
    
    # 加入團隊積分資訊
    if team_result.get('success'):
        points_earned = team_result.get('points_earned', 0)
        multiplier_applied = team_result.get('multiplier_applied', False)
        
        reply += f"""
🏆 團隊積分更新
✅ 成功通報！您的團隊獲得 {points_earned} 積分"""
        
        if multiplier_applied:
            reply += " (極高風險 2x 獎勵)"
        
        reply += "\n"
        
        # 加入每日任務完成通知
        quest_result = team_result.get('quest_result')
        if quest_result and quest_result.get('quest_completed') and not quest_result.get('already_claimed'):
            bonus_awarded = quest_result.get('bonus_awarded', 0)
            reply += f"""
🎉 每日任務完成！
恭喜！團隊今日已通報 5 則 URL，獲得 {bonus_awarded} 點獎勵積分！
"""
    elif team_result.get('is_duplicate'):
        reply += """
🏆 團隊積分更新
ℹ️ 此 URL 已被通報，未獲得積分
"""
    
    reply += f"""
📊 查看完整分析記錄，請點選下方選單「我的儀表板」

🏆 查看團隊資訊與排行榜：
👉 {LIFF_URL_TEAM_MANAGEMENT}
"""
    
    return reply

# ==================== 啟動伺服器 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
