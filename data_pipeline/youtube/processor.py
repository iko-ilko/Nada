"""
YouTube 자막 텍스트 정제
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def clean_subtitles(subtitle_text: str) -> str:
    """
    VTT/자막 텍스트 정제

    Args:
        subtitle_text: 원본 자막 텍스트 (VTT 포맷)

    Returns:
        정제된 텍스트
    """
    if not subtitle_text:
        return ""

    paragraphs = []

    for line in subtitle_text.split('\n'):
        line = line.strip()

        if line.startswith(('Kind:', 'Language:', 'WEBVTT', 'NOTE')) or not line.strip(): # 양쪽 끝에 공백이 없다고 가정(그래보임)하고 제거된 라인 할당 x. 
            continue

        if '-->' in line or re.search(r'<\d{2}:\d{2}:', line):
            continue

        line = line.replace('&gt;', '').replace('[음악]', '')
        
        # 중복 제거
        if paragraphs and line == paragraphs[-1]:
            continue

        paragraphs.append(line)

    # 모든 텍스트를 공백으로 연결
    result = ' '.join(paragraphs)

    # 마침표, 물음표, 느낌표 기준으로 개행
    result = re.sub(r'([\.!?])\s+', r'\1\n', result)

    return result.strip()


def is_text_valid(text: str, min_length: int = 100) -> bool:
    """
    정제된 텍스트 유효성 검사

    Args:
        text: 정제된 텍스트
        min_length: 최소 길이

    Returns:
        유효 여부
    """
    if not text or len(text) < min_length:
        logger.warning(f"⚠️ 텍스트 길이 부족: {len(text)} < {min_length}")
        return False

    return True
