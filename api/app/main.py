"""
FastAPI 앱
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import analyze
from app.utils.logging import LoggingMiddleware, setup_logging

# PROJECT_ROOT 설정
PROJECT_ROOT = Path(__file__).parent.parent
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)

setup_logging()

app = FastAPI(
    title="NADA AI RAG API",
    description="이미지 기반 뷰티 코칭 API",
    version="1.0.0",
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 미들웨어
app.add_middleware(LoggingMiddleware)

# 라우터 등록
app.include_router(analyze.router)


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
