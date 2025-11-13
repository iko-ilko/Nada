# 🗺️ RAG 시스템 구축 전체 로드맵

AI 해커톤을 위한 RAG 시스템 개발 완전 가이드

---

## 📚 문서 가이드

| 문서 | 내용 | 대상 | 시간 |
|------|------|------|------|
| **RAG_LEARNING_GUIDE.md** | RAG 기본 개념, 아키텍처, 심화 기술 | 모두 | 읽기 |
| **QUICK_START.md** | 단계별 구현 코드, CLI 버전 | 초보자 | 1-2시간 |
| **WEB_API_GUIDE.md** | FastAPI 웹 서버, 프론트엔드 | 중급자 | 1시간 |
| **PROJECT_ROADMAP.md** | 전체 흐름, 일정 | 모두 | 읽기 |

---

## 🎯 전체 구현 흐름

### Phase 1: 학습 (1시간)
```
RAG_LEARNING_GUIDE.md 읽기
├── RAG 개념 이해
├── 임베딩과 벡터 DB 학습
├── Langchain 기본 구조 파악
└── 2025년 최신 기술 동향 확인
```

### Phase 2: CLI 구현 (1-1.5시간)
```
QUICK_START.md 따라하기
├── 프로젝트 구조 생성
├── 문서 로드 및 청킹
├── 벡터 DB 구축
├── RAG 파이프라인 구현
└── 대화형 CLI 테스트
```

### Phase 3: 웹 API 구현 (1시간)
```
WEB_API_GUIDE.md 따라하기
├── FastAPI 서버 구현
├── REST API 엔드포인트
├── 웹 프론트엔드 (HTML/CSS/JS)
└── 브라우저에서 테스트
```

### Phase 4: 최적화 & 배포 (자유)
```
고급 기능 추가
├── 성능 튜닝
├── 캐싱 구현
├── 멀티턴 대화
├── Docker 배포
└── 클라우드 배포
```

---

## 🏗️ 시스템 아키텍처

### 전체 구조도
```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 인터페이스                          │
├──────────────────┬──────────────────┬───────────────────────┤
│   CLI (main.py)  │  웹 UI (HTML)    │   모바일 앱 (미래)    │
└────────┬─────────┴────────┬─────────┴───────────────┬────────┘
         │                  │                        │
         └──────────────────┼────────────────────────┘
                            │
                     ┌──────▼────────┐
                     │  FastAPI 서버  │
                     │  (api_server)  │
                     └──────┬─────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼─────┐    ┌───────▼────────┐  ┌────▼──────┐
    │  RAG      │    │  LLM 모델      │  │  벡터 DB  │
    │  Chain    │    │ (GPT-3.5/LLM)  │  │ (Chroma)  │
    └────┬─────┘    └────────────────┘  └────┬──────┘
         │                                     │
    ┌────▼──────────────────────────────┬────┘
    │                                   │
┌───▼─────────┐              ┌──────────▼─────┐
│ Retriever   │              │ Document Store │
│ (검색 엔진) │              │ (임베딩 벡터) │
└─────────────┘              └────────────────┘
         │
┌────────▼────────────────────────────────┐
│         문서 처리 파이프라인             │
├────────────────────────────────────────┤
│  1. 문서 로드 (PDF, TXT, etc)          │
│  2. 텍스트 분할 (청킹)                  │
│  3. 임베딩 생성 (벡터화)                │
│  4. 벡터 DB 저장                       │
└────────┬───────────────────────────────┘
         │
┌────────▼──────────────────────────┐
│      원본 데이터 저장소            │
├───────────────────────────────────┤
│  data/papers/                    │
│  ├── paper1.pdf                  │
│  ├── paper2.pdf                  │
│  └── ...                         │
└───────────────────────────────────┘
```

---

## 📊 데이터 흐름

### 인덱싱 단계 (1회성)
```
문서 파일
    ↓
[DocumentLoader]
    ↓
원본 텍스트 문서
    ↓
[TextSplitter]
    ↓
청크들 (300토큰 단위)
    ↓
[Embeddings] - HuggingFace 또는 OpenAI
    ↓
벡터 (예: 384차원)
    ↓
[Chroma VectorDB]
    ↓
메타데이터와 함께 저장
```

### 질의 단계 (사용자 매번)
```
사용자 질문
    ↓
[질문 임베딩]
    ↓
질문 벡터
    ↓
[벡터 DB 유사도 검색]
    ↓
상위 K개 문서 선택 (top_k=3)
    ↓
[프롬프트 구성]
    ↓
system_prompt + context + question
    ↓
[LLM]
    ↓
최종 답변
    ↓
사용자에게 반환
```

---

## 💻 코드 구조

