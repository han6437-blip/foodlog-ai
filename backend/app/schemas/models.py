from datetime import datetime, date
from typing import Literal
from pydantic import BaseModel, Field


Goal = Literal["健康饮食", "减脂", "增肌", "控糖"]
BudgetLevel = Literal["低：≤20元", "中：21-50元", "高：>50元"]
CookType = Literal["外卖", "食堂", "自己做饭"]
MealType = Literal["早餐", "午餐", "晚餐", "加餐"]


class UserProfile(BaseModel):
    goal: Goal = "健康饮食"
    allergies: list[str] = Field(default_factory=list)
    disliked_foods: list[str] = Field(default_factory=list)
    preferred_foods: list[str] = Field(default_factory=list)
    budget_level: BudgetLevel = "中：21-50元"
    cook_type: CookType = "食堂"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MealAnalysis(BaseModel):
    foods: list[str]
    health_score: int = Field(ge=0, le=100)
    risk_tags: list[str]
    summary: str
    next_meal_advice: str


class MealRecord(BaseModel):
    id: str
    meal_type: MealType
    eaten_at: datetime
    image_url: str
    description: str = ""
    status: Literal["待分析", "已分析", "分析失败", "仅保存原始记录"] = "待分析"
    analysis: MealAnalysis | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MealCreateResponse(BaseModel):
    record: MealRecord


class FollowUpRequest(BaseModel):
    question: str


class FollowUpResponse(BaseModel):
    answer: str


class RecommendationRequest(BaseModel):
    temporary_conditions: str = ""


class Recommendation(BaseModel):
    meal_type: MealType
    basis: str
    combo: list[str]
    reason: str
    avoid: list[str]
    budget_note: str
    warning: str = ""


class WeeklyReport(BaseModel):
    week_start: date
    week_end: date
    completeness: str
    average_score: int | None = None
    summary: str
    frequent_risks: list[str]
    nutrition_lack: list[str]
    risk_analysis: str
    compensation_plan: list[str]
    note: str = ""
