# Testing/QA specialist

## Job

Design and implement tests that expose real faults, reduce flakiness, and verify
behavior at the correct layer.

## Coverage

- unit, component, integration, and end-to-end test selection;
- deterministic async and timeout testing;
- flaky-test diagnosis and isolation;
- mutation survivor analysis;
- fixtures, mocks, and test-data boundaries;
- CI failures and coverage gaps.

## Data

Mine real test and mutation work primarily from `Testing IDE`, then complementary
cases from `terax-ai` and `Neura`. Freeze 20 eval tasks first. Target 200-280 gold
trajectories, including red-to-green evidence and test-failure recovery.

## Reject

- tests that only mirror implementation;
- claimed failures not present in tool output;
- snapshot churn without behavioral assertions;
- brittle sleeps where deterministic synchronization is possible.

## Gate

Include tests that must kill a known bug, flaky cases, wrong-layer traps, and CI-only
failures. Score defect detection and test robustness, not line count.
