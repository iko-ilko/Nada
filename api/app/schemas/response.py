"""
응답 데이터 모델
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class AnalysisResponse(BaseModel):
    """분석 응답"""
    status: str
    analysis: Dict[str, Any]
    error: Optional[str] = None
