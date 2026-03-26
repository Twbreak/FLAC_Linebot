#!/usr/bin/env python3
"""示範 PointsCalculator 的 normalize_url() 功能"""

from points_calculator import PointsCalculator


def main():
    print("=" * 70)
    print("PointsCalculator - URL 標準化示範")
    print("=" * 70)
    print()
    
    calc = PointsCalculator()
    
    # 示範案例
    examples = [
        "https://scam-site.com/fake-investment?ref=123",
        "https://Example.COM/Path/",
        "https://phishing.com/login?user=victim&session=abc123",
        "HTTP://SCAM.NET/OFFER/?promo=FAKE",
    ]
    
    print("📋 URL 標準化示範：")
    print()
    
    for url in examples:
        normalized = calc.normalize_url(url)
        print(f"原始 URL:")
        print(f"  {url}")
        print(f"標準化後:")
        print(f"  {normalized}")
        print()
    
    print("-" * 70)
    print()
    print("🎯 積分計算示範：")
    print()
    
    risk_scores = [5, 7, 8, 9, 10]
    
    for score in risk_scores:
        points = calc.calculate_points(score)
        multiplier = " (2x 倍數)" if score >= 9 else ""
        print(f"風險評分: {score:2d} → 獲得積分: {points:2d}{multiplier}")
    
    print()
    print("=" * 70)
    print("✅ 示範完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
