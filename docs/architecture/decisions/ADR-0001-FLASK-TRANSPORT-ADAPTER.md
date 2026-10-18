# ADR-0001: Flask Transport Adapter Around a Shared Application Service

**Status:** Accepted for the Pre-Alpha local integration profile

**Date:** 2026-10-17

## Context

The application must be callable from Python, a CLI and a backend framework.
The existing pipeline is synchronous and CPU-bound. Introducing framework logic
inside detection code would couple domain behavior to transport and make CLI/API
parity difficult.

## Decision

Create `ptcg.service` as the shared application boundary and use a thin Flask
application factory as the optional HTTP adapter. Keep the CLI as the primary
operator interface. Use Gunicorn for containerized WSGI execution. Bind the
provided Compose profile to loopback and do not represent it as a public
production service.

## Consequences

- Python, CLI and HTTP reuse the same orchestration path.
- Flask/Gunicorn are optional dependencies.
- The adapter is easy to test and replace.
- Synchronous HTTP work holds a worker for the duration; production realization
  therefore requires the planned durable job/worker contract.
- FastAPI/ASGI may be added later only if a measured requirement justifies it;
  it must remain an adapter to the same application service.

## Rejected alternatives

- Framework logic in `pipeline.py`: violates dependency direction.
- Immediate microservices: no measured scale or governance boundary justifies
  operational distribution.
- FastAPI solely for novelty: generated schemas and async I/O do not improve the
  current CPU-bound synchronous pipeline enough to offset another framework
  decision.
