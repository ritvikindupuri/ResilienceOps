import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },
    { duration: '5m', target: 50 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.02'], // SLO: less than 2% failure rate
    http_req_duration: ['p(95)<500', 'p(99)<1500'], // SLO: 95% under 500ms
  },
};

const BASE_URL = __ENV.GATEWAY_URL || 'http://localhost:8000';

export default function () {
  // 1. Health / Home
  let res = http.get(`${BASE_URL}/health`);
  check(res, { 'status is 200': (r) => r.status === 200 });

  // 2. Create Order
  const payload = JSON.stringify({
    item_id: 'prod-macbook-pro',
    quantity: 1,
    amount: 1999.00,
    user_id: `user_${__VU}`
  });
  const params = { headers: { 'Content-Type': 'application/json' } };
  
  res = http.post(`${BASE_URL}/api/orders/orders`, payload, params);
  check(res, { 'order created': (r) => r.status === 200 });

  if (res.status === 200) {
    const order = res.json();
    // 3. Pay
    const payPayload = JSON.stringify({
      order_id: order.order_id,
      amount: 1999.00,
      currency: 'USD'
    });
    let payRes = http.post(`${BASE_URL}/api/payments/payments`, payPayload, params);
    check(payRes, { 'payment processed': (r) => r.status === 200 });
  }

  sleep(1);
}