```
rag_system/
│
├── 📄 설정 파일
│   ├── .env
│   ├── .gitignore
│   └── requirements.txt
│
├── 📂 src/ (코어 모듈)
│   ├── __init__.py
│   ├── config.py           # 설정 관리
│   ├── loader.py           # 문서 로드
│   ├── embedder.py         # 임베딩 처리
│   ├── db.py              # 벡터 DB 관리
│   └── rag.py             # RAG 파이프라인
│
├── 📂 web/ (웹 서버)
│   ├── api.py             # FastAPI 앱
│   ├── models.py          # Pydantic 모델
│   └── static/            # 프론트엔드
│       ├── index.html
│       ├── styles.css
│       └── script.js
│
├── 📂 data/ (데이터)
│   ├── papers/            # 논문 PDF
│   │   ├── paper1.pdf
│   │   └── ...
│   └── chroma_db/         # 벡터 DB
│
├── 🚀 실행 파일
│   ├── main.py            # CLI 버전
│   └── api_server.py      # API 서버
│
└── 📚 문서
    ├── RAG_LEARNING_GUIDE.md
    ├── QUICK_START.md
    ├── WEB_API_GUIDE.md
    └── PROJECT_ROADMAP.md
```

---

## ⏱️ 2시간 구현 일정 (상세)

### 시간표

#### **0:00 ~ 0:15 | 환경 설정 (15분)**
```
□ 프로젝트 디렉토리 생성
□ requirements.txt 작성
□ pip install 실행
□ .env 파일 작성 (API 키)
□ 소스 파일 템플릿 생성
```

#### **0:15 ~ 0:35 | 데이터 준비 및 벡터 DB (20분)**
```
□ 테스트용 PDF 파일 준비 (2-3개)
□ DocumentLoader 구현
□ TextSplitter 구현
□ EmbeddingManager 구현
□ VectorDB 구현
□ 첫 번째 인덱싱 (시간이 걸릴 수 있음)
```

#### **0:35 ~ 0:50 | RAG 파이프라인 (15분)**
```
□ RAGSystem 클래스 구현
□ Retriever 설정
□ Prompt Template 커스터마이징
□ LLM 연결
□ 테스트 질문 작성
```

#### **0:50 ~ 1:15 | CLI 테스트 및 기본 기능 (25분)**
```
□ main.py 작성
□ 기본 대화형 인터페이스
□ 샘플 질문 테스트
□ 답변 품질 확인
□ 출처 문서 검증
□ 성능 측정
```

#### **1:15 ~ 1:45 | 웹 API 구현 (30분)**
```
□ FastAPI 기본 앱 구성
□ /api/query 엔드포인트
□ Pydantic 모델 정의
□ CORS 설정
□ 기본 HTML UI
□ JavaScript로 API 호출
```

#### **1:45 ~ 2:00 | 최종 테스트 (15분)**
```
□ 웹 브라우저에서 테스트
□ API 응답 검증
□ UI/UX 확인
□ 오류 처리 점검
□ 문서 최종 검토
```

---

## 🎯 주요 선택지와 결정

### 1. LLM 선택

| 옵션 | 장점 | 단점 | 추천 |
|------|------|------|------|
| **OpenAI GPT-3.5** | 가장 정확함, 한국어 우수 | 비용 ($) | 본격 프로젝트 |
| **로컬 Ollama** | 무료, 프라이빗 | 느림, 품질 낮음 | 개발 단계 |
| **Hugging Face** | 무료, 빠름 | 한국어 부족 | 영문 프로젝트 |

**추천**: OpenAI API (신용카드 필요, 무료 크레딧)

### 2. 임베딩 모델 선택

| 모델 | 크기 | 속도 | 정확도 | 추천 |
|------|------|------|--------|------|
| **all-MiniLM-L6-v2** | 33MB | 빠름 | 중간 | ⭐ 기본 |
| **all-mpnet-base-v2** | 438MB | 느림 | 높음 | 정확도 중요 |
| **multilingual-e5** | 200MB | 중간 | 높음 | 다국어 |
| **ko-e5** | 200MB | 중간 | 매우높음 | 한국어 |

**추천**: `all-MiniLM-L6-v2` (빠른 시작용)

### 3. 벡터 DB 선택

| DB | 설정 | 성능 | 기능 | 추천 |
|----|----|------|------|------|
| **Chroma** | 매우 쉬움 | 중간 | 기본 | ⭐ 시작 |
| **FAISS** | 어려움 | 빠름 | 고급 | 대규모 |
| **Pinecone** | 쉬움 | 빠름 | 매우고급 | 클라우드 |
| **Milvus** | 복잡 | 빠름 | 고급 | 프로덕션 |

**추천**: `Chroma` (로컬, 간단, 배우기 쉬움)

---

## 🚀 실행 체크리스트

### 준비 단계
- [ ] Python 3.9+ 설치 확인
- [ ] pip 최신 버전 (`pip install --upgrade pip`)
- [ ] 테스트용 PDF 파일 2-3개 준비
- [ ] 텍스트 에디터/IDE 준비

### 환경 설정
- [ ] 프로젝트 디렉토리 생성
- [ ] 가상 환경 생성 (선택)
- [ ] requirements.txt 생성
- [ ] pip install 실행

### 코드 구현
- [ ] config.py 작성
- [ ] loader.py 작성
- [ ] embedder.py 작성
- [ ] db.py 작성
- [ ] rag.py 작성
- [ ] main.py 작성

