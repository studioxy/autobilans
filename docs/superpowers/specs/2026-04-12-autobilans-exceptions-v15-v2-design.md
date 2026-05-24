# AutoBilans Exceptions `v1.5` / Assistant `v2`

**Goal:** Dodać do lokalnego systemu AutoBilans bezpieczny workflow obsługi wyjątków oraz mały lokalny model LLM jako warstwę sugestii, bez oddawania mu kontroli nad obliczeniami i końcową prawdą księgową.

**Status:** Spec implementacyjna dla kolejnego etapu po `v1`.

**Scope:** Dokument obejmuje:

- kolejkę wyjątków `v1.5`
- zapis decyzji operatorskich
- polityki reguł trwałych i rocznych
- wejścia i wyjścia dla małego modelu `v2`
- zasady bezpieczeństwa i walidacji

---

## Problem

Rdzeń `v1` działa poprawnie technicznie:

- parsery wejściowe są stabilne
- mapowanie historyczne działa
- obliczenia są wykonywane w Pythonie
- walidacja XML pokazuje rozjazdy

Pozostałe błędy nie wynikają już głównie z braku parsera albo z braku infrastruktury. Są to najczęściej:

- konta mieszane, które zasilają więcej niż jedną interpretację
- lokalne wyjątki dla konkretnej spółki
- konflikty aktywa vs pasywa dla podobnych kont
- przypadki wymagające decyzji księgowej, a nie tylko klasyfikacji technicznej

W tym miejscu sam system reguł daje coraz mniejszy zwrot. Potrzebny jest workflow, który:

- pokazuje wyjątki w czytelnej formie
- pozwala człowiekowi rozstrzygnąć przypadek
- zapisuje decyzję tak, aby system nie pytał drugi raz o to samo
- dopiero później korzysta z małego LLM jako warstwy sugestii

## Zasada nadrzędna

Model LLM nie jest źródłem prawdy.

Źródłami prawdy pozostają:

- dane wejściowe `ZOiS`
- reguły jawne
- obliczenia Python
- walidacja względem XML
- decyzja operatora w trybie wyjątków

LLM może:

- proponować
- uzasadniać
- klasyfikować
- wskazywać podobne przypadki

LLM nie może:

- samodzielnie zatwierdzać wyniku końcowego
- wykonywać matematyki
- zapisywać reguł bez decyzji operatora
- omijać walidacji XML

---

## Architektura Etapu `v1.5`

### 1. Exception Queue

Nowa warstwa po walidacji buduje kolejkę wyjątków.

Pojedynczy wyjątek to obiekt opisujący jedną nierozstrzygniętą sytuację, na przykład:

- pozycję bilansu z rozjazdem do XML
- nierozwiązane konto
- konto z konfliktem między kodem głównym i pomocniczym
- konto z niskim confidence

Proponowana struktura:

```json
{
  "id": "metro-2025-Pasywa_B_III_3_D_1",
  "company": "metro",
  "year": 2025,
  "kind": "validation_mismatch",
  "target_code": "Pasywa_B_III_3_D_1",
  "expected": 15493.2,
  "actual": 0.0,
  "delta": -15493.2,
  "candidate_source_codes": [
    "BABII3a_D12__NEG",
    "BPBIII3d_D12__NEG"
  ],
  "top_contributors": [
    {
      "account_no": "202-2-1-BARTON",
      "bucket_amount": 9225.0
    }
  ],
  "status": "open"
}
```

### 2. Exception Review CLI

W `v1.5` rekomendowany jest prosty interfejs CLI zamiast UI webowego.

Proponowane komendy:

- `python -m autobilans.cli build-exception-queue --company metro --year 2025`
- `python -m autobilans.cli review-exceptions --company metro --year 2025`
- `python -m autobilans.cli apply-decisions --company metro --year 2025`
- `python -m autobilans.cli rerun-after-decisions --company metro --year 2025`

CLI ma pokazywać jeden wyjątek naraz i udostępniać kilka bezpiecznych akcji:

- przypisz konto do konkretnej pozycji
- usuń konto z konkretnego kodu pomocniczego
- ogranicz regułę do spółki
- ogranicz regułę do roku
- oznacz jako precedens globalny
- zostaw do dalszej analizy

### 3. Decision Store

Potrzebne są trzy poziomy zapisu decyzji:

#### `config/manual_rules.yaml`

Dla prostych reguł:

- `konto -> pozycja`
- `konto -> kod bilansowy`

Zakres:

- `all`
- `company`
- `company + year`

#### `config/decision_policies.yaml`

Nowy plik dla reguł bardziej złożonych.

Przykłady:

- wyklucz konto z kodu pomocniczego
- uwzględniaj tylko bucket `__NEG`
- preferuj pozycję aktywów zamiast pasywów
- ignoruj wtórny kod dla wskazanego kontrahenta

Przykładowy kształt:

```yaml
decision_policies:
  metro:
    "2025":
      exclude_secondary_codes:
        "201-2-1-8510205610":
          - BPBIII3d_D12
      force_target_code:
        "260-2":
          balance_code: Aktywa_B_II_1_B
      prefer_bucket:
        "202-2-1-BARTON":
          code: BPBIII3d_D12
          bucket: NEG
```

#### `outputs/decisions/*.json`

To jest dziennik audytowy działań operatora:

- kto podjął decyzję
- kiedy
- dla jakiej spółki i roku
- jaka była treść wyjątku
- jaka została zatwierdzona reguła

---

## Dane wejściowe dla operatora

Każdy wyjątek powinien być budowany z istniejących artefaktów:

- `validation_report.csv/json`
- `gap_analysis.json`
- `mapping_report.csv/json`
- `calculated_balance.json`
- `code_contributions.csv/json`

