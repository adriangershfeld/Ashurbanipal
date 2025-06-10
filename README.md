# Ashurbanipal - Local AI Research Assistant

A privacy-focused, local-first AI research assistant that helps you search, analyze, and chat with your document corpus using semantic search and RAG (Retrieval-Augmented Generation).

## 🚀 Features

- **Semantic Search**: Find relevant content across your documents using AI embeddings
- **RAG Chat**: Ask questions and get contextual answers from your document corpus
- **Multi-format Support**: PDF, TXT, MD, DOCX document processing
- **Browser Integration**: LibreWolf integration for research sessions with clipboard monitoring
- **Privacy-First**: All processing happens locally, no data leaves your machine
- **Modern UI**: Clean, responsive TypeScript/React frontend

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **LibreWolf Portable** (already included in `/librewolf/`)

## 🛠️ Installation & Setup

### 1. Backend Setup

```powershell
# Navigate to the project directory
cd C:\Users\Agency\Desktop\dev\Ashurbanipal

# Install Python dependencies
pip install -r requirements.txt

# Start the FastAPI backend
cd backend
python app.py
```

The backend will be available at `http://127.0.0.1:8000`

### 2. Frontend Setup

```powershell
# In a new terminal, navigate to frontend
cd frontend

# Install Node dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 📚 Usage

### Document Ingestion

1. **Via API**: Send POST requests to `/api/ingest/folder` with folder paths
2. **Via Scripts**: Use the Python scripts in `/scripts/` directory

```powershell
# Example: Ingest a folder of documents
python scripts/ingest_documents.py "C:\path\to\your\documents"
```

### Search & Chat

1. Open the web interface at `http://localhost:5173`
2. Use the **Search** tab for semantic document search
3. Use the **Chat** tab for conversational queries with RAG
4. Use the **Files** tab to browse and manage your corpus

### Research Sessions

Launch integrated research sessions with browser + clipboard monitoring:

```powershell
# Start a research session with optional search query
python scripts/scrape_session.py "AI research topics"
```

This will:
- Launch LibreWolf browser with your search query
- Monitor clipboard for copied text
- Automatically capture and store research content

## 🗂️ Project Structure

```
Ashurbanipal/
├── backend/                 # Python FastAPI backend
│   ├── app.py              # Main application
│   ├── api/                # API endpoints
│   ├── embeddings/         # Vector search & embeddings
│   ├── utils/              # Utilities (PDF, clipboard, browser)
│   └── data/               # Database & vector storage
├── frontend/               # TypeScript React frontend  
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── api/           # API client
│   │   └── types/         # TypeScript definitions
│   └── dist/              # Built frontend (after npm run build)
├── librewolf/             # Portable browser
├── scripts/               # Utility scripts
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and adjust settings:

```bash
# Database
DATABASE_URL=sqlite:///./data/corpus.db
VECTOR_STORE_PATH=./data/vector_store

# Embedding Model  
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
```

### LibreWolf Configuration

The included LibreWolf portable browser is pre-configured for research:
- Privacy-focused settings
- Ad-blocking ready
- Custom profile in `/librewolf/Profiles/Default/`

## 📊 API Endpoints

### Search & Query
- `POST /api/search` - Semantic search
- `POST /api/chat` - RAG chat
- `GET /api/similar/{chunk_id}` - Find similar chunks

### Document Management
- `POST /api/ingest/folder` - Ingest document folder
- `POST /api/ingest/file` - Upload single file
- `GET /api/files` - List all files
- `GET /api/files/{file_id}` - Get file details

### System
- `GET /health` - Health check
- `GET /api/ingest/status` - Corpus statistics

## 🚧 Development Status

### ✅ Completed
- [x] Project structure and scaffolding
- [x] FastAPI backend with API endpoints
- [x] React frontend with modern UI
- [x] Document processing utilities
- [x] LibreWolf integration
- [x] Clipboard monitoring

### 🔄 In Progress  
- [ ] Vector embedding implementation
- [ ] Database integration (SQLite + FAISS)
- [ ] Local LLM integration
- [ ] File management UI

### 📋 Planned
- [ ] Auto-tagging and categorization
- [ ] Document summarization
- [ ] Cross-reference search
- [ ] Packaging for distribution

## 🤝 Contributing

This is a local development project. Feel free to modify and extend based on your research needs.

## 📝 License

MIT License - see LICENSE file for details.

---

**Ashurbanipal** - Named after the ancient Assyrian king who created one of the world's first organized libraries. Perfect for a modern digital research assistant! 📚
