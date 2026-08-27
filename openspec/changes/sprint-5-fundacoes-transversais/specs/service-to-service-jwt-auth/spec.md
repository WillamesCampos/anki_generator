## ADDED Requirements

### Requirement: Django signs a service JWT before calling the document-generator microservice
The system SHALL attach a self-signed JWT (HS256), minted locally without a network round-trip, to every outgoing request from Django to the `document-generator` microservice. The token SHALL include an issuer claim identifying the calling application, an audience claim identifying the target service, and a short expiration (30-60 seconds).

#### Scenario: Django calls document-generator
- **WHEN** Django makes a request to `document-generator`
- **THEN** the request carries an `Authorization: Bearer <jwt>` header with a freshly minted, short-lived token identifying `django-core` as the issuer

### Requirement: document-generator rejects requests without a valid service JWT
The system SHALL verify the service JWT's signature, issuer, audience, and expiration locally in the `document-generator` microservice, without calling back to Django or any other service to validate the token. Requests with a missing, invalid, expired, or unknown-issuer token SHALL be rejected with 401.

#### Scenario: Valid service JWT is accepted
- **WHEN** `document-generator` receives a request with a service JWT signed with a key it recognizes, not expired, with the expected audience
- **THEN** the request is processed normally

#### Scenario: Missing or invalid service JWT is rejected
- **WHEN** `document-generator` receives a request with no `Authorization` header, an expired token, or a token signed with an unrecognized key
- **THEN** the system responds 401 and does not process the request

### Requirement: Service signing keys are scoped per issuer-verifier pair and separate from user auth
The system SHALL use a distinct signing secret for each issuer-verifier service pair (not a single secret shared across all services), and this secret SHALL be separate from the secret(s) used to sign end-user JWTs (`SIMPLE_JWT`/`DJANGO_SECRET_KEY`).

#### Scenario: Service secret is independent of user auth secret
- **WHEN** the service-to-service signing key is rotated or compromised
- **THEN** end-user session tokens remain valid and unaffected, because they are signed with a different key

### Requirement: Service signing keys support versioned rotation without downtime
The system SHALL support rotating the service signing key by versioning it with a key identifier (`kid`) carried in the JWT header. The verifier SHALL accept any key present in its locally configured key map, not only the most recently added one, so that tokens signed during a rotation window with either the old or the new key are both accepted.

#### Scenario: Rotation window accepts both old and new keys
- **WHEN** a new signing key has been added to both services' configuration but the old key has not yet been removed
- **THEN** tokens signed with either the old or the new key are accepted by the verifier

#### Scenario: Removed key is no longer accepted
- **WHEN** an old signing key has been removed from the verifier's configured key map
- **THEN** tokens signed with that key are rejected, even if otherwise well-formed and unexpired
