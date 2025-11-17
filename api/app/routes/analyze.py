"""
분석 라우터
"""
import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.request import AnalysisRequest
from app.schemas.response import AnalysisResponse
from app.services.analysis_service import get_analysis_service

logger = logging.getLogger("app")
router = APIRouter(prefix="/api", tags=["analysis"])


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(
    image_file: UploadFile = File(...),
    user_state: str = Form(...)
):
    """
    이미지 + 사용자 상태로 분석 수행

    Args:
        image_file: 분석할 이미지 파일
        user_state: 사용자 상태

    Returns:
        AnalysisResponse: 분석 결과
    """
    try:
        request = AnalysisRequest(image_file=image_file, user_state=user_state)
        service = get_analysis_service()
        response = service.analyze(request)

        if response.status == "error":
            raise HTTPException(status_code=500, detail=response.error)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ 분석 중 에러 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
