"""
Research Projects API for managing project hierarchy and organization
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

class ResearchProject(BaseModel):
    id: str
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    created: str
    updated: str
    filesCount: int = 0
    chunksCount: int = 0
    tags: List[str] = []
    settings: Dict[str, Any] = {}

class CreateProjectRequest(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = Field(..., max_length=1000)
    tags: List[str] = []
    settings: Dict[str, Any] = {}

class UpdateProjectRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None

class ProjectStats(BaseModel):
    total_projects: int
    total_files: int
    total_chunks: int
    recent_activity: List[Dict[str, Any]]
    project_distribution: List[Dict[str, Any]]

def get_db_path():
    """Get database path"""
    return Path(__file__).parent.parent / "data" / "corpus.db"

def get_corpus_path():
    """Get corpus directory path"""
    return Path(__file__).parent.parent / "data" / "corpus"

def scan_folder_projects():
    """Scan corpus directory for project folders and register them"""
    corpus_path = get_corpus_path()
    
    if not corpus_path.exists():
        return []
    
    folder_projects = []
    
    # Scan for directories in corpus folder (excluding hidden dirs and files)
    for item in corpus_path.iterdir():
        if item.is_dir() and not item.name.startswith('.') and item.name != '__pycache__':
            # Count files in the project folder
            files_count = len([f for f in item.iterdir() if f.is_file() and not f.name.startswith('.')])
            
            folder_projects.append({
                'id': f"folder_{item.name}",
                'name': item.name.replace('-', ' ').replace('_', ' ').title(),
                'description': f"Folder-based project from {item.name}",
                'folder_path': str(item),
                'files_count': files_count
            })
    
    return folder_projects

def init_projects_table():
    """Initialize projects table if it doesn't exist"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT,
                settings TEXT,
                files_count INTEGER DEFAULT 0,
                chunks_count INTEGER DEFAULT 0
            )
        """)
        
        # Create project_files table for file-project associations
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS project_files (
                project_id TEXT NOT NULL,
                file_id TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (project_id, file_id),
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)
        
        # Create default project if none exists
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] == 0:
            default_project = {
                'id': 'default',
                'name': 'General Research',
                'description': 'Default research project for unorganized files',
                'created': datetime.now().isoformat(),
                'updated': datetime.now().isoformat(),
                'tags': json.dumps([]),
                'settings': json.dumps({}),
                'files_count': 0,
                'chunks_count': 0
            }
            
            cursor.execute("""
                INSERT INTO projects (id, name, description, created, updated, tags, settings, files_count, chunks_count)
                VALUES (:id, :name, :description, :created, :updated, :tags, :settings, :files_count, :chunks_count)
            """, default_project)
            
            logger.info("Created default project")
        
        conn.commit()

# Initialize table on import
try:
    init_projects_table()
    logger.info("Projects table initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize projects table: {e}")
    # Don't raise the exception to allow the module to load

@router.post("/projects", response_model=ResearchProject)
async def create_project(request: CreateProjectRequest):
    """Create a new research project"""
    try:
        project_id = f"project_{int(time.time() * 1000)}"
        now = datetime.now().isoformat()
        
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if name already exists
            cursor.execute("SELECT id FROM projects WHERE name = ?", (request.name,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Project name already exists")
            
            # Insert new project
            cursor.execute("""
                INSERT INTO projects (id, name, description, created, updated, tags, settings, files_count, chunks_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0)
            """, (
                project_id,
                request.name,
                request.description,
                now,
                now,
                json.dumps(request.tags),
                json.dumps(request.settings)
            ))
            
            conn.commit()
        
        logger.info(f"Created project: {project_id} - {request.name}")
        
        return ResearchProject(
            id=project_id,
            name=request.name,
            description=request.description,
            created=now,
            updated=now,
            filesCount=0,
            chunksCount=0,
            tags=request.tags,
            settings=request.settings
        )
        
    except sqlite3.Error as e:
        logger.error(f"Database error creating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to create project")
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects", response_model=List[ResearchProject])
async def list_projects():
    """Get all research projects including folder-based projects"""
    try:
        db_path = get_db_path()
        projects = []
        
        # Get database projects
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, created, updated, tags, settings, files_count, chunks_count
                FROM projects
                ORDER BY updated DESC
            """)
            
            for row in cursor.fetchall():
                projects.append(ResearchProject(
                    id=row[0],
                    name=row[1],
                    description=row[2] or "",
                    created=row[3],
                    updated=row[4],
                    filesCount=row[7],
                    chunksCount=row[8],
                    tags=json.loads(row[5]) if row[5] else [],
                    settings=json.loads(row[6]) if row[6] else {}
                ))
        
        # Get folder-based projects
        folder_projects = scan_folder_projects()
        for folder_proj in folder_projects:
            projects.append(ResearchProject(
                id=folder_proj['id'],
                name=folder_proj['name'],
                description=folder_proj['description'],
                created=datetime.now().isoformat(),
                updated=datetime.now().isoformat(),
                filesCount=folder_proj['files_count'],
                chunksCount=0,  # Will be calculated when files are ingested
                tags=[],
                settings={"folder_path": folder_proj['folder_path']}
            ))
        
        return projects
            
    except sqlite3.Error as e:
        logger.error(f"Database error listing projects: {e}")
        raise HTTPException(status_code=500, detail="Failed to list projects")
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}", response_model=ResearchProject)
async def get_project(project_id: str):
    """Get a specific research project"""
    try:
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, name, description, created, updated, tags, settings, files_count, chunks_count
                FROM projects
                WHERE id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Project not found")
            
            return ResearchProject(
                id=row[0],
                name=row[1],
                description=row[2] or "",
                created=row[3],
                updated=row[4],
                filesCount=row[7],
                chunksCount=row[8],
                tags=json.loads(row[5]) if row[5] else [],
                settings=json.loads(row[6]) if row[6] else {}
            )
            
    except sqlite3.Error as e:
        logger.error(f"Database error getting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project")
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/projects/{project_id}", response_model=ResearchProject)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """Update a research project"""
    try:
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if project exists
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Build update query dynamically
            updates = []
            params = []
            
            if request.name is not None:
                updates.append("name = ?")
                params.append(request.name)
            
            if request.description is not None:
                updates.append("description = ?")
                params.append(request.description)
            
            if request.tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(request.tags))
            
            if request.settings is not None:
                updates.append("settings = ?")
                params.append(json.dumps(request.settings))
            
            if updates:
                updates.append("updated = ?")
                params.append(datetime.now().isoformat())
                params.append(project_id)
                
                cursor.execute(f"""
                    UPDATE projects 
                    SET {', '.join(updates)}
                    WHERE id = ?
                """, params)
                
                conn.commit()
            
            # Get updated project
            cursor.execute("""
                SELECT id, name, description, created, updated, tags, settings, files_count, chunks_count
                FROM projects
                WHERE id = ?
            """, (project_id,))
            
            row = cursor.fetchone()
            return ResearchProject(
                id=row[0],
                name=row[1],
                description=row[2] or "",
                created=row[3],
                updated=row[4],
                filesCount=row[7],
                chunksCount=row[8],
                tags=json.loads(row[5]) if row[5] else [],
                settings=json.loads(row[6]) if row[6] else {}
            )
            
    except sqlite3.Error as e:
        logger.error(f"Database error updating project: {e}")
        raise HTTPException(status_code=500, detail="Failed to update project")
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a research project"""
    try:
        if project_id == "default":
            raise HTTPException(status_code=400, detail="Cannot delete default project")
        
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if project exists
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Move files back to default project
            cursor.execute("""
                UPDATE project_files 
                SET project_id = 'default' 
                WHERE project_id = ?
            """, (project_id,))
            
            # Delete the project
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            conn.commit()
        
        logger.info(f"Deleted project: {project_id}")
        
        return {"message": "Project deleted successfully"}
        
    except sqlite3.Error as e:
        logger.error(f"Database error deleting project: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete project")
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/files/{file_id}")
async def add_file_to_project(project_id: str, file_id: str):
    """Add a file to a research project"""
    try:
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check if project exists
            cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Project not found")
            
            # Add file to project (replace if exists)
            cursor.execute("""
                INSERT OR REPLACE INTO project_files (project_id, file_id, added_at)
                VALUES (?, ?, ?)
            """, (project_id, file_id, datetime.now().isoformat()))
            
            # Update project file count
            await _update_project_counts(cursor, project_id)
            
            conn.commit()
        
        return {"message": "File added to project successfully"}
        
    except sqlite3.Error as e:
        logger.error(f"Database error adding file to project: {e}")
        raise HTTPException(status_code=500, detail="Failed to add file to project")
    except Exception as e:
        logger.error(f"Error adding file to project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/projects/{project_id}/files/{file_id}")
