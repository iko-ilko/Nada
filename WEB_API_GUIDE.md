# 🌐 RAG 시스템 웹 API 구현 가이드

FastAPI를 사용한 REST API 서버 구현 (QUICK_START.md 이후 진행)

---

## 📋 개요

- **프레임워크**: FastAPI (빠르고 현대적)
- **데이터베이스**: Chroma (QUICK_START와 동일)
- **배포**: Uvicorn 로컬 서버
- **시간**: ~30분

---

## 🚀 빠른 시작 (API만)

### 1. 필수 라이브러리 추가
```bash
pip install fastapi uvicorn pydantic
```

### 2. API 서버 코드
```python
# api_server.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

# 기존 RAG 시스템 임포트
from config import Config
from embedder import EmbeddingManager
from db import VectorDB
from rag import RAGSystem

# 요청/응답 모델
class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = Config.TOP_K

class SourceDocument(BaseModel):
    source: str
    page: int
    content: str

class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]

# FastAPI 앱 초기화
app = FastAPI(
    title="RAG System API",
    description="논문 검색 RAG 시스템",
    version="1.0.0"
)

# CORS 설정 (프론트엔드 연결용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수로 RAG 시스템 저장
rag_system = None

@app.on_event("startup")
async def startup():
    """서버 시작시 RAG 시스템 초기화"""
    global rag_system

    print("🔄 RAG 시스템 초기화 중...")

    # 임베딩 초기화
    embedding_manager = EmbeddingManager()
    embeddings = embedding_manager.get_embeddings()

    # 벡터 DB 로드
    vector_db = VectorDB(embeddings)
    if not os.path.exists(Config.CHROMA_DB_PATH):
        raise Exception("벡터 DB를 찾을 수 없습니다. QUICK_START.md를 먼저 실행하세요.")

    vector_db.load_vectorstore()
    retriever = vector_db.get_retriever()

    # RAG 시스템 초기화
    rag_system = RAGSystem(retriever)
    print("✅ RAG 시스템 준비 완료")

@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": "RAG System API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """질문 처리 엔드포인트"""
    if not rag_system:
        raise HTTPException(
            status_code=503,
            detail="RAG 시스템이 준비되지 않았습니다"
        )

    if not request.question.strip():
        raise HTTPException(
            status_code=400,
            detail="질문을 입력해주세요"
        )

    try:
        result = rag_system.query(request.question)

        # 응답 포맷팅
        sources = [
            SourceDocument(
                source=doc.metadata.get("source", "Unknown"),
                page=doc.metadata.get("page", 0),
                content=doc.page_content[:200]  # 처음 200자만
            )
            for doc in result["sources"]
        ]

        return QueryResponse(
            answer=result["answer"],
            sources=sources
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류: {str(e)}"
        )

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "rag_system": "ready" if rag_system else "not ready"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. 실행
```bash
python api_server.py

# 또는
uvicorn api_server:app --reload
```

### 4. API 테스트
```bash
# Swagger UI 접속
http://localhost:8000/docs

# cURL로 테스트
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "논문의 주요 내용은?"}'
```

---

## 📐 완전한 구현

### 프로젝트 구조
```
rag_system/
├── src/
│   ├── config.py
│   ├── loader.py
│   ├── embedder.py
│   ├── db.py
│   └── rag.py
├── web/
│   ├── api.py           # FastAPI 앱
│   ├── models.py        # Pydantic 모델
│   └── static/
│       ├── index.html
│       └── styles.css
├── data/papers/
├── chroma_db/
├── requirements.txt
├── .env
├── main.py             # CLI 버전
└── api_server.py       # API 버전
```

### Step 1: models.py - 데이터 모델
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class QueryRequest(BaseModel):
    """질문 요청"""
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: Optional[int] = Field(default=3, ge=1, le=10)
    include_content: Optional[bool] = Field(default=False)

    class Config:
        examples = {
            "question": "이 논문의 주요 기여는 무엇인가?",
            "top_k": 3
        }

class SourceMetadata(BaseModel):
    """출처 메타데이터"""
    source: str
    page: Optional[int] = None
    filepath: Optional[str] = None

class SourceDocument(BaseModel):
    """출처 문서"""
    content: str = Field(..., description="문서 내용")
    metadata: SourceMetadata

class QueryResponse(BaseModel):
    """질문 응답"""
    answer: str
    sources: List[SourceDocument]
    query_time: float = Field(..., description="쿼리 처리 시간(초)")

class ErrorResponse(BaseModel):
    """오류 응답"""
    error: str
    detail: Optional[str] = None
```

