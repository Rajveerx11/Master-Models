# Backend-stack specialist

## Job

Implement and repair APIs, services, persistence, provider integrations, concurrency,
error handling, and resource lifecycles.

## Coverage

- request/response contracts and validation;
- state and persistence boundaries;
- async cancellation, timeouts, retries, and idempotency;
- provider failures and error propagation;
- migrations and backward compatibility;
- focused unit and integration verification.

## Data

Mine real changes from `Testing IDE`, `terax-ai`, and `Neura`. Freeze 20 eval tasks
before generation. Target 200-280 gold trajectories, weighted toward multi-file
contract changes and failure recovery.

## Reject

- frontend-dominant changes;
- invented API responses or test output;
- migrations without compatibility reasoning;
- broad rewrites when a focused service change exists.

## Gate

5 easy, 9 medium, 6 hard tasks. Include at least four timeout/concurrency cases, four
contract/persistence cases, and four real failure-path cases.
