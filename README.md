# Ptaḥ - Local AI Research Assistant

A privacy-focused, local-first AI research assistant using semantic search and RAG.

## 🛠️ Quick Start

### Launch Options

Use the `launcher.py` script to manage all components:

```bash
# Full application
python launcher.py

# Backend only (API development)
python launcher.py --no-frontend --no-browser

# Frontend only (UI development)
python launcher.py --no-backend --no-browser

# With search query
python launcher.py --search "AI research"

# Install dependencies
python launcher.py --install-deps

# Check status
python launcher.py --status

# Stop all components
python launcher.py --stop
```

### VS Code Integration

- **Ctrl+Shift+P** → "Tasks: Run Task" → "Start Ptaḥ (Full)"
- **F5** → "Debug Ptaḥ Launcher"

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **LibreWolf Portable** (included in `/librewolf/`)

## 🚧 Features To Be Implemented

### **File Management UI (20% Complete)**

**Status**: Basic structure exists, needs implementation

- [ ] **File Upload Interface**: Drag-and-drop upload with progress
- [ ] **Document Management**: View, organize, and delete documents
- [ ] **Batch Processing**: Folder upload and bulk operations
- [ ] **File Preview**: In-browser document viewing

### **Browser & Automation Integration (15% Complete)**

**Status**: Infrastructure ready, automation needs connection

- [ ] **Browser Integration**: Auto-launch and session management
- [ ] **Clipboard Monitoring**: Real-time content capture and processing
- [ ] **Web Scraping**: Automated research session recording
- [ ] **Advanced Search**: Filters, faceted search, date ranges

**Files to complete**:

- `backend/utils/browser_launcher.py` (complete automation)
- `backend/utils/clipboard_watcher.py` (real-time monitoring)
- `scripts/scrape_session.py` (research automation)

## 📝 License

MIT License

---
