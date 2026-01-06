# API Contracts

## Overview

This document defines the API contracts for [Service Name], including REST endpoints, gRPC services, and event schemas.

## REST API Specification

### API Information

- **API Version**: v1
- **Base URL**: `/api/v1/[service-endpoint]`
- **Authentication**: Bearer Token (JWT)
- **Content Type**: `application/json`

### Common Response Formats

#### Success Response Format

```json
{
  "success": true,
  "data": {
    // Response data object or array
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid",
    "version": "v1"
  }
}
```

#### Error Response Format (RFC 7807)

```json
{
  "type": "https://api.platform.com/errors/[error-type]",
  "title": "Error Title",
  "status": 400,
  "detail": "Detailed error description",
  "instance": "/api/v1/[service-endpoint]/[resource-id]",
  "timestamp": "2024-01-01T00:00:00Z",
  "requestId": "uuid",
  "errors": [
    {
      "code": "VALIDATION_ERROR",
      "field": "fieldName",
      "message": "Field validation failed"
    }
  ]
}
```

### Resource Endpoints

#### Resource: [Resource Name]

##### Get All Resources

```http
GET /api/v1/[resource]
```

**Description**: Retrieve a list of [resource] items

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| limit | integer | No | Items per page (default: 20, max: 100) |
| sort | string | No | Sort field (default: id) |
| order | string | No | Sort order: asc or desc (default: asc) |
| filter | string | No | Filter criteria |

**Response**: `200 OK`

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "field1": "value1",
      "field2": "value2",
      "createdAt": "2024-01-01T00:00:00Z",
      "updatedAt": "2024-01-01T00:00:00Z"
    }
  ],
  "metadata": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "totalPages": 5,
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid"
  }
}
```

**Error Responses**:

- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `500 Internal Server Error` - Server error

##### Get Resource by ID

```http
GET /api/v1/[resource]/{id}
```

**Description**: Retrieve a specific [resource] by ID

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource identifier (UUID) |

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid"
  }
}
```

**Error Responses**:

- `400 Bad Request` - Invalid ID format
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

##### Create Resource

```http
POST /api/v1/[resource]
```

**Description**: Create a new [resource]

**Request Body**:

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Response**: `201 Created`

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid"
  }
}
```

**Error Responses**:

- `400 Bad Request` - Invalid request body or validation errors
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `409 Conflict` - Resource already exists
- `500 Internal Server Error` - Server error

##### Update Resource

```http
PUT /api/v1/[resource]/{id}
```

**Description**: Update an existing [resource]

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource identifier (UUID) |

**Request Body**:

```json
{
  "field1": "updated_value1",
  "field2": "updated_value2"
}
```

**Response**: `200 OK`

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "field1": "updated_value1",
    "field2": "updated_value2",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "requestId": "uuid"
  }
}
```

**Error Responses**:

- `400 Bad Request` - Invalid request body or validation errors
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Conflict with current resource state
- `500 Internal Server Error` - Server error

##### Delete Resource

```http
DELETE /api/v1/[resource]/{id}
```

**Description**: Delete a [resource]

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string | Yes | Resource identifier (UUID) |

**Response**: `204 No Content`

**Error Responses**:

- `400 Bad Request` - Invalid ID format
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Cannot delete due to dependencies
- `500 Internal Server Error` - Server error

### Health and Status Endpoints

#### Health Check

```http
GET /health
```

