from autobilans.cli import _print_next_steps


def test_print_next_steps_for_clean_run(capsys) -> None:
    _print_next_steps(has_queue=True, queue_items=0, mismatched=0, unresolved=0)
    output = capsys.readouterr().out
    assert "Nie ma wyjątków" in output
    assert "wynik końcowy" in output


def test_print_next_steps_for_open_exceptions(capsys) -> None:
    _print_next_steps(has_queue=True, queue_items=3, mismatched=2, unresolved=1)
    output = capsys.readouterr().out
    assert "Wybierz 2" in output
    assert "Wybierz 5" in output


def test_print_next_steps_for_clean_validation_with_unresolved(capsys) -> None:
    _print_next_steps(has_queue=True, queue_items=0, mismatched=0, unresolved=2)
    output = capsys.readouterr().out
    assert "Nie ma wyjątków" in output
    assert "nie blokują" in output
