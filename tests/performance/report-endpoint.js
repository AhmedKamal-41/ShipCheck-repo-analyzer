import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '10s', target: 5 },
    { duration: '20s', target: 10 },
    { duration: '10s', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests should be below 1s
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
// Use a known report ID from fixtures or create one first
const REPORT_ID = __ENV.REPORT_ID || '123e4567-e89b-12d3-a456-426614174001';

export default function () {
  // Test report endpoint
  const res = http.get(`${BASE_URL}/api/reports/${REPORT_ID}`);
  
  check(res, {
    'report status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'report response time < 1s': (r) => r.timings.duration < 1000,
    'report response has valid structure': (r) => {
      if (r.status === 404) return true; // 404 is valid
      try {
        const body = JSON.parse(r.body);
        return body.id && body.repo_url && typeof body.status === 'string';
      } catch {
        return false;
      }
    },
  });
  
  sleep(1);
}
