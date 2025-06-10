"""
Launch LibreWolf browser for research sessions
"""
import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from utils.browser_launcher import BrowserLauncher

def main():
    logging.basicConfig(level=logging.INFO)
    
    search_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    
    launcher = BrowserLauncher()
    
    if search_query:
        print(f"Launching LibreWolf with search: {search_query}")
        success = launcher.launch_research_session(search_query)
    else:
        print("Launching LibreWolf")
        success = launcher.launch()
    
    if success:
        print("Browser launched successfully")
        return 0
    else:
        print("Failed to launch browser")
        return 1

if __name__ == "__main__":
    exit(main())
