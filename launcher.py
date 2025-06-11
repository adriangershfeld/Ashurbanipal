"""
Ptaḥ Simple Launcher - Basic working version
"""

import os
import sys
import time
import subprocess
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.processes = {}
        
    def is_port_in_use(self, port):
        """Check if a port is in use"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('127.0.0.1', port))
                return result == 0
        except:
            return False
    
    def start_backend(self):
        """Start backend server"""
        if self.is_port_in_use(8000):
            logger.info("Backend already running on port 8000")
            return True
            
        logger.info("Starting backend...")
        backend_dir = self.project_root / "backend"
        
        try:
            self.processes["backend"] = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=backend_dir,                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for startup
            for _ in range(30):
                if self.is_port_in_use(8000):
                    logger.info(f"✓ Backend started (PID: {self.processes['backend'].pid})")
                    return True
                time.sleep(1)
            
            logger.error("Backend failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start frontend server"""
        if self.is_port_in_use(5173):
            logger.info("Frontend already running on port 5173")
            return True
            
        logger.info("Starting frontend...")
        frontend_dir = self.project_root / "frontend"
        
        try:
            # Use shell=True to ensure npm is found in PATH
            self.processes["frontend"] = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                shell=True,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Wait for startup
            for _ in range(30):
                if self.is_port_in_use(5173):
                    logger.info(f"✓ Frontend started (PID: {self.processes['frontend'].pid})")
                    return True
                time.sleep(1)
            
            logger.error("Frontend failed to start within timeout")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start frontend: {e}")
            return False
    
    def start_browser(self, search_query=""):
        """Start browser"""
        logger.info("Starting browser...")
        
        try:
            sys.path.insert(0, str(self.project_root / "backend"))
            from utils.browser_launcher import BrowserLauncher
            
            launcher = BrowserLauncher()
            
            if search_query:
                success = launcher.launch_research_session(search_query)
            else:
                success = launcher.launch()
            
            if success:
                logger.info("✓ Browser started")
                return True
            else:
                logger.error("Failed to start browser")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    def stop_all(self):
        """Stop all processes"""
        logger.info("Stopping all processes...")
        
        for name, process in self.processes.items():
            try:
                logger.info(f"Stopping {name}...")
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"✓ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                logger.warning(f"Force killed {name}")
            except:
                pass
        self.processes.clear()
    
    def show_status(self):
        """Show current status"""
        print("\n" + "="*50)
        print("PTAḤ STATUS")
        print("="*50)
        
        # Check backend
        if self.is_port_in_use(8000):
            print("✓ Backend API          RUNNING    http://127.0.0.1:8000")
        else:
            print("✗ Backend API          STOPPED")
        
        # Check frontend  
        if self.is_port_in_use(5173):
            print("✓ Frontend Server      RUNNING    http://localhost:5173")
        else:
            print("✗ Frontend Server      STOPPED")
        
        print("="*50)
        if self.is_port_in_use(5173):
            print("Application: http://localhost:5173")
        if self.is_port_in_use(8000):
            print("API Docs: http://127.0.0.1:8000/docs")
        print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Ptaḥ Simple Launcher")
    parser.add_argument("--no-backend", action="store_true", help="Don't start backend")
    parser.add_argument("--no-frontend", action="store_true", help="Don't start frontend")
    parser.add_argument("--no-browser", action="store_true", help="Don't start browser")
    parser.add_argument("--search", type=str, help="Search query for browser")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--stop", action="store_true", help="Stop all")
    
    args = parser.parse_args()
    
    launcher = SimpleLauncher()
    
    try:
        if args.status:
            launcher.show_status()
            return
        
        if args.stop:
            launcher.stop_all()
            return
          # Start components
        logger.info("🚀 Starting Ptaḥ...")
        
        success = True
        
        if not args.no_backend:
            success &= launcher.start_backend()
        
        if not args.no_frontend and success:
            success &= launcher.start_frontend()
        
        if not args.no_browser and success:
            launcher.start_browser(args.search or "")
        
        if success:
            logger.info("✅ All components started!")
            launcher.show_status()
            
            # Auto-open LibreWolf if frontend is running and browser was started
            if not args.no_browser and not args.no_frontend and launcher.is_port_in_use(5173):
                time.sleep(2)
                # Use the browser launcher to open localhost in LibreWolf
                try:
                    sys.path.insert(0, str(launcher.project_root / "backend"))
                    from utils.browser_launcher import BrowserLauncher
                    browser_launcher = BrowserLauncher()
                    browser_launcher.launch("http://localhost:5173", private=False)
                    logger.info("✓ Opened frontend in LibreWolf")
                except Exception as e:
                    logger.warning(f"Failed to open LibreWolf, falling back to default browser: {e}")
                    import webbrowser
                    webbrowser.open("http://localhost:5173")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down...")
        
        launcher.stop_all()
        
    except Exception as e:
        logger.error(f"Launcher error: {e}")
        launcher.stop_all()

if __name__ == "__main__":
    main()
# This script is the entry point for the Ptaḥ Simple Launcher.