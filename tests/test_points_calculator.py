import pytest
from points_calculator import PointsCalculator


class TestPointsCalculator:
    """測試 PointsCalculator 類別"""
    
    def setup_method(self):
        """每個測試前初始化"""
        self.calculator = PointsCalculator()
    
    # normalize_url() 測試
    
    def test_normalize_url_removes_query_parameters(self):
        """測試移除 query parameters"""
        url = "https://scam-site.com/fake-investment?ref=123"
        result = self.calculator.normalize_url(url)
        assert result == "https://scam-site.com/fake-investment"
        assert "?" not in result
        assert "ref=123" not in result
    
    def test_normalize_url_removes_trailing_slash(self):
        """測試移除 trailing slash"""
        url = "https://example.com/path/"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com/path"
        assert not result.endswith("/")
    
    def test_normalize_url_converts_to_lowercase(self):
        """測試轉換為小寫"""
        url = "https://Example.COM/Path"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com/path"
        assert result.islower()
    
    def test_normalize_url_removes_query_and_trailing_slash(self):
        """測試同時移除 query parameters 和 trailing slash"""
        url = "https://scam-site.com/fake-investment/?ref=abc"
        result = self.calculator.normalize_url(url)
        assert result == "https://scam-site.com/fake-investment"
    
    def test_normalize_url_handles_multiple_query_parameters(self):
        """測試處理多個 query parameters"""
        url = "https://example.com/page?param1=value1&param2=value2&param3=value3"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com/page"
        assert "param1" not in result
        assert "param2" not in result
        assert "param3" not in result
    
    def test_normalize_url_preserves_path(self):
        """測試保留路徑"""
        url = "https://example.com/path/to/resource"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com/path/to/resource"
    
    def test_normalize_url_handles_url_without_path(self):
        """測試處理沒有路徑的 URL"""
        url = "https://example.com"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com"
    
    def test_normalize_url_handles_url_with_port(self):
        """測試處理帶 port 的 URL"""
        url = "https://example.com:8080/path?query=123"
        result = self.calculator.normalize_url(url)
        assert result == "https://example.com:8080/path"
    
    def test_normalize_url_idempotence(self):
        """測試冪等性：normalize(normalize(url)) == normalize(url)"""
        url = "https://Example.com/Path/?query=123"
        normalized_once = self.calculator.normalize_url(url)
        normalized_twice = self.calculator.normalize_url(normalized_once)
        assert normalized_once == normalized_twice
    
    def test_normalize_url_handles_http_scheme(self):
        """測試處理 HTTP scheme"""
        url = "http://example.com/path?query=123"
        result = self.calculator.normalize_url(url)
        assert result == "http://example.com/path"
        assert result.startswith("http://")
    
    # calculate_points() 測試
    
    def test_calculate_points_normal_risk(self):
        """測試一般風險評分（< 9）"""
        assert self.calculator.calculate_points(5) == 5
        assert self.calculator.calculate_points(7) == 7
        assert self.calculator.calculate_points(8) == 8
    
    def test_calculate_points_high_risk_multiplier(self):
        """測試極高風險倍數獎勵（>= 9）"""
        assert self.calculator.calculate_points(9) == 18  # 9 * 2
        assert self.calculator.calculate_points(10) == 20  # 10 * 2
    
    def test_calculate_points_boundary(self):
        """測試邊界值"""
        assert self.calculator.calculate_points(8) == 8  # 不觸發倍數
        assert self.calculator.calculate_points(9) == 18  # 觸發倍數