**Description**: Service health check

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "version": "1.0.0",
  "uptime": "5d 12h 30m",
  "dependencies": {
    "database": "healthy",
    "cache": "healthy",
    "messageQueue": "healthy"
  }
}
```

#### Readiness Check

```http
GET /ready
```

**Description**: Service readiness check

**Response**: `200 OK` or `503 Service Unavailable`

```json
{
  "ready": true,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## gRPC Service Specification

### Service Definition

```protobuf
syntax = "proto3";

package [service_package];

import "google/protobuf/timestamp.proto";
import "google/protobuf/empty.proto";

service [ServiceName]Service {
  rpc Get[Resource](Get[Resource]Request) returns (Get[Resource]Response);
  rpc List[Resource](List[Resource]Request) returns (List[Resource]Response);
  rpc Create[Resource](Create[Resource]Request) returns (Create[Resource]Response);
  rpc Update[Resource](Update[Resource]Request) returns (Update[Resource]Response);
  rpc Delete[Resource](Delete[Resource]Request) returns (google.protobuf.Empty);
}

message [Resource] {
  string id = 1;
  string field1 = 2;
  string field2 = 3;
  google.protobuf.Timestamp created_at = 4;
  google.protobuf.Timestamp updated_at = 5;
}

message Get[Resource]Request {
  string id = 1;
}

message Get[Resource]Response {
  [Resource] resource = 1;
}

message List[Resource]Request {
  int32 page = 1;
  int32 limit = 2;
  string sort = 3;
  string order = 4;
  string filter = 5;
}

message List[Resource]Response {
  repeated [Resource] resources = 1;
  int32 total = 2;
  int32 page = 3;
  int32 limit = 4;
  int32 total_pages = 5;
}

message Create[Resource]Request {
  string field1 = 1;
  string field2 = 2;
}

message Create[Resource]Response {
  [Resource] resource = 1;
}

message Update[Resource]Request {
  string id = 1;
  string field1 = 2;
  string field2 = 3;
}

message Update[Resource]Response {
  [Resource] resource = 1;
}

message Delete[Resource]Request {
  string id = 1;
}
```

## Event Schemas

### CloudEvents Format

All events follow the CloudEvents v1.0 specification:

```json
{
  "specversion": "1.0",
  "type": "com.platform.[service].[resource].[action].v1",
  "source": "https://platform.com/services/[service]",
  "id": "uuid",
  "time": "2024-01-01T00:00:00Z",
  "datacontenttype": "application/json",
  "subject": "[resource-id]",
  "data": {
    // Event-specific data
  }
}
```

### Event Types

#### [Resource] Created Event

**Event Type**: `com.platform.[service].[resource].created.v1`

**Data Schema**:

```json
{
  "resourceId": "uuid",
  "resource": {
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    "createdAt": "2024-01-01T00:00:00Z"
  },
  "metadata": {
    "userId": "uuid",
    "correlationId": "uuid"
  }
}
```

#### [Resource] Updated Event

**Event Type**: `com.platform.[service].[resource].updated.v1`

**Data Schema**:

```json
{
  "resourceId": "uuid",
  "previousState": {
    "field1": "old_value1",
    "field2": "old_value2"
  },
  "currentState": {
    "field1": "new_value1",
    "field2": "new_value2"
  },
  "updatedAt": "2024-01-01T00:00:00Z",
  "metadata": {
    "userId": "uuid",
    "correlationId": "uuid"
  }
}
```

#### [Resource] Deleted Event

**Event Type**: `com.platform.[service].[resource].deleted.v1`

**Data Schema**:

```json
{
  "resourceId": "uuid",
  "deletedAt": "2024-01-01T00:00:00Z",
  "metadata": {
    "userId": "uuid",
    "correlationId": "uuid"
  }
}
```

### Events Consumed

#### External Event: [Event Name]

**Event Type**: `com.platform.[other-service].[event].v1`

**Expected Data Schema**:

```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Processing Logic**: [Description of how this event is processed]

## Data Transfer Objects (DTOs)

### Request DTOs

#### Create[Resource]Request

```typescript
interface Create[Resource]Request {
  field1: string;
  field2: string;
  // Additional fields
}
```

#### Update[Resource]Request

```typescript
interface Update[Resource]Request {
  field1?: string;
  field2?: string;
  // Additional fields
}
```

### Response DTOs

#### [Resource]Response

```typescript
interface [Resource]Response {
  id: string;
  field1: string;
  field2: string;
  createdAt: string;
  updatedAt: string;
}
```

#### PaginatedResponse

```typescript
interface PaginatedResponse<T> {
  data: T[];
  metadata: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    timestamp: string;
    requestId: string;
  };
}
```

## Authentication & Authorization

### Authentication Requirements

- **Authentication Method**: Bearer Token (JWT)
- **Token Location**: Authorization header
- **Token Format**: `Authorization: Bearer <jwt_token>`

### Authorization Scopes

| Endpoint | Required Scope | Description |
|----------|---------------|-------------|
| GET /[resource] | `[resource]:read` | Read access to resources |
| POST /[resource] | `[resource]:write` | Create new resources |
| PUT /[resource]/{id} | `[resource]:write` | Update existing resources |
| DELETE /[resource]/{id} | `[resource]:delete` | Delete resources |

## Rate Limiting

### Rate Limit Configuration

| Endpoint Pattern | Rate Limit | Window |
|-----------------|------------|---------|
| GET /[resource] | 1000 requests | per hour |
| POST /[resource] | 100 requests | per hour |
| PUT /[resource]/* | 100 requests | per hour |
| DELETE /[resource]/* | 50 requests | per hour |

### Rate Limit Headers

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1641024000
X-RateLimit-Window: 3600
```

## OpenAPI Specification

### OpenAPI Document Location

The complete OpenAPI 3.0 specification is available at:

- **Development**: `https://dev-api.platform.com/[service]/swagger.json`
- **Staging**: `https://staging-api.platform.com/[service]/swagger.json`
- **Production**: `https://api.platform.com/[service]/swagger.json`

### Interactive Documentation

Swagger UI is available at:

- **Development**: `https://dev-api.platform.com/[service]/swagger`
- **Staging**: `https://staging-api.platform.com/[service]/swagger`
- **Production**: `https://api.platform.com/[service]/swagger`

## API Versioning

### Versioning Strategy

- **URL Versioning**: `/api/v1/`, `/api/v2/`
- **Backward Compatibility**: Minimum 12 months for deprecated versions
- **Version Sunset**: 6-month notice period for version retirement

### Version Support Matrix

| Version | Status | Support End Date | Notes |
|---------|--------|------------------|-------|
| v1 | Current | - | Active development |
| v0 | Deprecated | 2024-12-31 | Legacy support only |

## Error Handling

### Error Code Categories

| Code Range | Category | Description |
|------------|----------|-------------|
| 1000-1999 | Validation Errors | Input validation failures |
| 2000-2999 | Business Logic Errors | Domain-specific errors |
| 3000-3999 | External Service Errors | Third-party service failures |
| 4000-4999 | System Errors | Infrastructure and system errors |

### Common Error Codes

| Code | Title | Description |
|------|-------|-------------|
| 1001 | VALIDATION_ERROR | Request validation failed |
| 1002 | REQUIRED_FIELD_MISSING | Required field not provided |
| 2001 | BUSINESS_RULE_VIOLATION | Business rule constraint violated |
| 2002 | DUPLICATE_RESOURCE | Resource already exists |
| 3001 | EXTERNAL_SERVICE_UNAVAILABLE | External service not available |
| 4001 | DATABASE_CONNECTION_ERROR | Database connection failed |

## Related Documentation

- [Service Overview](./service-overview.md)
- [Functional Requirements](./functional-requirements.md)
- [Data Model](./data-model.md)
- [Dependencies](./dependencies.md)
