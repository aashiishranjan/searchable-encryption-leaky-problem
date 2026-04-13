"""
attack_simulation.py - Frequency analysis attack on an SSE scheme.

Inspired by: Islam et al. 2012 — "Access Pattern disclosure on Searchable
Encryption: Ramification, Attack and Mitigation".

The FrequencyAnalysisAttack class simulates a *known-data* adversary that:
  1. Possesses a background keyword frequency distribution (e.g., from a
     public corpus or domain knowledge).
  2. Observes the frequency histogram of trapdoors issued to the server.
  3. Ranks both distributions and correlates them by rank to guess which
     trapdoor corresponds to which keyword.

This is the simplest possible frequency analysis attack.  More sophisticated
variants (e.g., using co-occurrence matrices) are described in the literature.
"""

from typing import Dict, List, Tuple


class FrequencyAnalysisAttack:
    """
    Simulates a rank-based frequency analysis attack against SSE.

    The adversary knows:
      - A *background* keyword frequency distribution (plaintext side).
      - The *observed* trapdoor frequency distribution (ciphertext side).

    By aligning both distributions in descending frequency order the
    adversary can guess the plaintext keyword for each trapdoor.
    """

    def __init__(
        self,
        known_frequencies: Dict[str, float],
        observed_frequencies: Dict[str, int],
    ) -> None:
        """
        Args:
            known_frequencies: keyword → relative frequency (float 0–1).
                               E.g. {"encryption": 0.07, "malware": 0.05}.
            observed_frequencies: trapdoor_hex → query count (int).
                                  Typically the output of
                                  LeakageAnalyzer.detect_frequency_leakage().
        """
        self._known: Dict[str, float] = known_frequencies
        self._observed: Dict[str, int] = observed_frequencies
        # Results populated by run_attack()
        self._results: List[Dict] = []

    # ------------------------------------------------------------------
    # Attack execution
    # ------------------------------------------------------------------

    def run_attack(self) -> List[Dict]:
        """
        Execute the rank-correlation frequency analysis attack.

        Algorithm:
          1. Sort known keywords by descending frequency → rank list K.
          2. Sort observed trapdoors by descending query count → rank list T.
          3. Zip K and T: the i-th most frequent trapdoor is guessed to
             correspond to the i-th most frequent known keyword.
          4. Assign a confidence score based on the closeness of the two
             normalised frequency values.

        Returns:
            List[dict]: One entry per matched pair, each with:
              - ``trapdoor``:   hex token (truncated for display)
              - ``guessed_keyword``: candidate plaintext keyword
              - ``trapdoor_frequency``: observed query count
              - ``known_frequency``: background frequency value
              - ``confidence``:  float 0–1 (1 = perfect frequency match)
        """
        # Sort known keywords: highest frequency first
        known_ranked: List[Tuple[str, float]] = sorted(
            self._known.items(), key=lambda kv: kv[1], reverse=True
        )

        # Sort observed trapdoors: highest count first
        observed_ranked: List[Tuple[str, int]] = sorted(
            self._observed.items(), key=lambda kv: kv[1], reverse=True
        )

        # Normalise observed counts to [0, 1] for comparison
        max_count = max((cnt for _, cnt in observed_ranked), default=1)

        self._results = []
        for i, (trapdoor, count) in enumerate(observed_ranked):
            if i >= len(known_ranked):
                # More trapdoors than known keywords — no guess available
                self._results.append(
                    {
                        "trapdoor": trapdoor,
                        "guessed_keyword": "<unknown>",
                        "trapdoor_frequency": count,
                        "known_frequency": 0.0,
                        "confidence": 0.0,
                    }
                )
                continue

            keyword, kfreq = known_ranked[i]
            norm_count = count / max_count if max_count > 0 else 0.0

            # Confidence: 1 minus the absolute difference of normalised frequencies
            # (both normalised to [0,1]).
            max_known = known_ranked[0][1] if known_ranked else 1.0
            norm_kfreq = kfreq / max_known if max_known > 0 else 0.0
            confidence = max(0.0, 1.0 - abs(norm_count - norm_kfreq))

            self._results.append(
                {
                    "trapdoor": trapdoor,
                    "guessed_keyword": keyword,
                    "trapdoor_frequency": count,
                    "known_frequency": kfreq,
                    "confidence": round(confidence, 4),
                }
            )

        return self._results

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def print_attack_results(self) -> None:
        """
        Print a nicely formatted table of the attack results to stdout.

        Calls run_attack() automatically if it has not been called yet.
        """
        if not self._results:
            self.run_attack()

        sep = "-" * 70
        print("=" * 70)
        print("  FREQUENCY ANALYSIS ATTACK RESULTS")
        print("  (Islam et al. 2012 — rank-correlation method)")
        print("=" * 70)
        print(
            f"  {'Trapdoor (last 12)':20s}  {'Guessed Keyword':20s}"
            f"  {'Obs. Freq':9s}  {'Confidence':10s}"
        )
        print(sep)
        for r in self._results:
            td_short = "..." + r["trapdoor"][-12:]
            kw = r["guessed_keyword"]
            freq = r["trapdoor_frequency"]
            conf = r["confidence"]
            bar = "*" * int(conf * 10)
            print(
                f"  {td_short:20s}  {kw:20s}  {freq:9d}  {conf:.2%}  {bar}"
            )
        print("=" * 70)
        print()
        print(
            "  NOTE: The adversary correctly ordered trapdoors without ever\n"
            "  seeing a single plaintext keyword.  Only frequency statistics\n"
            "  from the *encrypted* query log were used."
        )
        print("=" * 70)
