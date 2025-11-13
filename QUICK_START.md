# 🚀 RAG 시스템 빠른 시작 가이드 (2시간 실전)

**목표**: 기본 RAG 시스템을 2시간 내에 구현하고 테스트하기

---

## 📋 사전 준비

### 필수
- Python 3.9 이상
- 테스트용 PDF 파일 2-3개
- 텍스트 에디터 또는 IDE

### 선택 (비용 절감)
- OpenAI API 키 (선택) - 로컬 모델 사용 가능

---

## ⚡ 5분 안에 시작하기

### Step 1: 디렉토리 구조 생성
```bash
mkdir rag_system
cd rag_system
mkdir -p data/papers
mkdir src
```

### Step 2: 의존성 설치
```bash
# 최소한의 의존성만 설치 (빠른 시작)
pip install langchain langchain-community chromadb sentence-transformers pypdf python-dotenv

# LLM 사용 (선택)
pip install langchain-openai  # OpenAI 사용시
# 또는 로컬 LLM 사용 (다음 섹션 참조)
```

### Step 3: 테스트 데이터 준비
- `data/papers/` 에 PDF 파일 2-3개 복사

### Step 4: 최소 구현 코드
```python
# main.py
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# 1. 문서 로드
loader = PyPDFLoader("data/papers/your_paper.pdf")
docs = loader.load()

# 2. 청킹
splitter = RecursiveCharacterTextSplitter(
    chunk_size=300,
    chunk_overlap=50
)
chunks = splitter.split_documents(docs)

# 3. 임베딩 + 벡터 DB
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(
    chunks,
    embeddings,
    persist_directory="./chroma_db"
)

# 4. RAG 체인
llm = ChatOpenAI(model_name="gpt-3.5-turbo")
chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    return_source_documents=True
)

# 5. 질의
result = chain({"query": "논문의 주요 내용은?"})
print(result["result"])
```

---

## 🎯 상세 구현 (모듈화)

### 프로젝트 구조 (완전)
```
rag_system/
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── loader.py
│   ├── embedder.py
│   ├── db.py
│   └── rag.py
├── data/
│   └── papers/
│       ├── paper1.pdf
│       ├── paper2.pdf
│       └── paper3.pdf
├── chroma_db/
│   └── (Chroma 데이터베이스 저장소)
├── requirements.txt
├── .env
└── main.py
```

### 1️⃣ config.py - 설정 파일
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM 설정
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    # 임베딩 설정
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "all-MiniLM-L6-v2"  # 빠른 시작용
    )

    # 벡터 DB 설정
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    COLLECTION_NAME = "papers"

    # 문서 처리 설정
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

    # RAG 설정
    TOP_K = int(os.getenv("TOP_K", "3"))

    # 경로 설정
    PAPERS_DIR = os.getenv("PAPERS_DIR", "./data/papers")

    @classmethod
    def validate(cls):
        """설정 검증"""
        if not os.path.exists(cls.PAPERS_DIR):
            os.makedirs(cls.PAPERS_DIR, exist_ok=True)
            print(f"📁 {cls.PAPERS_DIR} 디렉토리 생성됨")
```

### 2️⃣ loader.py - 문서 로더
```python
import os
from pathlib import Path
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.schema import Document
from typing import List
from config import Config

