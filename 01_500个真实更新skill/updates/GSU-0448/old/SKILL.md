---
name: tenancy-enforcer
description: Use this skill when writing MongoDB queries, repository methods, or service logic in Aegis. It enforces strict multi-tenancy by ensuring communityId is always included.
---

# Aegis Multi-Tenancy Enforcer

## Instructions
- Before generating any MongoDB query, verify that `communityId` is present in the filter object.
- If a query is proposed without `communityId`, stop and request it from the authentication context.
- Ensure `communityId` is never accepted from a request body; it must resolve from JWT metadata.

## Verification
1. Grep the proposed code for `communityId`.
2. Ensure it is used in the first layer of any `.find()`, `.updateOne()`, or `.delete()` call.