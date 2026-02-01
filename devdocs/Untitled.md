aw debate submit \
  --debate-id $DEBATE_ID \
  --role opponent \
  --target-id ee36f6ad-305c-4f98-a8da-27e16e078f62 \
  --content "## Review Summary

After reviewing the plan (doc_id=$DOC_ID), I found the following issues:

## Issues Found

### M1: Missing Error Handling
**Problem:** The plan doesn't mention error handling for failed uploads
**Suggestion:** Add error handling section for file validation, size limits, format checks
**Severity:** Major

### M2: Missing Storage Strategy
**Problem:** No mention of where avatars will be stored (local/S3/CDN)
**Suggestion:** Define storage strategy and add to implementation plan
**Severity:** Major

## Positive Points

- Clear task breakdown
- Reasonable timeline

## Action Required

Please address M1 and M2 before approval."