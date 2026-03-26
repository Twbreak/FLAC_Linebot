#!/usr/bin/env python3
"""
測試腳本：產生團隊邀請連結
"""

from team_service import TeamService

# 初始化團隊服務
team_service = TeamService()

# 你的團隊 ID 和 LINE UID
team_id = "82d9f298-c492-4356-b1d3-8569e41b03a3"
inviter_uid = "U8933f07c168af61985f11cc8a56b7292"

# 產生邀請連結
try:
    invite_url = team_service.invite_member(team_id, inviter_uid)
    print("=" * 80)
    print("團隊邀請連結已產生：")
    print("=" * 80)
    print(invite_url)
    print("=" * 80)
    print("\n請將上面的完整連結複製並傳給好友。")
    print("好友點擊連結後應該會看到「🎉 加入團隊邀請」頁面。")
except Exception as e:
    print(f"產生邀請連結失敗: {str(e)}")
