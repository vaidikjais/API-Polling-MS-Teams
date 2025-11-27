# Microsoft Teams Message Fetcher API

Enterprise-grade FastAPI application for retrieving Microsoft Teams messages through Microsoft Graph API with OAuth 2.0 authentication, intelligent token caching, and comprehensive error handling.

---

## Overview

This service provides a REST API endpoint to programmatically fetch messages from Microsoft Teams channels and chats. Built with modern Python async patterns, it handles authentication, pagination, and error recovery automatically.

**Status:** ✅ Production Ready  
**Version:** 1.0.0  
**Last Updated:** November 27, 2025

---

## Key Features

| Feature                          | Description                                                     |
| -------------------------------- | --------------------------------------------------------------- |
| **OAuth 2.0 Client Credentials** | Secure app-only authentication with automatic token refresh     |
| **Intelligent Token Caching**    | Thread-safe in-memory cache with 5-minute expiry buffer         |
| **Automatic Pagination**         | Seamlessly fetches all messages across multiple Graph API pages |
| **Timestamp Filtering**          | Client-side filtering for messages after specified datetime     |
| **Comprehensive Error Handling** | Proper HTTP status codes (400, 401, 403, 404, 500, 504)         |
| **Async Architecture**           | Non-blocking I/O using `httpx` and `asyncio`                    |
| **Type Safety**                  | Full type hints with Pydantic validation                        |
| **Interactive Documentation**    | Auto-generated Swagger UI and ReDoc                             |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Client Application                                 │
└────────────────────┬────────────────────────────────┘
                     │ HTTP Request
                     ↓
┌─────────────────────────────────────────────────────┐
│  main.py (FastAPI Layer)                            │
│  • Request validation                               │
│  • Parameter parsing                                │
│  • Error mapping                                    │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  graph.py (Graph API Integration)                   │
│  • Endpoint construction                            │
│  • Pagination handling                              │
│  • Response processing                              │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  auth.py (Authentication Layer)                     │
│  • Token acquisition                                │
│  • Cache management                                 │
│  • Expiry tracking                                  │
└────────────────────┬────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────┐
│  Microsoft Identity Platform & Graph API            │
└─────────────────────────────────────────────────────┘
```

---

## Prerequisites

- **Python:** 3.10 or higher
- **Azure AD App Registration** with the following **Application permissions**:
  - `Channel.ReadBasic.All` — Read channel metadata
  - `ChannelMessage.Read.All` — Read channel messages
  - `Chat.Read.All` — Read chat messages
- **Admin Consent:** Must be granted in Azure Portal

---

## Quick Start

### 1. Environment Setup

```bash
# Clone repository
git clone <repository-url>
cd apiFetchTeams

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Configure your Azure credentials:

```env
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here
```

**Obtaining Credentials:**

1. Navigate to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Select your application or create new registration
3. Copy **Directory (tenant) ID** → `TENANT_ID`
4. Copy **Application (client) ID** → `CLIENT_ID`
5. Navigate to **Certificates & secrets** → Generate new client secret → `CLIENT_SECRET`

### 3. Run Application

**Development mode with auto-reload:**

```bash
python main.py
```

**Production mode with multiple workers:**

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Access Points:**

- API Base: `http://localhost:8000`
- Swagger Documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Reference

### Endpoint: `GET /messages`

Retrieve messages from a Teams channel or chat with optional timestamp filtering.

#### Query Parameters

| Parameter    | Type   | Required      | Description                                       |
| ------------ | ------ | ------------- | ------------------------------------------------- |
| `team_id`    | string | Conditional\* | Team identifier (UUID format)                     |
| `channel_id` | string | Conditional\* | Channel thread ID                                 |
| `chat_id`    | string | Conditional\* | Chat conversation ID                              |
| `since`      | string | Optional      | ISO 8601 timestamp (e.g., `2024-11-01T00:00:00Z`) |

\*Must provide either (`team_id` + `channel_id`) OR `chat_id` (mutually exclusive)

#### Response Format

```json
{
  "count": 42,
  "messages": [
    {
      "id": "1234567890",
      "createdDateTime": "2024-11-26T10:30:00Z",
      "from": {
        "user": {
          "displayName": "John Doe",
          "id": "user-id"
        }
      },
      "body": {
        "content": "Message content here",
        "contentType": "html"
      }
    }
  ]
}
```

#### Status Codes

| Code  | Description                                  |
| ----- | -------------------------------------------- |
| `200` | Success — Messages retrieved                 |
| `400` | Bad Request — Invalid parameters             |
| `401` | Unauthorized — Authentication failed         |
| `403` | Forbidden — Insufficient permissions         |
| `404` | Not Found — Team/channel/chat does not exist |
| `500` | Internal Server Error — Unexpected failure   |
| `504` | Gateway Timeout — Graph API timeout          |

---

## Usage Examples

### Fetch Channel Messages

```bash
curl -X GET "http://localhost:8000/messages?team_id=983b6db8-a123-46f9-bcfc-13ee471c1a6d&channel_id=19%3Akuts30Wo2Yd7KxWLWZUsHzw-sHbGK-JOpHSx9kY_B001%40thread.tacv2"
```

### Fetch Chat Messages

