"""
RAG 시스템 메인 파일
모든 모듈을 조합해서 실행합니다.
"""
from pathlib import Path
import sys
import os

# 프로젝트 루트 디렉토리 설정
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
os.environ['PROJECT_ROOT'] = str(project_root)

from src.config import Config
from src.loader import DocumentLoader
from src.embedder import EmbeddingManager
from src.db import TextChunker, VectorStoreManager
from src.rag import MultimodalRAGChain


def _prepare_vectorstore():
    """
    벡터 DB 생성/로드
    기존 DB가 있으면 재구성 여부를 묻고, 없으면 자동 생성
    """
    print("=" * 60)
    print("🔄 벡터 DB 준비 중...")
    print("=" * 60)

    # 설정 검증
    Config.validate()

    vectorstore = None

    # 벡터 DB가 있으면 재구성 여부 확인
    if os.path.exists(Config.CHROMA_DB_PATH):
        print(f"\n📂 기존 벡터 DB 발견: {Config.CHROMA_DB_PATH}")
        response = input("벡터 DB를 재구성하시겠습니까? (y/n): ").strip().lower()

        if response == 'n':
            # 기존 벡터 DB 사용
            print("✅ 기존 벡터 DB를 사용합니다")
            embedding_manager = EmbeddingManager()
            embeddings = embedding_manager.get_embeddings()
            db_manager = VectorStoreManager(embeddings)
            try:
                vectorstore = db_manager.load_vectorstore()
            except Exception as e:
                print(f"❌ 벡터 DB 로드 실패: {e}")
                print("   벡터 DB를 재구성합니다...")
                vectorstore = None
        # y 또는 기타 입력이면 재구성

    # 벡터 DB가 없거나 사용자가 재구성을 선택한 경우
    if vectorstore is None:
        # 1️⃣ 문서 로드
        print("\n1️⃣ 문서 로드 중...")
        loader = DocumentLoader()
        documents = loader.load_documents()

        if len(documents) == 0:
            print("\n❌ 문서를 로드할 수 없습니다")
            return None

        # 2️⃣ 청킹
        print("\n2️⃣ 문서 청킹 중...")
        chunker = TextChunker()
        chunks = chunker.chunk_documents(documents)

        # 3️⃣ 임베딩 + 벡터 DB
        print("\n3️⃣ 벡터 DB 생성 중...")
        embedding_manager = EmbeddingManager()
        embeddings = embedding_manager.get_embeddings()

        db_manager = VectorStoreManager(embeddings)
        vectorstore = db_manager.create_vectorstore(chunks)

    print("\n✅ 벡터 DB 준비 완료!")
    print("=" * 60)
    return vectorstore


def load_prompt(path: str) -> str:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    return text


def main(
    image_url: str = "https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
    user_state: str = "어제 저녁에 라면을 먹어서 부은것같아",
    image_detail: str = "low"
):
    """
    멀티모달 RAG 파이프라인
    이미지 분석 + 문서 검색 + LLM을 통한 미용 코칭

    Args:
        image_url: 분석할 이미지 URL
        user_state: 사용자 상태 설명
        image_detail: 이미지 디테일 레벨 ("low" 또는 "high")
    """
    # 1️⃣ 벡터 DB 준비 (없으면 자동 생성, 있으면 재구성 여부 묻기)
    _prepare_vectorstore()

    print("\n" + "=" * 60)
    print("🔍 멀티모달 RAG 파이프라인")
    print("=" * 60)

    Config.validate()

    # 이미지 디테일 설정 변경 (필요시)
    if image_detail != Config.IMAGE_DETAIL:
        print(f"\n⚙️  이미지 디테일 설정 변경: {Config.IMAGE_DETAIL} → {image_detail}")
        Config.IMAGE_DETAIL = image_detail

    print(f"\n📝 입력 파라미터:")
    print(f"   이미지 URL: {image_url[:50]}...")
    print(f"   사용자 상태: {user_state}")
    print(f"   이미지 디테일: {image_detail}")

    # 파이프라인 구성
    print(f"\n{'='*60}")
    print("🔄 파이프라인 구성 중...")
    print(f"{'='*60}")

    # 임베딩 모델 로드
    print(f"\n1️⃣ 임베딩 모델 로드")
    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    # 벡터 스토어 로드
    print(f"\n2️⃣ 벡터 스토어 로드")
    db_manager = VectorStoreManager(embeddings)
    try:
        db_manager.load_vectorstore()
    except Exception as e:
        print(f"❌ 벡터 DB 로드 실패: {e}")
        return

    # Retriever 생성
    print(f"\n3️⃣ Retriever 생성")
    retriever = db_manager.get_retriever()
    print(f"   검색 타입: similarity")
    print(f"   Top-K: {Config.TOP_K}")

    # MultimodalRAGChain 생성
    print(f"\n4️⃣ MultimodalRAGChain 구성")
    multimodal_chain = MultimodalRAGChain(retriever)

    # 시스템 프롬프트 로드
    print(f"\n5️⃣ 시스템 프롬프트 로드")
    system_prompt = load_prompt("src/prompt/response_ko.prt")

    # 파이프라인 실행
    print(f"\n{'='*60}")
    print("🚀 파이프라인 실행")
    print(f"{'='*60}")

    try:
        result = multimodal_chain.query_with_image_and_state(
            image_url=image_url,
            user_state=user_state,
            system_prompt=system_prompt
        )

        # 결과 출력
        print(f"\n{'='*60}")
        print("📊 분석 결과")
        print(f"{'='*60}")

        # 1️⃣ 검색된 문서
        print(f"\n1️⃣ 검색된 문서 ({len(result['search_results'])}개):")
        if result["papers_info"]:
            for paper in result["papers_info"]:
                print(f"\n   [{paper['rank']}] {paper['source']}")
                print(f"       페이지: {paper['page']} | 타입: {paper['type']}")
                print(f"       미리보기: {paper['content_preview'][:100]}...")
                content_len = len(paper.get('full_content', ''))
                print(f"       컨텍스트 길이: {content_len} 글자")
        else:
            print(f"   검색된 문서가 없습니다.")

        # 2️⃣ LLM 분석 결과
        print(f"\n2️⃣ LLM 분석 결과:")
        print(f"   모델: {result['model']}")
        print(f"   이미지 디테일: {result['image_detail']}")

        import json
        if isinstance(result["analysis"], dict):
            print(json.dumps(result["analysis"], indent=4, ensure_ascii=False))
        else:
            print(result["analysis"])

        # 3️⃣ 결과 저장
        print(f"\n3️⃣ 결과 저장:")
        print(f"   로그 파일: {result['log_path']}")

        print(f"\n{'='*60}")
        print(f"✅ 파이프라인 실행 완료!")
        print(f"{'='*60}")

        return result

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 멀티모달 RAG 실행 (벡터 DB가 없으면 자동 생성)
    main(
        image_url="https://res.cloudinary.com/nadacloud/image/upload/v1756530521/qmfzfedoxpkt1phjn1ag.jpg",
        # user_state="머리색을 바꾸고 싶은데 나한테 어울리는게 뭘까?",
        # user_state="어제 저녁에 라면을 먹어서 부은것같아",
        # user_state="얼굴이 처져 보이는데 개선 방법이 있을까?",
        user_state="피부가 더 좋아지고 싶어.",
        image_detail="low"
    )
