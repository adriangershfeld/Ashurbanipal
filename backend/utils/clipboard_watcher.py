"""
Clipboard monitoring utilities - Stub implementation
"""
import time
import logging
import threading
from typing import Callable, Optional
from datetime import datetime
import queue

logger = logging.getLogger(__name__)

class ClipboardWatcher:
    """Monitor clipboard for new content - Stub implementation"""
    
    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        self.callback = callback
        self.running = False
        self.thread = None
        self.last_clipboard_content = ""
        self.content_queue = queue.Queue()
        logger.warning("Clipboard monitoring dependencies not available. Using stub implementation.")
        
    def start(self, check_interval: float = 1.0):
        """Start monitoring clipboard - Stub implementation"""
        logger.warning("Clipboard monitoring not implemented")
        self.running = True
    
    def stop(self):
        """Stop monitoring clipboard"""
        self.running = False
        logger.info("Clipboard watcher stopped")
    
    def get_recent_content(self, max_items: int = 10) -> list:
        """Get recent clipboard content"""
        return []
    
    def clear_queue(self):
        """Clear the content queue"""
        pass

def simple_clipboard_callback(content: str):
    """Simple callback that logs clipboard content"""
    logger.info(f"Clipboard updated: {content[:100]}...")

if __name__ == "__main__":
    # Test the clipboard watcher
    logging.basicConfig(level=logging.INFO)
    
    watcher = ClipboardWatcher(callback=simple_clipboard_callback)
    watcher.start()
    
    try:
        print("Clipboard watcher running (stub). Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("Clipboard watcher stopped.")
