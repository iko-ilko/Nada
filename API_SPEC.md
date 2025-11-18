# NADA AI RAG API Specification

**Project:** NADA AI RAG - Beauty Coaching Web Service
**Version:** 1.0.0
**Tech Stack:** FastAPI, LangChain, Chroma, OpenAI GPT-4o-mini

---

## Endpoint

### POST `/api/analyze`

Analyzes user image and input using hybrid RAG to provide beauty coaching insights.

**Request:**
- Content-Type: `multipart/form-data`
- Parameters:
  - `image_file` (File, required): Image to analyze
  - `user_state` (String, required): User question/request

**Response:**
- Content-Type: `application/json`

**Success Response (200 OK):**
```json
{
  "status": "success",
  "analysis": {
    "Hair": {
      "status": "Hair condition summary",
      "improvement_tips": ["Action 1", "Action 2"]
    },
    "Skin": {
      "status": "Skin condition summary",
      "improvement_tips": ["Action 1", "Action 2"]
    },
    "Contour": {
      "status": "Contour/facial shape summary",
      "improvement_tips": ["Action 1", "Action 2"]
    }
  },
  "references": ["paper1.pdf", "paper2.pdf", "paper3.pdf"]
}
```

**Error Response (500):**
```json
{
  "status": "error",
  "analysis": {},
  "error": "Error message"
}
```

---

## Processing Pipeline

1. **Image Upload** - Upload to Cloudinary with time limit (5 min)
2. **Hybrid Search** - Dense (vector) + BM25 (keyword) + RRF (rank fusion) → 7 documents
3. **Query Optimization** - LLM analyzes image and generates optimized search query
4. **Final Analysis** - LLM provides beauty coaching based on documents + image
5. **Logging** - Save results to JSON log file

---

## Request/Response Models

```python
# Request
class AnalysisRequest:
    image_file: UploadFile      # User uploaded image
    user_state: str             # User question

# Response
class AnalysisResponse(BaseModel):
    status: str                 # "success" or "error"
    analysis: Dict[str, Any]    # Analysis result (JSON)
    error: Optional[str]        # Error message if failed
```

---

## Search Metrics

Retrieved documents contain these scores:

| Score | Range | Description |
|-------|-------|-------------|
| `dense_score` | 0.0-1.0 | Vector similarity (cosine) |
| `bm25_score` | null | Keyword score (not implemented) |
| `rrf_score` | 0.0-1.0 | Reciprocal Rank Fusion score |

---

## Log File

**Location:** `api/logs/analysis_{YYYYMMDD_HHMMSS}.json`

**Structure:**
```json
{
  "timestamp": "2025-11-18T20:19:36.123456",
  "metadata": {
    "config": {
      "LLM_MODEL": "gpt-4o-mini",
      "EMBEDDING_MODEL": "intfloat/multilingual-e5-large",
      "IMAGE_DETAIL": "low",
      "CHUNK_SIZE": 1000,
      "TOP_K": 7
    },
    "image": {
      "url": "https://res.cloudinary.com/...",
      "detail_level": "low"
    },
    "input": {
      "user_state": "User question"
    },
    "search": {
      "total_results": 7,
      "llm_raw_response": {
        "image_analysis": {
          "hair": "...",
          "skin": "...",
          "contour": "..."
        },
        "search_query": "..."
      },
      "papers": [
        {
          "rank": 1,
          "source": "paper.pdf",
          "page": 13,
          "dense_score": 0.326,
          "bm25_score": null,
          "rrf_score": 0.016,
          "content_preview": "...",
          "full_content": "..."
        }
      ]
    }
  },
  "analysis": {
    "topic": {
      "current_state": "...",
      "recommendations": "..."
    }
  }
}
```

---

## Configuration

**Environment Variables (.env):**
```bash
OPEN_API_KEY=sk-...
CLOUDINARY_CLOUD_NAME=...
CLOUDINARY_API_KEY=...
CLOUDINARY_API_SECRET=...
```

**Settings (config.py):**
```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "intfloat/multilingual-e5-large"
NORMALIZE_EMBEDDINGS = True
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.7
TOP_K = 7
RRF_K = 60
IMAGE_DETAIL = "low"
CLOUDINARY_EXPIRE_MINUTES = 5
```

---

## Error Codes

| Situation | Status | Message |
|-----------|--------|---------|
| Vector DB not found | 500 | Vector DB load failed |
| Cloudinary upload failed | 500 | Image upload failed |
| LLM analysis failed | 500 | Analysis error |
| Missing image_file | 422 | Missing required field |
| Missing user_state | 422 | Missing required field |

---

## Example

**Request:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "image_file=@photo.jpg" \
  -F "user_state=How to brighten skin tone?"
```

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "Hair": {
      "status": "Healthy hair with good volume and shine. Natural brown tone with slight waves.",
      "improvement_tips": [
        "Use weekly deep conditioning treatment to maintain moisture",
        "Apply hair oil serum on damp hair before blow drying"
      ]
    },
    "Skin": {
      "status": "Fair complexion with balanced skin tone. Minor dryness on cheeks, good overall hydration.",
      "improvement_tips": [
        "Use vitamin C serum in the morning for brightening",
        "Apply lightweight moisturizer immediately after cleansing while skin is damp"
      ]
    },
    "Contour": {
      "status": "Well-proportioned facial structure with balanced features. Good definition in cheekbones and jawline.",
      "improvement_tips": [
        "Apply contour with warm brown shade slightly below cheekbones",
        "Use highlighter on high points of cheekbones and above eyebrows"
      ]
    }
  },
  "references": [
    "피부톤개선연구.pdf",
    "비타민C세럼효과.pdf",
    "메이크업기술가이드.pdf"
  ]
}
```

---

## Performance

| Task | Time |
|------|------|
| Image upload | 1-3s |
| Hybrid search | 2-5s |
| Query generation | 3-8s |
| LLM analysis | 8-15s |
| **Total** | **20-30s** |
