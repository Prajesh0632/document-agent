# Document Agent — Nepal NIN Extraction Pipeline

An Azure Functions-based document intelligence pipeline that extracts structured
fields from **Nepal National Identity (NIN)** documents (scanned PDFs and images).

---

## Architecture

```
POST /api/nin-extract
        │
        ▼
┌─────────────────────┐
│   function_app.py   │  Azure Functions HTTP entry point
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ document_pipeline.py│  LangGraph orchestrator
└────────┬────────────┘
         │
    ┌────▼────────────────────────────────────┐
    │           LangGraph State Graph         │
    │                                         │
    │  load_image → preprocess → analyze_blur │
    │         ↓ blurry   ↓ borderline ↓clear  │
    │    flag_blur   deep_check    mark_ok    │
    │         ↓                       ↓       │
    │    ask_reupload ←──────────→ run_ocr   │
    │                                  ↓      │
    │                          extract_fields  │
    │                          (Gemini Flash)  │
    │                                  ↓      │
    │                         generate_report  │
    └─────────────────────────────────────────┘
```

## Extracted Fields

| Field              | Source              | Notes                         |
|--------------------|---------------------|-------------------------------|
| application_number | आवेदन नम्बर         | 16-digit number               |
| nin                | राष्ट्रिय परिचय नम्बर | Format: XXX-XXX-XXX-X        |
| first_name         | English section     | Title case                    |
| last_name          | English section     | Title case                    |
| dob_ad             | ई.सं.               | YYYY-MM-DD format             |

---

## Prerequisites

| Tool         | Version   | Notes                                       |
|--------------|-----------|---------------------------------------------|
| Python       | 3.11+     | (3.13.3 confirmed working)                  |
| Tesseract    | 5.5       | Must include `nep` tessdata                 |
| Poppler      | 26.02.0   | For PDF → image conversion                  |
| Node.js      | v24.16.0  | Optional — only needed for Azure Functions Core Tools |
| Gemini API   | free tier | gemini-1.5-flash model                      |

---

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.local` and add your Gemini API key:

```
GEMINI_API_KEY=your-key-from-aistudio.google.com
POPPLER_PATH=C:\path\to\poppler\Library\bin   # Windows only
```

Get a free Gemini API key at: https://aistudio.google.com/app/apikey

### 3. Run locally (no Azure tools needed)

```bash
python run_local.py
```

### 4. Test with curl

```bash
# Image upload
curl -X POST http://127.0.0.1:7071/api/nin-extract \
     -F "file=@/path/to/nin_document.jpg"

# PDF upload
curl -X POST http://127.0.0.1:7071/api/nin-extract \
     -F "file=@/path/to/nin_document.pdf"

# Health check
curl http://127.0.0.1:7071/api/health
```

---

## Example Response

**Success:**
```json
{
  "status": "success",
  "verdict": "clear",
  "blur_score": 0.8142,
  "extracted_fields": {
    "application_number": "7612345678901234",
    "nin": "123-456-789-0",
    "first_name": "Manoj",
    "last_name": "Niraula",
    "dob_ad": "1995-04-12"
  },
  "extraction_error": ""
}
```

**Rejected (blurry image):**
```json
{
  "status": "rejected",
  "verdict": "blurry",
  "blur_score": 0.1023,
  "reupload_message": "Image is not suitable for field extraction.\n\nPlease reupload..."
}
```

---

## Running Tests

```bash
# All tests (no Gemini key needed — blur tests use synthetic images)
python tests/test_pipeline.py

# With pytest
python -m pytest tests/ -v
```

---

## Project Structure

```
Document_Agent/
├── function_app.py              # Azure Functions HTTP entry point
├── config.py                    # Environment-aware settings
├── run_local.py                 # Local dev server (no Azure tools needed)
├── requirements.txt
├── .env.local                   # Local secrets (not committed)
├── host.json                    # Azure Functions host config
├── tests/
│   └── test_pipeline.py         # Smoke tests for all pipeline stages
└── document_agent/
    ├── agents/
    │   ├── intake_agent.py      # Standalone blur-check graph
    │   ├── ocr_agent.py         # LangGraph OCR node
    │   └── extraction_agent.py  # LangGraph Gemini extraction node
    ├── utils/
    │   ├── state.py             # DocumentState TypedDict
    │   ├── node.py              # All blur-check node functions
    │   ├── ocr_utils.py         # Dual-pass pytesseract OCR
    │   ├── pdf_utils.py         # PDF → PIL image conversion
    │   ├── gemini_utils.py      # Gemini Flash API wrapper
    │   └── tools.py             # LangChain tool stubs
    ├── prompts/
    │   └── nin_extraction_prompt.py  # Versioned extraction prompt
    └── pipeline/
        └── document_pipeline.py # Full LangGraph pipeline (entry point)
```
