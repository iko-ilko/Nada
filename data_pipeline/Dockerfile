FROM python:3.12-slim

WORKDIR /app

# 시스템 패키지 설치 (yt-dlp 필요)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# 데이터베이스 디렉토리 생성
RUN mkdir -p data

# 스크립트 실행
CMD ["python", "scripts/collect_youtube.py"]