Operator powinien widzieć:

1. kod pozycji bilansu
2. oczekiwaną wartość z XML
3. wartość obliczoną
4. różnicę
5. top wkłady do konfliktowego kodu
6. etykiety `S_12_1`, `S_12_2`, `S_12_3`
7. źródło obecnej decyzji:
   - label
   - history-company
   - history-global
   - manual-rule
   - unresolved

## Klasy wyjątków

Warto od razu wprowadzić typologię:

### `validation_mismatch`

Pozycja z XML nie zgadza się z wynikiem.

### `unresolved_account`

Konto bez przypisanego kodu.

### `secondary_code_conflict`

Konto ma dodatkowy kod (`S_12_2/S_12_3`), który prowadzi do konfliktu.

### `mixed_sign_account`

To samo konto albo grupa kont daje dodatnie i ujemne wkłady, które trafiają do różnych znaczeń biznesowych.

### `low_confidence`

Mapowanie pochodzi z fallbacku albo ma niski confidence.

---

## Architektura Etapu `v2`

### Rola modelu

Mały lokalny model działa tylko jako `exception assistant`.

Wejście do modelu:

- opis wyjątku
- konto lub grupa kont
- nazwa kontrahenta
- kwota i znak
- istniejące `S_12_1/S_12_2/S_12_3`
- podobne przypadki historyczne
- dostępne kandydaty docelowe

Wyjście modelu ma być ściśle strukturalne:

```json
{
  "suggested_action": "force_target_code",
  "suggested_target": "Pasywa_B_III_3_D_1",
  "suggested_scope": "company_year",
  "confidence": 0.82,
  "reason": "Konto reprezentuje zobowiązanie krótkoterminowe do 12 miesięcy i w danych historycznych podobne przypadki były rozstrzygane po stronie pasywów.",
  "requires_human_review": true
}
```

### Model

Rekomendacja:

- `3B-8B instruct`
- kwantyzacja `Q4`
- lokalnie przez `Ollama` albo `llama.cpp`

Nie rekomenduję większego modelu na tym etapie.

### Kiedy uruchamiać LLM

Tylko dla:

- `unresolved_account`
- `secondary_code_conflict`
- `mixed_sign_account`
- `validation_mismatch`, jeśli istnieje mały zbiór kandydatów

Nie uruchamiać dla:

- pozycji już rozstrzygniętych regułą twardą
- obliczeń
- oczywistych aliasów
- pełnego bilansu jako całości

### Confidence Policy

- `>= 0.90`
  szybka rekomendacja do zatwierdzenia
- `0.60 - 0.89`
  pokaż operatorowi jako propozycję
- `< 0.60`
  nie proponuj automatycznego rozstrzygnięcia, tylko pokaż analizę

---

## Zmiany w kodzie

### Nowe moduły

- `src/autobilans/exceptions/models.py`
- `src/autobilans/exceptions/builder.py`
- `src/autobilans/exceptions/review.py`
- `src/autobilans/exceptions/store.py`
- `src/autobilans/llm/assistant.py`
- `src/autobilans/llm/prompts.py`
- `src/autobilans/llm/schema.py`

### Nowe pliki konfiguracyjne

- `config/decision_policies.yaml`
- `config/llm.local.example.yaml`

### Rozszerzenia CLI

- `review-exceptions`
- `build-exception-queue`
- `apply-decisions`
- `suggest-exception-resolution`

### Rozszerzenia artefaktów wyjściowych

- `outputs/runs/<company>/<year>/exception_queue.json`
- `outputs/runs/<company>/<year>/decision_log.json`
- `outputs/runs/<company>/<year>/llm_suggestions.json`

---

## Zasady bezpieczeństwa

1. Każde rozstrzygnięcie musi zostawić ślad audytowy.
2. Decyzja operatora ma pierwszeństwo przed LLM.
3. Reguła globalna może zostać zapisana tylko po jawnym wyborze operatora.
4. Pipeline po zastosowaniu decyzji musi być uruchamiany ponownie.
5. XML walidacyjny nadal pozostaje kontrolą końcową.

## Kolejność wdrożenia

### Etap 1: `v1.5` bez LLM

1. builder kolejki wyjątków
2. modele wyjątków
3. CLI do przeglądu wyjątków
4. zapis decyzji i polityk
5. ponowny rerun po decyzjach

### Etap 2: `v2` z małym LLM

1. provider lokalny `ollama/llama.cpp`
2. prompt strukturalny
3. integracja z kolejką wyjątków
4. zapis sugestii obok decyzji operatora
5. benchmark jakości sugestii

## Kryteria sukcesu

### `v1.5`

- operator może zamknąć wyjątek bez ręcznej edycji YAML
- zatwierdzona decyzja jest pamiętana przy kolejnym uruchomieniu
- pipeline po powtórce pokazuje mniejszą liczbę rozjazdów

### `v2`

- model redukuje liczbę ręcznych decyzji
- model nie pogarsza wyniku końcowego
- każda sugestia ma confidence i uzasadnienie
- operator może ją łatwo zaakceptować albo odrzucić

---

## Rekomendacja końcowa

Najpierw implementować pełne `v1.5`, dopiero później `v2`.

Powód:

- największa wartość biznesowa jest dziś w zapamiętywaniu wyjątków
- to samo da najlepszy materiał treningowy i benchmark dla małego LLM
- bez tej warstwy LLM będzie tylko kolejnym źródłem niejawnych decyzji

Docelowo najlepszy układ to:

- `v1`: deterministyczny rdzeń
- `v1.5`: kolejka wyjątków + pamięć decyzji
- `v2`: mały LLM jako doradca dla wyjątków
