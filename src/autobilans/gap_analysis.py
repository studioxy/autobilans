from __future__ import annotations

from itertools import combinations


def find_candidate_combos(
    mapping_rows: list[dict[str, str]],
    expected: float,
    max_group: int = 3,
    max_results: int = 5,
) -> list[dict[str, object]]:
    candidates = []
    leaf_rows = []
    for row in mapping_rows:
        amount = float(row["persaldo"])
        if abs(amount) < 0.009:
            continue
        if row["source"] == "unresolved":
            continue
        leaf_rows.append(row)

    for size in range(1, max_group + 1):
        for combo in combinations(leaf_rows, size):
            total = round(sum(abs(float(item["persaldo"])) for item in combo), 2)
            if abs(total - expected) <= 0.01:
                candidates.append(
                    {
                        "total": total,
                        "rows": [
                            {
                                "account_no": item["account_no"],
                                "name": item["name"],
                                "persaldo": float(item["persaldo"]),
                                "balance_code": item["balance_code"],
                                "source": item["source"],
                            }
                            for item in combo
                        ],
                    }
                )
                if len(candidates) >= max_results:
                    return candidates
    return candidates


def suggest_aliases(
    *,
    calculated_balance: dict[str, float],
    expected: float,
    tolerance: float = 0.01,
) -> list[str]:
    matches = [
        code
        for code, value in calculated_balance.items()
        if abs(round(float(value), 2) - expected) <= tolerance
    ]
    return sorted(matches)


def analyze_gaps(
    *,
    mapping_rows: list[dict[str, str]],
    validation_rows: list[dict[str, str]],
    calculated_balance: dict[str, float],
) -> list[dict[str, object]]:
    report: list[dict[str, object]] = []
    for row in validation_rows:
        if row["matched"] != "False":
            continue
        expected = float(row["expected"])
        report.append(
            {
                "code": row["code"],
                "expected": expected,
                "actual": float(row["actual"]),
                "delta": float(row["delta"]),
                "suggested_aliases": suggest_aliases(
                    calculated_balance=calculated_balance,
                    expected=expected,
                ),
                "candidate_combos": find_candidate_combos(mapping_rows, expected),
            }
        )
    return report
