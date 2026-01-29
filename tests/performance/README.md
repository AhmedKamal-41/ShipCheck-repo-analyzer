# Performance Tests

This directory contains k6 performance test scripts.

## Prerequisites

Install k6:
- macOS: `brew install k6`
- Linux: See https://k6.io/docs/getting-started/installation/
- Windows: See https://k6.io/docs/getting-started/installation/

## Running Tests

### Health Check Test
```bash
k6 run health-check.js
```

### Report Endpoint Test
```bash
# Set a valid report ID (create one via API first)
REPORT_ID=your-report-id k6 run report-endpoint.js
```

### Custom Base URL
```bash
BASE_URL=http://localhost:8000 k6 run health-check.js
```

## Test Configuration

- **Virtual Users**: 10 max
- **Duration**: 30 seconds total
- **Thresholds**: 
  - Health: <500ms response time (95th percentile)
  - Report: <1s response time (95th percentile)
  - <1% error rate

## CI Integration

These tests can be run in CI as optional/manual jobs or nightly.
