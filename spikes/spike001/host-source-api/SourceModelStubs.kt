package eu.kanade.tachiyomi.source.model

// Compile-only stand-ins for Source API's return and argument model types.
// This test compiles the real pinned Source interface, not a rewritten interface.
class FilterList
class MangasPage
class Page
class SChapter
class SManga
class SMangaUpdate(val manga: SManga, val chapters: List<SChapter>)
