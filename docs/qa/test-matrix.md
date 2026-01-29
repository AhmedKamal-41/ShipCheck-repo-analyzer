# Test Matrix - HireLens

## Feature Coverage by Test Type

| Feature | Unit | Integration | E2E | Contract | Performance |
|---------|------|-------------|-----|----------|-------------|
| **API Endpoints** |
| POST /api/analyze | ✅ | ✅ | ✅ | ✅ | ⚠️ |
| GET /api/reports/{id} | ✅ | ✅ | ✅ | ✅ | ✅ |
| GET /api/reports (list) | ✅ | ✅ | ❌ | ✅ | ❌ |
| GET /health | ✅ | ✅ | ❌ | ✅ | ✅ |
| GET /db-check | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Business Logic** |
| GitHub URL parsing | ✅ | ✅ | ✅ | ❌ | ❌ |
| Repository analysis | ✅ | ✅ | ✅ | ❌ | ❌ |
| Score calculation | ✅ | ✅ | ✅ | ❌ | ❌ |
| Detection logic (README, CI, Docker) | ✅ | ✅ | ❌ | ❌ | ❌ |
| Rate limiting | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Frontend** |
| Home page load | ❌ | ❌ | ✅ | ❌ | ❌ |
| Analyze flow | ❌ | ❌ | ✅ | ❌ | ❌ |
| Report page display | ❌ | ❌ | ✅ | ❌ | ❌ |
| Filters (All/Fail/Warn/Pass) | ❌ | ❌ | ✅ | ❌ | ❌ |
| Search functionality | ❌ | ❌ | ✅ | ❌ | ❌ |
| Error states | ❌ | ✅ | ✅ | ❌ | ❌ |
| Visual regression | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Database** |
| Report CRUD | ❌ | ✅ | ❌ | ❌ | ❌ |
| Timestamps | ❌ | ✅ | ❌ | ❌ | ❌ |
| JSONB storage | ❌ | ✅ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ Fully covered
- ⚠️ Partially covered
- ❌ Not covered (out of scope or not applicable)

## Test Count Summary

| Test Type | Count | Location |
|-----------|-------|----------|
| Unit Tests | ~25 | `backend/tests/unit/` |
| Integration Tests | ~15 | `backend/tests/integration/` |
| E2E Tests | ~15 | `frontend/tests/e2e/` |
| Contract Tests | ~8 | `tests/contract/` |
| Performance Tests | 2 | `tests/performance/` |
| **Total** | **~65** | |

## Coverage Goals

- **Backend**: ≥80% code coverage (enforced in CI)
- **Frontend**: Critical user flows covered by E2E
- **API**: All endpoints have contract tests
- **Performance**: Health and report endpoints tested

## Gaps and Future Work

1. **E2E Coverage**: Add tests for report list page
2. **Performance**: Add tests for analyze endpoint (requires async job)
3. **Visual Regression**: Expand to mobile viewports
4. **Accessibility**: Add a11y tests
5. **Security**: Add security-focused tests
