# Release Checklist - HireLens

Use this checklist before deploying to production.

## Pre-Release

### Code Quality
- [ ] All tests pass locally (`make test-all`)
- [ ] CI pipeline is green (all jobs passing)
- [ ] Code coverage ≥80% (backend)
- [ ] No linting errors (`npm run lint`, `pytest --flake8` if configured)
- [ ] No TypeScript errors
- [ ] No console errors in browser

### Code Review
- [ ] All PRs reviewed and approved
- [ ] All review comments addressed
- [ ] No merge conflicts
- [ ] Branch is up to date with main/master

### Documentation
- [ ] README updated (if needed)
- [ ] API documentation updated (if API changed)
- [ ] Changelog updated
- [ ] Migration guide (if database changes)

### Version Management
- [ ] Version bumped (semantic versioning)
- [ ] Version tags created
- [ ] Release notes prepared

### Database
- [ ] Migrations tested locally
- [ ] Migration rollback tested
- [ ] Backup strategy confirmed
- [ ] Migration script ready (if needed)

### Environment Variables
- [ ] `.env.example` updated (if new vars added)
- [ ] Production environment variables configured
- [ ] Secrets stored securely (not in code)

## Release

### Staging Deployment
- [ ] Deploy to staging environment
- [ ] Verify staging deployment successful
- [ ] Run smoke tests on staging
- [ ] Verify database migrations (if any)
- [ ] Check logs for errors

### Staging Verification
- [ ] Home page loads correctly
- [ ] Analyze flow works end-to-end
- [ ] Report page displays correctly
- [ ] Filters and search work
- [ ] Error handling works
- [ ] No console errors
- [ ] Performance acceptable

### Production Deployment
- [ ] Create release tag
- [ ] Deploy to production
- [ ] Verify deployment successful
- [ ] Run database migrations (if any)
- [ ] Monitor deployment logs

### Production Verification
- [ ] Health endpoint responds (`/health`)
- [ ] Database connectivity verified (`/db-check`)
- [ ] Home page loads
- [ ] Analyze flow works (test with real repo)
- [ ] Report retrieval works
- [ ] No critical errors in logs

## Post-Release

### Monitoring
- [ ] Monitor application logs (first 30 minutes)
- [ ] Check error rates (should be <1%)
- [ ] Verify response times (health <500ms, reports <1s)
- [ ] Monitor database performance
- [ ] Check GitHub API rate limit usage

### Rollback Plan
- [ ] Rollback procedure documented
- [ ] Rollback tested (if possible)
- [ ] Team knows how to rollback

### Communication
- [ ] Release announcement sent (if applicable)
- [ ] Team notified of deployment
- [ ] Known issues documented (if any)

### Follow-Up
- [ ] Monitor for 24-48 hours
- [ ] Collect user feedback
- [ ] Address any critical issues
- [ ] Update documentation based on feedback

## Emergency Rollback

If critical issues are found:

1. **Stop**: Identify the issue and impact
2. **Assess**: Determine if rollback is needed
3. **Rollback**: Revert to previous stable version
4. **Verify**: Confirm rollback successful
5. **Communicate**: Notify team and users
6. **Fix**: Address issue in development
7. **Re-deploy**: Deploy fix after testing

## Release Notes Template

```markdown
# Release vX.Y.Z - [Date]

## Added
- New feature X
- New feature Y

## Changed
- Improved Z
- Updated dependency versions

## Fixed
- Bug fix A
- Bug fix B

## Security
- Security patch C (if applicable)

## Breaking Changes
- None (or list breaking changes)

## Migration Notes
- None (or migration steps if database changes)
```

## Sign-Off

- **Developer**: _________________ Date: _______
- **QA**: _________________ Date: _______
- **DevOps**: _________________ Date: _______
- **Product Owner**: _________________ Date: _______