### Step 2: api.py - FastAPI 앱
```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import time
import logging
from typing import Optional

from config import Config
from embedder import EmbeddingManager
from db import VectorDB
from rag import RAGSystem
from models import QueryRequest, QueryResponse, SourceDocument, SourceMetadata

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 RAG 시스템
class State:
    rag_system: Optional[RAGSystem] = None
    status: str = "initializing"

state = State()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작
    logger.info("🔄 RAG 시스템 초기화 중...")
    try:
        embedding_manager = EmbeddingManager()
        embeddings = embedding_manager.get_embeddings()

        vector_db = VectorDB(embeddings)
        if not os.path.exists(Config.CHROMA_DB_PATH):
            raise Exception("벡터 DB를 찾을 수 없습니다")

        vector_db.load_vectorstore()
        retriever = vector_db.get_retriever()
        state.rag_system = RAGSystem(retriever)
        state.status = "ready"
        logger.info("✅ RAG 시스템 준비 완료")
    except Exception as e:
        state.status = "failed"
        logger.error(f"❌ 초기화 실패: {e}")
        raise

    yield

    # 종료
    logger.info("🛑 서버 종료")

# FastAPI 앱
app = FastAPI(
    title="RAG System API",
    description="논문 검색 및 분석을 위한 RAG 시스템 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 제공 (프론트엔드)
if os.path.exists("web/static"):
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

# 라우트

@app.get("/")
async def root():
    """루트 경로"""
    return {
        "message": "RAG System API",
        "docs": "/docs",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": state.status,
        "rag_system": "ready" if state.rag_system else "not ready",
        "db_path": Config.CHROMA_DB_PATH
    }

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """질문 처리"""
    if state.status != "ready":
        raise HTTPException(
            status_code=503,
            detail=f"서비스 준비 중: {state.status}"
        )

    start_time = time.time()

    try:
        result = state.rag_system.query(request.question)

        sources = [
            SourceDocument(
                content=doc.page_content,
                metadata=SourceMetadata(
                    source=doc.metadata.get("source", "Unknown"),
                    page=doc.metadata.get("page"),
                    filepath=doc.metadata.get("filepath")
                )
            )
            for doc in result["sources"]
        ]

        query_time = time.time() - start_time

        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            query_time=query_time
        )

    except Exception as e:
        logger.error(f"❌ 질의 처리 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"질의 처리 중 오류: {str(e)}"
        )

@app.get("/api/config")
async def get_config():
    """현재 설정 반환"""
    return {
        "embedding_model": Config.EMBEDDING_MODEL,
        "llm_model": Config.LLM_MODEL,
        "chunk_size": Config.CHUNK_SIZE,
        "top_k": Config.TOP_K,
        "db_path": Config.CHROMA_DB_PATH
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
```

### Step 3: 웹 프론트엔드

#### web/static/index.html
```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG 논문 검색 시스템</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>📚 논문 RAG 검색 시스템</h1>
            <p class="subtitle">AI를 활용한 지능형 논문 검색 및 분석</p>
        </header>

        <main class="main">
            <div class="search-section">
                <div class="input-group">
                    <textarea
                        id="questionInput"
                        placeholder="논문에 대해 질문해주세요... 예: 이 논문의 주요 기여는?"
                        rows="3"
                    ></textarea>
                    <button id="searchBtn" class="btn btn-primary">
                        🔍 검색
                    </button>
                </div>

                <div class="options">
                    <label>
                        상위 결과 개수:
                        <select id="topK">
                            <option value="1">1개</option>
                            <option value="3" selected>3개</option>
                            <option value="5">5개</option>
                            <option value="10">10개</option>
                        </select>
                    </label>
                </div>
            </div>

            <div id="result" class="result hidden">
                <div class="answer-section">
                    <h2>💬 답변</h2>
                    <div id="answerText" class="answer-text"></div>
                    <div id="queryTime" class="query-time"></div>
                </div>

                <div class="sources-section">
                    <h2>📚 출처 문서</h2>
                    <div id="sourcesList" class="sources-list"></div>
                </div>
            </div>

            <div id="loading" class="loading hidden">
                <div class="spinner"></div>
                <p>검색 중...</p>
            </div>

            <div id="error" class="error hidden">
                <div id="errorText"></div>
            </div>
        </main>

        <footer class="footer">
            <p>⚡ 빠른 응답 • 🎯 정확한 결과 • 📖 출처 확인</p>
        </footer>
    </div>

    <script src="script.js"></script>
</body>
</html>
```

