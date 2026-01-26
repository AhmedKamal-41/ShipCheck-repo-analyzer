# Architecture

High-level architecture will be documented here.

```mermaid
flowchart LR
  frontend[Frontend\nNext.js]
  backend[Backend\nFastAPI]
  postgres[(Postgres)]
  frontend --> backend
  backend --> postgres
```
