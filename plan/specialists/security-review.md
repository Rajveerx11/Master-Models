# Security-review specialist

## Job

Find and fix exploitable trust-boundary failures with evidence, minimal patches, and
regression tests.

## Coverage

- command, header, path, template, and prompt injection;
- authorization and workspace containment;
- secrets and unsafe logging;
- SSRF and unsafe fetch boundaries;
- archive/symlink/temp-file safety;
- denial-of-service and unbounded resource use.

## Data

Mine security fixes and adjacent vulnerable parents from local repositories. Reserve
20 eval commits first. Generate paired reasoning from vulnerable code to exact fix and
test evidence. Target 180-240 gold records.

## Reject

- generic checklist prose without code evidence;
- speculative vulnerability claims;
- exploit instructions beyond what is required to validate the local fix;
- severity inflation and unrelated hardening.

## Gate

Require zero critical regressions. Include false-positive traps so the model must avoid
claiming vulnerabilities that the code already prevents.
