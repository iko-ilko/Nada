"""
서버 로깅 유틸리티
"""
import logging
import time
import pytz
from datetime import datetime
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger("app")


class KSTFormatter(logging.Formatter):
    """KST 타임존으로 로그 시간을 포맷하는 커스텀 포매터"""

    def formatTime(self, record, datefmt=None):
        # UTC 시간을 KST로 변환
        dt = datetime.fromtimestamp(record.created, tz=pytz.UTC)
        kst_dt = dt.astimezone(pytz.timezone('Asia/Seoul'))

        if datefmt:
            return kst_dt.strftime(datefmt)
        else:
            return kst_dt.strftime('%Y-%m-%d %H:%M:%S')


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP 요청/응답 로깅 미들웨어"""

    async def dispatch(self, request: Request, call_next) -> Response:
        """요청과 응답을 로깅합니다"""
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s"
        )

        return response


def setup_logging():
    """로깅 설정 (KST)"""
    formatter = KSTFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
