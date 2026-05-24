# AutoBilans

Lokalny system do generowania bilansu na podstawie ZOiS z kontrolą zgodności względem historycznych sprawozdań XML.

## Założenia

- `v1` działa lokalnie, bez hostingu i bez zależności od dużego modelu LLM.
- Matematyka i agregacja są wykonywane wyłącznie w Pythonie.
- Dane finansowe pozostają na lokalnym serwerze lub stacji roboczej.
- Warstwa LLM jest opcjonalna i wchodzi dopiero w `v2` jako fallback dla niejednoznacznych mapowań.

## Szybki start

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup_local.ps1
python .\scripts\build_dataset_index.py --config .\config\local.example.yaml
python .\scripts\run_local_pipeline.py --config .\config\local.example.yaml --company 8spzoo --year 2025
```

## Workflow wyjątków (v1.5)

```powershell
# Tryb krok po kroku (menu)
python -m autobilans.cli menu --config .\config\local.example.yaml
# Menu zawiera m.in.:
# - Run pipeline
# - Review/Suggest/Apply decisions
# - Show run status and result files + rekomendowane kolejne kroki
# - Onboard new company/year

# 1) Zbuduj lub odczytaj kolejkę wyjątków
python -m autobilans.cli review-exceptions --config .\config\local.example.yaml --company metro --year 2025 --limit 20

# 2) Wygeneruj propozycje decyzji (heurystyczne, bez zapisu reguł)
python -m autobilans.cli suggest-decisions --config .\config\local.example.yaml --company metro --year 2025

# 3) Sprawdź decyzje bez zapisu
python -m autobilans.cli apply-decisions --config .\config\local.example.yaml --company metro --year 2025 --decision-file .\outputs\runs\metro\2025\suggested_decisions.json --dry-run

# 4) Zastosuj decyzje i wykonaj automatyczny re-run + before/after
python -m autobilans.cli apply-decisions --config .\config\local.example.yaml --company metro --year 2025 --decision-file .\outputs\runs\metro\2025\suggested_decisions.json
```

Po każdym `run` powstaje także plik `bilans.xlsx` w katalogu `outputs/runs/<spolka>/<rok>/`.

## Struktura

- `config/` - lokalne pliki konfiguracyjne
- `docs/` - specyfikacje i plan wdrożenia
- `scripts/` - skrypty operatorskie
- `src/autobilans/` - kod aplikacji
- `tests/` - testy
- `outputs/` - wyniki uruchomień i artefakty

## Etapy

- `v1`: parsery, indeks danych, reguły mapowania, walidacja, eksport
- `v2`: mały lokalny model `3B-8B` jako fallback i warstwa uzasadnień
