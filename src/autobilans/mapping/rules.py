import functools
from collections import Counter, defaultdict

from autobilans.models import ZoisRow

@functools.lru_cache(maxsize=1024)
def account_prefixes(account_no: str) -> tuple[str, ...]:
    """
    Returns all prefixes for a given account number.
    e.g. "123-45-6" -> ("123", "123-45", "123-45-6")
    ⚡ Bolt: Cached to prevent repeated string splitting and joining for the same accounts
    across thousands of ZOiS rows.
    """
    parts = str(account_no).split("-")
    prefixes = []
    current = ""
    for part in parts:
        if current:
            current += "-" + part
        else:
            current = part
        prefixes.append(current)
    return tuple(prefixes)

def build_history_rules(rows: list[ZoisRow]) -> dict[str, dict[str, str]]:
    by_account: dict[str, Counter[str]] = defaultdict(Counter)
    by_prefix: dict[str, Counter[str]] = defaultdict(Counter)

    for row in rows:
        if not row.balance_code:
            continue
        by_account[row.account_no][row.balance_code] += 1
        for prefix in account_prefixes(row.account_no):
            by_prefix[prefix][row.balance_code] += 1

    def pick_best(counter_map: dict[str, Counter[str]]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for key, counter in counter_map.items():
            if not counter:
                continue
            resolved[key] = counter.most_common(1)[0][0]
        return resolved

    return {
        "account": pick_best(by_account),
        "prefix": pick_best(by_prefix),
    }
