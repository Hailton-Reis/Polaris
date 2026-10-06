# Spike-021 — R001 domain scenario simulation

Cross-spike integration test for the core Polaris reading decision path without Android.

The simulation composes the same policies that Work/Codex will wire into Yomotsu:

SourceHealthTracker
-> LanguageRoutePlanner
-> SourceRanker / ChapterOpenPlanner
-> TranslationDecisionPolicy
-> CanonicalProgressPolicy

Scenario:
1. PT-BR 80 is healthy.
2. PT-BR 83 is challenged.
3. EN 85 is healthy.
4. Chapter 79 selects healthy PT-BR and reads original.
5. Chapter 84 exists only in EN and queues translation.
6. Reopening chapter 84 with translation cached uses the cache.
7. Canonical completion survives a later source switch.
8. Page index is not copied to the new source variant.
9. A challenged source can recover after a successful manual revalidation/probe.

Result in the current environment:
`SPIKE021_R001_SCENARIO_SIMULATION_PASS`.

This does not replace Android runtime acceptance; it proves the domain policies compose coherently.
