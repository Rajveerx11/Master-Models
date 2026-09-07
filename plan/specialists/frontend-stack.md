# Frontend-stack specialist

## Job

Implement and repair React/TypeScript interfaces with correct state, accessibility,
styling, component contracts, and focused verification.

## Data

- Whole-corpus static audit leaves 237 replay candidates and 5 quarantined records.
  Reuse task ideas only until real source identity and execution are captured.
  Four explanations are corrected in candidate copies, not approved for training.
- Prioritize state races, lifecycle cleanup, multi-file prop/API changes, overflow,
  keyboard behavior, accessibility, and failed-check recovery.
- Add 30-50 new records only for measured coverage gaps.
- Target 180-220 clean domain rows after removing weak examples.
- Five of the [30 selected pilot tasks](../../datasets/frontend-stack/v2/review/pilot/README.md)
  now pass captured checks. All five complete traces exceed 3,072 tokens; fix capture
  length and obtain independent review before the remaining 25. The corrected source
  inventory has 143 candidates; 60 eval collisions were excluded. Gold remains zero.

## Reject

- cosmetic-only bulk;
- unsupported browser or test claims;
- edits without reading affected contracts;
- shallow one-file examples that repeat existing patterns.

## Gate

Reuse the frozen 20-task frontend set. Compare trained Qwen3-4B against stock
Qwen3-4B. Require 10/10 frontend smoke before the gate.
