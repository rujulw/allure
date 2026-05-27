# allure

allure is a curated discovery platform for collecting, organizing, and sharing recommendations for places, products, and experiences.

The MVP focuses on fast list creation, high-signal recommendation detail, and lightweight collaboration so individuals and small teams can publish trusted collections without managing a complex content system.

## Vision

allure emphasizes:

- trusted recommendations over noisy social feeds
- fast publishing for curated lists and collections
- structured metadata that supports search and reuse
- a clean separation between product planning and implementation slices

## Current Implementation Status

Implemented:

- repository bootstrap and planning baseline
- product direction, architecture, and roadmap docs

Not implemented yet:

- backend API, persistence layer, and auth flows
- frontend application, collection management, and sharing UX

## Documentation

- [Architecture](docs/architecture.md): system boundaries and runtime flow
- [Roadmap](docs/roadmap.md): phased delivery plan for the MVP
- [Design Log](docs/design.md): accepted technical and product decisions
- [Bug Log](docs/bug-log.md): issue tracking and verification history

## Tech Stack

### Server

- Python 3.12
- FastAPI
- PostgreSQL
- SQLAlchemy 2, Alembic, Pydantic

### Client

- React 19
- TypeScript
- Vite
- React Router, TanStack Query, Tailwind CSS

## MVP Scope

- email-based account creation and sign-in
- create, edit, and publish recommendation collections
- attach notes, tags, links, and cover images to collection items
- browse public collections and save favorites
- simple collaborator roles for shared collection editing

## Non-Goals

- marketplace transactions or checkout
- algorithmic feed ranking
- native mobile clients in the first release
- advanced creator monetization

## Project Structure

```text
allure/
├── server/
├── client/
├── docs/
│   ├── architecture.md
│   ├── roadmap.md
│   ├── design.md
│   └── bug-log.md
└── README.md
```

## Quick Start Plan

### 1. Server foundation

```bash
mkdir -p server/app server/tests
```

### 2. Client foundation

```bash
mkdir -p client/src client/public
```

## Environment Variables

### Server (`server/.env`)

```env
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_TTL_MINUTES=
```

### Client (`client/.env`)

```env
VITE_API_BASE_URL=
```

## Quality Gates

```bash
pytest
npm run lint
npm run test
npm run build
```

## Known Gaps

- auth, permissions, and audit requirements still need concrete schema design
- list ranking and search quality will depend on later analytics decisions

## Development Workflow

1. capture design decisions before implementation
2. branch from `development` for feature slices
3. keep tests and docs in the same change set
4. land backend and frontend work in reviewable vertical slices