class DocumentLoader:
    """문서 로딩 및 메타데이터 추가"""

    def __init__(self, papers_dir: str = None):
        self.papers_dir = papers_dir or Config.PAPERS_DIR

    def load_single_pdf(self, filepath: str) -> List[Document]:
        """단일 PDF 로드"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {filepath}")

        loader = PyPDFLoader(filepath)
        docs = loader.load()

        # 메타데이터 추가
        filename = os.path.basename(filepath)
        for doc in docs:
            doc.metadata.update({
                "source": filename,
                "filepath": filepath,
                "type": "pdf"
            })

        print(f"✅ {filename} 로드 완료: {len(docs)}페이지")
        return docs

    def load_all_pdfs(self) -> List[Document]:
        """디렉토리의 모든 PDF 로드"""
        if not os.path.exists(self.papers_dir):
            raise FileNotFoundError(f"디렉토리를 찾을 수 없습니다: {self.papers_dir}")

        pdf_files = list(Path(self.papers_dir).glob("*.pdf"))

        if not pdf_files:
            print(f"⚠️  {self.papers_dir} 에 PDF 파일이 없습니다")
            return []

        all_docs = []
        for pdf_file in pdf_files:
            try:
                docs = self.load_single_pdf(str(pdf_file))
                all_docs.extend(docs)
            except Exception as e:
                print(f"❌ {pdf_file} 로드 실패: {e}")

        total_pages = sum(1 for doc in all_docs)
        print(f"\n📊 총 {len(pdf_files)}개 파일, {total_pages}페이지 로드됨")
        return all_docs
```

### 3️⃣ embedder.py - 임베딩 관리
```python
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from config import Config

class EmbeddingManager:
    """임베딩 모델 관리"""

    def __init__(self, model_name: str = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL
        self.embeddings = None

    def get_embeddings(self):
        """임베딩 모델 로드"""
        if self.embeddings is not None:
            return self.embeddings

        if self.model_name.startswith("text-embedding"):
            # OpenAI 임베딩
            print(f"🔄 OpenAI 임베딩 모델 로드: {self.model_name}")
            self.embeddings = OpenAIEmbeddings(
                model=self.model_name,
                api_key=Config.OPENAI_API_KEY
            )
        else:
            # 오픈소스 임베딩
            print(f"🔄 로컬 임베딩 모델 로드: {self.model_name}")
            print("   (첫 실행시 모델 다운로드: 300MB 정도)")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name
            )

        return self.embeddings

# 임베딩 모델 옵션
EMBEDDING_OPTIONS = {
    "light": "all-MiniLM-L6-v2",  # 가볍고 빠름 ⭐ 추천
    "medium": "all-mpnet-base-v2",  # 중간 크기
    "large": "all-MiniLM-L12-v2",  # 좀 더 정확함
    "korean": "ko-e5-base",  # 한국어 특화 (설치 필요)
}
```

### 4️⃣ db.py - 벡터 DB 관리
```python
import os
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config import Config
from typing import List
from langchain.schema import Document

class VectorDB:
    """벡터 데이터베이스 관리"""

    def __init__(self, embeddings, collection_name: str = None):
        self.embeddings = embeddings
        self.collection_name = collection_name or Config.COLLECTION_NAME
        self.persist_dir = Config.CHROMA_DB_PATH
        self.vectorstore = None

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """문서 청킹"""
        print(f"\n🔪 문서 청킹 중...")
        print(f"   청크 크기: {Config.CHUNK_SIZE} 토큰")
        print(f"   오버랩: {Config.CHUNK_OVERLAP} 토큰")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(documents)
        print(f"✅ 청킹 완료: {len(chunks)}개 청크 생성됨")
        return chunks

    def create_vectorstore(self, chunks: List[Document]):
        """벡터 스토어 생성"""
        print(f"\n🔄 벡터 임베딩 중...")
        print(f"   모델: {Config.EMBEDDING_MODEL}")
        print(f"   저장 위치: {self.persist_dir}")

        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name=self.collection_name
        )

        self.vectorstore.persist()
        print(f"✅ 벡터 스토어 저장 완료")
        return self.vectorstore

    def load_vectorstore(self):
        """기존 벡터 스토어 로드"""
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(f"벡터 DB를 찾을 수 없습니다: {self.persist_dir}")

        print(f"📂 벡터 스토어 로드 중: {self.persist_dir}")
        self.vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name=self.collection_name
        )
        print(f"✅ 벡터 스토어 로드 완료")
        return self.vectorstore

    def get_retriever(self):
        """Retriever 반환"""
        if self.vectorstore is None:
            raise ValueError("벡터 스토어가 초기화되지 않았습니다")

        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.TOP_K}
        )
```

### 5️⃣ rag.py - RAG 체인
```python
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from config import Config
from typing import Dict, Any

class RAGSystem:
    """RAG 시스템"""

    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = None
        self.chain = None
        self._init_llm()
        self._init_chain()

    def _init_llm(self):
        """LLM 초기화"""
        print(f"\n🔄 LLM 초기화 중: {Config.LLM_MODEL}")

        if Config.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model_name=Config.LLM_MODEL,
                temperature=Config.LLM_TEMPERATURE,
                api_key=Config.OPENAI_API_KEY
            )
            print(f"✅ OpenAI LLM 준비됨")
        else:
            # 로컬 모델 사용 (Ollama 필요)
            try:
                from langchain.llms import Ollama
                self.llm = Ollama(model="mistral")
                print(f"✅ 로컬 Ollama LLM 준비됨")
                print(f"   ⚠️  Ollama 설치 필요: https://ollama.ai")
            except Exception as e:
                print(f"❌ LLM 초기화 실패: {e}")
                print(f"   OPENAI_API_KEY를 .env에 설정하거나 Ollama를 설치하세요")
                raise

    def _init_chain(self):
        """RAG 체인 초기화"""
        # 프롬프트 템플릿
        prompt_template = """당신은 학술 논문 분석 전문가입니다.