#### web/static/styles.css
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 900px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.header {
    text-align: center;
    color: white;
    margin-bottom: 40px;
}

.header h1 {
    font-size: 2.5rem;
    margin-bottom: 10px;
}

.subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
}

.main {
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 40px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.search-section {
    margin-bottom: 30px;
}

.input-group {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}

textarea {
    flex: 1;
    padding: 15px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    font-family: inherit;
    resize: vertical;
    transition: border-color 0.3s;
}

textarea:focus {
    outline: none;
    border-color: #667eea;
}

.btn {
    padding: 15px 30px;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    transition: all 0.3s;
    white-space: nowrap;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
}

.btn-primary:active {
    transform: translateY(0);
}

.options {
    display: flex;
    gap: 15px;
}

.options label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.95rem;
}

select {
    padding: 8px 12px;
    border: 2px solid #e0e0e0;
    border-radius: 6px;
    font-size: 0.95rem;
    cursor: pointer;
}

.result {
    display: none;
}

.result.hidden {
    display: none !important;
}

.answer-section,
.sources-section {
    margin-bottom: 30px;
}

.answer-section h2,
.sources-section h2 {
    font-size: 1.3rem;
    margin-bottom: 15px;
    color: #333;
}

.answer-text {
    background: #f8f9fa;
    padding: 20px;
    border-left: 4px solid #667eea;
    border-radius: 6px;
    line-height: 1.6;
    color: #555;
    white-space: pre-wrap;
    word-break: break-word;
}

.query-time {
    margin-top: 10px;
    font-size: 0.85rem;
    color: #999;
}

.sources-list {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.source-item {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 6px;
    border-left: 4px solid #764ba2;
}

.source-item strong {
    color: #667eea;
    display: block;
    margin-bottom: 8px;
}

.source-content {
    color: #666;
    font-size: 0.9rem;
    line-height: 1.5;
}

.loading,
.error {
    display: none;
    text-align: center;
    padding: 40px;
}

.loading.hidden,
.error.hidden {
    display: none !important;
}

.spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #e0e0e0;
    border-top-color: #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.error {
    background: #fee;
    border: 2px solid #fcc;
    border-radius: 6px;
    color: #c33;
}

.footer {
    text-align: center;
    color: white;
    padding: 20px;
    opacity: 0.9;
}

@media (max-width: 600px) {
    .header h1 {
        font-size: 1.8rem;
    }

    .main {
        padding: 20px;
    }

    .input-group {
        flex-direction: column;
    }

    .btn {
        width: 100%;
    }
}
```

#### web/static/script.js
```javascript
const API_BASE = '/api';
const questionInput = document.getElementById('questionInput');
const searchBtn = document.getElementById('searchBtn');
const resultDiv = document.getElementById('result');
const loadingDiv = document.getElementById('loading');
const errorDiv = document.getElementById('error');
const topKSelect = document.getElementById('topK');

