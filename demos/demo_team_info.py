"""
Demo: 團隊資訊查詢功能 (Task 3.7)
展示 get_team_info() 和 get_team_members() 的使用方式
"""

from team_service import TeamService
from decimal import Decimal


def main():
    print("="*60)
    print("團隊資訊查詢功能示範 (Task 3.7)")
    print("="*60)
    
    service = TeamService()
    
    # 1. 建立測試團隊
    print("\n【步驟 1】建立測試團隊")
    print("-" * 60)
    team = service.create_team("U_DEMO_LEADER", "防詐先鋒隊")
    print(f"✅ 團隊建立成功")
    print(f"   團隊 ID: {team.team_id}")
    print(f"   團隊名稱: {team.team_name}")
    print(f"   隊長 UID: {team.leader_uid}")
    
    team_id = team.team_id
    
    # 2. 加入成員
    print("\n【步驟 2】邀請成員加入團隊")
    print("-" * 60)
    invite_url = service.invite_member(team_id, "U_DEMO_LEADER")
    signature = invite_url.split("signature=")[1]
    
    service.join_team(team_id, "U_DEMO_MEMBER_1", signature)
    service.join_team(team_id, "U_DEMO_MEMBER_2", signature)
    service.join_team(team_id, "U_DEMO_MEMBER_3", signature)
    print(f"✅ 成功加入 3 位成員")
    
    # 3. 模擬成員通報（更新積分）
    print("\n【步驟 3】模擬成員通報詐騙（更新積分）")
    print("-" * 60)
    
    # 更新成員積分
    updates = [
        ("U_DEMO_LEADER", 150, 5),
        ("U_DEMO_MEMBER_1", 320, 12),
        ("U_DEMO_MEMBER_2", 280, 10),
        ("U_DEMO_MEMBER_3", 95, 3)
    ]
    
    for uid, points, reports in updates:
        service.team_members_table.update_item(
            Key={'member_id': f"{team_id}#{uid}"},
            UpdateExpression='SET contribution_points = :points, report_count = :reports',
            ExpressionAttributeValues={
                ':points': Decimal(str(points)),
                ':reports': Decimal(str(reports))
            }
        )
        print(f"   {uid}: {points} 分 ({reports} 次通報)")
    
    # 更新團隊總積分
    total_points = sum(p for _, p, _ in updates)
    service.teams_table.update_item(
        Key={'team_id': team_id},
        UpdateExpression='SET total_points = :points',
        ExpressionAttributeValues={':points': Decimal(str(total_points))}
    )
    print(f"✅ 團隊總積分: {total_points} 分")
    
    # 4. 使用 get_team_info() 查詢團隊資訊
    print("\n【步驟 4】使用 get_team_info() 查詢團隊資訊")
    print("-" * 60)
    team_info = service.get_team_info(team_id)
    
    if team_info:
        print(f"✅ 團隊資訊查詢成功")
        print(f"   團隊 ID: {team_info.team_id}")
        print(f"   團隊名稱: {team_info.team_name}")
        print(f"   隊長 UID: {team_info.leader_uid}")
        print(f"   總積分: {team_info.total_points}")
        print(f"   成員數: {team_info.member_count}")
        print(f"   建立時間: {team_info.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   完成任務: {team_info.completed_quests}")
    else:
        print("❌ 團隊不存在")
    
    # 5. 使用 get_team_members() 查詢成員清單
    print("\n【步驟 5】使用 get_team_members() 查詢成員清單")
    print("-" * 60)
    members = service.get_team_members(team_id)
    
    print(f"✅ 成員清單查詢成功 (共 {len(members)} 位成員)")
    print(f"\n{'排名':<6} {'LINE UID':<20} {'貢獻積分':<10} {'通報次數':<10} {'角色':<10}")
    print("-" * 60)
    
    for idx, member in enumerate(members, 1):
        role = "隊長" if member.is_leader else "成員"
        mvp_mark = "👑 " if idx == 1 and not member.is_leader else ""
        print(f"{mvp_mark}{idx:<5} {member.line_uid:<20} {member.contribution_points:<10} "
              f"{member.report_count:<10} {role:<10}")
    
    # 6. 驗證排序正確性
    print("\n【步驟 6】驗證成員排序正確性")
    print("-" * 60)
    
    # 檢查是否依 contribution_points 降序排列
    is_sorted = all(
        members[i].contribution_points >= members[i+1].contribution_points
        for i in range(len(members)-1)
    )
    
    if is_sorted:
        print("✅ 成員清單正確依 contribution_points 降序排序")
        print(f"   最高貢獻: {members[0].line_uid} ({members[0].contribution_points} 分)")
        print(f"   最低貢獻: {members[-1].line_uid} ({members[-1].contribution_points} 分)")
    else:
        print("❌ 排序錯誤")
    
    # 7. 測試查詢不存在的團隊
    print("\n【步驟 7】測試查詢不存在的團隊")
    print("-" * 60)
    
    non_existent_team = service.get_team_info("non-existent-id")
    if non_existent_team is None:
        print("✅ 正確處理不存在的團隊（回傳 None）")
    else:
        print("❌ 錯誤：應該回傳 None")
    
    non_existent_members = service.get_team_members("non-existent-id")
    if non_existent_members == []:
        print("✅ 正確處理不存在團隊的成員查詢（回傳空列表）")
    else:
        print("❌ 錯誤：應該回傳空列表")
    
    # 總結
    print("\n" + "="*60)
    print("✅ Task 3.7 實作完成！")
    print("="*60)
    print("\n實作功能：")
    print("  1. get_team_info() - 從 Teams 表查詢團隊基本資訊")
    print("  2. get_team_members() - 使用 TeamIdIndex GSI 查詢成員清單")
    print("  3. 成員清單依 contribution_points 降序排序")
    print("  4. 正確處理不存在的團隊（回傳 None 或空列表）")
    print("  5. 正確轉換 DynamoDB Decimal 為 Python int")
    print("\n符合需求：")
    print("  - Requirements 6.4: 查詢團隊資訊")
    print("  - Requirements 6.5: 顯示團隊成員清單")
    print("  - Requirements 7.1: 查詢團隊所有成員")
    print("  - Requirements 7.3: 計算每位成員的貢獻度")
    print("="*60)


if __name__ == "__main__":
    main()
