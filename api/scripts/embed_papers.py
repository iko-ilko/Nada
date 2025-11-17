"""
벡터 DB 생성 스크립트
수동으로 벡터 DB를 생성하거나 업데이트할 때 사용합니다.

Usage:
    python scripts/embed_papers.py
"""
import os
import sys
from pathlib import Path

# PROJECT_ROOT 설정
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ['PROJECT_ROOT'] = str(PROJECT_ROOT)

from app.core.indexer import DocumentIndexer


def main():
    """벡터 DB 생성"""
    print("=" * 80)
    print("벡터 DB 생성 시작")
    print("=" * 80)

    try:
        indexer = DocumentIndexer()
        db_manager = indexer.build_vectorstore()

        if db_manager:
            print("\n" + "=" * 80)
            print("✅ 벡터 DB 생성 완료")
            print("=" * 80)
            return 0
        else:
            print("\n" + "=" * 80)
            print("❌ 벡터 DB 생성 실패")
            print("=" * 80)
            return 1

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
