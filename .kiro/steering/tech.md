---
inclusion: auto
---

# Technology Stack

## Backend Framework
- **FastAPI**: Modern Python web framework for API and webhook endpoints
- **Uvicorn**: ASGI server for running FastAPI applications

## External Services
- **LINE Messaging API**: Bot integration and LIFF applications
- **AWS Bedrock**: AI model inference (Gemma 3-12B-IT)
- **AWS DynamoDB**: NoSQL database for storing detection records

## Core Libraries
- `line-bot-sdk`: LINE Bot SDK v3 for webhook handling
- `boto3`: AWS SDK for Python (Bedrock and DynamoDB)
- `pydantic`: Data validation and settings management
- `python-dotenv`: Environment variable management

## Frontend
- **Tailwind CSS**: Utility-first CSS framework
- **LINE LIFF SDK**: Frontend SDK for LINE integration
- Vanilla JavaScript (no framework)

## Development Environment
- Python 3.x with virtual environment (`.venv/`)
- Environment variables stored in `.env` file

## Common Commands

### Installation
```bash
pip install fastapi uvicorn python-dotenv line-bot-sdk boto3
```

### Running the Application
```bash
# Development
python main.py

# Production (with uvicorn directly)
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Testing
```bash
# Test DynamoDB connection
python test_dynamodb.py

# Test API endpoints
curl http://localhost:8080/api/history/U1234567890
curl http://localhost:8080/api/leaderboard
```

### Deployment
```bash
# Using ngrok for development
ngrok http 8080

# Using systemd for production (see README.md)
sudo systemctl start flac-linebot
sudo systemctl status flac-linebot
```

## Environment Variables Required
- `LINE_CHANNEL_ACCESS_TOKEN`: LINE Bot access token
- `LINE_CHANNEL_SECRET`: LINE Bot channel secret
- `aws_access_key_id` or `AWS_ACCESS_KEY_ID`: AWS credentials
- `aws_secret_access_key` or `AWS_SECRET_ACCESS_KEY`: AWS credentials
- `AWS_REGION`: AWS region (default: us-east-1)

## Database Schema

### DynamoDB Table: ScamDetectionRecords
- **Primary Key**: `record_id` (String) - format: `{user_id}#{timestamp}`
- **GSI**: `UserIdIndex` - partition key: `user_id`, sort key: `created_at`
- **Attributes**: user_id, input_content, risk_score, category, analysis, expert_warning, created_at

Table is auto-created on application startup if it doesn't exist.
