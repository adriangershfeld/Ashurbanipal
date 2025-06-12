"""
Ptaḥ Simple Launcher - Basic working version (Fixed)
"""

import os
import sys
import time
import subprocess
import logging
import argparse
import psutil
import json
from pathlib import Path


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleLauncher:
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.processes = {}
        self.pid_file = self.project_root / "ptah.pids"
        
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
    
    def save_pids(self):
        """Save process IDs to file"""
        pids = {}
        for name, process in self.processes.items():
            if process and process.poll() is None:
                pids[name] = process.pid
        
        try:
            with open(self.pid_file, 'w') as f:
                json.dump(pids, f)
        except Exception as e:
            logger.warning(f"Failed to save PIDs: {e}")
    
    def load_pids(self):
        """Load process IDs from file"""
        if not self.pid_file.exists():
            return {}
        
        try:
            with open(self.pid_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load PIDs: {e}")
            return {}
    
    def kill_existing_processes(self):
        """Kill any existing Ptaḥ processes"""
        logger.info("Checking for existing Ptaḥ processes...")
        
        saved_pids = self.load_pids()
        killed_any = False
        
        for name, pid in saved_pids.items():
            try:
                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    cmdline = ' '.join(process.cmdline())
                    if 'app.py' in cmdline or 'npm' in cmdline:
                        logger.info(f"Killing existing {name} process (PID: {pid})")
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            process.kill()
                        killed_any = True
            except (psutil.NoSuchProcess, psutil.TimeoutExpired, psutil.AccessDenied):
                pass
        
        for port in [8000, 5173]:
            if self.is_port_in_use(port):
                self.kill_process_on_port(port)
                killed_any = True
        
        if killed_any:
            logger.info("Existing processes terminated")
            time.sleep(2)
        
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def kill_process_on_port(self, port):
        """Kill process using a specific port"""
        try:
            import subprocess
            import os
            
            if os.name == 'nt':  # Windows
                result = subprocess.run(
                    f'netstat -ano | findstr :{port}',
                    shell=True, capture_output=True, text=True
                )
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTENING' in line:
                        parts = line.split()
                        if len(parts) > 4:
                            pid = parts[-1]
                            try:
                                subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
                                logger.info(f"Killed process (PID: {pid}) using port {port}")
                                return
                            except:
                                pass
            else:  # Linux/Mac
                result = subprocess.run(
                    f'lsof -ti:{port}',
                    shell=True, capture_output=True, text=True
                )
                if result.stdout.strip():
                    pids = result.stdout.strip().split('\n')
                    for pid in pids:
                        try:
                            subprocess.run(f'kill -9 {pid}', shell=True, check=True)
                            logger.info(f"Killed process (PID: {pid}) using port {port}")
                        except:
                            pass
        except Exception as e:
            logger.warning(f"Failed to kill process on port {port}: {e}")
    
    def cleanup_on_exit(self):
        """Cleanup when exiting"""
        if self.pid_file.exists():
            self.pid_file.unlink()
    
    def start_backend(self):
        """Start backend server"""
        logger.info("Starting backend...")
        backend_dir = self.project_root / "backend"
        
        try:
            self.processes["backend"] = subprocess.Popen(
                [sys.executable, "app.py"],
                cwd=backend_dir,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.save_pids()

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
        logger.info("Starting frontend...")
        frontend_dir = self.project_root / "frontend"
        
        try:
            self.processes["frontend"] = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                shell=True,
                env=os.environ.copy(),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            self.save_pids()

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
    
    def start_browser(self, search_query="", frontend_running=False):
        """Start browser - intelligently choose what to open"""
        logger.info("Starting browser...")
        
        try:
            sys.path.insert(0, str(self.project_root / "backend"))
            from utils.browser_launcher import BrowserLauncher
            
            launcher = BrowserLauncher()
            

            
            if frontend_running and self.is_port_in_use(5173) and not search_query:
                success = launcher.launch("http://localhost:5173", private=False)
                if success:
                    logger.info("✓ Browser started with frontend URL")
            elif search_query:
                success = launcher.launch_research_session(search_query)
                if success:
                    logger.info("✓ Browser started with search query")
            else:
                success = launcher.launch()
                if success:
                    logger.info("✓ Browser started")
            
            if not success:
                logger.error("Failed to start browser")
                return False
                
            return True
                
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            return False
    
    def stop_all(self):
        """Stop all processes"""
        logger.info("Stopping all processes...")
        
        for name, process in self.processes.items():
            try:
                if process and process.poll() is None:
                    logger.info(f"Stopping {name}...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                        logger.info(f"✓ {name} stopped")
                    except subprocess.TimeoutExpired:
                        process.kill()
                        logger.warning(f"Force killed {name}")
            except Exception as e:
                logger.warning(f"Error stopping {name}: {e}")
        
        for port in [8000, 5173]:
            if self.is_port_in_use(port):
                self.kill_process_on_port(port)
        
        self.processes.clear()
        self.cleanup_on_exit()
    
    def show_status(self):
        """Show current status"""
        print("\n" + "="*50)
        print("PTAḤ STATUS")
        print("="*50)
        

        if self.is_port_in_use(8000):
            print("✓ Backend API          RUNNING    http://127.0.0.1:8000")
        else:
            print("✗ Backend API          STOPPED")
        

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
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies")
    
    args = parser.parse_args()
    
    launcher = SimpleLauncher()
    
    try:
        if args.status:
            launcher.show_status()
            return
        
        if args.stop:
            launcher.stop_all()
            return
        
        if args.install_deps:
            logger.info("Installing dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                          cwd=launcher.project_root, check=True)
            subprocess.run(["npm", "install"], cwd=launcher.project_root / "frontend", 
                          shell=True, check=True)
            logger.info("✓ Dependencies installed")
            return
        
        # Kill any existing processes before starting new ones
        launcher.kill_existing_processes()

        logger.info("🚀 Starting Ptaḥ...")
        
        success = True
        
        if not args.no_backend:
            success &= launcher.start_backend()
        
        if not args.no_frontend and success:
            success &= launcher.start_frontend()
        

        if not args.no_browser and success:
            frontend_running = not args.no_frontend and launcher.is_port_in_use(5173)
            launcher.start_browser(args.search or "", frontend_running)
        
        if success:
            logger.info("✅ All components started!")
            launcher.show_status()
            

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
