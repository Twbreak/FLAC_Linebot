# team_service.py
"""
團隊管理服務模組
負責團隊建立、成員管理、邀請連結產生等業務邏輯
"""

import uuid
from datetime import datetime
from typing import Optional, List
import boto3
import os
from dotenv import load_dotenv
from decimal import Decimal
from models import Team, TeamMember
from security import SecurityService

# 載入環境變數
load_dotenv()

# DynamoDB 設定
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("aws_access_key_id") or os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("aws_secret_access_key") or os.getenv("AWS_SECRET_ACCESS_KEY")

# 初始化 DynamoDB client
dynamodb = boto3.resource(
    'dynamodb',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)


class TeamService:
    """團隊管理服務類別"""
    
    def __init__(self):
        """初始化團隊服務"""
        self.teams_table = dynamodb.Table('Teams')
        self.team_members_table = dynamodb.Table('TeamMembers')
        self.security_service = SecurityService()
    
    def _convert_decimal_to_int(self, obj):
        """將 Decimal 轉換為 int（DynamoDB 回傳的數字是 Decimal 型別）"""
        if isinstance(obj, list):
            return [self._convert_decimal_to_int(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_int(v) for k, v in obj.items()}
        elif isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        else:
            return obj
    
    def create_team(self, leader_uid: str, team_name: str) -> Team:
        """
        建立新團隊
        
        Args:
            leader_uid: 隊長的 LINE UID
            team_name: 團隊名稱（1-30 字元）
            
        Returns:
            Team: 建立的團隊物件
            
        Raises:
            ValueError: 當使用者已是隊長時
            
        Example:
            >>> service = TeamService()
            >>> team = service.create_team("U1234567890", "防詐先鋒隊")
            >>> print(team.team_id)
            '550e8400-e29b-41d4-a716-446655440000'
        """
        # 檢查使用者是否已是隊長（查詢 Teams 表）
        existing_teams = self.teams_table.scan(
            FilterExpression='leader_uid = :uid',
            ExpressionAttributeValues={':uid': leader_uid}
        )
        
        if existing_teams.get('Items'):
            raise ValueError("您已經是隊長，無法建立多個團隊")
        
        # 產生 UUID 格式的 team_id
        team_id = str(uuid.uuid4())
        created_at = datetime.now()
        
        # 建立團隊物件
        team = Team(
            team_id=team_id,
            team_name=team_name,
            leader_uid=leader_uid,
            total_points=0,
            member_count=1,
            created_at=created_at,
            completed_quests=[]
        )
        
        # 寫入 Teams 表
        self.teams_table.put_item(
            Item={
                'team_id': team.team_id,
                'team_name': team.team_name,
                'leader_uid': team.leader_uid,
                'total_points': team.total_points,
                'member_count': team.member_count,
                'created_at': team.created_at.isoformat(),
                'completed_quests': team.completed_quests
            }
        )
        
        # 寫入 TeamMembers 表（隊長作為首位成員）
        member_id = f"{team_id}#{leader_uid}"
        team_member = TeamMember(
            member_id=member_id,
            team_id=team_id,
            line_uid=leader_uid,
            contribution_points=0,
            report_count=0,
            joined_at=created_at,
            is_leader=True
        )
        
        self.team_members_table.put_item(
            Item={
                'member_id': team_member.member_id,
                'team_id': team_member.team_id,
                'line_uid': team_member.line_uid,
                'contribution_points': team_member.contribution_points,
                'report_count': team_member.report_count,
                'joined_at': team_member.joined_at.isoformat(),
                'is_leader': team_member.is_leader
            }
        )
        
        return team
    
    def invite_member(self, team_id: str, inviter_uid: str) -> str:
        """
        產生邀請連結（含 HMAC 簽章）
        
        Args:
            team_id: 團隊唯一識別碼
            inviter_uid: 邀請者的 LINE UID（用於驗證權限）
            
        Returns:
            str: 包含 team_id 與 signature 的 LIFF URL
            
        Raises:
            ValueError: 當團隊不存在或邀請者不是團隊成員時
            
        Example:
            >>> service = TeamService()
            >>> invite_url = service.invite_member("550e8400-e29b-41d4-a716-446655440000", "U1234567890")
            >>> print(invite_url)
            'https://liff.line.me/2009609029-RlBZuNs2?team_id=550e8400-e29b-41d4-a716-446655440000&signature=abc123...'
        """
        # 驗證團隊是否存在
        try:
            response = self.teams_table.get_item(Key={'team_id': team_id})
            if 'Item' not in response:
                raise ValueError("團隊不存在或已解散")
        except Exception as e:
            raise ValueError(f"查詢團隊失敗: {str(e)}")
        
        # 驗證邀請者是否為團隊成員
        member_id = f"{team_id}#{inviter_uid}"
        try:
            member_response = self.team_members_table.get_item(Key={'member_id': member_id})
            if 'Item' not in member_response:
                raise ValueError("您不是該團隊成員，無法邀請他人")
        except Exception as e:
            raise ValueError(f"驗證成員身分失敗: {str(e)}")
        
        # 使用 SecurityService 產生 HMAC-SHA256 簽章
        signature = self.security_service.generate_signature(team_id)
        
        # 從環境變數讀取 LIFF ID（用於團隊加入頁面）
        liff_id = os.getenv("LIFF_ID_TEAM_JOIN", "2009609029-RlBZuNs2")
        
        # 組合 LIFF URL（使用 liff.state 參數來傳遞 team_id 和 signature）
        # 重要：liff.state 的值需要進行 URL 編碼
        from urllib.parse import quote
        state_params = f"/team.html?team_id={team_id}&signature={signature}"
        encoded_state = quote(state_params, safe='')
        invite_url = f"https://liff.line.me/{liff_id}?liff.state={encoded_state}"
        
        return invite_url
    
    def join_team(self, team_id: str, member_uid: str, signature: str) -> bool:
        """
        加入團隊（驗證簽章）
        
        Args:
            team_id: 團隊唯一識別碼
            member_uid: 加入者的 LINE UID
            signature: HMAC-SHA256 簽章
            
        Returns:
            bool: 加入是否成功
            
        Raises:
            ValueError: 當簽章無效、團隊不存在、使用者已是成員或屬於其他團隊時
            
        Example:
            >>> service = TeamService()
            >>> success = service.join_team("550e8400-e29b-41d4-a716-446655440000", "U9876543210", "abc123...")
            >>> print(success)
            True
        """
        # 1. 驗證 HMAC 簽章
        if not self.security_service.verify_signature(team_id, signature):
            raise ValueError("無效的邀請連結")
        
        # 2. 檢查團隊是否存在
        try:
            team_response = self.teams_table.get_item(Key={'team_id': team_id})
            if 'Item' not in team_response:
                raise ValueError("團隊不存在或已解散")
            team_data = team_response['Item']
        except Exception as e:
            if "團隊不存在" in str(e):
                raise
            raise ValueError(f"查詢團隊失敗: {str(e)}")
        
        # 3. 檢查使用者是否已是該團隊成員
        member_id = f"{team_id}#{member_uid}"
        try:
            existing_member = self.team_members_table.get_item(Key={'member_id': member_id})
            if 'Item' in existing_member:
                raise ValueError("您已經是團隊成員")
        except ValueError:
            raise
        except Exception as e:
            # 查詢失敗但不是因為成員已存在，繼續執行
            pass
        
        # 4. 檢查使用者是否屬於其他團隊（使用 LineUidIndex GSI）
        try:
            other_teams = self.team_members_table.query(
                IndexName='LineUidIndex',
                KeyConditionExpression='line_uid = :uid',
                ExpressionAttributeValues={':uid': member_uid}
            )
            
            if other_teams.get('Items'):
                # 使用者已在其他團隊
                raise ValueError("您已加入其他團隊，請先退出")
        except ValueError:
            raise
        except Exception as e:
            # GSI 查詢失敗，記錄但繼續（避免阻擋正常流程）
            print(f"警告：LineUidIndex 查詢失敗: {str(e)}")
        
        # 5. 寫入 TeamMembers 表
        joined_at = datetime.now()
        team_member = TeamMember(
            member_id=member_id,
            team_id=team_id,
            line_uid=member_uid,
            contribution_points=0,
            report_count=0,
            joined_at=joined_at,
            is_leader=False
        )
        
        try:
            self.team_members_table.put_item(
                Item={
                    'member_id': team_member.member_id,
                    'team_id': team_member.team_id,
                    'line_uid': team_member.line_uid,
                    'contribution_points': team_member.contribution_points,
                    'report_count': team_member.report_count,
                    'joined_at': team_member.joined_at.isoformat(),
                    'is_leader': team_member.is_leader
                }
            )
        except Exception as e:
            raise ValueError(f"加入團隊失敗: {str(e)}")
        
        # 6. 更新 Teams 表的 member_count（使用原子性更新）
        try:
            self.teams_table.update_item(
                Key={'team_id': team_id},
                UpdateExpression='SET member_count = member_count + :inc',
                ExpressionAttributeValues={':inc': 1}
            )
        except Exception as e:
            # 成員已加入但計數更新失敗，記錄錯誤但不回滾
            print(f"警告：更新 member_count 失敗: {str(e)}")
        
        return True
    
    def get_team_info(self, team_id: str) -> Optional[Team]:
        """
        取得團隊資訊
        
        Args:
            team_id: 團隊唯一識別碼
            
        Returns:
            Optional[Team]: 團隊物件，若團隊不存在則回傳 None
            
        Example:
            >>> service = TeamService()
            >>> team = service.get_team_info("550e8400-e29b-41d4-a716-446655440000")
            >>> print(team.team_name)
            '防詐先鋒隊'
        """
        try:
            response = self.teams_table.get_item(Key={'team_id': team_id})
            
            if 'Item' not in response:
                return None
            
            # 轉換 Decimal 為 int
            item = self._convert_decimal_to_int(response['Item'])
            
            # 轉換為 Team 物件
            team = Team(
                team_id=item['team_id'],
                team_name=item['team_name'],
                leader_uid=item['leader_uid'],
                total_points=item.get('total_points', 0),
                member_count=item.get('member_count', 1),
                created_at=datetime.fromisoformat(item['created_at']),
                completed_quests=item.get('completed_quests', [])
            )
            
            return team
        except Exception as e:
            print(f"查詢團隊資訊失敗: {str(e)}")
            return None
    
    def get_team_members(self, team_id: str) -> List[TeamMember]:
        """
        取得團隊成員清單（使用 TeamIdIndex GSI，依 contribution_points 降序排序）
        
        Args:
            team_id: 團隊唯一識別碼
            
        Returns:
            List[TeamMember]: 成員清單，依貢獻積分降序排列
            
        Example:
            >>> service = TeamService()
            >>> members = service.get_team_members("550e8400-e29b-41d4-a716-446655440000")
            >>> for member in members:
            ...     print(f"{member.line_uid}: {member.contribution_points} 分")
            'U1234567890: 450 分'
            'U9876543210: 320 分'
        """
        try:
            # 使用 TeamIdIndex GSI 查詢團隊所有成員
            response = self.team_members_table.query(
                IndexName='TeamIdIndex',
                KeyConditionExpression='team_id = :tid',
                ExpressionAttributeValues={':tid': team_id},
                ScanIndexForward=False  # 降序排列（contribution_points 作為 Sort Key）
            )
            
            items = response.get('Items', [])
            
            # 轉換 Decimal 為 int
            items = self._convert_decimal_to_int(items)
            
            # 轉換為 TeamMember 物件
            members = []
            for item in items:
                member = TeamMember(
                    member_id=item['member_id'],
                    team_id=item['team_id'],
                    line_uid=item['line_uid'],
                    contribution_points=item.get('contribution_points', 0),
                    report_count=item.get('report_count', 0),
                    joined_at=datetime.fromisoformat(item['joined_at']),
                    is_leader=item.get('is_leader', False)
                )
                members.append(member)
            
            return members
        except Exception as e:
            print(f"查詢團隊成員失敗: {str(e)}")
            return []
