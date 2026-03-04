# RAG Pipeline Upgrades

This document details the major upgrades made to the RAG pipeline to improve accuracy, format support, and response quality.

## Retrieval Flow: Before vs. After

### Previous Flow
```text
Query -> Vector Search (Cosine Similarity) -> Top K Chunks -> Response
```

### New Hybrid Flow
```text
Query -> LLM Intent Classifier (Metadata Topic Extraction)
      -> Parallel Search:
         1. BM25 (Keyword Retrieval)
         2. Vector Store (Semantic Retrieval)
      -> reciprocal_rank_fusion (Merge Results)
      -> rerank_stage_1: FlashRank (Lightweight cross-encoder prune)
      -> rerank_stage_2: BGE Cross-Encoder (Heavy precision reranking)
      -> Confidence Filter (Threshold: 0.4)
      -> LLM Judge (Response evaluation & regeneration)
      -> Final Answer with Source Attribution
```

## Core Library Table

| Library | Purpose | Status | Link |
|---------|---------|--------|------|
| `unstructured` | Universal document partitioning (PDF, DOCX, etc.) | **New** | [unstructured](https://unstructured.io/) |
| `BGE-Reranker` | Precision second-stage reranking (Cross-Encoder) | **New** | [BAAI/BGE](https://github.com/FlagOpen/FlagEmbedding) |
| `FlashRank` | Ultra-fast first-stage reranking | **New** | [FlashRank](https://github.com/PrithivirajDamodaran/FlashRank) |
| `litellm` | Unified interface for Ollama, OpenAI, Gemini | **New** | [LiteLLM](https://docs.litellm.ai/) |
| `pytesseract` | OCR for scanned documents and screenshots | **New** | [Tesseract](https://github.com/madmantools/pytesseract) |
| `rank_bm25` | Industrial-grade keyword retrieval | **New** | [RankBM25](https://github.com/dorianbrown/rank_bm25) |
| `ollama` | Local LLM execution (Llama 3.2, LLaVA) | Existing | [Ollama](https://ollama.com/) |

## Supported File Formats

| Category | Formats | Handler | Features |
|----------|---------|---------|----------|
| Documents | PDF, DOCX, PPTX, XLSX, CSV | `unstructured` | Auto-detects layout, handles tables |
| Web/Code | MB, HTML, TXT, JSON | `unstructured` | Clean text extraction |
| Images | PNG, JPG, JPEG, TIFF | `LLaVA` + `OCR` | Visual description + text extraction |
| Scanned | Scanned PDF | `pytesseract` | Automatic OCR fallback |

## LLM Judge & Governance
- **Intent Classifier**: Before searching, an LLM classifies the query to apply precise metadata filters (e.g., locking search to "S3" documents).
- **Confidence Threshold**: Any result with a reranking score < 0.4 is discarded to prevent hallucinations from irrelevant context.
- **LLM Judge**: After generating an answer, a second LLM (`llama3.2`) evaluates if the answer is grounded in the provided context (Score 1-5).
    - Score < 3 triggers an automatic regeneration with stricter "context-only" instructions.

## Running Locally
1. **Pull Models**:
   ```bash
   ollama pull llama3.2
   ollama pull llava
   ```
2. **Install Tesseract**:
   - Mac: `brew install tesseract`
   - Linux: `sudo apt install tesseract-ocr`
3. **Environment**:
   - Add `OLLAMA_TEXT_MODEL=llama3.2` and `OLLAMA_VISION_MODEL=llava` to `.env`.
