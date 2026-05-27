# Architecture

## Overview

allure is planned as a split-stack web application with a React client, a FastAPI server, and a PostgreSQL data store. The MVP prioritizes reliable CRUD workflows for recommendation collections, clear ownership rules, and clean API contracts so frontend and backend work can move in parallel.

## Boundaries

- Client: handles authentication screens, collection editing flows, public browsing, and optimistic UI interactions for saved items
- Server: owns authentication, authorization, collection lifecycle rules, persistence, search endpoints, and audit-friendly business validation
- Shared contracts: REST JSON endpoints, typed request and response schemas, and a stable error envelope for client-side handling

## Runtime Flow

1. A signed-in user creates or edits a collection from the client.
2. The client sends validated payloads to the FastAPI server.
3. The server applies ownership and collaboration rules, persists data in PostgreSQL, and returns normalized collection views for rendering.

## Security + Ownership

- Auth model: email/password authentication with short-lived access tokens and rotated refresh tokens
- Access rules: collections are private by default, can be published explicitly, and support owner plus collaborator permissions in the MVP

## Operational Notes

- local run: `server` and `client` will be started independently during development
- health endpoint: `/health`
