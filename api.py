"""
FastAPI application for Multi-Agent System.
Provides REST API endpoints for the parallel multi-agent system.
"""
from dotenv import load_dotenv
load_dotenv()
import time
import logging
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import io

from src.config.settings import config
from graph import create_agent_graph, create_initial_state
from src.core.types import AgentState, IntentScore, AgentResult
from src.database.model_s3 import get_s3_manager


# Pydantic models for API
class ProcessRequest(BaseModel):
    """Request model for processing user input."""
    input: str = Field(..., description="User input to process", min_length=1, max_length=2000)
    use_parallel: Optional[bool] = Field(True, description="Enable parallel processing if multiple intents detected")
    confidence_threshold: Optional[float] = Field(0.3, description="Minimum confidence threshold for intents", ge=0.0, le=1.0)


class IntentInfo(BaseModel):
    """Intent information model."""
    intent: str
    confidence: float
    reasoning: Optional[str] = None


class AgentResultInfo(BaseModel):
    """Agent result information model."""
    agent_name: str
    intent: str
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None


class ExecutionSummary(BaseModel):
    """Execution summary model."""
    total_agents: int
    successful_agents: int
    failed_agents: int
    total_execution_time: float
    intents_processed: List[str]


class ProcessResponse(BaseModel):
    """Response model for processing results."""
    success: bool
    input: str
    primary_intent: Optional[str]
    processing_mode: Optional[str]
    detected_intents: Optional[List[IntentInfo]]
    agent_results: Optional[Dict[str, AgentResultInfo]]
    final_result: Optional[str]
    execution_summary: Optional[ExecutionSummary]
    errors: Optional[List[str]]
    processing_time: float


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: float
    version: str = "1.0.0"
    components: Dict[str, str]


# Global variables
agent_graph = None
startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global agent_graph
    
    # Startup
    logging.info("🚀 Starting Multi-Agent System API...")
    try:
        agent_graph = create_agent_graph()
        logging.info("✅ Agent graph initialized successfully")
    except Exception as e:
        logging.error(f"❌ Failed to initialize agent graph: {e}")
        raise
    
    yield
    
    # Shutdown
    logging.info("🛑 Shutting down Multi-Agent System API...")


# Create FastAPI app
app = FastAPI(
    title="Multi-Agent System API",
    description="Intelligent multi-agent system with parallel execution capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def convert_agent_state_to_response(state: AgentState, processing_time: float) -> ProcessResponse:
    """Convert AgentState to ProcessResponse."""
    # Convert detected intents
    detected_intents = None
    if state.get("detected_intents"):
        detected_intents = [
            IntentInfo(
                intent=intent.intent,
                confidence=intent.confidence,
                reasoning=intent.reasoning
            )
            for intent in state["detected_intents"]
        ]
    
    # Convert agent results
    agent_results = None
    if state.get("agent_results"):
        agent_results = {
            intent: AgentResultInfo(
                agent_name=result.agent_name,
                intent=result.intent,
                success=result.success,
                result=result.result,
                error=result.error,
                execution_time=result.execution_time
            )
            for intent, result in state["agent_results"].items()
        }
    
    # Convert execution summary
    execution_summary = None
    if state.get("execution_summary"):
        summary = state["execution_summary"]
        execution_summary = ExecutionSummary(
            total_agents=summary.get("total_agents", 0),
            successful_agents=summary.get("successful_agents", 0),
            failed_agents=summary.get("failed_agents", 0),
            total_execution_time=summary.get("total_execution_time", 0.0),
            intents_processed=summary.get("intents_processed", [])
        )
    
    return ProcessResponse(
        success=not state.get("errors") or len(state.get("errors", [])) == 0,
        input=state["input"],
        primary_intent=state.get("primary_intent"),
        processing_mode=state.get("processing_mode"),
        detected_intents=detected_intents,
        agent_results=agent_results,
        final_result=state.get("final_result"),
        execution_summary=execution_summary,
        errors=state.get("errors"),
        processing_time=processing_time
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "Multi-Agent System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        # Test if agent graph is available
        graph_status = "healthy" if agent_graph is not None else "unhealthy"
        
        return HealthResponse(
            status="healthy" if graph_status == "healthy" else "unhealthy",
            timestamp=time.time(),
            components={
                "agent_graph": graph_status,
                "llm_provider": config.llm.provider,
                "model": config.llm.model
            }
        )
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=time.time(),
            components={
                "error": str(e)
            }
        )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "status": "healthy",
        "uptime": time.time() - startup_time if 'startup_time' in globals() else 0,
        "requests_total": 0,  # Could be implemented with middleware
        "version": "1.0.0",
        "agent_graph_ready": 1 if agent_graph is not None else 0
    }


