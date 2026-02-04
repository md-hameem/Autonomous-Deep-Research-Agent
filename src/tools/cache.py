"""
Cache module for research data persistence.

Provides SQLite-based caching for search results
to improve performance on repeated queries.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

from ..config import get_config


class ResearchCache:
    """
    SQLite-based cache for research data.
    
    Caches search results to avoid redundant API calls
    for repeated or similar queries.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        config = get_config()
        self.db_path = db_path or config.cache.database_path
        self.ttl_hours = config.cache.ttl_hours
        self._ensure_db()
    
    def _ensure_db(self):
        """Create database and tables if they don't exist."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS search_cache (
                    query_hash TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    results TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_sessions (
                    session_id TEXT PRIMARY KEY,
                    topic TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _hash_query(self, query: str, provider: str) -> str:
        """Create a hash for cache key."""
        key = f"{query.lower().strip()}:{provider}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]
    
    def get_cached_results(self, query: str, provider: str) -> Optional[list[dict]]:
        """
        Get cached search results if they exist and aren't expired.
        
        Args:
            query: The search query
            provider: The search provider name
            
        Returns:
            Cached results or None if not found/expired
        """
        query_hash = self._hash_query(query, provider)
        
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT results, expires_at FROM search_cache WHERE query_hash = ?",
                (query_hash,)
            )
            row = cursor.fetchone()
            
            if row:
                results, expires_at = row
                if datetime.fromisoformat(expires_at) > datetime.now():
                    return json.loads(results)
                else:
                    # Expired, delete it
                    conn.execute(
                        "DELETE FROM search_cache WHERE query_hash = ?",
                        (query_hash,)
                    )
                    conn.commit()
        
        return None
    
    def cache_results(self, query: str, provider: str, results: list[dict]):
        """
        Cache search results.
        
        Args:
            query: The search query
            provider: The search provider name
            results: The results to cache
        """
        query_hash = self._hash_query(query, provider)
        now = datetime.now()
        expires = now + timedelta(hours=self.ttl_hours)
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO search_cache 
                (query_hash, query, provider, results, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                query_hash,
                query,
                provider,
                json.dumps(results),
                now.isoformat(),
                expires.isoformat()
            ))
            conn.commit()
    
    def save_session(self, session_id: str, topic: str, state: dict):
        """Save or update a research session."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO research_sessions
                (session_id, topic, state, created_at, updated_at)
                VALUES (?, ?, ?, COALESCE(
                    (SELECT created_at FROM research_sessions WHERE session_id = ?),
                    ?
                ), ?)
            """, (session_id, topic, json.dumps(state), session_id, now, now))
            conn.commit()
    
    def load_session(self, session_id: str) -> Optional[dict]:
        """Load a research session by ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT topic, state FROM research_sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    "topic": row[0],
                    "state": json.loads(row[1])
                }
        
        return None
    
    def list_sessions(self, limit: int = 10) -> list[dict]:
        """List recent research sessions."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT session_id, topic, created_at, updated_at
                FROM research_sessions
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
            
            return [
                {
                    "session_id": row[0],
                    "topic": row[1],
                    "created_at": row[2],
                    "updated_at": row[3]
                }
                for row in cursor.fetchall()
            ]
    
    def clear_expired(self):
        """Remove expired cache entries."""
        now = datetime.now().isoformat()
        
        with self._get_connection() as conn:
            conn.execute(
                "DELETE FROM search_cache WHERE expires_at < ?",
                (now,)
            )
            conn.commit()


# Singleton instance
_cache: Optional[ResearchCache] = None


def get_cache() -> ResearchCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = ResearchCache()
    return _cache
