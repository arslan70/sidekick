# User Story Writing Best Practices

## Overview

This guide provides comprehensive best practices for writing effective user stories that follow the EARS (Easy Approach to Requirements Syntax) format and INCOSE quality standards.

**Target Audience**: Product Managers, Business Analysts, Engineering Teams  
**Last Updated**: October 2025

---

## 1. User Story Format

### Basic Structure
```
As a [role/persona],
I want [feature/capability],
So that [business value/benefit]
```

### Example
```
As a registered user,
I want to securely log into the application,
So that I can access my personalized dashboard and protected resources
```

---

## 2. EARS Format for Acceptance Criteria

EARS (Easy Approach to Requirements Syntax) provides six patterns for writing clear, testable requirements.

### Pattern 1: Ubiquitous Requirements
**Format**: `THE <system> SHALL <response>`

**Use When**: Requirement applies universally, no conditions

**Example**:
```
THE Authentication System SHALL encrypt all passwords using bcrypt with cost factor 12
```

### Pattern 2: Event-Driven Requirements
**Format**: `WHEN <trigger>, THE <system> SHALL <response>`

**Use When**: Requirement triggered by specific event

**Examples**:
```
WHEN a user enters valid credentials, THE Authentication System SHALL authenticate and redirect to dashboard

WHEN a user clicks the "Submit" button, THE Form Validator SHALL validate all required fields
```

### Pattern 3: State-Driven Requirements
**Format**: `WHILE <condition>, THE <system> SHALL <response>`

**Use When**: Requirement applies during specific state

**Examples**:
```
WHILE a user session is active, THE Session Manager SHALL refresh the authentication token every 15 minutes

WHILE the database connection pool is above 80% capacity, THE Monitoring System SHALL send warning alerts
```

### Pattern 4: Unwanted Event Requirements
**Format**: `IF <condition>, THEN THE <system> SHALL <response>`

**Use When**: Handling error conditions or unwanted events

**Examples**:
```
IF a user enters invalid credentials, THEN THE Authentication System SHALL display error message and remain on login page

IF a payment transaction fails, THEN THE Payment Service SHALL retry up to 3 times with exponential backoff
```

### Pattern 5: Optional Feature Requirements
**Format**: `WHERE <option>, THE <system> SHALL <response>`

**Use When**: Feature is optional or configurable

**Examples**:
```
WHERE two-factor authentication is enabled, THE Authentication System SHALL require verification code after password

WHERE the user has admin privileges, THE Dashboard SHALL display administrative controls
```

### Pattern 6: Complex Requirements
**Format**: `[WHERE] [WHILE] [WHEN/IF] THE <system> SHALL <response>`

**Order**: WHERE → WHILE → WHEN/IF → THE → SHALL

**Example**:
```
WHERE two-factor authentication is enabled, WHILE the user session is active, WHEN the user attempts to access sensitive data, THE Authorization System SHALL require re-authentication
```

---

## 3. INCOSE Quality Rules

### Rule 1: Use Active Voice
✅ **Good**: "THE System SHALL validate the input"  
❌ **Bad**: "The input SHALL be validated"

### Rule 2: Avoid Vague Terms
❌ **Avoid**: quickly, adequate, sufficient, user-friendly, robust  
✅ **Use**: Specific, measurable terms with numbers

**Example**:
- ❌ "The system SHALL respond quickly"
- ✅ "THE System SHALL respond within 500 milliseconds"

### Rule 3: No Escape Clauses
❌ **Avoid**: "where possible", "if feasible", "as appropriate"  
✅ **Use**: Definitive statements

**Example**:
- ❌ "The system SHALL encrypt data where possible"
- ✅ "THE System SHALL encrypt all user data using AES-256"

### Rule 4: No Negative Statements
❌ **Avoid**: "SHALL NOT", "must not", "will not"  
✅ **Use**: Positive statements about what system SHALL do

**Example**:
- ❌ "The system SHALL NOT allow weak passwords"
- ✅ "THE System SHALL require passwords with minimum 12 characters, including uppercase, lowercase, numbers, and special characters"

### Rule 5: One Thought Per Requirement
❌ **Bad**: "THE System SHALL validate email format and send confirmation email and log the event"  
✅ **Good**: Split into three requirements:
1. "THE System SHALL validate email addresses using RFC 5322 format"
2. "WHEN email validation succeeds, THE System SHALL send confirmation email"
3. "WHEN confirmation email is sent, THE System SHALL log the event with timestamp"