@app.post("/process", response_model=ProcessResponse)
async def process_input(request: ProcessRequest):
    """
    Process user input through the multi-agent system.
    
    Supports both single and parallel processing modes based on detected intents.
    """
    if not agent_graph:
        raise HTTPException(status_code=503, detail="Agent graph not initialized")
    
    start_time = time.time()
    
    try:
        # Create initial state
        initial_state = create_initial_state(request.input)
        
        # Process through the graph
        result_state = agent_graph.invoke(initial_state)
        
        processing_time = time.time() - start_time
        
        # Convert to response format
        response = convert_agent_state_to_response(result_state, processing_time)
        
        logging.info(f"Processed request in {processing_time:.2f}s - Mode: {response.processing_mode}")
        
        return response
        
    except Exception as e:
        processing_time = time.time() - start_time
        logging.error(f"Error processing request: {e}")
        
        return ProcessResponse(
            success=False,
            input=request.input,
            primary_intent=None,
            processing_mode=None,
            detected_intents=None,
            agent_results=None,
            final_result=None,
            execution_summary=None,
            errors=[f"Processing error: {str(e)}"],
            processing_time=processing_time
        )


@app.get("/agents", response_model=Dict[str, List[str]])
async def get_available_agents():
    """Get information about available agents and intents."""
    return {
        "available_intents": ["math", "english", "poem"],
        "agents": ["MathAgent", "EnglishAgent", "PoemAgent"],
        "processing_modes": ["single", "parallel"]
    }


@app.get("/config")
async def get_configuration():
    """Get current system configuration (non-sensitive information only)."""
    return {
        "llm_provider": config.llm.provider,
        "model": config.llm.model,
        "temperature": config.llm.temperature,
        "debug": config.debug,
        "parallel_config": {
            "max_concurrent_agents": 3,
            "timeout_seconds": 30.0,
            "confidence_threshold": 0.3
        }
    }


# S3 File Management Endpoints
@app.post("/api/s3/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file to S3 storage."""
    try:
        s3_manager = get_s3_manager()

        # Read file content
        file_content = await file.read()
        file_obj = io.BytesIO(file_content)

        # Upload to S3
        result = s3_manager.upload_file(file_obj, file.filename or "unnamed_file")

        if result['success']:
            return JSONResponse(content={
                "success": True,
                "message": "File uploaded successfully",
                "file_info": result['file_info']
            })
        else:
            raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.get("/api/s3/files")
async def list_files():
    """List all files in S3 storage."""
    try:
        s3_manager = get_s3_manager()
        result = s3_manager.list_files()

        if result['success']:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        logger.error(f"List files error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")


@app.get("/api/s3/download/{file_key:path}")
async def download_file(file_key: str):
    """Download a file from S3 storage."""
    try:
        s3_manager = get_s3_manager()
        result = s3_manager.download_file(file_key)

        if result['success']:
            file_data = result['file_data']
            content_type = result['content_type']

            # Extract filename from file_key
            filename = file_key.split('/')[-1]

            return StreamingResponse(
                io.BytesIO(file_data),
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        else:
            raise HTTPException(status_code=404, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.delete("/api/s3/delete/{file_key:path}")
async def delete_file(file_key: str):
    """Delete a file from S3 storage."""
    try:
        s3_manager = get_s3_manager()
        result = s3_manager.delete_file(file_key)

        if result['success']:
            return JSONResponse(content=result)
        else:
            raise HTTPException(status_code=500, detail=result['error'])

    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@app.get("/api/s3/info/{file_key:path}")
async def get_file_info(file_key: str):
    """Get detailed information about a file."""
    try:
        s3_manager = get_s3_manager()
        result = s3_manager.get_file_info(file_key)

        if 'error' not in result:
            return JSONResponse(content={"success": True, "file_info": result})
        else:
            raise HTTPException(status_code=404, detail=result['error'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get file info error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get file info: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the API
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level="info"
    )
