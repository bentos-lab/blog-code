"""Context Compactor — deterministic, LLM-free history compression.

Compaction is REVERSIBLE: it strips verbose fields from cycle entries down to
thin metadata. The original data (test output, file contents) lives on disk and
can be re-derived. No LLM call, no tokens spent.

Contrast with summarizer.py (irreversible): that uses an LLM and loses structure.
"""


def compact_entry(entry: dict) -> dict:
    """Strip verbose fields from a single cycle entry. Pure Python — no LLM."""
    if entry.get("type") in ("compact_summary", "narrative_summary"):
        return entry  # already reduced, pass through
    return {
        "type": "compact_summary",
        "cycle": entry.get("cycle"),
        "bugs_count": len(entry.get("bugs_found", [])),
        "files_patched": [
            r.get("path") for r in entry.get("exec_results", [])
            if isinstance(r, dict) and r.get("patched")
        ],
        "test_summary_before": (entry.get("test_output", "") or "")[-120:],
        "test_summary_after": entry.get("test_summary_after", ""),
    }


def compact_history(full_history: list) -> dict:
    """Compact all entries in full_history into one merged thin record.

    Merges cycle metadata across all entries — no information is sent to an LLM.
    """
    compacted = [compact_entry(e) for e in full_history]
    all_files = list({
        f
        for e in compacted
        for f in (e.get("files_patched") or [])
        if f
    })
    return {
        "type": "compact_summary",
        "cycles": [e.get("cycle") for e in compacted if e.get("cycle")],
        "total_bugs_addressed": sum(e.get("bugs_count", 0) for e in compacted),
        "all_files_patched": all_files,
        "last_test_summary": compacted[-1].get("test_summary_after", "") if compacted else "",
    }
