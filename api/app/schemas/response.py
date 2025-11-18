"""
응답 데이터 모델
"""
from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, List


class AnalysisResponse(BaseModel):
    """분석 응답"""
    model_config = ConfigDict(exclude_none=True)

    status: str
    analysis: Dict[str, Any]
    references: Optional[List[str]] = None
    error: Optional[str] = None
