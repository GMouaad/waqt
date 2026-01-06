# Integration Patterns

## Service Communication Strategy

### Communication Pattern Selection

**Synchronous Communication (Request-Response)**

- **REST APIs**: Primary pattern for real-time user-facing operations requiring immediate response
- **gRPC**: High-performance communication for internal service-to-service calls requiring low latency
- **GraphQL**: Client-driven data fetching for complex user interfaces with multiple data requirements

**Asynchronous Communication (Event-Driven)**

- **Domain Events**: Broadcast significant business events for loose coupling between services
- **Message Queues**: Reliable message delivery for workflows and background processing
- **Event Streaming**: Real-time data processing and event sourcing for audit trails

### API Design Standards

#### REST API Guidelines

**URL Structure**

- Use noun-based resource URLs: `/api/v1/users/{id}`
- Consistent naming conventions: kebab-case for multi-word resources
- Version in URL path for breaking changes: `/api/v1/`, `/api/v2/`
- Query parameters for filtering, sorting, pagination: `?page=1&size=20&sort=createdAt:desc`

**HTTP Method Usage**

- `GET`: Retrieve data (idempotent, cacheable)
- `POST`: Create new resources or non-idempotent operations
- `PUT`: Replace entire resource (idempotent)
- `PATCH`: Partial resource updates
- `DELETE`: Remove resources (idempotent)

**Response Format Standards**

```json
{
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "type": "user",
    "attributes": {
      "email": "user@example.com",
      "firstName": "John",
      "lastName": "Doe"
    }
  },
  "meta": {
    "timestamp": "2025-08-23T10:30:00Z",
    "requestId": "req_123456789",
    "version": "v1"
  },
  "links": {
    "self": "/api/v1/users/123e4567-e89b-12d3-a456-426614174000"
  }
}
```

**Error Response Standards**

```json
{
  "errors": [
    {
      "id": "error_123456",
      "status": "400",
      "code": "VALIDATION_ERROR",
      "title": "Validation Failed",
      "detail": "The provided email address is not valid",
      "source": {
        "pointer": "/data/attributes/email"
      },
      "meta": {
        "timestamp": "2025-08-23T10:30:00Z",
        "requestId": "req_123456789"
      }
    }
  ]
}
```

#### API Versioning Strategy

**Version in URL Path**

- Major versions in URL: `/api/v1/`, `/api/v2/`
- Semantic versioning for internal tracking: `1.2.3`
- Backward compatibility maintained for at least 12 months
- Deprecation notices provided 6 months before removal

**Header-Based Versioning (Alternative)**

- `Accept: application/vnd.api+json;version=1`
- `API-Version: 2024-08-23` for date-based versioning
- Content negotiation for different response formats

## Event-Driven Architecture

### Domain Event Design

**Event Naming Convention**

- Past tense verbs indicating completed actions: `UserRegistered`, `OrderCompleted`, `PaymentProcessed`
- Domain-specific prefixes: `User.Registered`, `Order.Completed`, `Payment.Processed`
- Include aggregate ID and timestamp in all events

**Event Schema Structure**

```json
{
  "eventId": "evt_123456789",
  "eventType": "UserRegistered",
  "aggregateId": "user_123e4567-e89b-12d3-a456-426614174000",
  "aggregateType": "User",
  "eventVersion": "1.0",
  "occurredAt": "2025-08-23T10:30:00Z",
  "causationId": "cmd_987654321",
  "correlationId": "corr_456789123",
  "data": {
    "userId": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "registrationSource": "web",
    "marketingConsent": true
  },
  "metadata": {
    "publishedBy": "user-service",
    "publishedAt": "2025-08-23T10:30:00Z",
    "schemaVersion": "1.0"
  }
}
```

### Event Publishing Patterns

**Outbox Pattern**

- Store events in database alongside business data within same transaction
- Separate process publishes events from outbox table to message bus
- Ensures at-least-once delivery and transactional consistency
- Prevents dual-write problem in distributed systems

**Event Store Pattern**

- Events as first-class citizens stored in append-only event store
- Business state derived from event replay
- Natural audit trail and temporal queries
- Supports event sourcing and CQRS patterns

### Message Bus Configuration

**Cloud-Native Event Streaming**

- NATS JetStream or Apache Kafka for high-throughput event streaming
- CloudEvents specification for interoperable event format
- Event sourcing support with stream-based persistence
- Kubernetes-native scaling and fault tolerance

**Message Durability and Reliability**

- Messages persisted until successfully processed or expired
- Automatic retry with exponential backoff and jitter
- Circuit breaker pattern for failing subscribers
- Dead letter queues for poison message handling

## Service Discovery and Communication

### Service Registry Pattern

**Dynamic Service Discovery**

- Services register themselves with discovery service on startup
- Health checks ensure only healthy services receive traffic
- Load balancing across multiple service instances
- Automatic deregistration on service shutdown or failure

