from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class DecisionValidationResult:
    valid: list[dict[str, object]]
    errors: list[str]
    duplicate_count: int


def suggest_decisions(queue: list[dict[str, object]]) -> list[dict[str, object]]:
    suggestions: list[dict[str, object]] = []
    for item in queue:
        kind = str(item.get("kind", ""))
        if kind == "unresolved_account":
            account_no = str(item.get("account_no", "")).strip()
            if not account_no:
                continue
            original_code = str(item.get("original_balance_code", "")).strip()
            if original_code:
                suggestions.append(
                    {
                        "exception_id": item.get("id"),
                        "action": "force_target_code",
                        "account_no": account_no,
                        "target_code": original_code,
                        "reason": "Użyto oryginalnego kodu bilansowego z ZOiS dla konta nierozstrzygniętego.",
                    }
                )
            continue

        if kind != "validation_mismatch":
            continue

        contributors = item.get("top_contributors", [])
        if not isinstance(contributors, list):
            continue

        top = next(
            (
                contributor
                for contributor in contributors
                if isinstance(contributor, dict)
                and str(contributor.get("account_no", "")).strip()
                and str(contributor.get("source_code", "")).strip()
            ),
            None,
        )
        if top is None:
            continue

        suggestions.append(
            {
                "exception_id": item.get("id"),
                "action": "exclude_secondary_code",
                "account_no": str(top["account_no"]),
                "secondary_code": str(top["source_code"]),
                "target_code": str(item.get("target_code", "")),
                "reason": (
                    "Największy wkład wskazuje prawdopodobny konflikt kodu wtórnego "
                    f"dla pozycji {item.get('target_code')}."
                ),
            }
        )
    return suggestions


def validate_decisions(
    decisions: list[dict[str, object]],
    *,
    known_target_codes: set[str] | None = None,
) -> DecisionValidationResult:
    normalized: list[dict[str, object]] = []
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()
    duplicates = 0
    allowed_codes = known_target_codes or set()

    for idx, raw_decision in enumerate(decisions, start=1):
        action = str(raw_decision.get("action", "")).strip()
        account_no = str(raw_decision.get("account_no", "")).strip()
        target_code = str(raw_decision.get("target_code", "")).strip()
        secondary_code = str(raw_decision.get("secondary_code", "")).strip()

        if action not in {"force_target_code", "exclude_secondary_code"}:
            errors.append(f"[{idx}] Unsupported action: {action!r}")
            continue
        if not account_no:
            errors.append(f"[{idx}] account_no is required.")
            continue

        if action == "force_target_code":
            if not target_code:
                errors.append(f"[{idx}] target_code is required for force_target_code.")
                continue
            if allowed_codes and target_code not in allowed_codes:
                errors.append(f"[{idx}] Unknown target_code: {target_code!r}")
                continue
            identity = (action, account_no, target_code)
        else:
            if not secondary_code:
                errors.append(f"[{idx}] secondary_code is required for exclude_secondary_code.")
                continue
            identity = (action, account_no, secondary_code)

        if identity in seen:
            duplicates += 1
            continue
        seen.add(identity)
        normalized.append(raw_decision)

    return DecisionValidationResult(valid=normalized, errors=errors, duplicate_count=duplicates)

