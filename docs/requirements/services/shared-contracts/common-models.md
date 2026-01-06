# Shared Data Contracts

## Common Data Models

### Standard Response Envelope

All API responses follow a consistent envelope structure to provide metadata and standardize error handling across services.

```json
{
  "data": {
    // Actual response payload
  },
  "meta": {
    "timestamp": "2025-08-23T10:30:00Z",
    "requestId": "req_123456789",
    "version": "v1",
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 150,
      "totalPages": 8
    }
  },
  "links": {
    "self": "https://api.platform.com/v1/resource",
    "next": "https://api.platform.com/v1/resource?page=2",
    "prev": null,
    "first": "https://api.platform.com/v1/resource?page=1",
    "last": "https://api.platform.com/v1/resource?page=8"
  }
}
```

### Error Response Structure

Standardized error responses follow RFC 7807 Problem Details for HTTP APIs specification.

```json
{
  "type": "https://platform.com/problems/validation-error",
  "title": "Validation Failed",
  "status": 400,
  "detail": "The provided email address is not valid",
  "instance": "/api/users/create",
  "timestamp": "2025-08-23T10:30:00Z",
  "traceId": "trace_abc123def456",
  "requestId": "req_123456789",
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "Email address format is invalid",
      "rejectedValue": "invalid-email"
    }
  ]
}
```

### Audit and Metadata Fields

**Standard Audit Information**

```json
{
  "createdAt": "2025-08-23T10:30:00Z",
  "createdBy": {
    "userId": "usr_123e4567-e89b-12d3-a456-426614174000",
    "displayName": "John Doe"
  },
  "updatedAt": "2025-08-23T11:45:00Z",
  "updatedBy": {
    "userId": "usr_987654321-a456-42d3-e89b-426614174000",
    "displayName": "Jane Smith"
  },
  "version": 3,
  "status": "active"
}
```

**Soft Delete Information**

```json
{
  "deletedAt": "2025-08-23T12:00:00Z",
  "deletedBy": {
    "userId": "usr_123e4567-e89b-12d3-a456-426614174000",
    "displayName": "John Doe"
  },
  "deletionReason": "User requested account closure"
}
```

## CloudEvents Domain Events

### CloudEvents Specification Compliance

