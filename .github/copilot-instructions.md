# Copilot Instructions for System Requirements Example

## Project Overview
This repository contains a comprehensive requirements documentation structure for a multi-service .NET platform following Self-Contained Systems (SCS) architecture patterns. The documentation demonstrates professional requirements management for distributed systems with emphasis on Domain-Driven Design, event-driven architecture, and cloud-native patterns.

## Repository Purpose and Context

### Primary Goals
- **Requirements Documentation Excellence**: Serve as a template and example for professional system requirements documentation
- **Architecture Guidance**: Demonstrate best practices for .NET microservices and Self-Contained Systems
- **Stakeholder Communication**: Provide clear documentation structure for different audience types (Product Managers, Architects, Developers, Operations)
- **Compliance and Governance**: Include comprehensive security, accessibility, and regulatory considerations

### Architecture Philosophy
- **Self-Contained Systems (SCS)**: Each service owns its data, UI, and business logic
- **Domain-Driven Design (DDD)**: Services aligned with business domains and bounded contexts
- **Event-Driven Architecture**: Loose coupling through domain events and asynchronous communication
- **API-First Design**: Well-defined contracts and OpenAPI specifications
- **Cloud-Native**: Cloud-focused with scalability, resilience, and observability built-in

## Documentation Structure and Standards

### File Organization Pattern
```
docs/
├── requirements/           # Core requirements documentation
│   ├── 01-system-overview.md          # High-level system description
│   ├── 02-system-capabilities.md      # Platform capabilities and roadmap
│   ├── 03-global-nfr.md              # System-wide non-functional requirements
│   ├── 04-integration-patterns.md     # Service communication patterns
│   ├── 05-security-architecture.md    # Security across all services
│   ├── user-experience/               # UX principles, journeys, accessibility
│   ├── services/                      # Service-specific requirements
│   └── cross-cutting/                 # Shared concerns (monitoring, testing, etc.)
├── decisions/             # Architecture Decision Records (ADRs)
└── operations/           # Deployment, SLAs, disaster recovery
```

### Documentation Standards
- **Consistent Structure**: Each service follows the same template pattern
- **Traceability**: Link requirements to business objectives and user needs
- **Completeness**: Cover functional, non-functional, security, and operational aspects
- **Version Control**: Track changes and decisions through ADRs
- **Multi-Audience**: Tailor content for different stakeholder types

## Technology Stack and Patterns

### Core Technologies
- **.NET 8+**: Primary development framework with ASP.NET Core
- **Cloud Platform**: Any major cloud provider (AWS, Azure, GCP) for infrastructure and services
- **Relational Database**: SQL Server, PostgreSQL, or MySQL for transactional data with read replicas
- **Document Database**: MongoDB, Amazon DocumentDB, Azure Cosmos DB, or Google Firestore for flexible schema requirements
- **Message Broker**: Apache Kafka, RabbitMQ, Amazon SQS/SNS, Azure Service Bus, or Google Pub/Sub for reliable messaging
- **Observability**: OpenTelemetry with Prometheus, Grafana, Jaeger, or cloud-native monitoring solutions

### Architectural Patterns
- **CQRS**: Command Query Responsibility Segregation for read/write optimization
- **Event Sourcing**: For audit trails and temporal data analysis
- **Saga Pattern**: For distributed transaction management
- **Circuit Breaker**: For resilience in service-to-service communication
- **API Gateway**: YARP, Kong, Istio, AWS API Gateway, Azure API Management, or Google Cloud Endpoints for service orchestration

### Integration Patterns
- **REST APIs**: Primary synchronous communication with OpenAPI 3.0 specs
- **gRPC**: High-performance internal service communication
- **Domain Events**: Asynchronous communication for business events
- **Webhook Support**: External system integration capabilities

## Key Principles for Contributors

### Requirements Documentation
1. **User-Centric Approach**: Always start with user needs and business outcomes
2. **Progressive Detail**: Move from high-level overview to specific implementation details
3. **Cross-References**: Maintain links between related requirements and decisions
4. **Measurable Criteria**: Include specific, testable acceptance criteria
5. **Non-Functional Coverage**: Address performance, security, usability, and operational concerns

### Service Design Guidelines
1. **Domain Boundaries**: Align services with business domains and bounded contexts
2. **Data Ownership**: Each service owns its data and doesn't share databases
3. **API Contracts**: Define clear, versioned APIs with comprehensive documentation
4. **Event Design**: Use past-tense verbs for domain events (UserRegistered, OrderCompleted)
5. **Error Handling**: Implement consistent error patterns and circuit breakers

