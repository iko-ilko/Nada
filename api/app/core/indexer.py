"""
문서 인덱싱 모듈
문서를 로드하고 청킹하여 벡터 DB에 저장합니다.

포함된 클래스:
- DocumentLoader: PDF/TXT 파일 로드
- TextChunker: 문서 청킹
- EmbeddingManager: 임베딩 모델 관리
- VectorStoreManager: 벡터 DB 관리
- DocumentIndexer: 전체 인덱싱 오케스트레이션
"""
import os
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.core.config import Config


class DocumentLoader:
    """문서 로더: PDF와 TXT 파일을 로드합니다."""

    def __init__(self, folder_path=None):
        self.folder_path = folder_path or Config.DATA_DIR

    def load_documents(self):
        """폴더 안의 모든 PDF와 TXT 파일을 로드

        PDF 파일은 페이지들을 병합하여 한 문서로 만듭니다.
        (청킹 전에 페이지를 나누면 의미 있는 청킹이 불가능)
        """
        documents = []

        if not os.path.exists(self.folder_path):
            logger.error(f"❌ 폴더 없음: {self.folder_path}")
            return documents

        pdf_files = list(Path(self.folder_path).glob("*.pdf"))
        txt_files = list(Path(self.folder_path).glob("*.txt"))

        logger.info(f"📄 문서 로드 중... (PDF: {len(pdf_files)}, TXT: {len(txt_files)})")

        if len(pdf_files) == 0 and len(txt_files) == 0:
            logger.warning("⚠️  문서가 없습니다. PDF 또는 TXT 파일을 추가해주세요.")
            return documents

        # PDF 로드: 페이지들을 병합하여 한 문서로
        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                pages = loader.load()

                if pages is None:
                    logger.warning(f"   ⚠️  {pdf_file.name}: loader returned None")
                    continue

                total_pages = len(pages)
                valid_pages = [p for p in pages if getattr(p, "page_content", "") and p.page_content.strip()]
                valid_count = len(valid_pages)
                chars = sum(len(p.page_content) for p in valid_pages) if valid_pages else 0
                logger.info(f"   [{pdf_file.name}] pages_loaded={total_pages}, valid_pages={valid_count}, chars={chars}")

                if not valid_pages:
                    logger.warning(f"   ⚠️  {pdf_file.name}: 유효한 텍스트가 없음 (OCR 필요 가능성)")
                    continue

                merged_content = "\n\n".join([p.page_content for p in valid_pages])

                merged_doc = Document(
                    page_content=merged_content,
                    metadata={
                        "source": pdf_file.name,
                        "type": "pdf",
                        "total_pages": valid_count,
                        "start_page": 0,
                        "end_page": valid_count - 1,
                    },
                )

                documents.append(merged_doc)
            except Exception as e:
                logger.error(f"   ❌ {pdf_file.name}: {e}")

        # TXT 로드
        for txt_file in txt_files:
            try:
                loader = TextLoader(str(txt_file), encoding="utf-8")
                docs = loader.load()

                for doc in docs:
                    wrapped = Document(page_content=doc.page_content, metadata={
                        "source": txt_file.name,
                        "type": "txt",
                    })
                    documents.append(wrapped)
            except Exception as e:
                logger.error(f"   ❌ {txt_file.name}: {e}")

        logger.info(f"   ✅ {len(pdf_files) + len(txt_files)}개 파일에서 {len(documents)}개 문서 로드")
        return documents


class TextChunker:
    """문서 청킹: 긴 문서를 작은 청크로 분할합니다."""

    def __init__(self, chunk_size=None, chunk_overlap=None):
        self.chunk_size = chunk_size or Config.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or Config.CHUNK_OVERLAP

    def chunk_documents(self, documents):
        """문서를 작은 청크로 분할"""
        logger.info(f"✂️  청킹 중... (크기: {self.chunk_size}, 오버랩: {self.chunk_overlap})")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " "],
            keep_separator=False,
        )

        chunks = splitter.split_documents(documents)

        min_length = Config.MIN_CHUNK_SIZE
        filtered_chunks = [chunk for chunk in chunks if len(chunk.page_content.strip()) >= min_length]

        removed_count = len(chunks) - len(filtered_chunks)
        logger.info(f"   ✅ {len(chunks)}개 청크 생성 → {removed_count}개 제거 → {len(filtered_chunks)}개 최종")

        return filtered_chunks


