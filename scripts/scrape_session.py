"""
Complete research session: launch browser + monitor clipboard
"""
import sys
import logging
import time
import threading
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from utils.browser_launcher import BrowserLauncher
from utils.clipboard_watcher import ClipboardWatcher

class ResearchSession:
    """Orchestrate a complete research session"""
    
    def __init__(self):
        self.browser_launcher = BrowserLauncher()
        self.clipboard_watcher = ClipboardWatcher(callback=self.handle_clipboard)
        self.session_data = []
    
    def handle_clipboard(self, content: str):
        """Handle clipboard content during research session"""
        if len(content.strip()) < 20:
            return
            
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        self.session_data.append({
            'timestamp': timestamp,
            'content': content,
            'length': len(content)
        })
        
        print(f"[{timestamp}] Captured: {len(content)} chars - {content[:100]}...")
    
    def start_session(self, search_query: str = ""):
        """Start a complete research session"""
        try:
            print("Starting research session...")
            
            # Create session directory
            session_dir = Path("data/sessions") / time.strftime("%Y%m%d_%H%M%S")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Launch browser
            print(f"Launching browser with query: '{search_query}'")
            if not self.browser_launcher.launch_research_session(search_query):
                print("Failed to launch browser")
                return False
            
            # Start clipboard monitoring
            print("Starting clipboard monitoring...")
            self.clipboard_watcher.start()
            
            print("Research session active. Browser launched and clipboard monitored.")
            print("Copy text from web pages to capture it. Press Ctrl+C to end session.")
            
            # Keep session running
            while True:
                time.sleep(1)
                if not self.browser_launcher.is_running():
                    print("Browser closed, ending session...")
                    break
        
        except KeyboardInterrupt:
            print("\nEnding research session...")
        
        finally:
            self.end_session(session_dir)
    
    def end_session(self, session_dir: Path):
        """End the research session and save data"""
        try:
            # Stop clipboard monitoring
            self.clipboard_watcher.stop()
            
            # Close browser if still running
            if self.browser_launcher.is_running():
                self.browser_launcher.close()
            
            # Save session data
            if self.session_data:
                import json
                
                session_file = session_dir / "session_data.json"
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(self.session_data, f, indent=2, ensure_ascii=False)
                
                # Save combined text content
                content_file = session_dir / "captured_content.txt"
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write("Research Session Content\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for item in self.session_data:
                        f.write(f"Timestamp: {item['timestamp']}\n")
                        f.write(f"Length: {item['length']} characters\n")
                        f.write("-" * 30 + "\n")
                        f.write(item['content'])
                        f.write("\n\n" + "=" * 50 + "\n\n")
                
                print(f"Session data saved to: {session_dir}")
                print(f"Captured {len(self.session_data)} clipboard items")
            else:
                print("No content captured during session")
        
        except Exception as e:
            print(f"Error ending session: {e}")

def main():
    logging.basicConfig(level=logging.INFO)
    
    search_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    session = ResearchSession()
    session.start_session(search_query)

if __name__ == "__main__":
    main()
