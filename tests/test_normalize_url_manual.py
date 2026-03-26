#!/usr/bin/env python3
"""手動測試 normalize_url() 方法"""

from points_calculator import PointsCalculator


def test_normalize_url():
    """測試 normalize_url() 方法的各種情況"""
    calc = PointsCalculator()
    
    # 測試案例
    test_cases = [
        # (輸入, 預期輸出, 描述)
        ("https://scam-site.com/fake-investment?ref=123", 
         "https://scam-site.com/fake-investment", 
         "移除 query parameters"),
        
        ("https://example.com/path/", 
         "https://example.com/path", 
         "移除 trailing slash"),
        
        ("https://Example.COM/Path", 
         "https://example.com/path", 
         "轉換為小寫"),
        
        ("https://scam-site.com/fake-investment/?ref=abc", 
         "https://scam-site.com/fake-investment", 
         "同時移除 query 和 trailing slash"),
        
        ("https://example.com/page?param1=value1&param2=value2", 
         "https://example.com/page", 
         "移除多個 query parameters"),
        
        ("https://example.com", 
         "https://example.com", 
         "沒有路徑的 URL"),
        
        ("https://example.com:8080/path?query=123", 
         "https://example.com:8080/path", 
         "帶 port 的 URL"),
        
        ("http://example.com/path?query=123", 
         "http://example.com/path", 
         "HTTP scheme"),
    ]
    
    print("開始測試 normalize_url() 方法...\n")
    
    passed = 0
    failed = 0
    
    for input_url, expected, description in test_cases:
        result = calc.normalize_url(input_url)
        if result == expected:
            print(f"✅ PASS: {description}")
            print(f"   輸入: {input_url}")
            print(f"   輸出: {result}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   輸入: {input_url}")
            print(f"   預期: {expected}")
            print(f"   實際: {result}")
            failed += 1
        print()
    
    # 測試冪等性
    print("測試冪等性...")
    url = "https://Example.com/Path/?query=123"
    normalized_once = calc.normalize_url(url)
    normalized_twice = calc.normalize_url(normalized_once)
    if normalized_once == normalized_twice:
        print(f"✅ PASS: 冪等性測試")
        print(f"   normalize(normalize(url)) == normalize(url)")
        print(f"   結果: {normalized_once}")
        passed += 1
    else:
        print(f"❌ FAIL: 冪等性測試")
        print(f"   第一次: {normalized_once}")
        print(f"   第二次: {normalized_twice}")
        failed += 1
    print()
    
    # 測試 calculate_points()
    print("測試 calculate_points() 方法...\n")
    
    points_tests = [
        (5, 5, "一般風險 (5)"),
        (7, 7, "一般風險 (7)"),
        (8, 8, "一般風險 (8)"),
        (9, 18, "極高風險 (9) - 2x 倍數"),
        (10, 20, "極高風險 (10) - 2x 倍數"),
    ]
    
    for risk_score, expected_points, description in points_tests:
        result = calc.calculate_points(risk_score)
        if result == expected_points:
            print(f"✅ PASS: {description}")
            print(f"   風險評分: {risk_score}, 獲得積分: {result}")
            passed += 1
        else:
            print(f"❌ FAIL: {description}")
            print(f"   風險評分: {risk_score}")
            print(f"   預期積分: {expected_points}")
            print(f"   實際積分: {result}")
            failed += 1
        print()
    
    # 總結
    print("=" * 60)
    print(f"測試完成！")
    print(f"通過: {passed} 個")
    print(f"失敗: {failed} 個")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = test_normalize_url()
    exit(0 if success else 1)
