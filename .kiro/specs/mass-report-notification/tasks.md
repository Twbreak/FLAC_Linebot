# Implementation Plan: Mass Report Notification System

## Overview

This implementation plan breaks down the mass report notification system into discrete coding tasks. The system will detect when a message receives mass reports (≥10), generate safe summaries using AWS Bedrock LLM, and broadcast alerts to all active users via LINE Messaging API. The implementation integrates with existing modules (bedrock_service.py, database.py, main.py) and follows the design specifications.

## Tasks

- [x] 1. Set up data models and database schema
  - [x] 1.1 Create MassReportAlert Pydantic model in models.py
    - Define MassReportAlert class with fields: alert_id, normalized_url, report_count, alert_summary, alert_warning, notified_user_count, created_at, status
    - Add validation rules: alert_id must be UUID format, report_count >= 10, status must be one of ["pending", "processing", "completed", "failed"]
    - _Requirements: 4.2, 4.3, 4.4, 12.1, 12.2, 12.3_
  
  - [x] 1.2 Extend ScamReport model with mass report fields
    - Add is_mass_reported (bool, default False) and mass_report_alert_id (Optional[str]) fields to existing ScamReport model
    - Add validation: when is_mass_reported is True, mass_report_alert_id must not be None
    - _Requirements: 2.4, 4.7, 12.4_
  
  - [x] 1.3 Create MassReportAlerts DynamoDB table in database.py
    - Implement create_mass_report_alerts_table() function
    - Define table schema: Partition Key = alert_id, GSI = NormalizedUrlIndex (Partition Key = normalized_url)
    - Add AttributeDefinitions for alert_id, normalized_url, created_at
    - _Requirements: 4.1, 1.4_

- [x] 2. Implement MassReportDetector component
  - [x] 2.1 Create MassReportDetector class in new file mass_report_detector.py
    - Implement __init__ method to initialize DynamoDB client
    - Define class with methods: check_report_threshold, mark_as_mass_reported, get_original_message
    - _Requirements: 1.1, 2.1_
  
  - [x] 2.2 Implement check_report_threshold() method
    - Query ScamReports table using NormalizedUrlIndex GSI to count reports for given normalized_url
    - Return True if count >= threshold (default 10), False otherwise
    - Ensure query completes within 50ms
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
  
  - [ ]* 2.3 Write property test for check_report_threshold()
    - **Property 1: Threshold check correctness**
    - **Validates: Requirements 1.2, 1.3**
    - Use Hypothesis to generate random URLs and report counts
    - Verify function returns True iff report_count >= threshold
  
  - [x] 2.4 Implement mark_as_mass_reported() method
    - Use DynamoDB conditional write to check if notification already exists for normalized_url
    - Query MassReportAlerts table using NormalizedUrlIndex GSI
    - Return False if alert already exists, True if successfully marked
    - _Requirements: 2.1, 2.2, 2.3, 2.5_
  
  - [ ]* 2.5 Write property test for duplicate prevention
    - **Property 2: Notification uniqueness**
    - **Validates: Requirements 2.2, 2.5**
    - Verify calling mark_as_mass_reported() twice for same URL only creates one alert
  
  - [x] 2.6 Implement get_original_message() method
    - Query ScamReports table for the first report with given normalized_url
    - Extract and return the original message content
    - Return None if no message found
    - _Requirements: 3.1_

- [x] 3. Implement BedrockSummarizer component
  - [x] 3.1 Create BedrockSummarizer class in bedrock_service.py
    - Add generate_mass_report_alert() method to existing bedrock_service.py
    - Initialize with Bedrock client and model configuration
    - _Requirements: 3.2_
  
  - [x] 3.2 Implement generate_mass_report_alert() method
    - Construct prompt for Bedrock LLM with original_message and report_count
    - Call Bedrock API with 10-second timeout
    - Parse response to extract alert_summary and alert_warning
    - Return dict with alert_summary and alert_warning keys
    - _Requirements: 3.2, 3.3, 3.4, 3.7_
  
  - [x] 3.3 Implement fallback for LLM failures
    - Catch exceptions from Bedrock API calls
    - Return default safe alert message when LLM fails or times out
    - Default message: "系統偵測到大量使用者通報相同詐騙訊息" with generic warning
    - _Requirements: 3.6, 3.7, 9.4_
  
  - [ ]* 3.4 Write unit tests for BedrockSummarizer
    - Test successful LLM response parsing
    - Test timeout handling (mock 10+ second delay)
    - Test API failure handling
    - Test default message generation
    - _Requirements: 3.6, 3.7_
  
  - [ ]* 3.5 Write property test for message safety
    - **Property 3: Message safety**
    - **Validates: Requirements 3.3, 3.5, 11.1, 11.2, 11.6**
    - Verify alert_summary text similarity to original_message is < 0.8
    - Use Levenshtein distance or similar algorithm