주어진 문서를 기반으로 질문에 정확하게 답변하세요.

규칙:
1. 문서에 명시된 정보만 사용하세요
2. 정보가 없으면 "문서에 이 정보가 없습니다"라고 답변하세요
3. 항상 정확하고 구체적으로 답변하세요
4. 가능하면 구체적인 수치나 예시를 포함하세요

문서:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        self.chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",  # 빠른 처리를 위해 "stuff" 사용
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )

        print(f"✅ RAG 체인 준비됨")

    def query(self, question: str) -> Dict[str, Any]:
        """질문에 답변"""
        if not self.chain:
            raise ValueError("RAG 체인이 초기화되지 않았습니다")

        print(f"\n❓ 질문: {question}")
        print(f"🔍 검색 및 답변 생성 중...")

        result = self.chain({"query": question})

        answer = result["result"]
        sources = result["source_documents"]

        print(f"\n✅ 답변 완료\n")
        print(f"📝 답변:\n{answer}")

        if sources:
            print(f"\n📚 출처 문서:")
            for i, doc in enumerate(sources, 1):
                source = doc.metadata.get("source", "Unknown")
                page = doc.metadata.get("page", "Unknown")
                print(f"   {i}. {source} (페이지 {page})")

        return {
            "answer": answer,
            "sources": sources,
            "source_metadata": [doc.metadata for doc in sources]
        }
```

### 6️⃣ main.py - 메인 실행 파일
```python
import os
from config import Config
from loader import DocumentLoader
from embedder import EmbeddingManager
from db import VectorDB
from rag import RAGSystem

def main():
    print("=" * 60)
    print("🚀 RAG 시스템 시작")
    print("=" * 60)

    # 설정 검증
    Config.validate()

    # 1️⃣ 문서 로드
    print("\n" + "=" * 60)
    print("1️⃣  STEP 1: 문서 로드")
    print("=" * 60)

    loader = DocumentLoader(Config.PAPERS_DIR)
    documents = loader.load_all_pdfs()

    if not documents:
        print("❌ 로드할 문서가 없습니다!")
        print(f"📁 {Config.PAPERS_DIR} 디렉토리에 PDF 파일을 넣어주세요")
        return

    # 2️⃣ 임베딩 초기화
    print("\n" + "=" * 60)
    print("2️⃣  STEP 2: 임베딩 초기화")
    print("=" * 60)

    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    # 3️⃣ 벡터 DB 생성 또는 로드
    print("\n" + "=" * 60)
    print("3️⃣  STEP 3: 벡터 데이터베이스")
    print("=" * 60)

    vector_db = VectorDB(embeddings)

    if os.path.exists(Config.CHROMA_DB_PATH):
        print("📂 기존 벡터 DB 발견")
        vector_db.load_vectorstore()
    else:
        print("✨ 새로운 벡터 DB 생성 중...")
        chunks = vector_db.split_documents(documents)
        vector_db.create_vectorstore(chunks)

    # 4️⃣ RAG 시스템 초기화
    print("\n" + "=" * 60)
    print("4️⃣  STEP 4: RAG 시스템 초기화")
    print("=" * 60)

    retriever = vector_db.get_retriever()
    rag_system = RAGSystem(retriever)

    # 5️⃣ 대화형 질의
    print("\n" + "=" * 60)
    print("5️⃣  STEP 5: 대화형 질의")
    print("=" * 60)
    print("\n💡 팁: 'quit' 또는 'exit'을 입력하여 종료하세요\n")

    while True:
        try:
            question = input("🔹 질문을 입력하세요: ").strip()

            if question.lower() in ["quit", "exit", "q"]:
                print("\n👋 프로그램 종료!")
                break

            if not question:
                print("⚠️  질문을 입력해주세요\n")
                continue

            result = rag_system.query(question)

        except KeyboardInterrupt:
            print("\n\n👋 프로그램 종료!")
            break
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            print("다시 시도해주세요\n")

if __name__ == "__main__":
    main()
```

### 7️⃣ .env 파일
```bash
# OpenAI API (선택사항)
OPENAI_API_KEY=sk-...

# LLM 모델
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.3

# 임베딩 모델
EMBEDDING_MODEL=all-MiniLM-L6-v2

# 벡터 DB
CHROMA_DB_PATH=./chroma_db
CHUNK_SIZE=300
CHUNK_OVERLAP=50
TOP_K=3

