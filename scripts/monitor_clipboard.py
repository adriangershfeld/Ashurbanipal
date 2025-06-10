"""
Monitor clipboard for new content and add to ingestion queue
"""
import sys
import logging
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from utils.clipboard_watcher import ClipboardWatcher
import requests

class ClipboardIngestor:
    """Monitor clipboard and send content to ingestion API"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:8000"):
        self.api_url = api_url
        self.watcher = ClipboardWatcher(callback=self.handle_clipboard_content)
    
    def handle_clipboard_content(self, content: str):
        """Handle new clipboard content"""
        try:
            # Filter out very short content
            if len(content.strip()) < 50:
                return
            
            print(f"New clipboard content: {len(content)} characters")
            
            # TODO: Send to ingestion API
            # For now, just log and save to file
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"clipboard_content_{timestamp}.txt"
            
            with open(f"data/clipboard/{filename}", "w", encoding="utf-8") as f:
                f.write(f"Captured at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n")
                f.write(content)
            
            print(f"Saved clipboard content to: {filename}")
            
        except Exception as e:
            logging.error(f"Error handling clipboard content: {e}")
    
    def start(self):
        """Start monitoring clipboard"""
        # Ensure data directory exists
        Path("data/clipboard").mkdir(parents=True, exist_ok=True)
        
        self.watcher.start()
        
        try:
            print("Clipboard monitor started. Copy text to capture it. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.watcher.stop()
            print("Clipboard monitor stopped.")

def main():
    logging.basicConfig(level=logging.INFO)
    
    ingestor = ClipboardIngestor()
    ingestor.start()

if __name__ == "__main__":
    main()