### Security and Compliance
1. **Security by Design**: Integrate security considerations from the start
2. **Zero Trust**: Never trust, always verify approach
3. **Data Protection**: GDPR, CCPA compliance with privacy by design
4. **Audit Trails**: Comprehensive logging for compliance and debugging
5. **Access Control**: Role-based and attribute-based access control patterns

## Content Guidelines and Best Practices

### Writing Style
- **Clear and Concise**: Use plain language appropriate for technical and business audiences
- **Consistent Terminology**: Maintain a glossary of domain-specific terms
- **Active Voice**: Prefer active voice for clarity and directness
- **Structured Format**: Use headers, lists, and tables for scannable content
- **Example-Driven**: Include concrete examples, code samples, and diagrams

### Technical Documentation
- **API Documentation**: OpenAPI 3.0 specifications with examples
- **Data Models**: JSON schemas with validation rules and examples
- **Integration Patterns**: Sequence diagrams and interaction patterns
- **Error Scenarios**: Comprehensive error handling and recovery procedures
- **Performance Metrics**: Specific, measurable performance requirements

### User Experience Documentation
- **User Journeys**: End-to-end workflows with pain points and success metrics
- **Accessibility**: WCAG 2.1 AA compliance with inclusive design principles
- **Responsive Design**: Multi-device support with specific breakpoints
- **Internationalization**: Multi-language and cultural adaptation considerations

## When Contributing to This Repository

### Adding New Services
1. **Follow Template Structure**: Use existing service documentation as template
2. **Define Domain Boundaries**: Clearly articulate service responsibilities
3. **API Contracts**: Provide comprehensive API documentation
4. **Integration Points**: Document how the service integrates with others
5. **Non-Functional Requirements**: Address service-specific performance, security, and operational needs

### Updating Requirements
1. **Impact Analysis**: Consider effects on dependent services and systems
2. **Stakeholder Review**: Ensure changes align with business objectives
3. **Version Control**: Document changes and rationale
4. **Cross-Reference Updates**: Update related documentation and contracts
5. **Testing Implications**: Consider testing strategy changes

### Architecture Decisions
1. **ADR Format**: Use Architecture Decision Records for significant choices
2. **Context and Rationale**: Clearly explain the decision context and reasoning
3. **Alternatives Considered**: Document options that were considered but rejected
4. **Consequences**: Articulate both positive and negative consequences
5. **Review Process**: Ensure appropriate stakeholder review and approval

## Special Considerations

### Business Context
- **Enterprise Environment**: Consider existing systems and corporate constraints
- **Regulatory Requirements**: Address compliance needs early and comprehensively
- **Stakeholder Alignment**: Balance technical excellence with business practicality
- **Phased Delivery**: Support incremental delivery and feedback incorporation

### Technical Excellence
- **Code Quality**: Emphasize testability, maintainability, and observability
- **Performance**: Address scalability and performance from the design phase
- **Resilience**: Build in fault tolerance and graceful degradation
- **Monitoring**: Comprehensive observability and alerting strategies

### Operational Readiness
- **Deployment Strategy**: Consider blue-green deployments and canary releases
- **Monitoring and Alerting**: Define comprehensive health checks and metrics
- **Disaster Recovery**: Document backup, recovery, and business continuity procedures
- **Capacity Planning**: Address scaling requirements and resource management

## Helpful Patterns and Examples

### When asked about specific services:
- Reference the appropriate service documentation in `docs/requirements/services/`
- Consider integration patterns from `04-integration-patterns.md`
- Check security requirements in `05-security-architecture.md`
- Review shared contracts in `services/shared-contracts/`

### When discussing architecture:
- Reference the system overview in `01-system-overview.md`
- Consider the capability roadmap in `02-system-capabilities.md`
- Review global non-functional requirements in `03-global-nfr.md`
- Check existing ADRs in `docs/decisions/`

### When addressing user experience:
- Review UX principles in `user-experience/ux-principles.md`
- Consider user journeys in `user-experience/user-journeys.md`
- Check accessibility requirements and standards
- Reference responsive design patterns and mobile considerations

This repository serves as both a template and a comprehensive example of professional requirements documentation for modern .NET microservices platforms. Contributors should maintain the high standard of documentation quality and architectural thinking demonstrated throughout the existing content.