# Spike-008 — SearchResultClusterer

Yomotsu/Mihon already has a global search engine:
- all enabled non-novel sources;
- source-language filtering;
- up to five source searches concurrently;
- results retained per source.

Polaris should reuse that engine.

This spike groups the flat source-specific results returned by global search into canonical-work candidates.

## Rules

- AUTO_MATCH results join the same cluster.
- REVIEW pairs do not merge silently.
- REVIEW pairs are emitted as semantic-review requests for LLM/metadata/user confirmation.
- DIFFERENT candidates stay separate.

This preserves the most important safety rule: uncertain works are never silently merged.

## Follow-up search

Some translated variants will not be discovered by the initial user query. After a canonical identity is established, Polaris can run targeted alias queries in a second pass. That query planning is intentionally kept separate from clustering.
