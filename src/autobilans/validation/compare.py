from __future__ import annotations

from dataclasses import asdict, dataclass

from autobilans.models import BilansPosition


@dataclass(slots=True)
class ValidationItem:
    code: str
    expected: float
    actual: float
    delta: float
    matched: bool


def compare_balance_to_xml(
    calculated: dict[str, float],
    xml_positions: list[BilansPosition],
    *,
    mapping_aliases: dict[str, str | list[str]] | None = None,
    tolerance: float = 0.01,
) -> list[ValidationItem]:
    aliases = mapping_aliases or {}
    results: list[ValidationItem] = []

    for position in xml_positions:
        mapped_code = aliases.get(position.code)
        actual = calculated.get(position.code)
        if actual is None and mapped_code is not None:
            if isinstance(mapped_code, list):
                actual = sum(calculated.get(code, 0.0) for code in mapped_code)
            else:
                actual = calculated.get(mapped_code)
        if actual is None:
            actual = 0.0
        if position.code.startswith("Pasywa_"):
            actual = abs(actual)

        expected = float(position.amount_current)
        delta = round(actual - expected, 2)
        results.append(
            ValidationItem(
                code=position.code,
                expected=expected,
                actual=round(actual, 2),
                delta=delta,
                matched=abs(delta) <= tolerance,
            )
        )

    return results


def summarize_validation(results: list[ValidationItem]) -> dict[str, int]:
    matched = sum(1 for item in results if item.matched)
    return {
        "total_positions": len(results),
        "matched_positions": matched,
        "mismatched_positions": len(results) - matched,
    }


def validation_item_to_dict(item: ValidationItem) -> dict[str, object]:
    return asdict(item)