async def remove_file_from_project(project_id: str, file_id: str):
    """Remove a file from a research project"""
    try:
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Remove file from project
            cursor.execute("""
                DELETE FROM project_files 
                WHERE project_id = ? AND file_id = ?
            """, (project_id, file_id))
            
            # Update project file count
            await _update_project_counts(cursor, project_id)
            
            conn.commit()
        
        return {"message": "File removed from project successfully"}
        
    except sqlite3.Error as e:
        logger.error(f"Database error removing file from project: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove file from project")
    except Exception as e:
        logger.error(f"Error removing file from project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """Get all files in a research project including folder-based projects"""
    try:
        # Check if it's a folder-based project
        if project_id.startswith("folder_"):
            folder_name = project_id.replace("folder_", "")
            corpus_path = get_corpus_path()
            project_folder = corpus_path / folder_name
            
            if not project_folder.exists():
                return {"project_id": project_id, "files": []}
            
            files = []
            for file_path in project_folder.iterdir():
                if file_path.is_file() and not file_path.name.startswith('.'):
                    files.append({
                        "filename": file_path.name,
                        "file_size": file_path.stat().st_size,
                        "created_at": datetime.fromtimestamp(file_path.stat().st_ctime).isoformat(),
                        "file_type": file_path.suffix[1:] if file_path.suffix else "unknown",
                        "chunks_count": 0,  # Will be calculated when ingested
                        "added_to_project": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        "folder_path": str(file_path)
                    })
            
            return {"project_id": project_id, "files": files}
        
        # Handle database projects
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT f.filename, f.file_size, f.created_at, f.file_type, f.chunks_count, pf.added_at
                FROM files f
                JOIN project_files pf ON f.filename = pf.file_id
                WHERE pf.project_id = ?
                ORDER BY pf.added_at DESC
            """, (project_id,))
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    "filename": row[0],
                    "file_size": row[1],
                    "created_at": row[2],
                    "file_type": row[3],
                    "chunks_count": row[4],
                    "added_to_project": row[5]
                })
            
            return {"project_id": project_id, "files": files}
            
    except sqlite3.Error as e:
        logger.error(f"Database error getting project files: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project files")
    except Exception as e:
        logger.error(f"Error getting project files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/projects/stats", response_model=ProjectStats)