# 데이터 경로
PAPERS_DIR=./data/papers
```

### 8️⃣ requirements.txt
```txt
langchain==0.1.14
langchain-community==0.0.29
langchain-openai==0.1.9
chromadb==0.5.0
sentence-transformers==2.7.0
pypdf==4.0.1
python-dotenv==1.0.0
pydantic==2.7.0
```

---

## 🎬 실행 방법

### 첫 번째 실행
```bash
# 1. 프로젝트 생성
mkdir rag_system && cd rag_system

# 2. 파일 구조 생성 (위의 코드 참조)
# src/, data/papers/, 각 py 파일 생성

# 3. 의존성 설치
pip install -r requirements.txt

# 4. .env 파일 작성 (OpenAI 키 추가 또는 로컬 LLM 설정)

# 5. PDF 파일 추가
# data/papers/ 에 PDF 파일 복사

# 6. 실행
python main.py
```

### 실행 예시
```
==============================================================
🚀 RAG 시스템 시작
==============================================================

==============================================================
1️⃣  STEP 1: 문서 로드
==============================================================

📁 ./data/papers 디렉토리 생성됨
✅ paper1.pdf 로드 완료: 15페이지
✅ paper2.pdf 로드 완료: 12페이지

📊 총 2개 파일, 27페이지 로드됨

==============================================================
2️⃣  STEP 2: 임베딩 초기화
==============================================================

🔄 로컬 임베딩 모델 로드: all-MiniLM-L6-v2
✅ 로컬 임베딩 모델 준비됨

==============================================================
3️⃣  STEP 3: 벡터 데이터베이스
==============================================================

✨ 새로운 벡터 DB 생성 중...

🔪 문서 청킹 중...
   청크 크기: 300 토큰
   오버랩: 50 토큰
✅ 청킹 완료: 89개 청크 생성됨

🔄 벡터 임베딩 중...
   모델: all-MiniLM-L6-v2
   저장 위치: ./chroma_db
✅ 벡터 스토어 저장 완료

==============================================================
4️⃣  STEP 4: RAG 시스템 초기화
==============================================================

🔄 LLM 초기화 중: gpt-3.5-turbo
✅ OpenAI LLM 준비됨
✅ RAG 체인 준비됨

==============================================================
5️⃣  STEP 5: 대화형 질의
==============================================================

💡 팁: 'quit' 또는 'exit'을 입력하여 종료하세요

🔹 질문을 입력하세요: 이 논문의 주요 기여는 무엇인가?

❓ 질문: 이 논문의 주요 기여는 무엇인가?
🔍 검색 및 답변 생성 중...

✅ 답변 완료

📝 답변:
이 논문의 주요 기여는 ...

📚 출처 문서:
   1. paper1.pdf (페이지 3)
   2. paper1.pdf (페이지 5)
```

---

## 🐛 일반적인 문제 해결

### 문제: "No module named 'langchain'"
```bash
pip install --upgrade langchain langchain-community langchain-openai
```

### 문제: 임베딩 모델 다운로드 시간이 오래 걸림
```python
# 더 작은 모델 사용
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 33MB
# 대신
EMBEDDING_MODEL=all-mpnet-base-v2  # 438MB (느림)
```

### 문제: OpenAI API 키 오류
```bash
# .env 파일에서 OPENAI_API_KEY 확인
# 또는 로컬 LLM 사용 (Ollama)
# https://ollama.ai 에서 설치
```

### 문제: 메모리 부족
```python
# 배치 크기 줄이기 또는 로컬 임베딩 모델 사용
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 경량
```

---

## 📊 성능 벤치마크 (참고)

### 임베딩 속도 (100개 청크 기준)
- `all-MiniLM-L6-v2`: ~2초 (권장)
- `all-mpnet-base-v2`: ~8초
- OpenAI API: ~3초 (네트워크 의존)

### 쿼리 응답 시간
- 벡터 검색: ~50ms
- LLM 답변 생성: 1-10초 (모델/길이 의존)
- 전체: ~1-15초

### 메모리 사용
- `all-MiniLM-L6-v2`: ~300MB
- Chroma DB: 데이터 크기에 따라 다름
- 전체 시스템: ~500MB-1GB

---

## 🎓 다음 단계

1. **프롬프트 최적화**: 더 나은 답변을 위해 시스템 프롬프트 개선
2. **고급 검색**: MMR (Maximal Marginal Relevance) 검색 적용
3. **멀티턴 대화**: 대화 이력을 고려한 질의응답
4. **웹 인터페이스**: FastAPI + React로 웹 앱 구축
5. **프로덕션 배포**: Docker + 클라우드 배포

---

**행운을 빕니다! 🚀**
