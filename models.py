from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from datetime import datetime
import uuid

class ScamDetectionRecord(BaseModel):
    """詐騙偵測記錄"""
    user_id: str
    input_content: str
    risk_score: int
    category: str
    analysis: List[str]
    expert_warning: str
    created_at: datetime = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserHistory(BaseModel):
    """使用者歷史記錄回應"""
    user_id: str
    input_content: str
    risk_score: int
    category: str
    analysis: List[str]
    expert_warning: str
    created_at: str
    timestamp: str  # 相容舊格式

class LeaderboardEntry(BaseModel):
    """排行榜項目"""
    user_id: str
    total_scams: int
    total_points: int
    coupons: int

# ==================== Team Collaboration Models ====================

class Team(BaseModel):
    """團隊資料模型"""
    team_id: str
    team_name: str
    leader_uid: str
    total_points: int = 0
    member_count: int = 1
    created_at: datetime
    completed_quests: List[str] = []
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TeamMember(BaseModel):
    """團隊成員資料模型"""
    member_id: str
    team_id: str
    line_uid: str
    contribution_points: int = 0
    report_count: int = 0
    joined_at: datetime
    is_leader: bool = False
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ScamReport(BaseModel):
    """詐騙通報記錄"""
    report_id: str
    url: str
    normalized_url: str
    reporter_uid: str
    team_id: Optional[str] = None
    risk_score: int
    category: str
    multiplier_applied: bool = False
    points_earned: int
    reported_at: datetime
    is_mass_reported: bool = False
    mass_report_alert_id: Optional[str] = None
    
    @field_validator('mass_report_alert_id')
    @classmethod
    def validate_mass_report_alert_id(cls, v: Optional[str], info) -> Optional[str]:
        """驗證當 is_mass_reported 為 True 時，mass_report_alert_id 不可為 None"""
        # Get is_mass_reported from the data being validated
        is_mass_reported = info.data.get('is_mass_reported', False)
        if is_mass_reported and v is None:
            raise ValueError('mass_report_alert_id must not be None when is_mass_reported is True')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ==================== Team Collaboration Request Models ====================

class CreateTeamRequest(BaseModel):
    """建立團隊請求"""
    leader_uid: str
    team_name: str = Field(..., min_length=1, max_length=30)

class JoinTeamRequest(BaseModel):
    """加入團隊請求"""
    team_id: str
    member_uid: str
    signature: str

class TeamLeaderboard(BaseModel):
    """團隊排行榜項目"""
    rank: int
    team_id: str
    team_name: str
    total_points: int
    report_count: int
    member_count: int

# ==================== Mass Report Notification Models ====================

class MassReportAlert(BaseModel):
    """大量通報警示記錄"""
    alert_id: str
    normalized_url: str
    report_count: int
    alert_summary: str
    alert_warning: str
    notified_user_count: int
    created_at: datetime
    status: Literal["pending", "processing", "completed", "failed"]
    
    @field_validator('alert_id')
    @classmethod
    def validate_alert_id(cls, v: str) -> str:
        """驗證 alert_id 必須為有效的 UUID 格式"""
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('alert_id must be a valid UUID format')
        return v
    
    @field_validator('report_count')
    @classmethod
    def validate_report_count(cls, v: int) -> int:
        """驗證 report_count 必須 >= 10"""
        if v < 10:
            raise ValueError('report_count must be greater than or equal to 10')
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
