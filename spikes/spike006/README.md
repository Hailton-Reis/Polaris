# Spike-006 — TranslationDecisionPolicy

Polaris should reuse Yomotsu's existing OCR/translation pipeline rather than rebuild it.

This spike defines only the decision boundary between source selection and Yomotsu translation.

## Key rule

Translation intelligence must be scoped to CanonicalWork, not to the source-specific manga title.

Without this, these source variants would create separate memories/glossaries:
- The Beginning After the End
- O Começo Depois do Fim
- O Começo Após o Fim

Polaris should pass one stable canonical translation context for all of them.

## Decisions

For a selected ChapterVariant:

1. If the selected language is already the target language -> READ_ORIGINAL.
2. If a translated result already exists -> READ_TRANSLATED_CACHE.
3. If foreign and translation is enabled/configured -> QUEUE_TRANSLATION.
4. If foreign and no translation provider is available -> READ_FOREIGN_UNTRANSLATED (with explicit diagnostic state).

## Yomotsu integration

Reuse:
- TranslationManager
- ChapterTranslator
- TranslationCache
- TranslationMemory
- TranslationGlossary
- TextTranslators / fallback engine
- OCR engine manager
- inpainting/typesetting pipeline

Required adaptation:
- add an automatic reader/source-selection origin to TranslationRequestOrigin;
- let TranslationManager/ChapterTranslator receive a canonical translation context title/key;
- cache/glossary/memory must share the same canonical context across source variants.