class EmbeddingManager:
    """임베딩 관리자: 문서를 벡터로 변환합니다."""

    def __init__(self, model_name=None, device=None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.device = device or os.getenv("HF_EMBEDDING_DEVICE", "cpu")
        self.embeddings = None

    def get_embeddings(self):
        """임베딩 모델 로드 (처음 로드시만 다운로드)"""
        if self.embeddings is not None:
            return self.embeddings

        logger.info(f"🔢 임베딩 모델 로드 중... ({self.model_name}) device={self.device}")

        try:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": self.device},
                encode_kwargs={'normalize_embeddings': True}
            )
        except TypeError:
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)

        logger.info(f"   ✅ 임베딩 모델 준비 완료")
        return self.embeddings


class VectorStoreManager:
    """벡터 DB 관리자: Chroma 벡터 DB를 관리합니다."""

    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.persist_dir = Config.CHROMA_DB_PATH
        self.collection_name = "papers"
        self.vectorstore = None

    def create_vectorstore(self, chunks):
        """청크들을 임베딩하고 벡터 DB에 저장"""
        logger.info(f"💾 벡터 DB 저장 중... ({len(chunks)}개 청크)")

        start_time = time.time()

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
        )

        elapsed_time = time.time() - start_time
        logger.info(f"   ✅ 벡터 DB 저장 완료 (소요: {elapsed_time:.2f}초)")
        return self.vectorstore

    def load_vectorstore(self):
        """기존 벡터 DB 로드"""
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(f"벡터 DB를 찾을 수 없습니다: {self.persist_dir}")

        logger.info(f"📂 벡터 DB 로드 중...")

        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
        )

        logger.info(f"   ✅ 벡터 DB 로드 완료")
        return self.vectorstore

    def get_retriever(self):
        """Retriever 반환 (검색용)"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다")

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.TOP_K},
        )

    def get_bm25_retriever(self, documents):
        """BM25 Retriever 생성"""
        from langchain_community.retrievers import BM25Retriever
        logger.info(f"🔍 BM25 리트리버 생성 중...")
        return BM25Retriever.from_documents(documents)


class DocumentIndexer:
    """문서 인덱싱 오케스트레이션"""

    def __init__(self):
        self.loader = DocumentLoader()
        self.chunker = TextChunker()
        self.embedding_manager = EmbeddingManager()
        self.db_manager = None

    def build_vectorstore(self):
        """
        벡터 DB 생성
        문서 로드 → 청킹 → 임베딩 → 벡터 DB 저장

        Returns:
            VectorStoreManager: 생성된 벡터 DB 관리자
        """
        logger.info("📑 문서 인덱싱 시작...")

        documents = self.loader.load_documents()
        if len(documents) == 0:
            logger.error("❌ 문서를 로드할 수 없습니다")
            return None

        chunks = self.chunker.chunk_documents(documents)

        embeddings = self.embedding_manager.get_embeddings()
        self.db_manager = VectorStoreManager(embeddings)
        self.db_manager.create_vectorstore(chunks)

        logger.info(f"✅ 벡터 DB 생성 완료")
        return self.db_manager

    def get_or_create_vectorstore(self):
        """
        기존 벡터 DB가 있으면 로드, 없으면 생성

        Returns:
            VectorStoreManager: 벡터 DB 관리자
        """
        embeddings = self.embedding_manager.get_embeddings()
        db_manager = VectorStoreManager(embeddings)

        if os.path.exists(Config.CHROMA_DB_PATH):
            logger.info(f"📂 기존 벡터 DB 발견")
            try:
                db_manager.load_vectorstore()
                logger.info(f"✅ 기존 벡터 DB 로드 완료")
                self.db_manager = db_manager
                return db_manager
            except Exception as e:
                logger.warning(f"⚠️  벡터 DB 로드 실패: {e}")
                logger.info(f"   새로 생성합니다...")

        self.db_manager = self.build_vectorstore()
        return self.db_manager
