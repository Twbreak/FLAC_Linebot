"""
Demo: Webhook Handler 與團隊積分整合
展示當團隊成員通報詐騙 URL 時，系統如何自動更新團隊積分
"""

import sys
import os
from datetime import datetime

# 將專案根目錄加入 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from team_service import TeamService
from points_calculator import PointsCalculator
from main import update_team_points_for_report, format_reply_with_team_points


def demo_webhook_team_integration():
    """展示 webhook handler 與團隊積分整合"""
    
    print("=" * 80)
    print("Demo: Webhook Handler 與團隊積分整合")
    print("=" * 80)
    print()
    
    # 初始化服務
    team_service = TeamService()
    calculator = PointsCalculator()
    
    # 步驟 1: 建立測試團隊
    print("步驟 1: 建立測試團隊")
    print("-" * 80)
    
    try:
        team = team_service.create_team(
            leader_uid="U_DEMO_LEADER_001",
            team_name="防詐先鋒隊 Demo"
        )
        print(f"✅ 團隊建立成功")
        print(f"   團隊 ID: {team.team_id}")
        print(f"   團隊名稱: {team.team_name}")
        print(f"   隊長 UID: {team.leader_uid}")
        print()
    except ValueError as e:
        print(f"⚠️  團隊已存在，使用現有團隊")
        # 查詢現有團隊
        from database import dynamodb
        teams_table = dynamodb.Table('Teams')
        response = teams_table.scan(
            FilterExpression='leader_uid = :uid',
            ExpressionAttributeValues={':uid': 'U_DEMO_LEADER_001'}
        )
        if response.get('Items'):
            team_data = response['Items'][0]
            team_id = team_data['team_id']
            print(f"   團隊 ID: {team_id}")
            print(f"   團隊名稱: {team_data['team_name']}")
            print()
            
            # 建立 Team 物件
            from models import Team
            team = Team(
                team_id=team_id,
                team_name=team_data['team_name'],
                leader_uid=team_data['leader_uid'],
                total_points=team_data.get('total_points', 0),
                member_count=team_data.get('member_count', 1),
                created_at=datetime.fromisoformat(team_data['created_at']),
                completed_quests=team_data.get('completed_quests', [])
            )
        else:
            print("❌ 無法找到團隊")
            return
    
    # 步驟 2: 加入第二位成員
    print("步驟 2: 加入第二位成員")
    print("-" * 80)
    
    try:
        # 產生邀請連結
        invite_url = team_service.invite_member(
            team_id=team.team_id,
            inviter_uid=team.leader_uid
        )
        
        # 解析簽章
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(invite_url)
        params = parse_qs(parsed.query)
        signature = params['signature'][0]
        
        # 加入團隊
        success = team_service.join_team(
            team_id=team.team_id,
            member_uid="U_DEMO_MEMBER_002",
            signature=signature
        )
        
        if success:
            print(f"✅ 成員加入成功")
            print(f"   成員 UID: U_DEMO_MEMBER_002")
            print()
    except ValueError as e:
        if "已經是團隊成員" in str(e):
            print(f"⚠️  成員已在團隊中")
            print()
        else:
            print(f"❌ 加入失敗: {e}")
            return
    
    # 步驟 3: 模擬隊長通報詐騙 URL（首次通報，高風險）
    print("步驟 3: 隊長通報詐騙 URL（首次通報，高風險 9 分）")
    print("-" * 80)
    
    url1 = "https://fake-investment-scam.com/invest?ref=demo123"
    risk_score1 = 9
    category1 = "假投資詐騙"
    
    result1 = update_team_points_for_report(
        reporter_uid=team.leader_uid,
        url=url1,
        risk_score=risk_score1,
        category=category1
    )
    
    if result1:
        print(f"✅ 積分更新成功")
        print(f"   通報 URL: {url1}")
        print(f"   風險評分: {risk_score1}/10")
        print(f"   獲得積分: {result1.get('points_earned', 0)}")
        print(f"   倍數獎勵: {'是' if result1.get('multiplier_applied') else '否'}")
        print(f"   是否重複: {'是' if result1.get('is_duplicate') else '否'}")
        print()
        
        # 顯示回覆訊息
        analysis1 = {
            'risk_score': risk_score1,
            'category': category1,
            'analysis': '這是一個高風險的假投資詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        reply1 = format_reply_with_team_points(analysis1, result1)
        print("📱 LINE Bot 回覆訊息:")
        print("-" * 80)
        print(reply1)
        print()
    else:
        print(f"⚠️  使用者不屬於任何團隊，未更新積分")
        print()
    
    # 步驟 4: 模擬成員通報詐騙 URL（首次通報，中風險）
    print("步驟 4: 成員通報詐騙 URL（首次通報，中風險 6 分）")
    print("-" * 80)
    
    url2 = "https://phishing-site.com/login?target=bank"
    risk_score2 = 6
    category2 = "釣魚網站"
    
    result2 = update_team_points_for_report(
        reporter_uid="U_DEMO_MEMBER_002",
        url=url2,
        risk_score=risk_score2,
        category=category2
    )
    
    if result2:
        print(f"✅ 積分更新成功")
        print(f"   通報 URL: {url2}")
        print(f"   風險評分: {risk_score2}/10")
        print(f"   獲得積分: {result2.get('points_earned', 0)}")
        print(f"   倍數獎勵: {'是' if result2.get('multiplier_applied') else '否'}")
        print(f"   是否重複: {'是' if result2.get('is_duplicate') else '否'}")
        print()
        
        # 顯示回覆訊息
        analysis2 = {
            'risk_score': risk_score2,
            'category': category2,
            'analysis': '這是一個中風險的釣魚網站',
            'expert_warning': '請小心查證，勿輸入帳號密碼'
        }
        reply2 = format_reply_with_team_points(analysis2, result2)
        print("📱 LINE Bot 回覆訊息:")
        print("-" * 80)
        print(reply2)
        print()
    
    # 步驟 5: 模擬重複通報（應該不獲得積分）
    print("步驟 5: 成員重複通報相同 URL（應該不獲得積分）")
    print("-" * 80)
    
    result3 = update_team_points_for_report(
        reporter_uid="U_DEMO_MEMBER_002",
        url=url1,  # 重複通報步驟 3 的 URL
        risk_score=9,
        category=category1
    )
    
    if result3:
        print(f"⚠️  重複通報檢測")
        print(f"   通報 URL: {url1}")
        print(f"   獲得積分: {result3.get('points_earned', 0)}")
        print(f"   是否重複: {'是' if result3.get('is_duplicate') else '否'}")
        print()
        
        # 顯示回覆訊息
        analysis3 = {
            'risk_score': 9,
            'category': category1,
            'analysis': '這是一個高風險的假投資詐騙網站',
            'expert_warning': '請勿點擊連結或提供個人資訊'
        }
        reply3 = format_reply_with_team_points(analysis3, result3)
        print("📱 LINE Bot 回覆訊息:")
        print("-" * 80)
        print(reply3)
        print()
    
    # 步驟 6: 查詢團隊最終積分
    print("步驟 6: 查詢團隊最終積分")
    print("-" * 80)
    
    team_info = team_service.get_team_info(team.team_id)
    if team_info:
        print(f"✅ 團隊資訊")
        print(f"   團隊名稱: {team_info.team_name}")
        print(f"   總積分: {team_info.total_points}")
        print(f"   成員數: {team_info.member_count}")
        print()
    
    # 步驟 7: 查詢成員貢獻度
    print("步驟 7: 查詢成員貢獻度")
    print("-" * 80)
    
    members = team_service.get_team_members(team.team_id)
    if members:
        print(f"✅ 成員清單（依貢獻度排序）")
        for idx, member in enumerate(members, 1):
            role = "隊長" if member.is_leader else "成員"
            print(f"   {idx}. {member.line_uid} ({role})")
            print(f"      貢獻積分: {member.contribution_points}")
            print(f"      通報次數: {member.report_count}")
        print()
    
    print("=" * 80)
    print("Demo 完成！")
    print("=" * 80)


if __name__ == '__main__':
    demo_webhook_team_integration()