All domain events follow the [CloudEvents v1.0 specification](https://cloudevents.io/) for interoperability across cloud platforms and event brokers.

```json
{
  "specversion": "1.0",
  "id": "user-registered-4174-7400-7567",
  "source": "/platform/user-service",
  "type": "com.platform.user.registered.v1",
  "time": "2025-08-23T10:30:00Z",
  "datacontenttype": "application/json",
  "subject": "usr_123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "userId": "usr_123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "registrationMethod": "email",
    "organizationId": "org_123e4567-e89b-12d3-a456-426614174000",
    "metadata": {
      "ipAddress": "192.168.1.100",
      "userAgent": "Mozilla/5.0...",
      "registrationSource": "web"
    }
  },
  "traceparent": "00-abc123def456-789012345678-01",
  "correlationid": "corr_456789123"
}
```

### Event Type Convention

**Event Type Format**: `{domain}.{entity}.{action}.{version}`

- **Domain**: `com.platform` for all platform events
- **Entity**: The aggregate or entity being acted upon
- **Action**: Past tense verb describing what occurred
- **Version**: Semantic version for schema evolution

**Standard Event Types**:

```text
com.platform.user.registered.v1
com.platform.user.activated.v1
com.platform.user.deactivated.v1
com.platform.user.profile.updated.v1
com.platform.organization.created.v1
com.platform.content.created.v1
com.platform.content.updated.v1
com.platform.notification.sent.v1
```

### Event Context Attributes

**Required CloudEvents Context Attributes**:

- `specversion`: CloudEvents specification version (1.0)
- `id`: Unique event identifier (UUID or similar)
- `source`: Event producer URI identifier
- `type`: Event type following domain convention
- `time`: RFC 3339 timestamp when event occurred

**Optional Platform-Specific Extensions**:

- `subject`: Entity identifier that the event is about
- `traceparent`: W3C Trace Context for distributed tracing
- `correlationid`: Business process correlation identifier
- `causationid`: Identifier of the command that caused this event
- `tenantid`: Multi-tenant organization identifier

### Event Data Schema

**User Domain Events**:

```json
{
  "type": "com.platform.user.registered.v1",
  "data": {
    "userId": "usr_123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "firstName": "John",
    "lastName": "Doe",
    "registrationMethod": "email",
    "organizationId": "org_123e4567-e89b-12d3-a456-426614174000",
    "roles": ["user"],
    "preferences": {
      "language": "en",
      "timezone": "America/Los_Angeles",
      "notifications": {
        "email": true,
        "push": false
      }
    }
  }
}
```

**Content Domain Events**:

```json
{
  "type": "com.platform.content.created.v1",
  "data": {
    "contentId": "cnt_123e4567-e89b-12d3-a456-426614174000",
    "userId": "usr_123e4567-e89b-12d3-a456-426614174000",
    "organizationId": "org_123e4567-e89b-12d3-a456-426614174000",
    "title": "Quarterly Business Report",
    "contentType": "report",
    "category": "business",
    "tags": ["quarterly", "report", "business"],
    "metadata": {
      "creationMethod": "web",
      "clientIp": "192.168.1.100",
      "status": "draft",
      "requiresReview": true
    }
  }
}
```

### Event Routing and Delivery

**Event Broker Integration**:

- **NATS JetStream**: Primary event streaming platform
- **Apache Kafka**: High-throughput event streaming for analytics
- **CloudEvents Bindings**: HTTP, AMQP, MQTT protocol support
- **Dead Letter Queues**: Failed event handling and retry mechanisms

**Event Delivery Guarantees**:

- **At-least-once delivery**: Events guaranteed to be delivered
- **Idempotent consumers**: Event handlers designed for duplicate processing
- **Ordering guarantees**: Events ordered by entity/aggregate ID
- **Retention policies**: Event storage duration based on business requirements

## API Standards

### Request Headers

**Required Headers**

- `Authorization`: Bearer token for authenticated requests
- `Content-Type`: MIME type of request body (application/json)
- `Accept`: Acceptable response MIME types
- `X-Request-ID`: Unique identifier for request tracing

**Optional Headers**

- `X-Correlation-ID`: Business process correlation identifier
- `Accept-Language`: Preferred response language
- `X-Organization-ID`: Organization context for multi-tenant operations
- `If-Match`: ETag for optimistic concurrency control

### Response Headers

**Standard Response Headers**

- `Content-Type`: Response MIME type
- `X-Request-ID`: Echo of request identifier
- `X-Rate-Limit-Remaining`: Remaining requests in current window
- `X-Rate-Limit-Reset`: Time when rate limit resets
- `ETag`: Entity tag for caching and concurrency control

### HTTP Status Codes

**Success Responses**

- `200 OK`: Successful GET, PUT, PATCH requests
- `201 Created`: Successful POST request creating new resource
- `202 Accepted`: Request accepted for async processing
- `204 No Content`: Successful DELETE request

**Client Error Responses**

- `400 Bad Request`: Invalid request syntax or parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Authenticated but insufficient permissions
- `404 Not Found`: Requested resource does not exist
- `409 Conflict`: Request conflicts with current resource state
- `422 Unprocessable Entity`: Valid syntax but semantic errors

**Server Error Responses**

- `500 Internal Server Error`: Unexpected server error
- `502 Bad Gateway`: Invalid response from upstream server
- `503 Service Unavailable`: Server temporarily unavailable
- `504 Gateway Timeout`: Timeout waiting for upstream server

## Data Validation Rules

### Common Field Validations

**Email Addresses**

- Must match RFC 5322 email format specification
- Maximum length of 254 characters
- Case-insensitive comparison for uniqueness
- Blocked disposable email domains for business accounts

**Passwords**

- Minimum 12 characters, maximum 128 characters
- Must contain uppercase, lowercase, digit, and special character
- Cannot contain user's email, name, or common dictionary words
- Cannot reuse last 5 passwords for the same account

**Phone Numbers**

- E.164 international format preferred (+1234567890)
- Support for national formats with country context
- Validation against libphonenumber library
- SMS verification required for security-sensitive operations

**Dates and Times**

- ISO 8601 format with timezone information (2025-08-23T10:30:00Z)
- UTC timezone for storage, local timezone for display
- Date ranges validated for logical consistency
- Support for various cultural date formats in user interfaces

### Business Rule Validations

**Unique Constraints**

- Email addresses unique across all user accounts
- Organization slugs unique for URL generation
- Content titles unique within organization or workspace
- API keys unique across all client applications

**Referential Integrity**

- User references validated against active user accounts
- Organization references checked for user membership
- Parent-child relationships maintained for hierarchical data
- Soft-deleted entities excluded from reference validation

## Integration Contracts

### Service-to-Service Communication

**Request Authentication**

- Service-to-service requests use client certificate authentication
- JWT tokens with service-specific claims and scopes
- Request signing with HMAC-SHA256 for high-security operations
- Rate limiting based on service identity and operation type

**Circuit Breaker Configuration**

- Failure threshold: 5 consecutive failures
- Timeout duration: 30 seconds in open state
- Success threshold: 3 consecutive successes to close
- Fallback responses for critical dependency failures

### External API Integration

**Third-Party Service Standards**

- OAuth 2.0 for user-authorized external services
- API key management for service-to-service integrations
- Webhook verification using signature validation
- Retry policies with exponential backoff for transient failures

**Data Exchange Formats**

- JSON as primary format for structured data with JSON Schema validation
- Protocol Buffers (gRPC) for high-performance service-to-service communication
- CloudEvents format for all event-driven communication
- OpenAPI 3.0 specifications for REST API documentation and contract testing
- AsyncAPI specifications for event-driven API documentation

## Versioning Strategy

### API Versioning

**Version Numbering**

- Semantic versioning for internal API tracking (1.2.3)
- Major version in URL path for breaking changes (/v1/, /v2/)
- Minor and patch versions handled transparently
- Deprecation notices 6 months before removal

**Backward Compatibility**

- Additive changes (new fields) are non-breaking
- Field removal or type changes require major version increment
- Default values provided for new required fields
- Migration guides provided for breaking changes

### Event Schema Evolution

**Schema Versioning**

- Event schema version included in event metadata
- Multiple schema versions supported simultaneously
- Automatic schema migration for minor version changes
- Manual intervention required for breaking schema changes

**Consumer Compatibility**

- Event consumers declare supported schema versions
- Event publishers maintain backward compatibility
- Schema registry for centralized schema management
- Version negotiation for optimal compatibility
