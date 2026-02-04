"""
FastAPI Backend - WebSocket streaming and REST API.

Provides real-time research progress streaming and
human-in-the-loop endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
from pathlib import Path
from datetime import datetime
import uuid

# Import research components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.state import create_initial_state, AgentState
from src.graph import create_research_graph

app = FastAPI(
    title="Advanced Research Agent API",
    description="Multi-agent research system with real-time streaming",
    version="2.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active research sessions
research_sessions: dict[str, dict] = {}


class ResearchRequest(BaseModel):
    """Request model for starting research."""
    topic: str
    max_revisions: int = 2
    citation_style: str = "apa"


class PlanApproval(BaseModel):
    """Request model for plan approval."""
    session_id: str
    approved: bool
    modified_queries: Optional[list[str]] = None


class ResearchSession(BaseModel):
    """Response model for research session."""
    session_id: str
    topic: str
    status: str
    created_at: str


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            
    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(message)


manager = ConnectionManager()


@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "online",
        "name": "Advanced Research Agent API",
        "version": "2.0.0"
    }


@app.post("/api/research/start", response_model=ResearchSession)
async def start_research(request: ResearchRequest):
    """Start a new research session."""
    session_id = str(uuid.uuid4())
    
    research_sessions[session_id] = {
        "id": session_id,
        "topic": request.topic,
        "status": "created",
        "state": create_initial_state(request.topic, request.max_revisions),
        "created_at": datetime.now().isoformat(),
        "config": {
            "max_revisions": request.max_revisions,
            "citation_style": request.citation_style
        }
    }
    
    return ResearchSession(
        session_id=session_id,
        topic=request.topic,
        status="created",
        created_at=research_sessions[session_id]["created_at"]
    )


@app.get("/api/research/{session_id}")
async def get_research_status(session_id: str):
    """Get status of a research session."""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = research_sessions[session_id]
    state = session["state"]
    
    return {
        "session_id": session_id,
        "topic": session["topic"],
        "status": state.get("status", "unknown"),
        "plan": state.get("plan", []),
        "plan_approved": state.get("plan_approved", False),
        "quality_report": state.get("quality_report"),
        "revision_number": state.get("revision_number", 0),
        "messages": state.get("messages", [])[-20:]  # Last 20 messages
    }


@app.post("/api/research/{session_id}/approve")
async def approve_plan(session_id: str, approval: PlanApproval):
    """Approve or modify the research plan."""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = research_sessions[session_id]
    state = session["state"]
    
    if approval.modified_queries:
        state["plan"] = approval.modified_queries
        
    state["plan_approved"] = approval.approved
    state["status"] = "researching" if approval.approved else "awaiting_approval"
    
    return {"status": "updated", "plan_approved": approval.approved}


@app.get("/api/research/{session_id}/report")
async def get_report(session_id: str):
    """Get the final research report."""
    if session_id not in research_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = research_sessions[session_id]
    state = session["state"]
    
    if state.get("status") != "complete":
        raise HTTPException(status_code=400, detail="Research not complete")
        
    return {
        "report": state.get("final_report", ""),
        "quality_report": state.get("quality_report"),
        "sources_count": len(state.get("sources", []))
    }


@app.websocket("/ws/research/{session_id}")
async def websocket_research(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time research streaming.
    
    Streams agent messages and state updates as research progresses.
    """
    await manager.connect(websocket, session_id)
    
    try:
        if session_id not in research_sessions:
            await websocket.send_json({"error": "Session not found"})
            return
            
        session = research_sessions[session_id]
        state = session["state"]
        
        # Send initial state
        await websocket.send_json({
            "type": "init",
            "topic": session["topic"],
            "status": state.get("status", "planning")
        })
        
        # Import and run the graph
        graph = create_research_graph(enable_hitl=False)
        
        # Stream the research process
        thread_config = {"configurable": {"thread_id": session_id}}
        
        async def stream_updates():
            """Stream state updates during research."""
            previous_messages_count = 0
            
            for event in graph.stream(state, thread_config, stream_mode="updates"):
                # Get the node name and updates
                for node_name, updates in event.items():
                    # Send new messages
                    new_messages = updates.get("messages", [])
                    if new_messages:
                        for msg in new_messages:
                            await websocket.send_json({
                                "type": "message",
                                "node": node_name,
                                "content": msg
                            })
                    
                    # Send status updates
                    if "status" in updates:
                        await websocket.send_json({
                            "type": "status",
                            "status": updates["status"]
                        })
                    
                    # Send plan when generated
                    if "plan" in updates:
                        await websocket.send_json({
                            "type": "plan",
                            "queries": updates["plan"]
                        })
                    
                    # Send quality report
                    if "quality_report" in updates:
                        await websocket.send_json({
                            "type": "quality",
                            "report": updates["quality_report"]
                        })
                    
                    # Update session state
                    for key, value in updates.items():
                        if key == "messages":
                            state["messages"] = state.get("messages", []) + value
                        elif key == "research_data":
                            state["research_data"] = state.get("research_data", []) + value
                        else:
                            state[key] = value
        
        await stream_updates()
        
        # Send final report
        await websocket.send_json({
            "type": "complete",
            "report": state.get("final_report", ""),
            "quality_report": state.get("quality_report")
        })
        
    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        manager.disconnect(session_id)


# Serve frontend static files if available
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
