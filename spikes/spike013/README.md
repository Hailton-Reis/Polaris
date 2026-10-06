# Spike-013 — LanguageRoutePlanner

Builds the language preference order used by SourceRanker.

Default Polaris route for a PT-BR user:

1. target language (pt-BR)
2. same base language (pt)
3. configured bridge language (en)
4. original work language
5. user-configured extra fallback languages

Duplicates are removed after normalization.

Examples:
- Korean manhwa: pt-BR -> pt -> en -> ko
- Japanese manga: pt-BR -> pt -> en -> ja
- English original: pt-BR -> pt -> en
- User extra Chinese fallback: pt-BR -> pt -> en -> ko -> zh
