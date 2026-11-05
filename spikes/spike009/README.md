# Spike-009 — AliasSearchPlanner

The first pass reuses Yomotsu global search with the user's query.

After Polaris has a plausible canonical identity, a second pass can search selected sources with language-appropriate aliases. This is how a query for an English title can still discover a PT-BR source whose site indexes only the Portuguese title.

## Guardrails

- max two queries per source by default;
- exact duplicate normalized queries are removed;
- healthy/degraded sources are searched first;
- blocked/auth/challenged sources are not background-searched;
- user interaction can later revalidate those sources;
- if no alias exists for a source language, the canonical title is used as fallback.

The planner only produces tasks; Android integration performs the actual Source.getSearchManga calls.