### Rule 6: Explicit and Measurable
Every requirement must be testable with clear pass/fail criteria.

**Example**:
- ❌ "The system SHALL be fast"
- ✅ "THE System SHALL process 1000 transactions per second with 99th percentile latency under 100 milliseconds"

### Rule 7: Consistent Terminology
Define terms in glossary and use consistently throughout.

**Glossary Example**:
- **Authentication System**: The subsystem responsible for verifying user identity
- **Session**: A period of authenticated user activity, maximum duration 24 hours
- **User**: A registered account holder with valid credentials

### Rule 8: No Pronouns
❌ **Avoid**: "it", "them", "they", "this"  
✅ **Use**: Specific system names

**Example**:
- ❌ "When it receives a request, it SHALL validate it"
- ✅ "WHEN the API Gateway receives a request, THE API Gateway SHALL validate the request payload"

### Rule 9: No Absolutes
❌ **Avoid**: "never", "always", "100%", "all", "every"  
✅ **Use**: Realistic, achievable targets

**Example**:
- ❌ "The system SHALL never fail"
- ✅ "THE System SHALL maintain 99.9% uptime measured monthly"

### Rule 10: Solution-Free
Focus on WHAT, not HOW. Implementation details belong in design documents.

**Example**:
- ❌ "THE System SHALL use Redis cache to store session data"
- ✅ "THE System SHALL retrieve session data within 50 milliseconds"

---

## 4. Complete User Story Example

### User Story
```
As a registered user,
I want to securely log into the application,
So that I can access my personalized dashboard and protected resources
```

### Glossary
- **Authentication System**: The subsystem responsible for verifying user credentials
- **User**: A registered account holder with valid email and password
- **Session**: An authenticated period of user activity with 24-hour maximum duration
- **Dashboard**: The personalized home page displaying user-specific information

### Acceptance Criteria (EARS Format)

1. **WHEN** a user enters valid credentials, **THE** Authentication System **SHALL** authenticate and redirect to dashboard within 2 seconds

2. **WHEN** a user enters invalid credentials, **THE** Authentication System **SHALL** display error message "Invalid email or password" and remain on login page

3. **IF** a user fails authentication 3 times within 15 minutes, **THEN THE** Authentication System **SHALL** temporarily lock the account for 15 minutes

4. **WHEN** a user successfully logs in, **THE** Authentication System **SHALL** create a secure session token with 24-hour expiration using JWT

5. **IF** a user's session expires, **THEN THE** Authentication System **SHALL** redirect to login page with message "Your session has expired. Please log in again"

6. **WHERE** two-factor authentication is enabled, **WHEN** a user enters valid password, **THE** Authentication System **SHALL** require verification code before granting access

7. **THE** Authentication System **SHALL** encrypt all passwords using bcrypt with cost factor 12

8. **WHEN** a user logs in, **THE** Authentication System **SHALL** log the event with timestamp, IP address, and user agent

9. **WHILE** a user session is active, **THE** Session Manager **SHALL** refresh the authentication token every 15 minutes

10. **THE** Authentication System **SHALL** support concurrent sessions from maximum 3 devices per user

### Technical Considerations
- Use bcrypt for password hashing (cost factor 12)
- Implement rate limiting: 5 login attempts per minute per IP
- Add CAPTCHA after 2 failed attempts
- Log all authentication events for security audit
- Support OAuth 2.0 for third-party authentication (future enhancement)

### Definition of Done
- [ ] All acceptance criteria implemented and tested
- [ ] Unit tests written with >80% coverage
- [ ] Integration tests pass
- [ ] Security review completed
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Deployed to staging environment
- [ ] User acceptance testing completed

---

## 5. Common Mistakes to Avoid

### Mistake 1: Vague Acceptance Criteria
❌ **Bad**:
```
- The system should be secure
- Login should be fast
- Errors should be handled gracefully
```

✅ **Good**:
```
- THE Authentication System SHALL encrypt passwords using bcrypt cost factor 12
- WHEN user enters credentials, THE System SHALL respond within 2 seconds
- IF authentication fails, THEN THE System SHALL display specific error message
```

