#!/usr/bin/env python3
"""
示範 join_team() 功能
展示加入團隊的完整流程
"""

import uuid
from team_service import TeamService
from security import SecurityService
from database import create_team_tables_if_not_exist

def main():
    print("=" * 60)
    print("🚀 示範：加入團隊功能")
    print("=" * 60)
    
    # 1. 初始化服務
    print("\n📦 初始化服務...")
    create_team_tables_if_not_exist()
    team_service = TeamService()
    security_service = SecurityService()
    print("✅ 服務初始化完成")
    
    # 2. 建立測試團隊
    print("\n👥 建立測試團隊...")
    leader_uid = f"U_DEMO_LEADER_{uuid.uuid4().hex[:8]}"
    team_name = "防詐先鋒隊"
    
    try:
        team = team_service.create_team(leader_uid, team_name)
        print(f"✅ 團隊建立成功！")
        print(f"   - Team ID: {team.team_id}")
        print(f"   - 團隊名稱: {team.team_name}")
        print(f"   - 隊長 UID: {team.leader_uid}")
        print(f"   - 成員數: {team.member_count}")
    except Exception as e:
        print(f"❌ 建立團隊失敗: {e}")
        return
    
    # 3. 產生邀請連結
    print("\n🔗 產生邀請連結...")
    try:
        invite_url = team_service.invite_member(team.team_id, leader_uid)
        print(f"✅ 邀請連結產生成功！")
        print(f"   {invite_url}")
        
        # 解析簽章
        signature = invite_url.split("signature=")[1]
        print(f"   - 簽章: {signature[:30]}...")
    except Exception as e:
        print(f"❌ 產生邀請連結失敗: {e}")
        return
    
    # 4. 新成員加入團隊
    print("\n👤 新成員加入團隊...")
    member_uid = f"U_DEMO_MEMBER_{uuid.uuid4().hex[:8]}"
    
    try:
        result = team_service.join_team(team.team_id, member_uid, signature)
        if result:
            print(f"✅ 成員加入成功！")
            print(f"   - 成員 UID: {member_uid}")
        else:
            print(f"❌ 成員加入失敗")
    except Exception as e:
        print(f"❌ 加入團隊失敗: {e}")
        return
    
    # 5. 驗證團隊資訊
    print("\n📊 驗證團隊資訊...")
    try:
        team_info = team_service.get_team_info(team.team_id)
        if team_info:
            print(f"✅ 團隊資訊查詢成功！")
            print(f"   - 團隊名稱: {team_info.team_name}")
            print(f"   - 成員數: {team_info.member_count}")
            print(f"   - 總積分: {team_info.total_points}")
        else:
            print(f"❌ 找不到團隊資訊")
    except Exception as e:
        print(f"⚠️  查詢團隊資訊失敗: {e}")
    
    # 6. 測試錯誤情境
    print("\n🧪 測試錯誤情境...")
    
    # 6.1 測試無效簽章
    print("\n   測試 1: 無效簽章")
    try:
        team_service.join_team(team.team_id, f"U_TEST_{uuid.uuid4().hex[:8]}", "invalid_signature")
        print("   ❌ 應該要拒絕無效簽章")
    except ValueError as e:
        print(f"   ✅ 正確拒絕: {e}")
    
    # 6.2 測試重複加入
    print("\n   測試 2: 重複加入同一團隊")
    try:
        team_service.join_team(team.team_id, member_uid, signature)
        print("   ❌ 應該要拒絕重複加入")
    except ValueError as e:
        print(f"   ✅ 正確拒絕: {e}")
    
    # 6.3 測試加入不存在的團隊
    print("\n   測試 3: 加入不存在的團隊")
    fake_team_id = str(uuid.uuid4())
    fake_signature = security_service.generate_signature(fake_team_id)
    try:
        team_service.join_team(fake_team_id, f"U_TEST_{uuid.uuid4().hex[:8]}", fake_signature)
        print("   ❌ 應該要拒絕加入不存在的團隊")
    except ValueError as e:
        print(f"   ✅ 正確拒絕: {e}")
    
    # 6.4 測試跨團隊加入
    print("\n   測試 4: 跨團隊加入")
    try:
        # 建立第二個團隊
        leader_uid_2 = f"U_DEMO_LEADER2_{uuid.uuid4().hex[:8]}"
        team2 = team_service.create_team(leader_uid_2, "第二個團隊")
        signature2 = security_service.generate_signature(team2.team_id)
        
        # 嘗試讓已在第一個團隊的成員加入第二個團隊
        team_service.join_team(team2.team_id, member_uid, signature2)
        print("   ❌ 應該要拒絕跨團隊加入")
    except ValueError as e:
        print(f"   ✅ 正確拒絕: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 示範完成！join_team() 功能運作正常")
    print("=" * 60)


if __name__ == "__main__":
    main()