// 검색 함수
async function search() {
    const question = questionInput.value.trim();

    if (!question) {
        showError('질문을 입력해주세요');
        return;
    }

    showLoading(true);
    hideError();

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                question: question,
                top_k: parseInt(topKSelect.value)
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '요청 실패');
        }

        const result = await response.json();
        displayResult(result);

    } catch (error) {
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// 결과 표시
function displayResult(result) {
    // 답변
    const answerText = document.getElementById('answerText');
    answerText.textContent = result.answer;

    // 쿼리 시간
    const queryTime = document.getElementById('queryTime');
    queryTime.textContent = `처리 시간: ${result.query_time.toFixed(2)}초`;

    // 출처
    const sourcesList = document.getElementById('sourcesList');
    sourcesList.innerHTML = '';

    result.sources.forEach((source, index) => {
        const item = document.createElement('div');
        item.className = 'source-item';
        item.innerHTML = `
            <strong>${index + 1}. ${source.metadata.source}</strong>
            <div class="source-content">${source.content}</div>
        `;
        sourcesList.appendChild(item);
    });

    resultDiv.classList.remove('hidden');
}

// UI 헬퍼 함수
function showLoading(show) {
    loadingDiv.classList.toggle('hidden', !show);
}

function showError(message) {
    errorDiv.classList.remove('hidden');
    document.getElementById('errorText').textContent = '❌ ' + message;
}

function hideError() {
    errorDiv.classList.add('hidden');
}

// 이벤트 리스너
searchBtn.addEventListener('click', search);
questionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
        search();
    }
});

// 초기화
document.addEventListener('DOMContentLoaded', async () => {
    // 헬스 체크
    try {
        const response = await fetch(`${API_BASE}/health`);
        const health = await response.json();
        console.log('서버 상태:', health);
    } catch (error) {
        showError('서버 연결 실패');
    }
});
```

---

## 🚀 실행 방법

### 1. 준비
```bash
# 1. QUICK_START.md의 기본 RAG 시스템 구축 완료 필수
# 2. 추가 라이브러리 설치
pip install fastapi uvicorn

# 3. web/static/ 디렉토리 생성
mkdir -p web/static
# 위의 HTML, CSS, JS 파일 저장
```

### 2. 실행
```bash
python api_server.py

# 또는 (개발 모드)
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### 3. 접속
```
- API Swagger UI: http://localhost:8000/docs
- 웹 인터페이스: http://localhost:8000/static/index.html
- API 직접 호출: POST http://localhost:8000/api/query
```

---

## 📊 API 엔드포인트

### GET /
루트 경로
```
응답: {"message": "RAG System API", "docs": "/docs"}
```

### POST /api/query
질문 처리
```
요청:
{
  "question": "논문의 주요 기여는?",
  "top_k": 3
}

응답:
{
  "answer": "이 논문의 주요 기여는...",
  "sources": [
    {
      "content": "...",
      "metadata": {
        "source": "paper1.pdf",
        "page": 3
      }
    }
  ],
  "query_time": 2.34
}
```

### GET /api/health
헬스 체크
```
응답:
{
  "status": "ready",
  "rag_system": "ready",
  "db_path": "./chroma_db"
}
```

### GET /api/config
현재 설정 조회
```
응답:
{
  "embedding_model": "all-MiniLM-L6-v2",
  "llm_model": "gpt-3.5-turbo",
  "chunk_size": 300,
  "top_k": 3
}
```

---

## 🔒 프로덕션 배포

### Docker 컨테이너화
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "api_server.py"]
```

### 빌드 및 실행
```bash
docker build -t rag-system .
docker run -p 8000:8000 -v $(pwd)/data:/app/data rag-system
```

### 환경 변수
```bash
export OPENAI_API_KEY=sk-...
export LLM_MODEL=gpt-3.5-turbo
export EMBEDDING_MODEL=all-MiniLM-L6-v2
python api_server.py
```

---

## 📈 성능 최적화

### 1. 응답 캐싱
```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_query(question: str):
    # 캐싱된 결과 반환
    pass
```

### 2. 비동기 처리
```python
from asyncio import create_task

@app.post("/api/query/async")
async def async_query(request: QueryRequest):
    task = create_task(process_query(request.question))
    return {"task_id": id(task)}
```

### 3. 로드 밸런싱
```bash
# Gunicorn으로 여러 워커 실행
gunicorn api_server:app -w 4 -k uvicorn.workers.UvicornWorker
```

---

**웹 API 구현 완료! 🎉**
