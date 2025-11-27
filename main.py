"""
FastAPI application for fetching Microsoft Teams messages via Graph API.
"""
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import uvicorn

from graph import fetch_graph_messages
from config import settings


# Initialize FastAPI app
app = FastAPI(
    title="Microsoft Teams Message Fetcher",
    description="API to fetch messages from Microsoft Teams channels and chats using Microsoft Graph API",
    version="1.0.0"
)


class MessageResponse(BaseModel):
    """Response model for messages endpoint."""
    count: int = Field(..., description="Number of messages returned")
    messages: List[Dict] = Field(..., description="List of message objects from Graph API")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Microsoft Teams Message Fetcher",
        "version": "1.0.0"
    }


@app.get(
    "/messages",
    response_model=MessageResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid parameters"},
        401: {"model": ErrorResponse, "description": "Unauthorized - Authentication failed"},
        403: {"model": ErrorResponse, "description": "Forbidden - Insufficient permissions"},
        404: {"model": ErrorResponse, "description": "Not Found - Resource does not exist"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
async def get_messages(
    team_id: Optional[str] = Query(
        None,
        description="Team ID (required for channel messages, mutually exclusive with chat_id)"
    ),
    channel_id: Optional[str] = Query(
        None,
        description="Channel ID (required for channel messages, must be used with team_id)"
    ),
    chat_id: Optional[str] = Query(
        None,
        description="Chat ID (required for chat messages, mutually exclusive with team_id/channel_id)"
    ),
    since: Optional[str] = Query(
        None,
        description="ISO 8601 timestamp to filter messages created after this time (e.g., 2024-01-01T00:00:00Z)",
        example="2024-01-01T00:00:00Z"
    )
):
    """
    Fetch messages from a Microsoft Teams channel or chat.
    
    **Authentication:**
    - Uses OAuth 2.0 Client Credentials flow
    - Requires valid TENANT_ID, CLIENT_ID, and CLIENT_SECRET in environment
    
    **Required Permissions:**
    - For channel messages: `Channel.ReadBasic.All` and `ChannelMessage.Read.All`
    - For chat messages: `Chat.Read.All`
    
    **Usage:**
    - For channel messages: Provide both `team_id` and `channel_id`
    - For chat messages: Provide `chat_id` only
    - Optionally provide `since` parameter to filter messages by timestamp
    
    **Returns:**
    - All messages with automatic pagination handling
    - Messages are returned in the order provided by Graph API
    """
    # TODO: Add request rate limiting per client
    # TODO: Add structured logging for request tracking and audit
    
    try:
        # Validate mutually exclusive parameters
        if chat_id and (team_id or channel_id):
            raise HTTPException(
                status_code=400,
                detail="Cannot specify both chat_id and team_id/channel_id. "
                       "Use chat_id for chat messages OR team_id + channel_id for channel messages."
            )
        
        if not chat_id and not (team_id and channel_id):
            raise HTTPException(
                status_code=400,
                detail="Must provide either chat_id OR both team_id and channel_id"
            )
        
        if (team_id and not channel_id) or (channel_id and not team_id):
            raise HTTPException(
                status_code=400,
                detail="Both team_id and channel_id are required for channel messages"
            )
        
        # Fetch messages from Graph API
        messages = await fetch_graph_messages(
            team_id=team_id,
            channel_id=channel_id,
            chat_id=chat_id,
            since=since
        )
        
        return MessageResponse(
            count=len(messages),
            messages=messages
        )
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
        
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        error_message = str(e)
        
        # Map specific errors to appropriate HTTP status codes
        if "Unauthorized" in error_message or "Invalid or expired token" in error_message:
            raise HTTPException(
                status_code=401,
                detail=error_message
            )
        elif "Forbidden" in error_message or "Insufficient permissions" in error_message:
            raise HTTPException(
                status_code=403,
                detail=error_message
            )
        elif "Not found" in error_message:
            raise HTTPException(
                status_code=404,
                detail=error_message
            )
        elif "timeout" in error_message.lower():
            raise HTTPException(
                status_code=504,
                detail="Gateway Timeout: Request to Microsoft Graph API timed out"
            )
        else:
            # Generic server error
            # TODO: Log full stack trace for debugging
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {error_message}"
            )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unexpected errors.
    """
    # TODO: Add error tracking/monitoring (e.g., Sentry, Application Insights)
    # TODO: Add structured logging
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again later."
        }
    )


if __name__ == "__main__":
    # Run the application
    # TODO: For production, use a production ASGI server with proper configuration
    # TODO: Add HTTPS/TLS termination
    # TODO: Configure workers based on CPU cores
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True  # Disable in production
    )
