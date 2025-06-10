"""
Browser launcher utilities for LibreWolf integration
"""
import subprocess
import logging
import os
from pathlib import Path
from typing import Optional
import psutil

logger = logging.getLogger(__name__)

class BrowserLauncher:
    """Launch and manage LibreWolf browser instances"""
    
    def __init__(self, librewolf_path: Optional[str] = None, profile_path: Optional[str] = None):
        self.librewolf_path = librewolf_path or self._find_librewolf_path()
        self.profile_path = profile_path
        self.process = None
    
    def _find_librewolf_path(self) -> str:
        """Find LibreWolf executable path"""
        # Default paths to check
        possible_paths = [
            "./librewolf/LibreWolf/librewolf.exe",
            "./librewolf/LibreWolf-Portable.exe",
            "../librewolf/LibreWolf/librewolf.exe",
            "../librewolf/LibreWolf-Portable.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return os.path.abspath(path)
        
        raise FileNotFoundError("LibreWolf executable not found")
    
    def launch(self, url: str = "about:blank", private: bool = True, headless: bool = False) -> bool:
        """
        Launch LibreWolf browser
        
        Args:
            url: Initial URL to open
            private: Launch in private browsing mode
            headless: Launch in headless mode
            
        Returns:
            True if launched successfully
        """
        try:
            cmd = [self.librewolf_path]
            
            if private:
                cmd.append("--private-window")
            
            if headless:
                cmd.append("--headless")
            
            if self.profile_path:
                cmd.extend(["--profile", self.profile_path])
            
            cmd.append(url)
            
            logger.info(f"Launching LibreWolf: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            logger.info(f"LibreWolf launched with PID: {self.process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch LibreWolf: {e}")
            return False
    
    def launch_research_session(self, search_query: str = "") -> bool:
        """Launch LibreWolf configured for research session"""
        # Construct search URL if query provided
        if search_query:
            # Use DuckDuckGo as default search engine
            url = f"https://duckduckgo.com/?q={search_query.replace(' ', '+')}"
        else:
            url = "https://duckduckgo.com"
        
        return self.launch(url=url, private=True)
    
    def is_running(self) -> bool:
        """Check if LibreWolf process is still running"""
        if not self.process:
            return False
        
        try:
            return self.process.poll() is None
        except:
            return False
    
    def close(self):
        """Close LibreWolf browser"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
                logger.info("LibreWolf process terminated")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning("LibreWolf process killed forcefully")
            except Exception as e:
                logger.error(f"Error closing LibreWolf: {e}")
            finally:
                self.process = None
    
    def get_librewolf_processes(self) -> list:
        """Get all running LibreWolf processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'librewolf' in proc.info['name'].lower():
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

def launch_research_browser(search_query: str = "") -> bool:
    """Convenience function to launch research browser session"""
    launcher = BrowserLauncher()
    return launcher.launch_research_session(search_query)

if __name__ == "__main__":
    # Test browser launcher
    logging.basicConfig(level=logging.INFO)
    
    launcher = BrowserLauncher()
    print(f"LibreWolf path: {launcher.librewolf_path}")
    
    if launcher.launch_research_session("AI research assistant"):
        print("Browser launched successfully")
        input("Press Enter to close browser...")
        launcher.close()
    else:
        print("Failed to launch browser")
