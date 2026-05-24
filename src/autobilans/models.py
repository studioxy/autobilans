from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ZoisRow:
    account_no: str
    name: str
    name_2: str
    closing_debit: float
    closing_credit: float
    persaldo: float
    balance_code: str | None
    additional_balance_codes: tuple[str, ...] = ()
    company: str | None = None
    year: int | None = None
    source_path: str | None = None


@dataclass(slots=True)
class BilansPosition:
    code: str
    section: str
    amount_current: float
    amount_previous: float
    source_path: str | None = None