**Static Configuration (Alternative)**

- Service endpoints configured through Kubernetes ConfigMaps
- DNS-based service discovery within Kubernetes cluster
- Configuration management through cloud-native config systems
- Suitable for stable, well-known service endpoints

### Load Balancing Strategies

**Round Robin**

- Default for services with similar processing capabilities
- Simple implementation with even distribution
- Suitable for stateless services with consistent response times

**Least Connections**

- Route to service instance with fewest active connections
- Better for services with varying processing times
- Requires connection tracking overhead

**Weighted Round Robin**

- Different weights based on service instance capabilities
- Useful for heterogeneous infrastructure
- Dynamic weight adjustment based on performance metrics

## API Gateway Patterns

### Centralized API Gateway

**Cross-Cutting Concerns**

- Authentication and authorization enforcement
- Rate limiting and throttling
- Request/response transformation
- Logging and monitoring
- SSL termination and security headers

**Routing and Load Balancing**

- Path-based routing to appropriate services
- Header-based routing for API versioning
- Circuit breaker pattern for failing services
- Request/response caching for performance

### Backend for Frontend (BFF) Pattern

**Client-Specific APIs**

- Separate API gateways for web, mobile, and external clients
- Tailored response formats and data aggregation
- Client-specific rate limiting and security policies
- Reduced over-fetching and under-fetching of data

## Integration Resilience Patterns

### Circuit Breaker Implementation

**Circuit States**

- **Closed**: Normal operation, requests flow through
- **Open**: Failure threshold exceeded, requests fail fast
- **Half-Open**: Test requests to determine service recovery

**Configuration Parameters**

- Failure threshold: 5 failures in 10 seconds
- Timeout period: 30 seconds in open state
- Success threshold: 3 consecutive successes to close circuit
- Rolling window for failure rate calculation

### Retry Strategies

**Exponential Backoff**

- Initial delay: 100ms
- Backoff multiplier: 2.0
- Maximum delay: 30 seconds
- Maximum retry attempts: 5
- Jitter to prevent thundering herd

**Retry Conditions**

- Transient network failures (timeouts, connection errors)
- HTTP 5xx server errors (not 4xx client errors)
- Specific exception types in client libraries
- Idempotent operations only

### Timeout Management

**Request Timeouts**

- API calls: 30 seconds maximum
- Database queries: 10 seconds for OLTP, 5 minutes for analytics
- External service calls: 15 seconds
- File uploads: 5 minutes for large files

**Cascading Timeout Prevention**

- Each service layer has shorter timeout than calling layer
- Total request timeout never exceeds user-facing SLA
- Timeout values configurable per environment
- Monitoring and alerting on timeout rates

## Data Integration Patterns

### Command Query Responsibility Segregation (CQRS)

**Command Side (Write)**

- Optimized for write operations and business logic
- Normalization for data consistency and integrity
- Immediate consistency within aggregate boundaries
- Domain events published after successful command processing

**Query Side (Read)**

- Optimized for read operations and reporting
- Denormalized views for query performance
- Eventually consistent with command side
- Multiple read models for different use cases

### Event Sourcing

**Event Store Design**

- Immutable event log as source of truth
- Aggregate state derived from event replay
- Snapshot mechanism for performance optimization
- Version conflict resolution for concurrent updates

**Projection Building**

- Real-time projections from event stream
- Batch rebuilding of corrupted projections
- Multiple projection types for different queries
- Schema evolution support for event versioning

### Saga Pattern for Distributed Transactions

**Choreography-Based Saga**

- Services coordinate through event publishing
- No central coordinator, fully distributed
- Each service knows which events to listen for
- Compensation actions for rollback scenarios

**Orchestration-Based Saga**

- Central saga manager coordinates transaction steps
- Clear visibility into transaction state and progress
- Easier error handling and compensation logic
- Single point of failure requires careful design

## Monitoring and Observability

### Distributed Tracing

**Trace Context Propagation**

- Correlation IDs passed through all service calls
- Parent-child relationships for request flow
- Trace sampling for performance and cost optimization
- Integration with Application Insights and Jaeger

### Health Check Endpoints

**Service Health Indicators**

- `/health/live`: Basic liveness check (service responding)
- `/health/ready`: Readiness check (service can handle requests)
- `/health/detailed`: Comprehensive health including dependencies
- Dependency health checks with circuit breaker protection

### Service Metrics

**Key Performance Indicators**

- Request rate, response time, error rate (RED metrics)
- CPU, memory, disk usage (USE metrics)
- Business metrics specific to service domain
- Custom metrics for monitoring business KPIs

**Alerting Thresholds**

- Response time >95th percentile SLA threshold
- Error rate >2% of total requests
- Dependency health check failures
- Resource utilization >80% sustained for 5 minutes