- [ ] 4. Implement NotificationDispatcher component
  - [x] 4.1 Create NotificationDispatcher class in new file notification_dispatcher.py
    - Initialize with LINE bot API client and DynamoDB client
    - Define methods: get_all_active_users, broadcast_mass_report_alert, send_push_message
    - _Requirements: 5.1, 6.1_
  
  - [x] 4.2 Implement get_all_active_users() method
    - Query database for all users who have submitted reports or interacted with system
    - Filter for valid LINE UIDs (starting with 'U')
    - Return list of user IDs, or empty list if none found
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 12.6_
  
  - [x] 4.3 Implement format_mass_report_notification() helper function
    - Format notification message with header, report count, alert_summary, alert_warning, and call-to-action
    - Use Traditional Chinese (繁體中文) text
    - Include appropriate emoji for readability
    - Ensure message length <= 5000 characters
    - _Requirements: 6.1, 6.2, 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7_
  
  - [x] 4.4 Implement broadcast_mass_report_alert() method
    - Split user list into batches of 500 (LINE API limit)
    - Use LINE multicast API for each batch
    - Track success_count and failed_count
    - For failed batches, retry individual users
    - Return dict with success_count, failed_count, failed_users
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_
  
  - [ ]* 4.5 Write property test for push completeness
    - **Property 4: Push completeness**
    - **Validates: Requirements 6.9**
    - Verify success_count + failed_count = len(user_ids) for any user list
  
  - [x] 4.6 Implement error handling for push failures
    - Log failures with user_id and error_reason
    - Continue processing other users when one fails
    - Maintain failed_users list
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [ ]* 4.7 Write unit tests for NotificationDispatcher
    - Test batch splitting logic (empty list, <500 users, >500 users)
    - Test individual retry on batch failure
    - Test error logging for blocked users and invalid IDs
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 5. Checkpoint - Ensure all component tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Implement main orchestration logic
  - [x] 6.1 Create process_mass_report() function in new file mass_report_service.py
    - Implement main orchestration algorithm from design document
    - Coordinate MassReportDetector, BedrockSummarizer, and NotificationDispatcher
    - Handle all steps: threshold check, duplicate check, message extraction, LLM call, alert creation, notification broadcast
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2, 4.1, 6.1_
  
  - [x] 6.2 Implement alert record creation and status management
    - Generate UUID for alert_id
    - Create alert record with status "processing"
    - Save to MassReportAlerts table
    - Update status to "completed" or "failed" after broadcast
    - Update notified_user_count with actual success count
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_
  
  - [x] 6.3 Implement mark reports as processed
    - Update all ScamReports with matching normalized_url
    - Set is_mass_reported = True and mass_report_alert_id = alert_id
    - _Requirements: 2.4, 4.7_
  
  - [ ]* 6.4 Write property test for idempotency
    - **Property 5: Idempotency**
    - **Validates: Requirements 2.2, 2.5**
    - Verify calling process_mass_report() twice for same URL only sends one notification
  
  - [ ]* 6.5 Write integration tests for process_mass_report()
    - Test end-to-end flow: 10 reports → notification sent
    - Test duplicate prevention: second call returns "already_notified"
    - Test LLM failure fallback
    - Test partial push failure handling
    - _Requirements: 1.2, 2.2, 3.6, 7.5_

- [ ] 7. Integrate with existing report flow
  - [x] 7.1 Modify handle_text() in main.py to call mass report check
    - After saving report to database, get current report count for normalized_url
    - Call process_mass_report() asynchronously (non-blocking)
    - Ensure user receives standard report confirmation immediately
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [x] 7.2 Add helper function to get report count
    - Implement get_report_count(normalized_url) in database.py
    - Query ScamReports using NormalizedUrlIndex GSI
    - Return count of reports for given URL
    - _Requirements: 1.1, 1.4_
  
  - [ ]* 7.3 Write integration test for report flow
    - Test that user report submission is not blocked by mass notification processing
    - Verify user receives confirmation before mass notification completes
    - _Requirements: 8.3, 8.4, 8.5_

- [ ] 8. Implement error handling and logging
  - [x] 8.1 Add comprehensive error logging to all components
    - Log errors with timestamp, component name, error type, error details
    - Use Python logging module with appropriate log levels
    - _Requirements: 9.1_
  
  - [x] 8.2 Implement database error handling
    - Catch DynamoDB exceptions in all database operations
    - Return database_error status when queries fail
    - Implement exponential backoff retry for write operations (up to 3 retries)
    - _Requirements: 9.2, 9.3, 10.6_
  
  - [x] 8.3 Implement external service error handling
    - Handle Bedrock LLM service unavailability with default message
    - Handle LINE API unavailability with logging and optional retry queue
    - Log all external service failures
    - _Requirements: 9.4, 9.5_
  
  - [x] 8.4 Configure log retention
    - Set up log rotation to maintain logs for at least 30 days
    - Configure appropriate log storage location
    - _Requirements: 9.6_

- [ ] 9. Implement security and performance features
  - [x] 9.1 Add rate limiting for report submissions
    - Implement rate limiter: 10 reports per user per minute
    - Track submission timestamps per user
    - Return error when rate limit exceeded
    - _Requirements: 11.4_
  
  - [x] 9.2 Secure LINE Channel Access Token
    - Verify token is loaded from environment variables
    - Add validation that token is not hardcoded in source
    - _Requirements: 11.3_
  
  - [x] 9.3 Implement concurrent request handling
    - Use DynamoDB conditional writes for atomic operations
    - Implement optimistic locking with is_mass_reported flag
    - _Requirements: 2.3, 2.5, 10.1_
  
  - [ ]* 9.4 Write performance tests
    - Test query performance: verify < 50ms for report count queries
    - Test broadcast performance: verify < 60s for 10,000 users
    - Test concurrent processing: verify 100 reports/second throughput
    - _Requirements: 1.5, 6.10, 10.1, 10.2, 10.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The implementation uses Python and integrates with existing modules (bedrock_service.py, database.py, main.py)
- Property tests validate universal correctness properties using Hypothesis framework
- Unit tests validate specific examples and edge cases
- Integration tests verify end-to-end functionality
- Checkpoints ensure incremental validation at reasonable breaks
