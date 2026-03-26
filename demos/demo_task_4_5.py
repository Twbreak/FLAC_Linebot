"""
Task 4.5 示範：積分計算與倍數獎勵

展示極高風險通報如何獲得 2 倍積分獎勵
"""

from points_calculator import PointsCalculator


def demo_points_calculation():
    """示範積分計算功能"""
    calculator = PointsCalculator()
    
    print("="*60)
    print("積分計算與倍數獎勵示範")
    print("="*60)
    
    # 示範不同風險等級的積分計算
    test_cases = [
        (3, "低風險", "一般購物網站"),
        (5, "中風險", "可疑的投資廣告"),
        (7, "高風險", "假冒銀行網站"),
        (8, "很高風險", "釣魚網站"),
        (9, "極高風險", "已知詐騙集團網站"),
        (10, "極高風險", "大規模詐騙網站")
    ]
    
    print("\n風險評分與積分對照表：")
    print("-" * 60)
    print(f"{'風險評分':<10} {'風險等級':<12} {'獲得積分':<10} {'倍數':<8} {'範例'}")
    print("-" * 60)
    
    for risk_score, risk_level, example in test_cases:
        points = calculator.calculate_points(risk_score)
        multiplier = "2x ⭐" if risk_score >= 9 else "1x"
        print(f"{risk_score:<10} {risk_level:<12} {points:<10} {multiplier:<8} {example}")
    
    print("-" * 60)
    
    # 重點說明
    print("\n💡 重點說明：")
    print("   • 風險評分 1-8：獲得等同於風險評分的積分")
    print("   • 風險評分 9-10：獲得 2 倍積分獎勵 ⭐")
    print("   • 目的：鼓勵團隊成員通報高危險性的詐騙內容")
    
    # 實際案例模擬
    print("\n" + "="*60)
    print("實際案例模擬")
    print("="*60)
    
    scenarios = [
        {
            "url": "https://fake-bank.com/login",
            "risk_score": 8,
            "description": "假冒銀行登入頁面"
        },
        {
            "url": "https://scam-investment.com/join",
            "risk_score": 9,
            "description": "已知詐騙投資平台"
        },
        {
            "url": "https://phishing-site.com/prize",
            "risk_score": 10,
            "description": "大規模釣魚詐騙網站"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n案例 {i}：{scenario['description']}")
        print(f"   URL: {scenario['url']}")
        print(f"   AI 風險評分: {scenario['risk_score']}/10")
        
        points = calculator.calculate_points(scenario['risk_score'])
        
        if scenario['risk_score'] >= 9:
            print(f"   ⭐ 觸發倍數獎勵！")
            print(f"   基礎積分: {scenario['risk_score']}")
            print(f"   倍數: 2x")
            print(f"   實際獲得: {points} 積分")
        else:
            print(f"   獲得積分: {points}")
    
    print("\n" + "="*60)
    print("✓ Task 4.5 實作完成")
    print("="*60)


if __name__ == "__main__":
    demo_points_calculation()
