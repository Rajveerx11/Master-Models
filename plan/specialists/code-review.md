# Code-review specialist

## Job

Review a patch, find concrete defects, rank severity, cite exact evidence, and propose
the smallest correct fix. Silence is preferred to invented findings.

## Coverage

- behavioral regressions and broken edge cases;
- concurrency and lifecycle defects;
- contract mismatches across files;
- unsafe assumptions and missing validation;
- inadequate tests for changed behavior;
- precise file/line evidence and severity.

## Data

Construct examples from real pre-fix patches and later corrective commits. Freeze 20
review tasks first. Include clean patches with no findings and ambiguous patches that
require inspection. Target 180-240 gold reviews.

## Reject

- style-only comments;
- findings without a reproducible failure path;
- summaries disguised as review;
- duplicate findings for one root cause.

## Gate

Measure true findings, false positives, missed critical defects, severity calibration,
and evidence quality. A high false-positive rate blocks release.