### CLI 테스트
- [ ] 문서 로드 성공
- [ ] 임베딩 생성 성공
- [ ] 벡터 DB 저장 성공
- [ ] 샘플 질문 테스트
- [ ] 답변 품질 확인

### 웹 API (선택)
- [ ] api_server.py 작성
- [ ] models.py 작성
- [ ] HTML/CSS/JS 작성
- [ ] http://localhost:8000 접속 확인
- [ ] Swagger UI 테스트

### 최종 점검
- [ ] 에러 로깅 확인
- [ ] 성능 측정
- [ ] 코드 정리
- [ ] 주석 추가
- [ ] 문서 완성

---

## 📈 해커톤 이후 개선 방향

### 단기 (1주일)
1. **검색 품질 개선**
   - 프롬프트 엔지니어링
   - 청킹 전략 최적화
   - 임베딩 모델 비교

2. **사용자 경험**
   - UI 디자인 개선
   - 반응 속도 최적화
   - 모바일 대응

### 중기 (1개월)
1. **기능 확장**
   - 다양한 파일 형식 지원 (DOCX, PPTX)
   - 실시간 문서 업데이트
   - 사용자 피드백 시스템

2. **성능 최적화**
   - 캐싱 구현
   - 배치 처리
   - 로드 밸런싱

### 장기 (3개월 이상)
1. **엔터프라이즈 기능**
   - 사용자 인증
   - 접근 제어
   - 감사 로그

2. **고급 RAG 기법**
   - Self-RAG
   - Adaptive RAG
   - Multi-hop reasoning

3. **프로덕션 배포**
   - Kubernetes 배포
   - 모니터링 대시보드
   - SLA 관리

---

## 🎓 학습 자료 (최신)

### 공식 문서
- [LangChain Docs](https://docs.langchain.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)
- [Chroma Docs](https://docs.trychroma.com/)

### 한국어 튜토리얼
- [WikiDocs - LangChain](https://wikidocs.net/book/14473)
- [테디노트 - RAG 튜토리얼](https://teddylee777.github.io/langchain/rag-tutorial/)
- [HelloLlama - RAG 구현](https://hellollama.net/)

### 커뮤니티
- [LangChain Discord](https://discord.gg/langchain)
- [OpenAI Community Forum](https://community.openai.com/)
- [Reddit r/MachineLearning](https://www.reddit.com/r/MachineLearning/)

---

## 🔗 빠른 링크

**이 프로젝트의 모든 문서**:
1. **RAG_LEARNING_GUIDE.md** - 개념 이해
2. **QUICK_START.md** - 구현 따라하기
3. **WEB_API_GUIDE.md** - 웹 서버 구축
4. **PROJECT_ROADMAP.md** - 이 파일

---

## 💡 팁과 트릭

### 빠른 개발을 위한 팁
```python
# 1. 먼저 작은 데이터로 테스트
documents = load_all_pdfs()  # 처음엔 1-2개만
vectors = embed_and_store(documents)

# 2. 로깅을 충분히 사용
import logging
logging.basicConfig(level=logging.DEBUG)

# 3. 중간 결과 저장
import pickle
with open('debug.pkl', 'wb') as f:
    pickle.dump(result, f)

# 4. 개발 중 API 키 테스트
import os
assert os.getenv('OPENAI_API_KEY'), "API 키 설정 필요"
```

### 문제 해결
```bash
# 메모리 부족 시
export PYTORCH_ENABLE_MPS_FALLBACK=1

# 프로세스 강제 종료
pkill -f "python main.py"

# 벡터 DB 초기화
rm -rf chroma_db/

# 의존성 재설치
pip install --upgrade --force-reinstall langchain
```

---

## 📞 문제 발생시

### 일반적인 오류

| 오류 | 원인 | 해결 |
|------|------|------|
| `ModuleNotFoundError` | 패키지 미설치 | `pip install` |
| `OPENAI_API_KEY error` | API 키 없음 | `.env` 파일 확인 |
| `OutOfMemory` | 메모리 부족 | 모델 크기 줄이기 |
| `No embeddings` | 임베딩 모델 로드 실패 | 인터넷 연결 확인 |

### 도움 받기
1. 에러 메시지 전체 복사
2. 다음 정보 포함:
   - OS, Python 버전
   - 설치된 패키지 버전 (`pip list`)
   - 어떤 단계에서 실패했는지
3. 온라인 커뮤니티에 질문

---

## 🎉 축하합니다!

이 가이드를 따라 완성하면:
- ✅ RAG의 기본 원리 이해
- ✅ LangChain으로 RAG 파이프라인 구축
- ✅ 벡터 DB를 통한 효율적 검색
- ✅ FastAPI로 웹 서비스 운영
- ✅ AI 해커톤 완성

**다음은 당신의 창의성과 도메인 지식을 추가할 차례입니다! 🚀**

---

**마지막 업데이트**: 2025-11-11
**작성자**: AI 해커톤 참가자
**라이선스**: MIT
