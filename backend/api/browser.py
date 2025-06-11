"""
Browser automation API for research workflow integration
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import asyncio
import subprocess
import threading
import time
from pathlib import Path

# Import the browser launcher and clipboard watcher
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.browser_launcher import BrowserLauncher
from utils.clipboard_watcher import ClipboardWatcher

router = APIRouter()
logger = logging.getLogger(__name__)

# Global session management
_active_sessions = {}
_session_counter = 0

class BrowserLaunchRequest(BaseModel):
    search_query: Optional[str] = None
    url: Optional[str] = None
    private: bool = True
    headless: bool = False

class BrowserLaunchResponse(BaseModel):
    success: bool
    message: str
    pid: Optional[int] = None

class ResearchSessionRequest(BaseModel):
    search_query: Optional[str] = None
    monitor_clipboard: bool = True

class ResearchSessionResponse(BaseModel):
    success: bool
    message: str
    session_id: Optional[str] = None
    browser_pid: Optional[int] = None

@router.post("/browser/launch", response_model=BrowserLaunchResponse)
async def launch_browser(request: BrowserLaunchRequest):
    """Launch LibreWolf browser with optional search query"""
    try:
        launcher = BrowserLauncher()
        
        if request.search_query:
            success = launcher.launch_research_session(request.search_query)
        elif request.url:
            success = launcher.launch(
                url=request.url,
                private=request.private,
                headless=request.headless
            )
        else:
            success = launcher.launch(
                private=request.private,
                headless=request.headless
            )
        
        if success:
            pid = launcher.process.pid if launcher.process else None
            logger.info(f"Browser launched successfully with PID: {pid}")
            return BrowserLaunchResponse(
                success=True,
                message="Browser launched successfully",
                pid=pid
            )
        else:
            logger.error("Failed to launch browser")
            return BrowserLaunchResponse(
                success=False,
                message="Failed to launch browser"
            )
    
    except Exception as e:
        logger.error(f"Browser launch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Browser launch failed: {str(e)}")

@router.post("/browser/research-session", response_model=ResearchSessionResponse)
async def start_research_session(request: ResearchSessionRequest):
    """Start a complete research session with browser and clipboard monitoring"""
    global _active_sessions, _session_counter
    
    try:
        _session_counter += 1
        session_id = f"session_{_session_counter}_{int(time.time())}"
        
        # Initialize session data
        session_data = {
            'id': session_id,
            'start_time': time.time(),
            'captured_content': [],
            'browser_launcher': None,
            'clipboard_watcher': None,
            'monitoring_thread': None
        }
        
        # Launch browser
        launcher = BrowserLauncher()
        
        if request.search_query:
            success = launcher.launch_research_session(request.search_query)
        else:
            success = launcher.launch()
        
        if not success:
            return ResearchSessionResponse(
                success=False,
                message="Failed to launch browser for research session"
            )
        
        session_data['browser_launcher'] = launcher
        browser_pid = launcher.process.pid if launcher.process else None
        
        # Start clipboard monitoring if requested
        if request.monitor_clipboard:
            def handle_clipboard_content(content: str):
                if len(content.strip()) < 20:
                    return
                    
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                session_data['captured_content'].append({
                    'timestamp': timestamp,
                    'content': content,
                    'length': len(content)
                })
                logger.info(f"Session {session_id}: Captured {len(content)} chars")
            
            clipboard_watcher = ClipboardWatcher(callback=handle_clipboard_content)
            session_data['clipboard_watcher'] = clipboard_watcher
            
            # Start monitoring in separate thread
            def start_monitoring():
                try:
                    clipboard_watcher.start()
                except Exception as e:
                    logger.error(f"Clipboard monitoring error: {str(e)}")
            
            monitoring_thread = threading.Thread(target=start_monitoring, daemon=True)
            session_data['monitoring_thread'] = monitoring_thread
            monitoring_thread.start()
        
        _active_sessions[session_id] = session_data
        
        return ResearchSessionResponse(
            success=True,
            message="Research session started successfully",
            session_id=session_id,
            browser_pid=browser_pid
        )
        
    except Exception as e:
        logger.error(f"Research session error: {str(e)}")
        return ResearchSessionResponse(
            success=False,
            message=f"Failed to start research session: {str(e)}"
        )

@router.get("/browser/status")
async def get_browser_status():
    """Get status of running LibreWolf processes"""
    try:
        launcher = BrowserLauncher()
        processes = launcher.get_librewolf_processes()
        
        return {
            "running_processes": len(processes),
            "processes": processes,
            "message": f"Found {len(processes)} LibreWolf processes"
        }
    
    except Exception as e:
        logger.error(f"Browser status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get browser status: {str(e)}")

@router.post("/browser/close")
async def close_browser():
    """Close LibreWolf browser processes"""
    try:
        launcher = BrowserLauncher()
        
        # Close the launcher's process if it exists
        if launcher.process:
            launcher.close()
            return {
                "success": True,
                "message": "Browser process closed"
            }
        else:
            return {
                "success": False,
                "message": "No active browser process found"
            }
    
    except Exception as e:
        logger.error(f"Browser close error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to close browser: {str(e)}")

@router.post("/clipboard/start-monitoring")
async def start_clipboard_monitoring():
    """Start clipboard monitoring for research content capture"""
    try:
        # Start the clipboard monitoring script as a background process
        script_path = Path(__file__).parent.parent.parent / "scripts" / "monitor_clipboard.py"
        
        if not script_path.exists():
            raise HTTPException(status_code=404, detail="Clipboard monitoring script not found")
        
        # Start the clipboard monitoring process
        process = subprocess.Popen(
            ["python", str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Clipboard monitoring started with PID: {process.pid}")
        
        return {
            "success": True,
            "message": "Clipboard monitoring started",
            "pid": process.pid
        }
    
    except Exception as e:
        logger.error(f"Clipboard monitoring start error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start clipboard monitoring: {str(e)}")

@router.get("/automation/workflow-status")
async def get_workflow_status():
    """Get status of all automation components"""
    try:
        # Check for running processes
        browser_launcher = BrowserLauncher()
        browser_processes = browser_launcher.get_librewolf_processes()
        
        # Check active sessions
        active_sessions = len(_active_sessions)
        session_details = []
        
        for session_id, session_data in _active_sessions.items():
            session_details.append({
                'id': session_id,
                'start_time': session_data.get('start_time'),
                'captured_items': len(session_data.get('captured_content', [])),
                'browser_running': session_data.get('browser_launcher') and session_data['browser_launcher'].is_running(),
                'clipboard_monitoring': session_data.get('clipboard_watcher') is not None
            })
        
        return {
            "browser": {
                "running": len(browser_processes) > 0,
                "processes": len(browser_processes)
            },
            "sessions": {
                "active": active_sessions,
                "details": session_details
            },
            "clipboard_monitoring": {
                "active_watchers": sum(1 for s in _active_sessions.values() if s.get('clipboard_watcher')),
                "total_captured": sum(len(s.get('captured_content', [])) for s in _active_sessions.values())
            }
        }
    
    except Exception as e:
        logger.error(f"Workflow status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get workflow status: {str(e)}")

@router.get("/research-session/{session_id}/status")
async def get_session_status(session_id: str):
    """Get status of a specific research session"""
    try:
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = _active_sessions[session_id]
        
        return {
            "session_id": session_id,
            "start_time": session_data.get('start_time'),
            "duration": time.time() - session_data.get('start_time', 0),
            "captured_content": len(session_data.get('captured_content', [])),
            "browser_running": session_data.get('browser_launcher') and session_data['browser_launcher'].is_running(),
            "clipboard_monitoring": session_data.get('clipboard_watcher') is not None,
            "status": "active"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session status error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.post("/research-session/{session_id}/ingest")
async def ingest_session_content(session_id: str):
    """Ingest captured content from a research session into the corpus"""
    try:
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = _active_sessions[session_id]
        captured_content = session_data.get('captured_content', [])
        
        if not captured_content:
            return {
                "status": "completed",
                "message": "No content to ingest",
                "items_processed": 0
            }
        
        # Import ingestion modules
        from embeddings.chunker import TextChunker
        from embeddings.embedder import EmbeddingModel
        from embeddings.store import VectorStore
        
        chunker = TextChunker()
        embedder = EmbeddingModel()
        vector_store = VectorStore()
        
        items_processed = 0
        chunks_created = 0
        
        for i, item in enumerate(captured_content):
            content = item.get('content', '')
            timestamp = item.get('timestamp', 'unknown')
            
            if len(content.strip()) < 50:
                continue
            
            # Create source identifier
            source_name = f"research_session_{session_id}_item_{i+1}_{timestamp}"
            
            # Chunk the content
            chunks = chunker.chunk_text(content, source_name, {
                "source": "research_session",
                "session_id": session_id,
                "timestamp": timestamp,
                "item_index": i
            })
            
            if chunks:
                # Generate embeddings
                chunk_texts = [chunk.content for chunk in chunks]
                embeddings = embedder.batch_embed(chunk_texts)
                
                # Store in vector database
                vector_store.add_chunks(chunks, embeddings)
                
                items_processed += 1
                chunks_created += len(chunks)
        
        logger.info(f"Ingested {items_processed} items ({chunks_created} chunks) from session {session_id}")
        
        return {
            "status": "completed",
            "message": f"Successfully ingested research session content",
            "items_processed": items_processed,
            "chunks_created": chunks_created,
            "session_id": session_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to ingest session content: {str(e)}")

@router.delete("/research-session/{session_id}")
async def stop_research_session(session_id: str):
    """Stop and cleanup a research session"""
    try:
        if session_id not in _active_sessions:
            raise HTTPException(status_code=404, detail="Session not found")
        
        session_data = _active_sessions[session_id]
        
        # Stop clipboard monitoring
        if session_data.get('clipboard_watcher'):
            try:
                session_data['clipboard_watcher'].stop()
            except Exception as e:
                logger.warning(f"Error stopping clipboard watcher: {e}")
        
        # Close browser
        if session_data.get('browser_launcher'):
            try:
                session_data['browser_launcher'].close()
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")
        
        # Remove from active sessions
        del _active_sessions[session_id]
        
        logger.info(f"Research session {session_id} stopped and cleaned up")
        
        return {
            "status": "stopped",
            "session_id": session_id,
            "message": "Research session stopped successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session stop error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")
