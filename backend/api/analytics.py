"""
Analytics API for usage statistics and insights
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

router = APIRouter()
logger = logging.getLogger(__name__)

class AnalyticsData(BaseModel):
    total_documents: int
    total_chunks: int
    total_searches: int
    total_chat_messages: int
    avg_response_time: float
    popular_documents: List[Dict[str, Any]]
    search_trends: List[Dict[str, Any]]
    daily_activity: List[Dict[str, Any]]
    document_stats: List[Dict[str, Any]]

@router.get("/analytics/overview")
async def get_analytics_overview() -> AnalyticsData:
    """Get comprehensive analytics overview"""
    try:
        # Connect to database
        db_path = Path("data/corpus.db")
        if not db_path.exists():
            logger.warning("Database not found for analytics")
            return _get_mock_analytics()
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get basic stats
            cursor.execute("SELECT COUNT(*) as count FROM files")
            total_documents = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM chunks")
            total_chunks = cursor.fetchone()['count']
            
            # Mock search and chat statistics (would come from logs or separate tracking)
            total_searches = 150
            total_chat_messages = 45
            avg_response_time = 1.2
            
            # Get popular documents (mock data for now)
            popular_documents = [
                {"filename": "research_paper.pdf", "views": 25, "searches": 15},
                {"filename": "project_notes.md", "views": 18, "searches": 12},
                {"filename": "documentation.txt", "views": 12, "searches": 8},
            ]
            
            # Get search trends (mock data)
            search_trends = [
                {"query": "machine learning", "count": 15, "avg_relevance": 0.87},
                {"query": "data analysis", "count": 12, "avg_relevance": 0.82},
                {"query": "neural networks", "count": 8, "avg_relevance": 0.91},
            ]
            
            # Get daily activity (mock data)
            daily_activity = []
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                daily_activity.append({
                    "date": date,
                    "searches": 15 + (i * 2),
                    "chats": 5 + i
                })
            
            # Get document type statistics
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN filepath LIKE '%.pdf' THEN 'PDF'
                        WHEN filepath LIKE '%.txt' THEN 'TXT'
                        WHEN filepath LIKE '%.md' THEN 'MD'
                        WHEN filepath LIKE '%.docx' THEN 'DOCX'
                        ELSE 'OTHER'
                    END as type,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM files 
                GROUP BY type
                ORDER BY count DESC
            """)
            
            document_stats = []
            for row in cursor.fetchall():
                document_stats.append({
                    "type": row['type'],
                    "count": row['count'],
                    "total_size": (row['total_size'] or 0) / (1024 * 1024)  # Convert to MB
                })
            
            return AnalyticsData(
                total_documents=total_documents,
                total_chunks=total_chunks,
                total_searches=total_searches,
                total_chat_messages=total_chat_messages,
                avg_response_time=avg_response_time,
                popular_documents=popular_documents,
                search_trends=search_trends,
                daily_activity=daily_activity,
                document_stats=document_stats
            )
            
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        # Return mock data on error
        return _get_mock_analytics()

def _get_mock_analytics() -> AnalyticsData:
    """Return mock analytics data for demonstration"""
    return AnalyticsData(
        total_documents=25,
        total_chunks=680,
        total_searches=125,
        total_chat_messages=38,
        avg_response_time=1.1,
        popular_documents=[
            {"filename": "sample_document.pdf", "views": 15, "searches": 8},
            {"filename": "notes.md", "views": 12, "searches": 6},
            {"filename": "research.txt", "views": 8, "searches": 4},
        ],
        search_trends=[
            {"query": "example query", "count": 10, "avg_relevance": 0.85},
            {"query": "test search", "count": 7, "avg_relevance": 0.78},
            {"query": "sample text", "count": 5, "avg_relevance": 0.82},
        ],
        daily_activity=[
            {"date": "2024-06-11", "searches": 18, "chats": 6},
            {"date": "2024-06-10", "searches": 15, "chats": 4},
            {"date": "2024-06-09", "searches": 22, "chats": 8},
            {"date": "2024-06-08", "searches": 12, "chats": 3},
            {"date": "2024-06-07", "searches": 20, "chats": 7},
            {"date": "2024-06-06", "searches": 16, "chats": 5},
            {"date": "2024-06-05", "searches": 14, "chats": 4},
        ],
        document_stats=[
            {"type": "PDF", "count": 15, "total_size": 25.6},
            {"type": "TXT", "count": 8, "total_size": 2.1},
            {"type": "MD", "count": 2, "total_size": 0.5},
        ]
    )

