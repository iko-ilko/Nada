"""
요청 데이터 모델
"""
from fastapi import File, UploadFile


class AnalysisRequest:
    """분석 요청"""
    def __init__(self, image_file: UploadFile = File(...), user_state: str = None):
        self.image_file = image_file
        self.user_state = user_state
