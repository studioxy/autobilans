# AutoBilans Local Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dostarczyć lokalnie działający fundament systemu AutoBilans dla `v1` oraz przygotować miejsce na `v2` z małym lokalnym LLM.

**Architecture:** Najpierw budujemy deterministyczny pipeline `index -> parse -> map -> calculate -> validate -> export`. Po uzyskaniu benchmarku jakości dokładamy `v2`, gdzie mały model lokalny działa wyłącznie jako fallback dla wyjątków.

**Tech Stack:** Python 3.10+, openpyxl, pydantic, PyYAML, xlsxwriter, pytest, opcjonalnie Ollama/llama.cpp od `v2`.

---

## Chunk 1: Foundation

### Task 1: Zbudować strukturę projektu

**Files:**
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `src/autobilans/__init__.py`
- Create: `src/autobilans/cli.py`
- Create: `config/local.example.yaml`
- Create: `scripts/setup_local.ps1`
- Test: `tests/test_smoke.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że `python -m autobilans.cli --help` uruchamia CLI bez błędu.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_smoke.py -v`

- [ ] **Step 3: Write minimal implementation**

Dodać pakiet, CLI i konfigurację lokalną.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_smoke.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: scaffold local autobilans project`

### Task 2: Zbudować indeks danych

**Files:**
- Create: `src/autobilans/dataset_index.py`
- Create: `scripts/build_dataset_index.py`
- Create: `outputs/.gitkeep`
- Test: `tests/test_dataset_index.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że indeks potrafi znaleźć `company/year/xlsx/xml/pdf`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dataset_index.py -v`

- [ ] **Step 3: Write minimal implementation**

Zaimplementować skanowanie katalogów i eksport indeksu do `outputs/index/datasets.json`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dataset_index.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add dataset indexing`

## Chunk 2: Parsing And Normalization

### Task 3: Dodać parser ZOiS

**Files:**
- Create: `src/autobilans/parsers/zois.py`
- Create: `src/autobilans/models.py`
- Test: `tests/test_zois_parser.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że parser czyta numer konta, nazwę, saldo końcowe i `S_12_1`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_zois_parser.py -v`

- [ ] **Step 3: Write minimal implementation**

Parsować pierwszy arkusz ZOiS i zwracać rekordy źródłowe.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_zois_parser.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add zois parser`

### Task 4: Dodać parser XML bilansu

**Files:**
- Create: `src/autobilans/parsers/bilans_xml.py`
- Test: `tests/test_bilans_xml_parser.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że parser zwraca pozycje bilansu z kwotą `A` i `B`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_bilans_xml_parser.py -v`

- [ ] **Step 3: Write minimal implementation**

Wydobyć pozycje aktywów i pasywów z nazw węzłów XML.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_bilans_xml_parser.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add bilans xml parser`

## Chunk 3: Mapping And Calculation

### Task 5: Zbudować reguły mapowania `v1`

**Files:**
- Create: `src/autobilans/mapping/rules.py`
- Create: `src/autobilans/mapping/service.py`
- Test: `tests/test_mapping_rules.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić kolejność decyzji: `S_12_1 -> reguła historyczna -> prefiks -> brak decyzji`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_mapping_rules.py -v`

- [ ] **Step 3: Write minimal implementation**

Zwracać wynik mapowania wraz z confidence i źródłem decyzji.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_mapping_rules.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add v1 mapping engine`

### Task 6: Zbudować kalkulator bilansu

**Files:**
- Create: `src/autobilans/calculation/balance.py`
- Test: `tests/test_balance_calculation.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić sumowanie per pozycja bilansowa i zgodność aktywa/pasywa.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_balance_calculation.py -v`

- [ ] **Step 3: Write minimal implementation**

Agregować kwoty po kodach bilansowych i sekcjach.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_balance_calculation.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add balance calculator`

## Chunk 4: Validation And Output

### Task 7: Dodać walidator wyniku względem XML

**Files:**
- Create: `src/autobilans/validation/compare.py`
- Test: `tests/test_validation_compare.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że walidator zgłasza różnice kwot i brakujące pozycje.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_validation_compare.py -v`

- [ ] **Step 3: Write minimal implementation**

Porównać wynik obliczeń z parserem XML i zwrócić raport.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_validation_compare.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add validation against xml`

### Task 8: Dodać eksport i runner lokalny

**Files:**
- Modify: `src/autobilans/cli.py`
- Create: `src/autobilans/exporters/xlsx.py`
- Create: `scripts/run_local_pipeline.py`
- Test: `tests/test_local_runner.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że runner przyjmuje `company/year` i tworzy katalog wyniku.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_local_runner.py -v`

- [ ] **Step 3: Write minimal implementation**

Połączyć indeks, parsery, mapowanie i eksport do jednego polecenia.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_local_runner.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: add local pipeline runner`

## Chunk 5: V2 Preparation

### Task 9: Przygotować interfejs fallback LLM

**Files:**
- Create: `src/autobilans/llm/contracts.py`
- Create: `src/autobilans/llm/fallback.py`
- Create: `tests/test_llm_contracts.py`

- [ ] **Step 1: Write the failing test**

Sprawdzić, że warstwa LLM jest opcjonalna i nie blokuje `v1`.

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_contracts.py -v`

- [ ] **Step 3: Write minimal implementation**

Zdefiniować interfejs `propose_mapping()` z możliwością podpięcia Ollama lub llama.cpp.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_contracts.py -v`

- [ ] **Step 5: Commit**

Commit: `feat: prepare llm fallback contract`

Plan complete and saved to `docs/superpowers/plans/2026-04-12-autobilans-local-v1-v2.md`. Ready to execute.
