---
inclusion: auto
---

# Project Structure

## File Organization

```
FLAC_Linebot/
├── main.py                    # FastAPI application entry point
├── models.py                  # Pydantic data models
├── database.py                # DynamoDB operations
├── bedrock_service.py         # AWS Bedrock AI service
├── static/                    # LIFF web applications
│   ├── index.html            # Personal dashboard
│   └── leaderboard.html      # Global rankings
├── .env                       # Environment variables (not in git)
├── .venv/                     # Python virtual environment
├── test_dynamodb.py          # Database connection test
└── scam_detection_db.json    # Legacy JSON database (deprecated)
```

## Module Responsibilities

### main.py
- FastAPI application initialization
- Route definitions (static pages, API endpoints, webhook)
- LINE Bot webhook handler setup
- Message event handlers (text and image)
- Reply message formatting

### models.py
- `ScamDetectionRecord`: Core data model for detection records
- `UserHistory`: Response model for user history API
- `LeaderboardEntry`: Response model for leaderboard API
- All models use Pydantic for validation

### database.py
- DynamoDB client initialization
- CRUD operations for detection records
- User history queries using GSI
- Leaderboard aggregation logic
- Auto-table creation on startup
- Decimal to int conversion utilities

### bedrock_service.py
- AWS Bedrock client setup
- Scam detection prompt engineering
- AI model invocation (Gemma 3-12B-IT)
- Response parsing and structuring
- Risk score extraction and categorization

## Architecture Patterns

### Modular Design
Each functional area is separated into its own module for maintainability and testability.

### Data Flow
1. User message → LINE webhook → `main.py` handler
2. Handler → `bedrock_service.py` for AI analysis
3. Analysis result → `database.py` for persistence
4. Response → LINE Bot API reply
5. Web UI → API endpoints → `database.py` queries

### Error Handling
- All API endpoints use try-catch with HTTPException
- Database operations handle missing credentials gracefully
- Bedrock service returns fallback response on errors

### Configuration
- Environment-based configuration via `.env`
- Case-insensitive AWS credential keys supported
- Auto-initialization of required resources (DynamoDB table)

## Naming Conventions

### Files
- Snake_case for Python modules: `bedrock_service.py`, `database.py`
- Kebab-case for HTML: `index.html`, `leaderboard.html`

### Variables
- Snake_case for Python: `user_id`, `risk_score`, `created_at`
- camelCase for JavaScript: `userId`, `riskScore`, `createdAt`

### Functions
- Snake_case for Python: `add_detection_record()`, `get_user_history()`
- camelCase for JavaScript: `fetchHistory()`, `handleLogout()`

### Constants
- UPPER_SNAKE_CASE: `TABLE_NAME`, `AWS_REGION`, `LIFF_ID`

## Static Assets

The `static/` directory contains LIFF applications that run in LINE's in-app browser:
- Self-contained HTML files with inline CSS and JavaScript
- Tailwind CSS loaded via CDN
- LINE LIFF SDK v2 for authentication and profile access
- Direct API calls to backend endpoints