async def get_projects_stats():
    """Get overall project statistics"""
    try:
        db_path = get_db_path()
        
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Get total projects
            cursor.execute("SELECT COUNT(*) FROM projects")
            total_projects = cursor.fetchone()[0]
            
            # Get total files and chunks
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(chunks_count), 0) FROM files")
            total_files, total_chunks = cursor.fetchone()
            
            # Get project distribution
            cursor.execute("""
                SELECT p.name, p.files_count, p.chunks_count
                FROM projects p
                ORDER BY p.files_count DESC
                LIMIT 10
            """)
            
            project_distribution = []
            for row in cursor.fetchall():
                project_distribution.append({
                    "name": row[0],
                    "files_count": row[1],
                    "chunks_count": row[2]
                })
            
            # Get recent activity (mock for now)
            recent_activity = [
                {"action": "file_added", "project": "General Research", "timestamp": datetime.now().isoformat()},
                {"action": "project_created", "project": "New Project", "timestamp": datetime.now().isoformat()}
            ]
        
            return ProjectStats(
                total_projects=total_projects,
                total_files=total_files,
                total_chunks=total_chunks,
                recent_activity=recent_activity,
                project_distribution=project_distribution
            )
            
    except sqlite3.Error as e:
        logger.error(f"Database error getting project stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project stats")
    except Exception as e:
        logger.error(f"Error getting project stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _update_project_counts(cursor, project_id: str):
    """Update file and chunk counts for a project"""
    cursor.execute("""
        UPDATE projects 
        SET files_count = (
            SELECT COUNT(*) FROM project_files WHERE project_id = ?
        ),
        chunks_count = (
            SELECT COALESCE(SUM(chunks_count), 0) 
            FROM files f
            JOIN project_files pf ON f.filename = pf.file_id
            WHERE pf.project_id = ?
        ),
        updated = ?
        WHERE id = ?
    """, (project_id, project_id, datetime.now().isoformat(), project_id))
