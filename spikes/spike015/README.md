# Spike-015 — Cross-source translation artifact identity

Polaris should not treat a source URL as the identity of a translated page.

Two different sources can serve identical image bytes. A translation should be reusable when the actual page content and translation pipeline configuration are equivalent.

## Key

The reusable artifact identity includes:
- SHA-256 of the original page bytes;
- target language;
- OCR revision;
- translator/provider ID;
- translator model;
- canonical glossary revision;
- rendering revision.

The source URL, source ID and manga title are deliberately NOT part of this reusable content key.

## Consequences

- identical page bytes from another source can reuse OCR/translation;
- changing glossary invalidates the translated text key;
- changing translation model can invalidate/recompute;
- rendering changes can invalidate final rendered artifact without changing source identity.

Yomotsu's existing source-specific translation files may remain the immediate storage format. This key can first be used as a secondary reusable cache index.

Validated in pure Kotlin:
- language aliases normalize to the same key;
- same bytes/config => same key;
- glossary/model/page changes => different key.
