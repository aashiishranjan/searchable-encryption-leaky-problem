"""
leakage_analyzer.py - Analyses and reports the four classic SSE leakage types.

The LeakageAnalyzer class acts as a passive, honest-but-curious server
that records every query it processes and later extracts statistical
information about the queries — without ever learning the plaintext
keywords.

The four leakage types modelled here are:

  1. **Search Pattern Leakage** — the server can tell when the *same*
     keyword is searched more than once because the trapdoor token is
     deterministic (same keyword ⟹ same token).

  2. **Access Pattern Leakage** — the server sees *which* encrypted
     documents are returned for each query, linking queries to document sets.

  3. **Volume (Size) Pattern Leakage** — the server counts *how many*
     documents each query returns, which leaks the keyword's document
     frequency.

  4. **Frequency Leakage** — over many queries, the server builds a
     histogram of trapdoor usage that mirrors the keyword frequency
     distribution in the original corpus / query log.
"""

from collections import defaultdict
from typing import Dict, List, Tuple


class LeakageAnalyzer:
    """
    Passive leakage monitor that intercepts SSE queries and extracts
    statistical information visible to the server.
    """

    def __init__(self) -> None:
        # List of (trapdoor, [result_doc_ids]) tuples — one per query
        self._query_log: List[Tuple[str, List[str]]] = []

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_query(self, trapdoor: str, results: List[str]) -> None:
        """
        Record a single SSE query.

        Args:
            trapdoor: The HMAC token submitted by the client.
            results: The list of encrypted doc-ID hex strings returned.
        """
        self._query_log.append((trapdoor, list(results)))

    # ------------------------------------------------------------------
    # Individual leakage detectors
    # ------------------------------------------------------------------

    def detect_search_pattern_leakage(self) -> Dict[str, int]:
        """
        Identify trapdoors that appear **more than once** in the query log.

        Search pattern leakage reveals that the *same keyword* was queried
        multiple times — even though the server never sees the keyword itself.

        Returns:
            dict: trapdoor → count, for trapdoors repeated ≥ 2 times.
        """
        counts: Dict[str, int] = defaultdict(int)
        for trapdoor, _ in self._query_log:
            counts[trapdoor] += 1
        return {td: cnt for td, cnt in counts.items() if cnt >= 2}

    def detect_access_pattern_leakage(self) -> Dict[str, List[str]]:
        """
        Show which encrypted document IDs are associated with each trapdoor.

        Access pattern leakage lets the server link queries to document sets.
        If the same document appears in the results of two different queries,
        the server learns that both keywords co-occur in that document.

        Returns:
            dict: trapdoor → sorted list of unique encrypted doc-ID hex strings.
        """
        access_map: Dict[str, set] = defaultdict(set)
        for trapdoor, results in self._query_log:
            for doc_id in results:
                access_map[trapdoor].add(doc_id)
        return {td: sorted(docs) for td, docs in access_map.items()}

    def detect_volume_leakage(self) -> Dict[str, int]:
        """
        Report the *number of results* returned for each unique trapdoor.

        Volume leakage reveals the document frequency of each keyword —
        a server can use this to distinguish common keywords (large result
        sets) from rare ones (small result sets).

        Returns:
            dict: trapdoor → result count.
        """
        volume_map: Dict[str, int] = {}
        for trapdoor, results in self._query_log:
            # Record the result count on first occurrence of this trapdoor
            if trapdoor not in volume_map:
                volume_map[trapdoor] = len(results)
        return volume_map

    def detect_frequency_leakage(self) -> Dict[str, int]:
        """
        Build a histogram of how often each trapdoor appears in the query log.

        Frequency leakage lets the server rank trapdoors by popularity and
        compare that ranking against known keyword frequency distributions
        (the basis of frequency analysis attacks, see Islam et al. 2012).

        Returns:
            dict: trapdoor → total query count, sorted by count descending.
        """
        counts: Dict[str, int] = defaultdict(int)
        for trapdoor, _ in self._query_log:
            counts[trapdoor] += 1
        return dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))

    # ------------------------------------------------------------------
    # Combined report
    # ------------------------------------------------------------------

    def generate_full_report(self) -> str:
        """
        Combine all four leakage analyses into a single formatted text report.

        Returns:
            str: Human-readable multi-section leakage report.
        """
        lines: List[str] = []
        sep = "-" * 60

        lines.append("=" * 60)
        lines.append("  LEAKAGE ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"  Total queries logged: {len(self._query_log)}")
        lines.append("")

        # ---- Search Pattern ----------------------------------------
        lines.append(sep)
        lines.append("[1] SEARCH PATTERN LEAKAGE")
        lines.append(sep)
        lines.append(
            "    The server can detect when the SAME keyword is searched\n"
            "    multiple times because the trapdoor token is deterministic."
        )
        lines.append("")
        repeated = self.detect_search_pattern_leakage()
        if repeated:
            lines.append(f"    {len(repeated)} trapdoor(s) were repeated:")
            for td, cnt in sorted(repeated.items(), key=lambda kv: -kv[1]):
                lines.append(f"      Token ...{td[-12:]}  →  queried {cnt} times")
        else:
            lines.append("    No repeated trapdoors detected.")
        lines.append("")

        # ---- Access Pattern ----------------------------------------
        lines.append(sep)
        lines.append("[2] ACCESS PATTERN LEAKAGE")
        lines.append(sep)
        lines.append(
            "    The server can see WHICH encrypted documents are returned\n"
            "    for each trapdoor — revealing document co-occurrence."
        )
        lines.append("")
        access = self.detect_access_pattern_leakage()
        for td, docs in access.items():
            lines.append(f"    Token ...{td[-12:]}  →  {len(docs)} doc(s)")
            for doc in docs:
                lines.append(f"      Doc ...{doc[-16:]}")
        lines.append("")

        # ---- Volume Pattern ----------------------------------------
        lines.append(sep)
        lines.append("[3] VOLUME (SIZE) PATTERN LEAKAGE")
        lines.append(sep)
        lines.append(
            "    The server learns HOW MANY documents match each query,\n"
            "    revealing the keyword's document frequency."
        )
        lines.append("")
        volume = self.detect_volume_leakage()
        for td, cnt in sorted(volume.items(), key=lambda kv: -kv[1]):
            lines.append(f"    Token ...{td[-12:]}  →  {cnt} result(s)")
        lines.append("")

        # ---- Frequency Leakage -------------------------------------
        lines.append(sep)
        lines.append("[4] FREQUENCY LEAKAGE")
        lines.append(sep)
        lines.append(
            "    Over many queries the server builds a frequency histogram\n"
            "    of trapdoor usage that mirrors keyword popularity."
        )
        lines.append("")
        freq = self.detect_frequency_leakage()
        total_queries = len(self._query_log)
        for td, cnt in freq.items():
            pct = (cnt / total_queries * 100) if total_queries > 0 else 0
            bar = "#" * cnt
            lines.append(
                f"    Token ...{td[-12:]}  →  {cnt:3d} queries  ({pct:5.1f}%)  {bar}"
            )
        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
