# points_calculator.py
from typing import Dict, Optional
from urllib.parse import urlparse


class PointsCalculator:
    """積分計算器，負責團隊積分計算與重複檢測"""
    
    def normalize_url(self, url: str) -> str:
        """標準化 URL（移除 query parameters 與 trailing slash，轉換為小寫）
        
        Args:
            url: 原始 URL
            
        Returns:
            標準化後的 URL
            
        Example:
            >>> calc = PointsCalculator()
            >>> calc.normalize_url("https://Example.com/Path?query=123")
            'https://example.com/path'
            >>> calc.normalize_url("https://scam-site.com/fake-investment/?ref=abc")
            'https://scam-site.com/fake-investment'
        """
        parsed = urlparse(url)
        # 組合標準化 URL：scheme + netloc + path（移除 trailing slash）
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
        # 轉換為小寫
        return normalized.lower()
    
    def check_duplicate(self, normalized_url: str) -> bool:
        """檢查 URL 是否已被通報
        
        Args:
            normalized_url: 標準化後的 URL
            
        Returns:
            True 如果 URL 已被通報，False 否則
        """
        from database import get_dynamodb_resource
        dynamodb = get_dynamodb_resource()
        
        # 取得 ScamReports 表
        scam_reports_table = dynamodb.Table('ScamReports')
        
        # 使用 NormalizedUrlIndex GSI 查詢
        response = scam_reports_table.query(
            IndexName='NormalizedUrlIndex',
            KeyConditionExpression='normalized_url = :url',
            ExpressionAttributeValues={
                ':url': normalized_url
            },
            Limit=1  # 只需要知道是否存在，不需要所有記錄
        )
        
        # 如果有任何記錄，表示已被通報
        return len(response.get('Items', [])) > 0
    
    def calculate_points(self, risk_score: int) -> int:
        """計算積分（含倍數獎勵）
        
        Args:
            risk_score: 風險評分 (1-10)
            
        Returns:
            計算後的積分
        """
        # 極高風險 (risk_score >= 9) 給予 2x 倍數獎勵
        if risk_score >= 9:
            return risk_score * 2
        return risk_score
    
    def update_team_points(self, team_id: str, member_uid: str, 
                          url: str, risk_score: int, category: str = "未分類") -> Dict:
        """更新團隊與成員積分
        
        Args:
            team_id: 團隊 ID
            member_uid: 成員 LINE UID
            url: 通報的 URL
            risk_score: 風險評分
            category: 詐騙類別（預設為"未分類"）
            
        Returns:
            包含積分更新結果的字典，格式：
            {
                'success': bool,
                'points_earned': int,
                'is_duplicate': bool,
                'multiplier_applied': bool,
                'normalized_url': str,
                'report_id': str (如果成功)
            }
        """
        from database import get_dynamodb_resource
        from datetime import datetime
        dynamodb = get_dynamodb_resource()
        
        # 1. 標準化 URL
        normalized_url = self.normalize_url(url)
        
        # 2. 檢查重複
        is_duplicate = self.check_duplicate(normalized_url)
        
        if is_duplicate:
            # 重複通報，不給予積分
            return {
                'success': False,
                'points_earned': 0,
                'is_duplicate': True,
                'multiplier_applied': False,
                'normalized_url': normalized_url,
                'message': '此 URL 已被通報'
            }
        
        # 3. 計算積分
        points_earned = self.calculate_points(risk_score)
        multiplier_applied = (risk_score >= 9)
        
        # 4. 更新 Teams.total_points（使用原子性計數器）
        teams_table = dynamodb.Table('Teams')
        try:
            teams_table.update_item(
                Key={'team_id': team_id},
                UpdateExpression='ADD total_points :points',
                ExpressionAttributeValues={':points': points_earned}
            )
        except Exception as e:
            return {
                'success': False,
                'points_earned': 0,
                'is_duplicate': False,
                'multiplier_applied': False,
                'normalized_url': normalized_url,
                'error': f'更新團隊積分失敗: {str(e)}'
            }
        
        # 5. 更新 TeamMembers.contribution_points（使用原子性計數器）
        team_members_table = dynamodb.Table('TeamMembers')
        member_id = f"{team_id}#{member_uid}"
        try:
            team_members_table.update_item(
                Key={'member_id': member_id},
                UpdateExpression='ADD contribution_points :points, report_count :count',
                ExpressionAttributeValues={
                    ':points': points_earned,
                    ':count': 1
                }
            )
        except Exception as e:
            # 如果更新成員積分失敗，嘗試回滾團隊積分（盡力而為）
            try:
                teams_table.update_item(
                    Key={'team_id': team_id},
                    UpdateExpression='ADD total_points :points',
                    ExpressionAttributeValues={':points': -points_earned}
                )
            except:
                pass  # 回滾失敗，記錄錯誤但不中斷
            
            return {
                'success': False,
                'points_earned': 0,
                'is_duplicate': False,
                'multiplier_applied': False,
                'normalized_url': normalized_url,
                'error': f'更新成員積分失敗: {str(e)}'
            }
        
        # 6. 寫入 ScamReports 表記錄通報
        scam_reports_table = dynamodb.Table('ScamReports')
        now = datetime.now()
        report_id = f"{member_uid}#{now.isoformat()}"
        
        try:
            scam_reports_table.put_item(
                Item={
                    'report_id': report_id,
                    'url': url,
                    'normalized_url': normalized_url,
                    'reporter_uid': member_uid,
                    'team_id': team_id,
                    'risk_score': risk_score,
                    'category': category,
                    'multiplier_applied': multiplier_applied,
                    'points_earned': points_earned,
                    'reported_at': now.isoformat()
                }
            )
        except Exception as e:
            # 寫入通報記錄失敗，但積分已更新，返回部分成功
            return {
                'success': True,  # 積分更新成功
                'points_earned': points_earned,
                'is_duplicate': False,
                'multiplier_applied': multiplier_applied,
                'normalized_url': normalized_url,
                'report_id': report_id,
                'warning': f'通報記錄寫入失敗: {str(e)}'
            }
        
        # 全部成功
        return {
            'success': True,
            'points_earned': points_earned,
            'is_duplicate': False,
            'multiplier_applied': multiplier_applied,
            'normalized_url': normalized_url,
            'report_id': report_id,
            'message': f'成功通報！獲得 {points_earned} 積分' + (' (極高風險 2x 獎勵)' if multiplier_applied else '')
        }


    def check_daily_quest(self, team_id: str) -> Dict:
        """檢查並處理每日任務完成狀態

        檢查團隊當日是否達成「單日通報 5 則 URL」任務，
        若達成且尚未領取獎勵，則給予 50 點獎勵積分。

        Args:
            team_id: 團隊 ID

        Returns:
            包含任務檢測結果的字典，格式：
            {
                'quest_completed': bool,  # 是否完成任務
                'already_claimed': bool,  # 是否已領取獎勵
                'bonus_awarded': int,     # 獎勵積分（0 或 50）
                'daily_report_count': int,  # 當日通報數量
                'message': str            # 結果訊息
            }
        """
        from database import get_dynamodb_resource
        from datetime import datetime, timezone
        dynamodb = get_dynamodb_resource()

        # 取得今日日期（UTC）
        today = datetime.now(timezone.utc).date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()
        today_end = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc).isoformat()

        # 產生今日任務 ID（格式：daily_5_reports_YYYY-MM-DD）
        quest_id = f"daily_5_reports_{today.isoformat()}"

        # 1. 查詢團隊資訊，檢查是否已完成此任務
        teams_table = dynamodb.Table('Teams')
        try:
            team_response = teams_table.get_item(Key={'team_id': team_id})
            team_data = team_response.get('Item')

            if not team_data:
                return {
                    'quest_completed': False,
                    'already_claimed': False,
                    'bonus_awarded': 0,
                    'daily_report_count': 0,
                    'message': '團隊不存在'
                }

            # 檢查 completed_quests 欄位
            completed_quests = team_data.get('completed_quests', [])
            if quest_id in completed_quests:
                # 今日任務已完成並領取獎勵
                return {
                    'quest_completed': True,
                    'already_claimed': True,
                    'bonus_awarded': 0,
                    'daily_report_count': 0,  # 不需要查詢
                    'message': '今日任務已完成'
                }
        except Exception as e:
            return {
                'quest_completed': False,
                'already_claimed': False,
                'bonus_awarded': 0,
                'daily_report_count': 0,
                'error': f'查詢團隊資訊失敗: {str(e)}'
            }

        # 2. 查詢團隊當日通報數量（使用 TeamIdIndex GSI）
        scam_reports_table = dynamodb.Table('ScamReports')
        try:
            response = scam_reports_table.query(
                IndexName='TeamIdIndex',
                KeyConditionExpression='team_id = :tid AND reported_at BETWEEN :start AND :end',
                ExpressionAttributeValues={
                    ':tid': team_id,
                    ':start': today_start,
                    ':end': today_end
                }
            )

            daily_report_count = len(response.get('Items', []))

        except Exception as e:
            return {
                'quest_completed': False,
                'already_claimed': False,
                'bonus_awarded': 0,
                'daily_report_count': 0,
                'error': f'查詢通報記錄失敗: {str(e)}'
            }

        # 3. 檢查是否達成任務條件（5 則通報）
        if daily_report_count < 5:
            return {
                'quest_completed': False,
                'already_claimed': False,
                'bonus_awarded': 0,
                'daily_report_count': daily_report_count,
                'message': f'當日通報 {daily_report_count}/5 則，尚未達成任務'
            }

        # 4. 達成任務，給予獎勵並更新 completed_quests
        bonus_points = 50
        try:
            teams_table.update_item(
                Key={'team_id': team_id},
                UpdateExpression='ADD total_points :bonus SET completed_quests = list_append(if_not_exists(completed_quests, :empty_list), :quest)',
                ExpressionAttributeValues={
                    ':bonus': bonus_points,
                    ':quest': [quest_id],
                    ':empty_list': []
                }
            )

            return {
                'quest_completed': True,
                'already_claimed': False,
                'bonus_awarded': bonus_points,
                'daily_report_count': daily_report_count,
                'message': f'🎉 完成每日任務！團隊獲得 {bonus_points} 點獎勵積分'
            }

        except Exception as e:
            return {
                'quest_completed': True,
                'already_claimed': False,
                'bonus_awarded': 0,
                'daily_report_count': daily_report_count,
                'error': f'更新任務獎勵失敗: {str(e)}'
            }
