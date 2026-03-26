# Requirements Document: Mass Report Notification System

## Introduction

This document specifies the requirements for a mass report notification system that alerts all users when a message receives a high volume of reports. The system protects user privacy by using AWS Bedrock LLM to generate summaries and risk warnings instead of broadcasting the original message content. This feature establishes a community-based fraud prevention mechanism, enabling users to stay informed about current scam tactics.

## Glossary

- **System**: The mass report notification system
- **MassReportDetector**: Component that monitors report counts and triggers notifications
- **BedrockSummarizer**: Component that generates safe summaries using AWS Bedrock LLM
- **NotificationDispatcher**: Component that broadcasts alerts to all users
- **ScamReports_Table**: DynamoDB table storing scam report records
- **MassReportAlerts_Table**: DynamoDB table storing mass report alert records
- **Normalized_URL**: A standardized URL format used for deduplication
- **Report_Threshold**: The minimum number of reports required to trigger a mass notification (default: 10)
- **Active_User**: A user who has previously interacted with the system
- **Alert_Summary**: LLM-generated summary of the reported message
- **Alert_Warning**: LLM-generated risk warning and prevention advice
- **LINE_Messaging_API**: External service for pushing messages to users
- **Original_Message**: The complete content of the reported scam message

## Requirements

### Requirement 1: Report Threshold Detection

**User Story:** As a system administrator, I want the system to detect when a message reaches the report threshold, so that mass notifications can be triggered automatically.

#### Acceptance Criteria

1. WHEN a new report is submitted, THE MassReportDetector SHALL query the ScamReports_Table to count reports for the Normalized_URL
2. WHEN the report count for a Normalized_URL reaches the Report_Threshold, THE MassReportDetector SHALL trigger the mass notification process
3. WHEN the report count is below the Report_Threshold, THE MassReportDetector SHALL not trigger any notification
4. THE MassReportDetector SHALL use the NormalizedUrlIndex GSI for querying report counts
5. WHEN querying report counts, THE System SHALL complete the query within 50 milliseconds

### Requirement 2: Duplicate Notification Prevention

**User Story:** As a system administrator, I want to ensure each URL only triggers one mass notification, so that users don't receive duplicate alerts.

#### Acceptance Criteria

1. WHEN a Normalized_URL reaches the Report_Threshold, THE MassReportDetector SHALL check if a mass notification has already been sent for that URL
2. IF a mass notification already exists for a Normalized_URL, THEN THE System SHALL not create a new notification
3. WHEN marking a URL as mass reported, THE System SHALL use DynamoDB conditional writes to ensure atomicity
4. THE System SHALL set the is_mass_reported flag to true for all reports associated with the Normalized_URL
5. WHEN concurrent requests attempt to create notifications for the same URL, THE System SHALL ensure only one notification is created

### Requirement 3: Safe Summary Generation

**User Story:** As a user, I want to receive summarized alerts instead of original scam messages, so that my privacy and security are protected.

#### Acceptance Criteria

1. WHEN a mass notification is triggered, THE BedrockSummarizer SHALL extract the Original_Message from the ScamReports_Table
2. WHEN generating an alert, THE BedrockSummarizer SHALL invoke AWS Bedrock LLM with the Original_Message and report count
3. THE BedrockSummarizer SHALL generate an Alert_Summary that does not contain the complete Original_Message content
4. THE BedrockSummarizer SHALL generate an Alert_Warning with specific prevention advice
5. THE Alert_Summary SHALL have a text similarity score less than 0.8 when compared to the Original_Message
6. IF the Bedrock LLM call fails, THEN THE BedrockSummarizer SHALL return a default safe alert message
7. WHEN the Bedrock LLM call exceeds 10 seconds, THE System SHALL timeout and use the default alert message

### Requirement 4: Alert Record Management

**User Story:** As a system administrator, I want to track all mass report alerts, so that I can monitor system behavior and analyze patterns.

#### Acceptance Criteria

1. WHEN a mass notification is triggered, THE System SHALL create a record in the MassReportAlerts_Table
2. THE System SHALL generate a unique alert_id in UUID format for each alert record
3. THE alert record SHALL include alert_id, normalized_url, report_count, alert_summary, alert_warning, status, and created_at fields
4. THE System SHALL set the initial status to "processing" when creating the alert record
5. WHEN the notification process completes, THE System SHALL update the status to "completed" and record the notified_user_count
6. IF the notification process fails, THEN THE System SHALL update the status to "failed"
7. THE System SHALL link all related ScamReports to the alert_id using the mass_report_alert_id field

### Requirement 5: Active User Identification

**User Story:** As a system administrator, I want to identify all active users, so that mass notifications reach the appropriate audience.

#### Acceptance Criteria

1. THE NotificationDispatcher SHALL query the database to retrieve all Active_User identifiers
2. THE System SHALL define an Active_User as any user who has previously submitted a report or interacted with the system
3. THE NotificationDispatcher SHALL return a list of valid LINE user IDs (UIDs starting with 'U')
4. WHEN no active users exist, THE NotificationDispatcher SHALL return an empty list and not attempt to send notifications

### Requirement 6: Batch Notification Broadcasting

**User Story:** As a user, I want to receive timely alerts about mass-reported scams, so that I can protect myself and my family from fraud.

#### Acceptance Criteria

