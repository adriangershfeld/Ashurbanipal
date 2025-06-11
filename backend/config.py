"""
Configuration settings for Ashurbanipal
"""
import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = Path(__file__).parent
DATA_ROOT = BACKEND_ROOT / "data"

# Default corpus location
DEFAULT_CORPUS_PATH = DATA_ROOT / "corpus"
DEFAULT_CORPUS_PATH.mkdir(exist_ok=True)

# Supported file extensions (excluding source code)
SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx', '.doc', '.rtf']

# File filters to exclude source code and system files
EXCLUDE_PATTERNS = [
    '*.py',      # Python files
    '*.js',      # JavaScript files
    '*.ts',      # TypeScript files
    '*.tsx',     # TypeScript React files
    '*.jsx',     # JavaScript React files
    '*.css',     # CSS files
    '*.scss',    # SCSS files
    '*.less',    # LESS files
    '*.json',    # JSON files
    '*.xml',     # XML files
    '*.html',    # HTML files
    '*.htm',     # HTML files
    '*.yaml',    # YAML files
    '*.yml',     # YAML files
    '*.toml',    # TOML files
    '*.ini',     # INI files
    '*.cfg',     # Config files
    '*.conf',    # Config files
    '*.log',     # Log files
    '*.tmp',     # Temporary files
    '*.cache',   # Cache files
    '*.git*',    # Git files
    '*.env*',    # Environment files
    '.DS_Store', # macOS system files
    'Thumbs.db', # Windows thumbnail cache
    '__pycache__', # Python cache directories
    'node_modules', # Node.js modules
    '.vscode',   # VS Code settings
    '.idea',     # IntelliJ settings
]

# Directory patterns to exclude
EXCLUDE_DIRECTORIES = [
    '__pycache__',
    'node_modules',
    '.git',
    '.vscode',
    '.idea',
    'logs',
    'cache',
    'tmp',
    'temp',
    'build',
    'dist',
    'target',
    'bin',
    'obj'
]