@router.get("/analytics/corpus-stats")
async def get_corpus_statistics():
    """Get detailed corpus statistics"""
    try:
        db_path = Path("data/corpus.db")
        if not db_path.exists():
            logger.warning("Database not found for corpus statistics")
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "total_size": 0,
                "avg_document_size": 0,
                "document_types": []
            }
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get basic corpus statistics
            cursor.execute("SELECT COUNT(*) as count FROM files")
            total_documents = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM chunks")
            total_chunks = cursor.fetchone()['count']
            
            cursor.execute("SELECT SUM(file_size) as total_size, AVG(file_size) as avg_size FROM files")
            size_stats = cursor.fetchone()
            total_size = size_stats['total_size'] or 0
            avg_size = size_stats['avg_size'] or 0
            
            # Get document type breakdown
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN filepath LIKE '%.pdf' THEN 'PDF'
                        WHEN filepath LIKE '%.txt' THEN 'TXT'
                        WHEN filepath LIKE '%.md' THEN 'MD'
                        WHEN filepath LIKE '%.docx' THEN 'DOCX'
                        ELSE 'OTHER'
                    END as type,
                    COUNT(*) as count,
                    SUM(file_size) as total_size
                FROM files 
                GROUP BY type
                ORDER BY count DESC
            """)
            
            document_types = []
            for row in cursor.fetchall():
                document_types.append({
                    "type": row['type'],
                    "count": row['count'],
                    "total_size": (row['total_size'] or 0) / (1024 * 1024),  # Convert to MB
                    "percentage": (row['count'] / max(total_documents, 1)) * 100
                })
            
            return {
                "total_documents": total_documents,
                "total_chunks": total_chunks,
                "total_size": total_size / (1024 * 1024),  # Convert to MB
                "avg_document_size": avg_size / (1024 * 1024),  # Convert to MB
                "document_types": document_types
            }
            
    except Exception as e:
        logger.error(f"Corpus statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve corpus statistics")

@router.get("/analytics/search-analytics")
async def get_search_analytics():
    """Get search analytics and performance metrics"""
    try:
        # For now, return mock data since we don't have search tracking in place
        # In a real implementation, this would query a search logs database
        
        return {
            "total_searches": 156,
            "avg_response_time": 1.3,
            "avg_relevance_score": 0.84,
            "search_success_rate": 0.92,
            "top_queries": [
                {
                    "query": "machine learning algorithms",
                    "count": 23,
                    "avg_relevance": 0.89,
                    "success_rate": 0.95
                },
                {
                    "query": "data preprocessing techniques",
                    "count": 18,
                    "avg_relevance": 0.86,
                    "success_rate": 0.94
                },
                {
                    "query": "neural network architectures",
                    "count": 15,
                    "avg_relevance": 0.91,
                    "success_rate": 0.93
                },
                {
                    "query": "statistical analysis methods",
                    "count": 12,
                    "avg_relevance": 0.82,
                    "success_rate": 0.88
                },
                {
                    "query": "feature engineering",
                    "count": 10,
                    "avg_relevance": 0.85,
                    "success_rate": 0.90
                }
            ],
            "query_length_distribution": {
                "1-2_words": 24,
                "3-4_words": 67,
                "5-6_words": 45,
                "7+_words": 20
            },
            "response_time_distribution": {
                "0-0.5s": 42,
                "0.5-1s": 58,
                "1-2s": 38,
                "2s+": 18
            },
            "search_patterns": {
                "peak_hours": ["14:00", "15:00", "16:00"],
                "busiest_day": "Wednesday",
                "avg_searches_per_session": 3.2
            },
            "daily_search_volume": [
                {"date": "2024-06-11", "count": 22},
                {"date": "2024-06-10", "count": 18},
                {"date": "2024-06-09", "count": 25},
                {"date": "2024-06-08", "count": 15},
                {"date": "2024-06-07", "count": 21},
                {"date": "2024-06-06", "count": 19},
                {"date": "2024-06-05", "count": 16}
            ]
        }
        
    except Exception as e:
        logger.error(f"Search analytics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search analytics")

@router.get("/analytics/search-stats")
async def get_search_statistics():
    """Get detailed search statistics"""
    try:
        # TODO: Implement search statistics tracking
        return {
            "total_searches": 150,
            "avg_response_time": 1.2,
            "top_queries": [
                {"query": "machine learning", "count": 15},
                {"query": "data analysis", "count": 12},
                {"query": "neural networks", "count": 8}
            ],
            "daily_searches": [
                {"date": "2024-06-11", "count": 18},
                {"date": "2024-06-10", "count": 15},
                {"date": "2024-06-09", "count": 22}
            ]
        }
    except Exception as e:
        logger.error(f"Search statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve search statistics")

@router.get("/analytics/document-stats")
async def get_document_statistics():
    """Get detailed document statistics"""
    try:
        db_path = Path("data/corpus.db")
        if not db_path.exists():
            return {"total_documents": 0, "total_size": 0, "by_type": []}
        
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get total statistics
            cursor.execute("SELECT COUNT(*) as count, SUM(file_size) as total_size FROM files")
            totals = cursor.fetchone()
            
            # Get statistics by file type
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN filepath LIKE '%.pdf' THEN 'PDF'
                        WHEN filepath LIKE '%.txt' THEN 'TXT'
                        WHEN filepath LIKE '%.md' THEN 'MD'
                        WHEN filepath LIKE '%.docx' THEN 'DOCX'
                        ELSE 'OTHER'
                    END as type,
                    COUNT(*) as count,
                    SUM(file_size) as total_size,
                    AVG(file_size) as avg_size
                FROM files 
                GROUP BY type
                ORDER BY count DESC
            """)
            
            by_type = []
            for row in cursor.fetchall():
                by_type.append({
                    "type": row['type'],
                    "count": row['count'],
                    "total_size": (row['total_size'] or 0) / (1024 * 1024),  # MB
                    "avg_size": (row['avg_size'] or 0) / (1024 * 1024)  # MB
                })
            
            return {
                "total_documents": totals['count'],
                "total_size": (totals['total_size'] or 0) / (1024 * 1024),  # MB
                "by_type": by_type
            }
            
    except Exception as e:
        logger.error(f"Document statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document statistics")
