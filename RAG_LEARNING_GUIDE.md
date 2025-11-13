# RAG (Retrieval-Augmented Generation) 학습 및 구현 플로우

**작성일**: 2025-11-11
**목표**: 2시간 내에 RAG 파이프라인 구축 및 논문 데이터 검색 시스템 구현

---

## 📚 목차
1. [RAG 개요](#rag-개요)
2. [핵심 개념](#핵심-개념)
3. [기술 스택](#기술-스택)
4. [RAG 파이프라인 구조](#rag-파이프라인-구조)
5. [구현 단계별 가이드](#구현-단계별-가이드)
6. [실제 코드 예제](#실제-코드-예제)
7. [최적화 전략](#최적화-전략)
8. [2시간 구현 로드맵](#2시간-구현-로드맵)

---

## RAG 개요

### 📌 RAG란?
**Retrieval-Augmented Generation(RAG)** 는 생성형 AI가 외부 데이터베이스에서 관련 정보를 검색한 후, 그 정보를 바탕으로 답변을 생성하는 기법입니다.

### 🎯 RAG의 장점
- **최신 정보 제공**: 학습 데이터 이후의 최신 정보 활용 가능
- **도메인 특화**: 특정 분야(논문, 보고서, 내부 문서 등) 데이터 활용
- **오류 감소**: 생성된 답변의 사실성과 정확도 향상
- **출처 제공**: 검색된 문서를 통해 답변의 근거 제시 가능

### 비교: 일반 LLM vs RAG
```
일반 LLM:  사용자 질문 → LLM (학습된 지식으로만 답변 생성)

RAG:       사용자 질문 → 벡터 DB 검색 → 관련 문서 추출
           → 프롬프트 구성 → LLM (검색된 문서를 기반으로 답변 생성)
```

---

## 핵심 개념

### 1️⃣ **임베딩(Embedding)**
텍스트, 이미지 등의 데이터를 고차원의 벡터(숫자 배열)로 변환하는 과정

**특징**:
- 의미가 유사한 데이터는 벡터 공간에서도 가깝게 위치
- 벡터 간 거리를 통해 유사도 계산 가능
- 수학적 연산이 빠르고 효율적

**임베딩 모델 선택 (2025년 최신)**:
- **OpenAI**: `text-embedding-3-small`, `text-embedding-3-large` (최신, 유료)
- **오픈소스**: `all-MiniLM-L6-v2`, `multilingual-e5-large` (무료, 로컬)
- **한국어 특화**: `KoSimCSE`, `ko-e5` (한국어 논문 최적화)

### 2️⃣ **벡터 데이터베이스(Vector DB)**
임베딩된 벡터를 저장하고 빠르게 검색할 수 있는 데이터베이스

**주요 선택지**:
- **Chroma**: 로컬/경량, 설정 간단, 학습용 최적 ⭐ 추천
- **FAISS**: 메모리 기반, 초고속, 대규모 데이터셋
- **Pinecone**: 클라우드 기반, 고급 기능, 유료
- **Milvus**: 오픈소스, 프로덕션급, 설정 복잡
- **PostgreSQL + pgvector**: 기존 DB 활용

### 3️⃣ **청킹(Chunking)**
긴 문서를 작은 단위로 분할하는 과정

**전략**:
- **고정 크기 청킹**: 200-500 토큰 단위 (기본)
- **재귀적 청킹**: 계층 구조 유지 (문서 구조가 있을 때)
- **의미 기반 청킹**: 문맥을 고려한 분할 (고급)

**권장 설정**:
```
- 청크 크기: 300-500 토큰 (약 200-400단어)
- 오버랩: 50-100 토큰 (문맥 보존)
```

---

## 기술 스택

### 필수 라이브러리
```python
# LLM 및 RAG 프레임워크
pip install langchain langchain-community langchain-openai

# 벡터 DB
pip install chromadb

# 문서 처리
pip install pypdf python-docx

# 임베딩
pip install sentence-transformers  # 오픈소스 임베딩 모델

# 유틸리티
pip install python-dotenv requests
```

### 선택 라이브러리 (선택)
```python
# 고급 RAG
pip install langgraph  # 에이전트 RAG

# 문서 로더
pip install unstructured[pdf]  # PDF 고급 처리

# 성능 모니터링
pip install langsmith  # LangChain 모니터링
```

---

## RAG 파이프라인 구조

### 📊 전체 파이프라인 다이어그램
```
┌─────────────────────────────────────────────────────────────┐
│                    RAG 파이프라인                            │
└─────────────────────────────────────────────────────────────┘

[인덱싱 단계 - 한 번 수행]
1. 문서 수집 → 2. 텍스트 분할 → 3. 임베딩 생성 → 4. 벡터 DB 저장

[실행 단계 - 사용자 쿼리마다 수행]
1. 사용자 질문 → 2. 질문 임베딩 → 3. 유사도 검색
→ 4. 관련 문서 검색 → 5. 프롬프트 구성 → 6. LLM 답변 생성

[결과 반환]
최종 답변 + 출처 문서 정보
```

### 단계별 상세 설명

#### **[인덱싱 단계]**

**1단계: 문서 수집 (Document Loading)**
```
입력: PDF, TXT, JSON, 웹 페이지 등
출력: 텍스트 내용
도구: LangChain DocumentLoaders (PyPDFLoader, TextLoader 등)
```

**2단계: 텍스트 분할 (Text Splitting)**
```
입력: 전체 문서 텍스트
처리: 청킹, 오버랩 적용
출력: 작은 청크들 (Document 객체)
도구: RecursiveCharacterTextSplitter
```

**3단계: 임베딩 생성 (Embedding)**
```
입력: 각 청크 텍스트
처리: 신경망 모델이 텍스트를 벡터로 변환
출력: 벡터 값 (1536 또는 384 차원 등)
시간: 데이터 크기에 따라 수분~수시간
```

**4단계: 벡터 DB 저장 (Vector Store)**
```
입력: 문서 청크 + 임베딩 벡터
처리: DB에 저장, 인덱싱
출력: 검색 가능한 벡터 DB
```

#### **[실행 단계 - 사용자 질의]**

**1단계: 사용자 질문**
```
입력: "논문 X의 주요 발견은 무엇인가?"
```

**2단계: 질문 임베딩**
```
같은 임베딩 모델 사용 → 질문 벡터화
```

**3단계: 유사도 검색 (Similarity Search)**
```
질문 벡터와 DB의 모든 문서 벡터 간 거리 계산
상위 K개 (보통 3-5개) 문서 선택
```

**4단계: 컨텍스트 구성**
```
검색된 문서들의 텍스트 연결
메모리 제한을 고려하여 최적화
```

**5단계: 프롬프트 구성**
```
system_prompt + 검색된 컨텍스트 + 사용자 질문
```

**6단계: LLM 답변 생성**
```
구성된 프롬프트 → LLM → 최종 답변 생성
```

---

## 구현 단계별 가이드

### ⏱️ Phase 1: 환경 설정 (15분)

#### 1.1 프로젝트 구조
```
project/
├── src/
│   ├── config.py          # 설정
│   ├── document_loader.py # 문서 로드
│   ├── embedder.py        # 임베딩 처리
│   ├── vector_store.py    # 벡터 DB 관리
│   └── rag_chain.py       # RAG 파이프라인
├── data/
│   ├── papers/           # 논문 PDF 저장소
│   └── chroma_db/        # Chroma DB 저장소
├── requirements.txt
├── .env
└── main.py               # 메인 실행 파일
```

#### 1.2 .env 파일 설정
```bash
# LLM 설정
OPENAI_API_KEY=your_key_here  # 또는 로컬 모델 사용

# 벡터 DB 설정
CHROMA_DB_PATH=./data/chroma_db

# 임베딩 모델
EMBEDDING_MODEL=all-MiniLM-L6-v2  # 로컬 모델
# EMBEDDING_MODEL=text-embedding-3-small  # OpenAI
```

---

### ⏱️ Phase 2: 데이터 준비 (20분)

#### 2.1 논문 데이터 준비
```
data/papers/ 에 PDF 파일들 저장
- 연구_논문_1.pdf
- 연구_논문_2.pdf
- ...
```

#### 2.2 문서 로더 구현
**주요 지점**:
- PDF 메타데이터 추출 (제목, 저자, 날짜)
- 텍스트 인코딩 문제 해결
- 페이지 번호 추적

---

### ⏱️ Phase 3: 임베딩 및 벡터 DB 구축 (30분)

#### 3.1 임베딩 프로세스
```
논문 로드 → 텍스트 청킹 (300 토큰 단위)
→ 임베딩 모델 로드 → 벡터 생성 → Chroma DB 저장
```

#### 3.2 주요 설정
- **청크 크기**: 300-500 토큰
- **오버랩**: 50-100 토큰
- **배치 처리**: 대량 데이터는 배치로 처리하여 메모리 효율화

#### 3.3 성능 고려사항
```
초기 빌드: 100개 논문 = 약 5-10분 (오픈소스 모델)
이후 쿼리: 평균 1-3초

비용 고려:
- 오픈소스 모델: 무료 (로컬 실행)
- OpenAI API: 약 $0.20 per 1M 토큰
```

---

### ⏱️ Phase 4: RAG 파이프라인 구축 (25분)

#### 4.1 Retriever 설정
```python
# 벡터 DB에서 관련 문서 검색
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # 상위 3개 문서
)
```

#### 4.2 RAG 체인 구성
```python
# LangChain RAG Chain
from langchain.chains import RetrievalQA

rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",  # 또는 "map_reduce", "refine"
    retriever=retriever,
    return_source_documents=True  # 출처 문서 반환
)
```

#### 4.3 프롬프트 커스터마이징
```python
# 논문 검색 특화 프롬프트
PAPER_PROMPT = """
당신은 학술 논문 전문가입니다.

주어진 논문 내용을 기반으로 다음 질문에 답변하세요.
정확하고 구체적인 답변을 제공하세요.

문서:
{context}

질문: {question}

답변:
"""
```

---

### ⏱️ Phase 5: 테스트 및 최적화 (20분)

#### 5.1 기본 테스트
```python
# 샘플 질문 테스트
questions = [
    "이 논문의 주요 기여는 무엇인가?",
    "연구 방법론을 설명해주세요",
    "실험 결과의 결론은?"
]

for q in questions:
    result = rag_chain({"query": q})
    print(f"질문: {q}")
    print(f"답변: {result['result']}")
    print(f"출처: {result['source_documents']}")
```

#### 5.2 성능 튜닝
- 검색 결과 개수 조정 (k 값)
- 임베딩 모델 크기 조정
- 프롬프트 엔지니어링
- 응답 시간 측정

---

## 실제 코드 예제

### 예제 1: 기본 RAG 시스템
```python
# requirements.txt
langchain
langchain-community
langchain-openai
chromadb
sentence-transformers
pypdf
python-dotenv
```

```python
# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./data/chroma_db")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
    CHUNK_SIZE = 300
    CHUNK_OVERLAP = 50
    TOP_K = 3
```

```python
# src/document_loader.py
from langchain.document_loaders import PyPDFLoader, DirectoryLoader
import os

class DocumentProcessor:
    def __init__(self, docs_path: str):
        self.docs_path = docs_path

    def load_documents(self):
        """PDF 파일들을 로드"""
        loader = DirectoryLoader(
            self.docs_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader
        )
        documents = loader.load()
        print(f"총 {len(documents)}개의 문서 로드됨")
        return documents

    def load_and_split(self, splitter):
        """문서 로드 및 청킹"""
        documents = self.load_documents()
        chunks = splitter.split_documents(documents)
        print(f"청킹 완료: {len(chunks)}개의 청크")
        return chunks
```

```python
# src/embedder.py
from langchain.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from config import Config

class EmbeddingManager:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or Config.EMBEDDING_MODEL

    def get_embeddings(self):
        """임베딩 모델 반환"""
        if self.model_name.startswith("text-embedding"):
            # OpenAI 모델
            return OpenAIEmbeddings(model=self.model_name)
        else:
            # 오픈소스 모델
            return HuggingFaceEmbeddings(model_name=self.model_name)
```

```python
# src/vector_store.py
from langchain.vectorstores import Chroma
from config import Config

class VectorStoreManager:
    def __init__(self, embeddings):
        self.embeddings = embeddings
        self.persist_dir = Config.CHROMA_DB_PATH

    def create_vectorstore(self, chunks):
        """벡터 스토어 생성 및 저장"""
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_dir,
            collection_name="papers"
        )
        vectorstore.persist()
        print(f"벡터 스토어 저장됨: {self.persist_dir}")
        return vectorstore

    def load_vectorstore(self):
        """기존 벡터 스토어 로드"""
        vectorstore = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embeddings,
            collection_name="papers"
        )
        return vectorstore
```

```python
# src/rag_chain.py
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from config import Config

class RAGChain:
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.llm = ChatOpenAI(
            model_name=Config.LLM_MODEL,
            temperature=0.3
        )
        self.retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": Config.TOP_K}
        )

    def get_rag_chain(self):
        """RAG 체인 생성"""
        prompt_template = """당신은 학술 논문 전문가입니다.
주어진 문서를 기반으로 질문에 정확하게 답변하세요.
정보가 없으면 "문서에서 이 정보를 찾을 수 없습니다"라고 답변하세요.

문서:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )

        chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        return chain

    def query(self, question: str):
        """질문에 답변"""
        chain = self.get_rag_chain()
        result = chain({"query": question})
        return {
            "answer": result["result"],
            "sources": [doc.metadata for doc in result["source_documents"]]
        }
```

```python
# main.py
from src.config import Config
from src.document_loader import DocumentProcessor
from src.embedder import EmbeddingManager
from src.vector_store import VectorStoreManager
from src.rag_chain import RAGChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os

def main():
    # 1. 문서 로드 및 청킹
    print("=== 1단계: 문서 처리 ===")
    doc_processor = DocumentProcessor("./data/papers")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    )
    chunks = doc_processor.load_and_split(splitter)

    # 2. 임베딩 및 벡터 스토어
    print("\n=== 2단계: 임베딩 및 벡터 스토어 생성 ===")
    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    vector_manager = VectorStoreManager(embeddings)
    if not os.path.exists(Config.CHROMA_DB_PATH):
        vectorstore = vector_manager.create_vectorstore(chunks)
    else:
        vectorstore = vector_manager.load_vectorstore()

    # 3. RAG 체인 생성 및 질의
    print("\n=== 3단계: RAG 질의 ===")
    rag_chain = RAGChain(vectorstore)

    # 테스트 질문
    questions = [
        "이 논문의 주요 기여는 무엇인가?",
        "연구 방법론을 설명해주세요",
        "실험 결과의 성능은?"
    ]

    for question in questions:
        print(f"\n질문: {question}")
        result = rag_chain.query(question)
        print(f"답변: {result['answer']}")
        print(f"출처: {result['sources']}")

if __name__ == "__main__":
    main()
```

---

## 최적화 전략

### 🚀 검색 성능 최적화

#### 1. 검색 파라미터 조정
```python
# 현재
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # 상위 3개
)

# 최적화
retriever = vectorstore.as_retriever(
    search_type="mmr",  # Maximal Marginal Relevance
    search_kwargs={
        "k": 5,
        "fetch_k": 10,  # 초기 검색 결과 수
        "lambda_mult": 0.25  # 다양성 조절
    }
)
```

#### 2. 청킹 전략 개선
```python
# 고정 크기 (기본)
TextSplitter(chunk_size=300, chunk_overlap=50)

# 재귀적 (마크다운, 코드 등 구조가 있을 때)
RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", " ", ""],
    chunk_size=300,
    chunk_overlap=50
)
```

#### 3. 메타데이터 활용
```python
# 문서 필터링
retriever = vectorstore.as_retriever(
    search_kwargs={
        "k": 3,
        "filter": {"author": "John Doe"}  # 저자별 필터링
    }
)
```

---

### 🎯 생성 품질 최적화

#### 1. 프롬프트 엔지니어링
```
좋은 프롬프트 패턴:
1. 역할 정의: "당신은 학술 논문 분석가입니다"
2. 문맥 제공: 검색된 문서 + 메타데이터
3. 지시사항: "정보가 없으면 모른다고 말하세요"
4. 출력 형식: "JSON 형식으로 답변하세요" (필요시)
```

#### 2. 체인 타입 선택
```python
# "stuff": 모든 문서를 한 번에 프롬프트에 포함 (빠름, 토큰 제한)
# "map_reduce": 각 문서를 개별 처리 후 결합 (느림, 안정적)
# "refine": 반복적으로 답변 개선 (느림, 고품질)
```

#### 3. 온도(Temperature) 조정
```python
ChatOpenAI(temperature=0.3)  # 논문 분석: 낮음 (0.0-0.3)
ChatOpenAI(temperature=0.7)  # 창의적 답변: 높음
```

---

### 💾 저장소 최적화

#### 1. Chroma DB 최적화
```python
# 컬렉션 명시
vectorstore = Chroma(
    collection_name="papers_v1",
    persist_directory="./data/chroma_db"
)

# 여러 컬렉션 분리
# - papers_v1: 최신 논문
# - papers_archive: 오래된 논문
```

#### 2. 인덱싱 전략
```python
# 메타데이터 인덱싱으로 쿼리 성능 향상
documents = [
    Document(
        page_content=text,
        metadata={
            "source": "paper_1.pdf",
            "page": 1,
            "year": 2024,
            "category": "AI"
        }
    )
]
```

---

## 2시간 구현 로드맵

### ⏱️ **0:00-0:15 | 환경 설정 & 프로젝트 구조**
- [ ] 프로젝트 디렉토리 생성
- [ ] requirements.txt 작성 및 pip install
- [ ] .env 파일 설정
- [ ] 소스 파일 생성 (config, embedder, vector_store 등)

### ⏱️ **0:15-0:35 | 데이터 준비 & 벡터 DB 구축**
- [ ] 논문 PDF 파일 준비 (최소 3-5개)
- [ ] Document Loader 구현
- [ ] Text Splitter 구현
- [ ] 임베딩 모델 로드 (오픈소스 추천)
- [ ] Chroma DB에 문서 저장

### ⏱️ **0:35-0:55 | RAG 파이프라인 구현**
- [ ] Retriever 설정
- [ ] RAG Chain 구현
- [ ] 프롬프트 템플릿 커스터마이징
- [ ] 기본 질의 테스트

### ⏱️ **0:55-1:10 | 테스트 & 통합**
- [ ] 샘플 질문으로 테스트
- [ ] 답변 품질 검증
- [ ] 출처 문서 확인
- [ ] 성능 측정

### ⏱️ **1:10-2:00 | API 통합 & 웹 인터페이스**
- [ ] FastAPI 서버 구현 (또는 Flask)
- [ ] RAG 엔드포인트 구현
- [ ] 간단한 웹 UI (HTML/JavaScript)
- [ ] 최종 테스트 및 배포

---

## 최신 동향 & 고급 기법 (2025년)

### 🌟 Self-RAG
자체 평가를 통해 검색 결과와 답변 품질을 동적으로 조정
```
질문 → 검색 → 검색 결과 평가 → 부족하면 재검색 → 답변
```

### 🌟 Adaptive RAG
사용자 쿼리 복잡도에 따라 검색 전략을 조정
```
간단한 질문: 직접 답변 (빠름)
복잡한 질문: 깊이 있는 검색 + 여러 단계 추론
```

### 🌟 Corrective RAG
검색된 문서의 관련성을 검증하고 필요시 재검색
```
검색 → 관련성 평가 → 낮으면 다른 전략으로 재검색
```

---

## 트러블슈팅

### 문제 1: "No module named 'langchain'"
```bash
pip install --upgrade langchain langchain-community
```

### 문제 2: 임베딩 모델 다운로드 실패
```python
# 더 작은 모델 사용
from langchain.embeddings import HuggingFaceEmbeddings
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
```

### 문제 3: OpenAI API 오류
```python
# 로컬 모델 사용으로 전환
from langchain.llms import Ollama
llm = Ollama(model="mistral")
```

### 문제 4: 메모리 부족
```python
# 배치 처리로 분할
def process_in_batches(documents, batch_size=10):
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        # 처리
```

---

## 참고 자료 (2025년 최신)

### 공식 문서
- [LangChain 공식 문서](https://docs.langchain.com/)
- [Chroma 벡터 DB](https://docs.trychroma.com/)
- [OpenAI API](https://platform.openai.com/docs/)

### 한국어 튜토리얼
- [WikiDocs - LangChain 입문부터 응용까지](https://wikidocs.net/book/14473)
- [테디노트 - LangChain RAG 파헤치기](https://teddylee777.github.io/langchain/rag-tutorial/)
- [HelloLlama - RAG 구현](https://hellollama.net/)

### 오픈소스 임베딩 모델
- `all-MiniLM-L6-v2`: 경량, 빠름 ⭐ 추천
- `multilingual-e5-large`: 다국어 지원
- `ko-e5`: 한국어 특화

### 벡터 DB 비교
| 이름 | 장점 | 단점 | 용도 |
|------|------|------|------|
| Chroma | 설정 간단, 로컬 | 기능 제한 | 학습, 프로토타입 |
| FAISS | 초고속 | 메모리만 저장 | 프로덕션 검색 |
| Pinecone | 클라우드 기반 | 유료 | 엔터프라이즈 |
| Milvus | 오픈소스 | 복잡한 설정 | 대규모 데이터 |

---

## 다음 단계

2시간 내 기본 구현 후:

1. **성능 최적화**
   - 검색 정확도 개선
   - 응답 시간 단축
   - 메모리 사용 최적화

2. **기능 확장**
   - 여러 문서 타입 지원 (PDF, DOCX, 웹페이지)
   - 실시간 문서 업데이트
   - 사용자 피드백 루프

3. **프로덕션 배포**
   - 서버 배포 (AWS, GCP, Azure)
   - 모니터링 및 로깅
   - 비용 최적화

---

**작성자**: AI 해커톤 참가자
**업데이트**: 2025-11-11
**상태**: 진행 중 ✅
