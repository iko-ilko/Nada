"""
yt-dlp를 활용한 YouTube 데이터 수집
"""
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def extract_video_urls(url: str) -> Optional[list[str]]:
    """
    채널/플레이리스트에서 3년 이내의 영상 URL 추출

    Args:
        url: YouTube 채널 또는 플레이리스트 URL

    Returns:
        영상 URL 리스트 또는 None
    """
    try:
        # 3년 이내의 영상만 필터링
        cutoff_date = (datetime.now() - timedelta(days=1095)).strftime('%Y%m%d')

        ydl_opts = {
            'extract_flat': 'in_playlist',
            'quiet': True,
            'no_warnings': True,
            'dateafter': cutoff_date,
        }

        video_urls = []
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        if 'entries' in info:
            for entry in info['entries']:
                if entry:
                    video_id = entry.get('id')
                    if video_id:
                        video_urls.append(f"https://www.youtube.com/watch?v={video_id}")

        if not video_urls:
            logger.warning(f"⚠️ 영상을 찾을 수 없음: {url}")
            return None

        logger.info(f"✅ {len(video_urls)}개 영상 발견 (3년 이내)")
        return video_urls

    except Exception as e:
        logger.error(f"❌ URL 추출 실패 ({url}): {str(e)}")
        return None


def download_video_data(url: str, output_dir: str = None) -> Optional[Dict[str, Any]]:
    """
    개별 영상의 메타데이터 및 자막 수집

    Args:
        url: YouTube 영상 URL (단일 영상만)
        output_dir: 저장 디렉토리 (기본: /tmp)

    Returns:
        {
            "video_id": str,
            "title": str,
            "url": str,
            "uploaded_at": datetime,
            "description": str,
            "subtitles": str (한국어 자막 내용),
            "has_subtitles": bool
        }
    """
    if output_dir is None:
        output_dir = "/tmp"

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'writesubtitles': True,
            'subtitleslangs': ['ko'],
            'writeautomaticsub': True,
            'skip_download': True,
            'outtmpl': '%(id)s.%(ext)s',
        }

        with YoutubeDL(ydl_opts) as ydl:
            # output_dir로 변경해서 자막 파일이 그곳에 저장되도록
            original_cwd = os.getcwd()
            os.chdir(output_dir)
            try:
                metadata = ydl.extract_info(url, download=True)
            finally:
                os.chdir(original_cwd)

        video_id = metadata.get('id')
        subtitle_path = Path(output_dir) / f"{video_id}.ko.vtt"

        subtitles = None
        has_subtitles = False

        if subtitle_path.exists():
            with open(subtitle_path, 'r', encoding='utf-8') as f:
                subtitles = f.read()
            has_subtitles = True
            subtitle_path.unlink()  # 임시 파일 삭제

        # 업로드 날짜 파싱
        uploaded_at = None
        if metadata.get('upload_date'):
            date_str = metadata['upload_date']  # YYYYMMDD 형식
            uploaded_at = datetime.strptime(date_str, '%Y%m%d')

        return {
            "video_id": video_id,
            "title": metadata.get('title', ''),
            "url": url,
            "description": metadata.get('description'),
            "uploaded_at": uploaded_at,
            "subtitles": subtitles,
            "has_subtitles": has_subtitles
        }

    except Exception as e:
        logger.error(f"❌ 데이터 수집 실패 ({url}): {str(e)}")
        return None
