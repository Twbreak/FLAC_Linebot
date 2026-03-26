---
inclusion: auto
---

# Product Overview

FLAC Linebot is a scam detection and risk assessment system integrated with LINE messaging platform. The system helps users identify potential scams by analyzing text messages and URLs using AI-powered risk assessment.

## Core Features

- LINE Bot webhook integration for real-time message analysis
- AI-powered scam detection using AWS Bedrock (Gemma 3 model)
- Risk scoring system (1-10 scale) with categorization
- User history tracking and leaderboard system
- LIFF web applications for personal dashboard and global rankings
- Coupon rewards for detecting high-risk scams (score ≥ 8)

## Scam Categories

The system detects three primary scam types:
1. Fake investment scams (假投資詐騙)
2. Fake police/prosecutor scams (假檢警詐騙)
3. Fake dating/marriage scams (假交友/徵婚詐財)

## User Flow

1. User sends text message or URL to LINE Bot
2. System analyzes content using AWS Bedrock AI
3. Bot replies with risk assessment report
4. Record saved to DynamoDB with risk score and analysis
5. Users can view history and rankings via LIFF web interface
