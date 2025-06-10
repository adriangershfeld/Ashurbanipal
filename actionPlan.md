# 🧠 Local AI Research Assistant – Full Development Roadmap w/ File Structure

This roadmap breaks down every stage of your local-first AI assistant project, specifying **exact files/modules** required for each step in both the **Python backend** and **TypeScript frontend**, assuming Vite + REST/WebSocket communication.

---

## 📁 Base Project Structure

```
project-root/
├── backend/
│   ├── app.py
│   ├── api/
│   │   ├── query.py
│   │   ├── ingest.py
│   │   ├── files.py
│   ├── embeddings/
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   ├── store.py
│   ├── utils/
│   │   ├── file_loader.py
│   │   ├── pdf_extractor.py
│   │   ├── clipboard_watcher.py
│   │   ├── browser_launcher.py
│   ├── data/
│   │   ├── corpus.db
│   │   └── vector_store/  # FAISS or Chroma
├── frontend/
│   ├── vite.config.ts
│   ├── index.html
│   ├── tsconfig.json
│   ├── public/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   ├── index.ts
│   │   ├── components/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── ResultList.tsx
│   │   │   ├── FileViewer.tsx
│   │   │   ├── ChatUI.tsx
│   │   ├── types/
│   │   │   ├── index.d.ts
│   ├── dist/  # build output
├── librewolf/
│   └── LibreWolf.exe + profile
├── scripts/
│   ├── launch_browser.py
│   ├── monitor_clipboard.py
│   └── scrape_session.py
├── README.md
├── requirements.txt
├── package.json
└── .env
```

---

## 🛠️ STAGE 1: Corpus Scanner + Embedder

### 🔹 Python Backend

* `file_loader.py`: Recursively walks through user-selected folders
* `pdf_extractor.py`: Extracts text using `PyMuPDF`, `pdfplumber`, or `unstructured`
* `chunker.py`: Breaks long texts into 300–500 token chunks
* `embedder.py`: Uses local `sentence-transformers` or quantized model
* `store.py`: Inserts embeddings + metadata into FAISS/Chroma
* `ingest.py`: Orchestrates the scan → extract → chunk → embed pipeline

### 🔹 Files Created

* `corpus.db`: SQLite file with file + chunk metadata
* `/vector_store/`: Folder containing the index

---

## 🌐 STAGE 2: Search, Retrieval & UI

### 🔹 Python Backend

* `query.py`: Takes a user query, embeds it, performs similarity search
* `files.py`: Opens original source files or returns structured metadata
* `app.py`: FastAPI server exposing `/query`, `/open`, `/meta` endpoints

### 🔹 TypeScript Frontend

* `SearchBar.tsx`: Input box, handles form logic
* `ResultList.tsx`: Displays search results with source highlights
* `FileViewer.tsx`: Optional, to preview docs or chunk context
* `api/index.ts`: HTTP client to talk to `/query` and `/open`
* `types/index.d.ts`: TS interfaces for result chunks, docs, tags

---

## 🤖 STAGE 3: Local Chat + Contextual RAG

### 🔹 Python Backend

* Extend `query.py` to support `rag_query(input: str, history: list)`
* Add local LLM inference module (`llm_infer.py`) using `llama.cpp` or similar
* Chat history stored in `corpus.db`

### 🔹 Frontend

* `ChatUI.tsx`: Full chat component, supports modes: "Ask AI", "Search Only"

---

## 🌍 STAGE 4: External Source Integration

### 🔹 Python Scripts

* `browser_launcher.py`: Opens LibreWolf Portable via CLI
* `clipboard_watcher.py`: Detects new copied text, writes to queue
* `scrape_session.py`: Monitors clipboard, sends content to `ingest.py`

### 🔹 Files Needed

* `librewolf/LibreWolf.exe`: Bundled browser
* `librewolf/profile/`: Preconfigured profile (optionally with uBlock)

---

## 📦 STAGE 5: Release & Packaging

### 🔹 Python

* `freeze_backend.py`: PyInstaller script

### 🔹 Node/Vite

* `vite.config.ts`: Configure static build

### 🔹 Bundle

* One folder with `/dist`, `/librewolf`, backend executable, etc.
* README.md with installation/setup instructions

---

## 🔚 Optional Advanced Features

* `auto_tagging.py`: NLP tagger for concepts, difficulty, domain
* `file_labeler.py`: Manual labeling of documents via UI
* `summarizer.py`: Extractive summary for large docs
* `cross_search.py`: Let users search across tags/topics

---