1. WHEN broadcasting an alert, THE NotificationDispatcher SHALL format the notification message with the Alert_Summary, Alert_Warning, and report count
2. THE notification message SHALL not exceed 5000 characters (LINE API limit)
3. THE NotificationDispatcher SHALL use the LINE_Messaging_API multicast function to send messages in batches of up to 500 users
4. WHEN the user list exceeds 500 users, THE NotificationDispatcher SHALL split the list into multiple batches
5. THE NotificationDispatcher SHALL process all batches sequentially
6. WHEN a batch push succeeds, THE System SHALL increment the success_count by the batch size
7. IF a batch push fails, THEN THE NotificationDispatcher SHALL attempt individual retry for each user in the failed batch
8. THE NotificationDispatcher SHALL record the final success_count and failed_count
9. THE sum of success_count and failed_count SHALL equal the total number of Active_Users
10. WHEN broadcasting to 10,000 users, THE System SHALL complete the process within 1 minute

### Requirement 7: Push Failure Handling

**User Story:** As a system administrator, I want the system to handle push failures gracefully, so that one failure doesn't prevent others from receiving alerts.

#### Acceptance Criteria

1. IF a user has blocked the bot, THEN THE System SHALL log the failure and continue processing other users
2. IF a user ID is invalid, THEN THE System SHALL log the failure and continue processing other users
3. WHEN the LINE_Messaging_API returns an error, THE System SHALL log the error details including user_id and error_reason
4. THE System SHALL maintain a list of failed_users for each broadcast operation
5. WHEN a batch fails, THE System SHALL attempt individual retry for each user in that batch before marking them as failed

### Requirement 8: Integration with Existing Report Flow

**User Story:** As a developer, I want the mass notification feature to integrate seamlessly with the existing report flow, so that no manual intervention is required.

#### Acceptance Criteria

1. WHEN a user submits a scam report through the LINE bot, THE System SHALL process the report using the existing workflow
2. AFTER storing the report in ScamReports_Table, THE System SHALL invoke the MassReportDetector to check the report threshold
3. WHEN the mass notification process is triggered, THE System SHALL not block the user's report submission response
4. THE System SHALL reply to the user with the standard report confirmation before processing mass notifications
5. THE mass notification process SHALL execute asynchronously without affecting the user experience

### Requirement 9: Error Recovery and Logging

**User Story:** As a system administrator, I want comprehensive error logging and recovery mechanisms, so that I can troubleshoot issues and ensure system reliability.

#### Acceptance Criteria

1. WHEN any component encounters an error, THE System SHALL log the error with timestamp, component name, error type, and error details
2. IF the ScamReports_Table query fails, THEN THE System SHALL return a database_error status and not proceed with notification
3. IF the MassReportAlerts_Table write fails, THEN THE System SHALL log the error and retry up to 3 times with exponential backoff
4. WHEN the Bedrock LLM service is unavailable, THE System SHALL use the default alert message and log the service failure
5. WHEN the LINE_Messaging_API is unavailable, THE System SHALL log the failure and store the notification for later retry
6. THE System SHALL maintain logs for at least 30 days for audit and debugging purposes

### Requirement 10: Performance and Scalability

**User Story:** As a system administrator, I want the system to handle high volumes efficiently, so that it can scale with user growth.

#### Acceptance Criteria

1. THE System SHALL support processing at least 100 concurrent report submissions per second
2. WHEN querying report counts using the NormalizedUrlIndex GSI, THE System SHALL complete queries in under 50 milliseconds
3. WHEN broadcasting to 10,000 users, THE System SHALL complete the operation within 60 seconds
4. THE System SHALL use DynamoDB on-demand billing or provisioned capacity of at least 5 RCU and 5 WCU
5. THE System SHALL process Bedrock LLM calls within 2-5 seconds under normal conditions
6. WHEN database operations experience high latency, THE System SHALL implement exponential backoff retry logic

### Requirement 11: Security and Privacy

**User Story:** As a user, I want my privacy protected, so that sensitive information in reported messages is not exposed to others.

#### Acceptance Criteria

1. THE System SHALL never broadcast the complete Original_Message content to users
2. THE Alert_Summary SHALL be generated by the BedrockSummarizer and SHALL not contain verbatim quotes from the Original_Message
3. THE System SHALL store the LINE Channel Access Token in environment variables, not in source code
4. THE System SHALL implement rate limiting of 10 reports per user per minute to prevent abuse
5. WHEN storing Original_Message content, THE System SHALL apply appropriate access controls to restrict unauthorized access
6. THE System SHALL validate that the Alert_Summary text similarity to Original_Message is below 0.8 before broadcasting

### Requirement 12: Data Model Validation

**User Story:** As a developer, I want strict data validation, so that data integrity is maintained across all operations.

#### Acceptance Criteria

1. THE MassReportAlert model SHALL validate that alert_id is a valid UUID format
2. THE MassReportAlert model SHALL validate that report_count is greater than or equal to the Report_Threshold
3. THE MassReportAlert model SHALL validate that status is one of: "pending", "processing", "completed", "failed"
4. WHEN is_mass_reported is true in a ScamReport, THE System SHALL ensure mass_report_alert_id is not null
5. THE System SHALL ensure each Normalized_URL is associated with at most one mass_report_alert_id
6. THE System SHALL validate that all LINE user IDs start with the character 'U' before attempting to send messages

### Requirement 13: Notification Message Format

**User Story:** As a user, I want clear and actionable alert messages, so that I understand the risk and know how to protect myself.

#### Acceptance Criteria

1. THE notification message SHALL include a clear header indicating it is a community fraud alert
2. THE notification message SHALL display the report count to show the severity of the threat
3. THE notification message SHALL include the Alert_Summary section with the risk description
4. THE notification message SHALL include the Alert_Warning section with prevention advice
5. THE notification message SHALL include a call-to-action encouraging users to report similar messages
6. THE notification message SHALL use appropriate emoji or symbols to enhance readability
7. THE notification message SHALL be formatted in Traditional Chinese (繁體中文) to match the user base