```bash
curl -X GET "http://localhost:8000/messages?chat_id=19%3A3f848474-84d3-46ce-8a0d-1f644d91b7ae_b37273df-c818-42ce-9b89-4a9a3c326406%40unq.gbl.spaces"
```

### Filter by Timestamp

```bash
curl -X GET "http://localhost:8000/messages?team_id=983b6db8-a123-46f9-bcfc-13ee471c1a6d&channel_id=19%3Akuts30Wo2Yd7...&since=2024-11-01T00:00:00Z"
```

### Python Client Example

```python
import requests

response = requests.get(
    "http://localhost:8000/messages",
    params={
        "team_id": "983b6db8-a123-46f9-bcfc-13ee471c1a6d",
        "channel_id": "19:kuts30Wo2Yd7KxWLWZUsHzw-sHbGK-JOpHSx9kY_B001@thread.tacv2",
        "since": "2024-11-01T00:00:00Z"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"Retrieved {data['count']} messages")
    for msg in data['messages']:
        print(f"{msg['from']['user']['displayName']}: {msg['body']['content']}")
else:
    print(f"Error: {response.status_code} - {response.json()}")
```

---

## Project Structure

```
apiFetchTeams/
├── main.py              # FastAPI application & routing
├── auth.py              # OAuth 2.0 authentication & token cache
├── graph.py             # Microsoft Graph API integration
├── config.py            # Environment configuration management
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
├── .env                 # Local credentials (git-ignored)
├── .gitignore           # Git exclusion rules
└── README.md            # Documentation
```

---

## Deployment Considerations

### Security Hardening

- [ ] Implement TLS/HTTPS termination (reverse proxy or load balancer)
- [ ] Store secrets in Azure Key Vault instead of `.env` files
- [ ] Add API key authentication for client applications
- [ ] Configure CORS policies for web clients
- [ ] Implement request rate limiting per client
- [ ] Enable audit logging for compliance

### Scalability

- [ ] Deploy Redis for distributed token caching (multi-instance deployments)
- [ ] Configure horizontal scaling with multiple uvicorn workers
- [ ] Implement response caching for frequently accessed messages
- [ ] Add connection pooling for Graph API requests

### Observability

- [ ] Integrate structured logging (JSON format)
- [ ] Add distributed tracing (OpenTelemetry)
- [ ] Configure error tracking (Sentry, Application Insights)
- [ ] Implement metrics collection (Prometheus)
- [ ] Set up health check endpoints for load balancers

### Resilience

- [ ] Implement exponential backoff retry logic for transient failures
- [ ] Handle Graph API rate limiting (429 responses)
- [ ] Add circuit breaker pattern for downstream failures
- [ ] Configure request timeouts appropriately

---

## Troubleshooting

### Authentication Failures

**Symptom:** `401 Unauthorized` or "Authentication failed"

**Solutions:**

- Verify `TENANT_ID`, `CLIENT_ID`, `CLIENT_SECRET` in `.env`
- Check client secret expiration in Azure Portal
- Ensure application permissions are granted (not delegated permissions)
- Confirm admin consent has been provided

### Permission Errors

**Symptom:** `403 Forbidden` or "Insufficient permissions"

**Solutions:**

- Navigate to Azure Portal → App registrations → API permissions
- Verify Application permissions are configured (not Delegated)
- Click "Grant admin consent" button
- Wait 5-10 minutes for permissions to propagate

### Resource Not Found

**Symptom:** `404 Not Found` or "Team, channel, or chat does not exist"

**Solutions:**

- Verify IDs are correctly URL-encoded
- Ensure application has access to the resource
- Check if channel is private (may require additional permissions)
- Use Graph Explorer to validate resource existence

### Network Issues

**Symptom:** `504 Gateway Timeout` or connection errors

**Solutions:**

- Verify outbound HTTPS (443) connectivity to `*.microsoft.com`
- Check firewall rules and proxy configurations
- Increase timeout values in `graph.py` if needed
- Monitor Microsoft 365 service health dashboard

---

## Obtaining Resource IDs

### Microsoft Teams Web Interface

1. Open Teams in browser: `https://teams.microsoft.com`
2. Navigate to desired channel or chat
3. Extract IDs from URL:

**Channel URL:**

```
https://teams.microsoft.com/l/channel/19%3Akuts30...%40thread.tacv2/...?groupId=983b6db8-a123-46f9-bcfc-13ee471c1a6d
```

- `groupId` = Team ID
- `threadId` (URL decoded) = Channel ID

**Chat URL:**

```
https://teams.microsoft.com/l/chat/19%3A3f848474...%40unq.gbl.spaces/...
```

- Chat ID in URL path

### Microsoft Graph Explorer

Use [Graph Explorer](https://developer.microsoft.com/en-us/graph/graph-explorer) to query:

```http
GET https://graph.microsoft.com/v1.0/me/joinedTeams
GET https://graph.microsoft.com/v1.0/teams/{team-id}/channels
GET https://graph.microsoft.com/v1.0/me/chats
```

---

## Support & Documentation

- **Microsoft Graph API:** [Official Documentation](https://learn.microsoft.com/en-us/graph/api/overview)
- **Azure AD Setup:** [App Registration Guide](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- **FastAPI Documentation:** [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

## License

MIT License — See LICENSE file for details

---

**Built with:** Python 3.12 | FastAPI | Microsoft Graph API | OAuth 2.0
