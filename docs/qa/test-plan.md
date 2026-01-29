# Test Plan - HireLens

## Scope

This test plan covers comprehensive testing of the HireLens application, including:

- **Backend API**: FastAPI endpoints, business logic, database operations
- **Frontend UI**: Next.js application, user interactions, error handling
- **API Contracts**: Response schema validation, type safety
- **Performance**: Load testing, response time validation

## Out of Scope

- Manual exploratory testing (covered by manual test cases)
- Production monitoring and alerting
- Security penetration testing (basic security checks included)
- Cross-browser compatibility (Chrome/Chromium only)

## Test Types

### 1. Unit Tests
- **Location**: `backend/tests/unit/`
- **Coverage**: Individual functions, classes, utilities
- **Speed**: Fast (<1s per test)
- **Examples**: URL parsing, scoring logic, detection algorithms

### 2. Integration Tests
- **Location**: `backend/tests/integration/`
- **Coverage**: API endpoints, database operations, error handling
- **Speed**: Medium (1-5s per test)
- **Examples**: Full analyze flow, report retrieval, error responses

### 3. E2E Tests
- **Location**: `frontend/tests/e2e/`
- **Coverage**: User workflows, UI interactions, error states
- **Speed**: Slow (5-30s per test)
- **Examples**: Analyze flow, report page interactions, visual regression

### 4. Contract Tests
- **Location**: `tests/contract/`
- **Coverage**: API response schemas, type validation
- **Speed**: Fast (<1s per test)
- **Examples**: Response structure validation, enum values

### 5. Performance Tests
- **Location**: `tests/performance/`
- **Coverage**: Response times, throughput, error rates
- **Speed**: Variable (30s-5min)
- **Examples**: Health endpoint load, report retrieval performance

## Environments

### Local Development
- **Backend**: SQLite (unit tests) or PostgreSQL (integration tests)
- **Frontend**: Next.js dev server (localhost:3000)
- **Database**: Docker Compose PostgreSQL or SQLite

### CI/CD
- **Backend**: PostgreSQL 16 container
- **Frontend**: Next.js build + Playwright headless
- **Database**: GitHub Actions PostgreSQL service

## Entry Criteria

- Code changes committed to repository
- Pull request opened
- All dependencies installed
- Database migrations run

## Exit Criteria

- All automated tests pass
- Backend code coverage ≥ 80%
- No critical or high-severity bugs
- Performance thresholds met (<500ms health, <1s reports)
- CI pipeline green

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Flaky tests | High | Retry logic, deterministic fixtures, proper waits |
| GitHub API rate limits | Medium | Mock all GitHub API calls in tests |
| Test database state | Medium | Use transactions, cleanup after tests |
| Slow E2E tests | Low | Run in parallel, use mocks, optimize selectors |
| Coverage gaps | Medium | Enforce 80% threshold, review coverage reports |

## Definition of Done

A feature/change is considered "done" when:

1. ✅ All relevant tests written and passing
2. ✅ Code coverage maintained (≥80% backend)
3. ✅ No new linting errors
4. ✅ CI pipeline passes all jobs
5. ✅ Documentation updated (if needed)
6. ✅ Manual test cases executed (for critical paths)
7. ✅ Performance impact assessed (if applicable)

## Test Execution

### Local
```bash
# Backend tests
make test-backend
# or
cd backend && pytest tests -v

# Frontend E2E tests
make test-frontend
# or
cd frontend && npm run test:e2e

# All tests
make test-all
```

### CI
- Runs automatically on push/PR to main/master
- All jobs run in parallel
- Artifacts uploaded (coverage, Playwright reports)

## Maintenance

- Review and update tests when API changes
- Add tests for new features before implementation
- Remove obsolete tests
- Update fixtures when data models change
- Review coverage reports monthly
