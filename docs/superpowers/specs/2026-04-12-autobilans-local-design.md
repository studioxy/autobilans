# AutoBilans Local Design

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Zbudować lokalny system generujący bilans z plików ZOiS, weryfikowany względem historycznych XML, bez zależności od hostingu i bez dużego LLM w krytycznej ścieżce.

**Architecture:** System składa się z parserów wejściowych, indeksu danych, deterministycznego silnika mapowania, warstwy obliczeń Python oraz walidatora porównującego wynik z historycznym XML. W `v2` dołączamy mały model lokalny tylko jako fallback dla pozycji niejednoznacznych.

**Tech Stack:** Python 3.10+, openpyxl, pydantic, PyYAML, xlsxwriter, opcjonalnie Ollama/llama.cpp od `v2`.

---

## Kontekst danych

Repo zawiera dane per spółka i rok:

- `8spzoo/2021-2025`
- `metro/2022-2025`
- `oksan/2023-2025`
- `oksanbud/2022-2025`

W każdym roczniku występuje komplet:

- `zoisXXXX.xlsx`
- sprawozdanie `.xml`
- sprawozdanie `.pdf`

W plikach `ZOiS` z roku `2025` pojawia się kolumna `S_12_1`, która zawiera techniczne kody mapowania do pozycji bilansu. Te etykiety są lokalnie stabilne, ale nie obejmują pełnej historii i nie pokrywają wszystkich wierszy. Traktujemy je więc jako wiarygodny, lecz niepełny sygnał treningowy i walidacyjny.

## Decyzje architektoniczne

### 1. Rdzeń `v1` bez dużego LLM

Krytyczna ścieżka działania systemu nie może zależeć od modelu `32B/70B` na CPU. Zadanie bardziej przypomina kontrolowany proces ETL i klasyfikację wspartą historią niż swobodne rozumowanie generatywne. Dlatego `v1` opiera się o:

- parser ZOiS
- parser XML bilansu
- normalizację kont i pozycji
- reguły mapowania
- obliczenia wyłącznie w Pythonie
- walidację różnic

### 2. LLM dopiero w `v2`

Mały model lokalny `3B-8B`, najlepiej w kwantyzacji `Q4`, będzie używany wyłącznie do:

- propozycji mapowania dla pozycji bez reguły
- wyjaśnienia, dlaczego wybrał daną pozycję
- klasyfikacji wyjątków po nazwie konta lub kontrahenta

Model nie wykonuje obliczeń i nie ma prawa samodzielnie zatwierdzić wyniku końcowego.

### 3. XML jako źródło prawdy wyjściowej

XML nie daje prostego mapowania konto -> pozycja, ale daje poprawny wynik bilansu w strukturze pozycji aktywów i pasywów. To idealny materiał do testów regresji i porównania wyniku systemu z historycznie złożonym sprawozdaniem.

## Architektura logiczna

### Warstwa wejścia

- wykrywanie plików `xlsx/xml/pdf`
- budowa indeksu datasetów
- obsługa filtrów `company/year`

### Warstwa normalizacji

- parsowanie kont syntetycznych i analitycznych
- wydzielenie salda końcowego i znaku
- normalizacja nazw firm i kont
- ujednolicenie etykiet `S_12_1`

### Warstwa mapowania

Kolejność decyzji:

1. bezpośrednia etykieta `S_12_1`, jeśli istnieje
2. reguła historyczna dla identycznego konta
3. reguła po prefiksie konta
4. reguła po nazwie konta i typie salda
5. fallback do `v2` LLM
6. skierowanie do ręcznej decyzji

### Warstwa obliczeń

- sumowanie per kod pozycji bilansowej
- agregacja do sekcji aktywów/pasywów
- kontrola zgodności sekcji i całego bilansu

### Warstwa walidacji

- porównanie wyniku z pozycjami z XML
- raport braków, nadmiarów i rozjazdów kwotowych
- confidence score dla każdego mapowania

### Warstwa wyjścia

- wynikowy `xlsx`
- raport walidacyjny `json`
- raport operatorski `csv/xlsx`

## Minimalne wymagania sprzętowe

### `v1`

- CPU: Ryzen 5 3600 lub podobny
- RAM: 16-32 GB
- Dysk: SSD/NVMe, minimum 20 GB wolnej przestrzeni roboczej

### `v2`

- CPU: ten sam serwer jest wystarczający
- RAM:
  - `3B Q4`: komfortowo od 8 do 12 GB dla samego modelu
  - `7B-8B Q4`: komfortowo od 16 do 24 GB dla samego modelu

Przy dostępnych `64 GB RAM` nie ma potrzeby przechodzenia na model `32B+` na starcie.

## Struktura projektu

```text
config/
docs/
outputs/
scripts/
src/autobilans/
tests/
```

## Ryzyka i zabezpieczenia

### Ryzyko: niepełne etykiety

Mitigacja:

- `S_12_1` traktować jako priorytetową podpowiedź, nie absolutną prawdę dla wszystkich lat
- utrzymywać walidację wyniku z XML
- wymuszać tryb ręcznego zatwierdzenia dla niepewnych przypadków

### Ryzyko: konta syntetyczne i agregaty

Mitigacja:

- osobne reguły dla syntetyk
- unikanie podwójnego sumowania parent/child
- jawne rozdzielenie poziomu źródłowego i poziomu raportowego

### Ryzyko: przeszacowanie potrzeby LLM

Mitigacja:

- benchmark `v1` przed `v2`
- dopiero po realnych brakach dołączać mały model

## Zakres `v1`

- lokalny setup
- indeks danych
- parser `xlsx`
- parser `xml`
- reguły mapowania bez LLM
- obliczenia bilansu
- walidacja
- eksport do `xlsx` i `json`

## Zakres `v2`

- retrieval podobnych mapowań
- fallback LLM `3B-8B`
- panel kolejki wyjątków do ręcznej decyzji
- utrwalanie zaakceptowanych mapowań do bazy reguł
