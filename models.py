from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

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