### Mistake 2: Implementation Details in Requirements
❌ **Bad**:
```
- Use Redis for session storage
- Implement JWT tokens with HS256 algorithm
- Store passwords in PostgreSQL users table
```

✅ **Good**:
```
- THE System SHALL retrieve session data within 50 milliseconds
- THE System SHALL maintain user sessions for 24 hours
- THE System SHALL store passwords securely with one-way encryption
```

### Mistake 3: Missing Edge Cases
❌ **Incomplete**:
```
- User can log in with email and password
```

✅ **Complete**:
```
- WHEN user enters valid credentials, THE System SHALL authenticate
- WHEN user enters invalid credentials, THE System SHALL reject
- IF user fails 3 times, THEN THE System SHALL lock account
- IF session expires, THEN THE System SHALL require re-authentication
- WHERE 2FA enabled, THE System SHALL require verification code
```

### Mistake 4: Non-Testable Requirements
❌ **Bad**:
```
- The system should be user-friendly
- Login should be intuitive
- Errors should be helpful
```

✅ **Good**:
```
- THE System SHALL display login form with labeled fields for email and password
- WHEN authentication fails, THE System SHALL display specific error message
- THE System SHALL complete login within 2 seconds for 95% of requests
```

### Mistake 5: Mixing Multiple Features
❌ **Bad**:
```
As a user, I want to log in, reset my password, and manage my profile
```

✅ **Good**: Split into separate stories:
```
Story 1: As a user, I want to log in
Story 2: As a user, I want to reset my password
Story 3: As a user, I want to manage my profile
```

---

## 6. Story Sizing Guidelines

### Small (1-2 days)
- Single feature with 3-5 acceptance criteria
- Minimal dependencies
- Clear implementation path

**Example**: Add "Remember Me" checkbox to login form

### Medium (3-5 days)
- Feature with 5-8 acceptance criteria
- Some dependencies
- Requires design decisions

**Example**: Implement OAuth 2.0 authentication

### Large (1-2 weeks)
- Complex feature with 8+ acceptance criteria
- Multiple dependencies
- Significant design work

**Example**: Build complete user management system

**Recommendation**: Break large stories into smaller ones

---

## 7. Refinement Checklist

Before marking a story as "Ready for Development":

- [ ] User story follows "As a... I want... So that..." format
- [ ] All acceptance criteria use EARS patterns
- [ ] Each criterion is testable with clear pass/fail
- [ ] Glossary defines all technical terms
- [ ] No vague terms (quickly, adequate, user-friendly)
- [ ] No escape clauses (where possible, if feasible)
- [ ] No negative statements (SHALL NOT)
- [ ] One thought per requirement
- [ ] Consistent terminology throughout
- [ ] No pronouns (it, them, they)
- [ ] Realistic, achievable targets (no absolutes)
- [ ] Solution-free (focuses on WHAT, not HOW)
- [ ] Edge cases covered
- [ ] Technical considerations documented
- [ ] Definition of Done defined
- [ ] Story sized appropriately (<2 weeks)
- [ ] Dependencies identified
- [ ] Acceptance criteria reviewed by team

---

## 8. Templates

### Template 1: Feature Story
```markdown
## User Story
As a [role],
I want [feature],
So that [benefit]

## Glossary
- **Term 1**: Definition
- **Term 2**: Definition

## Acceptance Criteria
1. WHEN [event], THE [System] SHALL [response]
2. IF [condition], THEN THE [System] SHALL [response]
3. WHILE [state], THE [System] SHALL [response]

## Technical Considerations
- [Technical note 1]
- [Technical note 2]

## Definition of Done
- [ ] Implemented and tested
- [ ] Code reviewed
- [ ] Documentation updated
```

### Template 2: Bug Fix Story
```markdown
## Problem Description
[Describe the bug]

## Expected Behavior
THE [System] SHALL [correct behavior]

## Actual Behavior
THE [System] currently [incorrect behavior]

## Acceptance Criteria
1. WHEN [scenario], THE [System] SHALL [correct response]
2. THE [System] SHALL [verification step]

## Root Cause
[If known]

## Definition of Done
- [ ] Bug fixed and verified
- [ ] Regression tests added
- [ ] Root cause documented
```

---

**Document Owner**: Product Management Team  
**Last Updated**: October 2025  
**Review Frequency**: Quarterly  
**Questions?**: Contact product@acmecorp.com
