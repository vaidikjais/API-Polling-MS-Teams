"""
Microsoft Graph API helper functions.
Handles fetching Teams and chat messages with pagination support.
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime
from auth import get_access_token
from config import settings


async def fetch_graph_messages(
    team_id: Optional[str] = None,
    channel_id: Optional[str] = None,
    chat_id: Optional[str] = None,
    since: Optional[str] = None
) -> List[Dict]:
    """
    Fetch messages from Microsoft Teams channel or chat.
    
    Args:
        team_id: Team ID (required for channel messages)
        channel_id: Channel ID (required for channel messages)
        chat_id: Chat ID (required for chat messages)
        since: ISO 8601 timestamp to filter messages (client-side filtering)
        
    Returns:
        List of message objects from Graph API
        
    Raises:
        ValueError: If invalid parameters provided
        httpx.HTTPStatusError: For API errors (401, 403, etc.)
        Exception: For other errors
    """
    # Validate input parameters
    if chat_id:
        if team_id or channel_id:
            raise ValueError("Cannot specify both chat_id and team_id/channel_id")
        endpoint = f"{settings.graph_api_base_url}/chats/{chat_id}/messages"
    elif team_id and channel_id:
        endpoint = f"{settings.graph_api_base_url}/teams/{team_id}/channels/{channel_id}/messages"
    else:
        raise ValueError("Must provide either chat_id OR both team_id and channel_id")
    
    # Get access token
    try:
        access_token = await get_access_token()
    except Exception as e:
        raise Exception(f"Failed to authenticate: {str(e)}")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    all_messages = []
    next_link = endpoint
    
    # Parse since timestamp if provided for client-side filtering
    since_datetime = None
    if since:
        try:
            since_datetime = datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 timestamp format: {since}")
    
    # TODO: Add rate limiting to respect Graph API throttling limits
    # TODO: Implement exponential backoff retry logic for transient failures
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            while next_link:
                # Fetch current page
                response = await client.get(next_link, headers=headers)
                
                # Handle specific HTTP errors
                if response.status_code == 401:
                    raise Exception("Unauthorized: Invalid or expired token")
                elif response.status_code == 403:
                    raise Exception("Forbidden: Insufficient permissions to access messages. "
                                  "Required permissions: Channel.ReadBasic.All, ChannelMessage.Read.All, "
                                  "or Chat.Read.All")
                elif response.status_code == 404:
                    raise Exception("Not found: Team, channel, or chat does not exist")
                
                response.raise_for_status()
                
                data = response.json()
                messages = data.get("value", [])
                
                # Apply client-side filtering by timestamp if needed
                if since_datetime:
                    filtered_messages = []
                    for msg in messages:
                        created_at_str = msg.get("createdDateTime")
                        if created_at_str:
                            try:
                                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                                if created_at >= since_datetime:
                                    filtered_messages.append(msg)
                            except ValueError:
                                # Include message if timestamp parsing fails
                                filtered_messages.append(msg)
                    messages = filtered_messages
                
                all_messages.extend(messages)
                
                # Check for next page
                next_link = data.get("@odata.nextLink")
                
                # TODO: Add configurable limit to prevent excessive pagination
                # For production, consider adding a max_pages parameter
                
    except httpx.TimeoutException:
        raise Exception("Request timeout: Microsoft Graph API did not respond in time")
    except httpx.NetworkError as e:
        raise Exception(f"Network error while contacting Microsoft Graph API: {str(e)}")
    except httpx.HTTPStatusError as e:
        error_detail = ""
        try:
            error_detail = e.response.json()
        except:
            error_detail = e.response.text
        raise Exception(f"Graph API error: {e.response.status_code} - {error_detail}")
    except Exception as e:
        # TODO: Add structured logging and error tracking
        if "Failed to authenticate" in str(e) or "Unauthorized" in str(e) or "Forbidden" in str(e):
            raise
        raise Exception(f"Failed to fetch messages: {str(e)}")
    
    return all_messages


async def get_message_replies(
    team_id: str,
    channel_id: str,
    message_id: str
) -> List[Dict]:
    """
    Fetch replies to a specific message in a channel.
    
    Args:
        team_id: Team ID
        channel_id: Channel ID
        message_id: Parent message ID
        
    Returns:
        List of reply message objects
        
    Note:
        This is a helper function for future extension.
        Currently not exposed via the main API endpoint.
    """
    # TODO: Implement reply fetching if needed
    # Endpoint: /teams/{team_id}/channels/{channel_id}/messages/{message_id}/replies
    pass
