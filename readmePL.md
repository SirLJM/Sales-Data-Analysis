# Stock Monitor 3

Kompleksowa aplikacja do zarządzania zapasami i analizy sprzedaży oparta na Streamlit, przeznaczona dla firm
handlowych i produkcyjnych. System wykorzystuje metody statystyczne do analizy historycznej sprzedaży, prognozowania
przyszłego popytu oraz optymalizacji decyzji zakupowych w celu maksymalizacji sprzedaży przy jednoczesnej minimalizacji
braków magazynowych i nadmiernych zapasów.

## Spis treści

- [Przegląd funkcji](#przegląd-funkcji)
- [Szybki start](#szybki-start)
- [Zakładki aplikacji](#zakładki-aplikacji)
- [Objaśnienie obliczeń statystycznych](#objaśnienie-obliczeń-statystycznych)
- [Algorytm optymalizacji wzorców](#algorytm-optymalizacji-wzorców)
- [System punktacji priorytetów](#system-punktacji-priorytetów)
- [Parametry konfiguracyjne](#parametry-konfiguracyjne)
- [Wymagania dotyczące danych](#wymagania-dotyczące-danych)
- [Architektura](#architektura)
- [Przewodnik biznesowy](#przewodnik-biznesowy)

---

## Przegląd funkcji

| Funkcja                           | Opis                                                                          |
|-----------------------------------|-------------------------------------------------------------------------------|
| **Analiza sprzedaży**             | Analiza statystyczna z obliczeniami Zapasu Bezpieczeństwa i Punktu Zamówienia |
| **Projekcja stanów**              | Wizualizacja momentu osiągnięcia krytycznych poziomów zapasów                 |
| **Optymalizator wzorców**         | Optymalizacja wzorców cięcia z automatycznym ładowaniem historii sprzedaży    |
| **Rekomendacje zamówień**         | Zamawianie priorytetowe z filtrami zakładów i filtrami aktywnych zamówień     |
| **Analiza tygodniowa**            | Porównanie sprzedaży tydzień do tygodnia i trendy                             |
| **Analiza miesięczna**            | Wydajność kategorii rok do roku                                               |
| **Tworzenie zamówień**            | Przekształcanie rekomendacji w zamówienia produkcyjne z ręcznym wprowadzaniem |
| **Śledzenie zamówień**            | Śledzenie i zarządzanie zamówieniami z odliczaniem do dostawy                 |
| **Dokładność prognozy**           | Monitoring jakości prognozy vs rzeczywista sprzedaż                           |
| **Porównanie prognoz**            | Generowanie wewnętrznych prognoz i porównanie z zewnętrznymi                  |
| **Prognoza ML**                   | Prognozy uczenia maszynowego z auto-selekcją modelu per jednostka             |
| **Zapytania w języku naturalnym** | Zapytania do danych w języku naturalnym (polski lub angielski)                |

---

## Szybki start

### Wymagania wstępne

- Python 3.13 (zarządzany automatycznie przez uv)
- Zainstalowane [`uv`](https://docs.astral.sh/uv/)

### Instalacja

```bash
# Sklonuj lub przejdź do katalogu projektu
cd stockMonitor3/src

# Zainstaluj zależności (tworzy .venv i instaluje z uv.lock)
uv sync
```

uv czyta `pyproject.toml` + `uv.lock` i tworzy powtarzalne środowisko. Nie trzeba ręcznie aktywować venv — komendy uruchamiaj z prefiksem `uv run` (np. `uv run streamlit run app.py`).

### Konfiguracja

1. **Tryb plikowy** (domyślny):
   ```bash
   # Skopiuj i skonfiguruj plik ścieżek
   cp src/sales_data/paths_to_files.txt.example src/sales_data/paths_to_files.txt
   # Edytuj paths_to_files.txt z katalogami swoich danych
   ```

2. **Tryb bazodanowy** (opcjonalny):
   ```bash
   # Utwórz plik .env
   cp .env.example .env
   # Edytuj .env z połączeniem do bazy danych
   # DATA_SOURCE_MODE=database
   # DATABASE_URL=postgresql://user:password@localhost:5432/inventory_db
   ```

### Uruchomienie aplikacji

```bash
cd src
py -V:3.13 -m streamlit run app.py
```

Aplikacja otwiera się pod adresem `http://localhost:8501`

---

## Zakładki aplikacji

### Zakładka 1: Analiza sprzedaży i zapasów

Główny pulpit analityczny zapewniający kompleksowy wgląd w zapasy.

**Funkcje:**

- Widoki danych na poziomie SKU lub Modelu (przełącznik w panelu bocznym)
- Filtrowanie: wyszukiwanie, poniżej ROP, bestsellery, typ produktu, nadstan
- Obliczenia Zapasu Bezpieczeństwa (SS) i Punktu Zamówienia (ROP)
- Wykresy projekcji stanów pokazujące moment osiągnięcia krytycznych poziomów
- Możliwość eksportu do CSV

**Objaśnienie kluczowych kolumn:**
| Kolumna | Opis |
|---------|------|
| `MONTHS` | Liczba miesięcy z historią sprzedaży |
| `QUANTITY` | Łączna sprzedana ilość (od początku) |
| `AVERAGE SALES` | Średnia miesięczna sprzedaż |
| `SD` | Odchylenie standardowe miesięcznej sprzedaży |
| `CV` | Współczynnik Zmienności (SD / Średnia) - mierzy zmienność popytu |
| `TYPE` | Klasyfikacja produktu: nowy, podstawowy, sezonowy lub regularny |
| `SS` | Zapas Bezpieczeństwa — bufor zapobiegający brakom |
| `ROP` | Punkt Zamówienia — poziom zapasu uruchamiający nowe zamówienie |
| `STOCK` | Aktualny poziom zapasów |
| `FORECAST_LEADTIME` | Prognozowany popyt w okresie lead time |

**Wykres projekcji stanów:**
Wprowadź kod SKU lub Modelu, aby zwizualizować przewidywany spadek zapasów w czasie. Wykres pokazuje:

- Aktualną trajektorię zapasów na podstawie prognozowanego popytu
- Linię progu ROP
- Daty osiągnięcia ROP i zera

---

### Zakładka 2: Optymalizator wzorców rozmiarowych

Samodzielne narzędzie do optymalizacji wzorców cięcia w produkcji.

**Pojęcia:**

- **Zestaw wzorców**: Zbiór wzorców cięcia (np. "Dorośli", "Dzieci")
- **Wzorzec**: Konkretna kombinacja rozmiarów do wspólnego cięcia (np. "L + XL")
- **Minimalne zamówienie**: Minimalna ilość na wzorzec dla opłacalności

**Przepływ pracy:**

1. Utwórz/wybierz zestaw wzorców
2. Zdefiniuj dostępne rozmiary (XL, L, M, S, XS itp.)
3. Zdefiniuj wzorce cięcia z kombinacjami rozmiarów
4. Wprowadź żądane ilości według rozmiaru LUB załaduj automatycznie z historii sprzedaży
5. Uruchom optymalizację, aby uzyskać alokację wzorców

**Automatyczne ładowanie historii sprzedaży:**

Zamiast ręcznego wprowadzania ilości rozmiarów, możesz załadować dane historyczne:

1. Wprowadź kod modelu (np. "CH031") w polu "Model"
2. Kliknij przycisk "Załaduj"
3. System automatycznie agreguje ostatnie 4 miesiące sprzedaży według rozmiaru dla wszystkich kolorów modelu
4. Ilości rozmiarów są wypełniane w polach wejściowych

**Wynik:**

- Które wzorce zamówić i ile
- Łączna produkcja na rozmiar
- Nadprodukcja
- Naruszenia minimalnego zamówienia

---

### Zakładka 3: Analiza tygodniowa

Trendy sprzedaży tydzień do tygodnia i wydajność produktów.

**Funkcje:**

- **Wschodzące gwiazdy**: Produkty z rosnącą sprzedażą vs ten sam tydzień rok temu
- **Spadające gwiazdy**: Produkty ze spadającą sprzedażą
- **Monitor nowych produktów**: Śledzenie sprzedaży produktów wprowadzonych w ostatnich 60 dniach

**Obliczenie:**

```
Zmiana procentowa = ((Bieżący tydzień - Ten sam tydzień rok temu) / Ten sam tydzień rok temu) * 100
```

Przypadki specjalne:

- Brak sprzedaży rok temu, sprzedaż teraz: +999% (nowy gracz)
- Sprzedaż rok temu, brak teraz: -100% (przestał się sprzedawać)

---

### Zakładka 4: Analiza miesięczna

Porównanie wydajności kategorii rok do roku.

**Funkcje:**

- Porównanie sprzedaży według kategorii (Podgrupa) i podkategorii (Kategoria)
- Automatycznie wyklucza bieżący niepełny miesiąc
- Identyfikacja rosnących/spadających kategorii
- Eksport CSV z porównaniem okresów

---

### Zakładka 5: Rekomendacje zamówień

**Najważniejsza funkcja** — Automatyczny system zamawiania priorytetowego.

**Wymagania:**

- Dane o stanach muszą być załadowane
- Dane prognozowe muszą być załadowane

**Jak to działa:**

1. Analizuje wszystkie SKU uwzględniając aktualny stan, ROP, prognozowany popyt i typ produktu
2. Oblicza wynik priorytetu dla każdej pozycji
3. Agreguje według MODEL+KOLOR do zamawiania
4. Automatycznie odfiltrowuje modele z aktywnymi zamówieniami
5. Pokazuje top N rekomendacji z rozbiciem na rozmiary

**Filtry zakładów:**

- **Uwzględnij zakłady**: Pokaż tylko pozycje z wybranych zakładów produkcyjnych
- **Wyklucz zakłady**: Ukryj pozycje z wybranych zakładów (ma pierwszeństwo przed uwzględnieniem)
- Filtry używają metadanych modelu (SZWALNIA GŁÓWNA) do dopasowania zakładu

**Tabela wyników:**
| Kolumna | Opis |
|---------|------|
| Model | 5-znakowy kod modelu |
| Kolor | 2-znakowy kod koloru |
| Nazwa koloru | Czytelna nazwa koloru z aliasów |
| Priorytet | Obliczony wynik priorytetu (wyższy = pilniejszy) |
| Deficyt | Ile poniżej ROP |
| Prognoza | Prognozowany popyt w okresie lead time |
| Rozmiary | Rozbicie na rozmiary (np. "08:15, 12:25, 13:30") |
| Szwalnia | Zakład produkcyjny (jeśli dostępne metadane) |

**Filtrowanie aktywnych zamówień:**

Pozycje są automatycznie wykluczane z rekomendacji, jeśli mają aktywne zamówienie w zakładce Śledzenie zamówień.
Zapobiega to podwójnemu zamawianiu.

---

### Zakładka 6: Tworzenie zamówień

Przekształcanie rekomendacji w realizowalne zamówienia produkcyjne.

**Dwie metody wprowadzania:**

1. **Z rekomendacji**: Zaznacz pozycje w zakładce 5 używając checkboxów, następnie przejdź do tej zakładki
2. **Ręczne wprowadzanie**: Wprowadź dowolny kod modelu bezpośrednio w sekcji "Ręczne tworzenie zamówienia"

**Przepływ pracy:**

1. Wprowadź kod modelu ręcznie LUB wybierz pozycje z zakładki 5
2. Kliknij "Utwórz zamówienie"
3. System automatycznie:
    - Ładuje zestaw wzorców pasujący do nazwy modelu
    - Wyświetla metadane produkcyjne (zakład, materiał, gramatura)
    - Uwzględnia wszystkie pilne kolory dla modelu
    - Uruchamia optymalizację wzorców dla każdego koloru
    - Pokazuje ostatnie 4 miesiące historii sprzedaży

**Podsumowanie zamówienia zawiera:**

- Alokację wzorców (np. "Dorośli: 2, Dzieci: 3")
- Łączne wzorce i nadprodukcję
- Wartości stanu, SS, ROP, prognozy, deficytu, luki pokrycia
- Miesięczną historię sprzedaży (ostatnie 4 miesiące)
- Rozbicie na rozmiary z aliasami (np. "XS: 10, S: 15, M: 20")

**Tabela produkcji Rozmiar × Kolor:**

Wizualna macierz pokazująca alokacje wzorców dla wszystkich kolorów modelu, z rozmiarami w wierszach i kolorami w
kolumnach.

**Akcje:**

- **Zapisz do bazy danych**: Przechowuje zamówienie z pełnymi danymi JSON
- **Pobierz CSV**: Eksportuje podsumowanie zamówienia jako plik CSV
- **Anuluj**: Czyści wybory i zaczyna od nowa

---

### Zakładka 7: Śledzenie zamówień

Śledzenie i zarządzanie utworzonymi zamówieniami produkcyjnymi z odliczaniem do dostawy.

**Funkcje:**

- **Ręczne wprowadzanie zamówienia**: Dodawaj zamówienia bezpośrednio przez wprowadzenie kodu modelu i daty
- **Lista aktywnych zamówień**: Przeglądaj wszystkie zamówienia ze statusem i liczbą dni od złożenia
- **Odliczanie do dostawy**: Pokazuje dni do oczekiwanej dostawy (domyślny próg: 41 dni)
- **Funkcja archiwizacji**: Przenieś zrealizowane zamówienia do archiwum

**Wskaźniki statusu zamówienia:**

- **Gotowe do dostawy**: Zamówienie przekroczyło próg dni dostawy
- **X dni pozostało**: Odliczanie do oczekiwanej dostawy

**Kolumny tabeli:**
| Kolumna | Opis |
|---------|------|
| ID zamówienia | Unikalny identyfikator zamówienia (ORD_MODEL_TIMESTAMP) |
| Model | 5-znakowy kod modelu |
| Data zamówienia | Kiedy zamówienie zostało złożone |
| Dni od złożenia | Dni od złożenia zamówienia |
| Status | Status dostawy z odliczaniem |
| Archiwum | Checkbox do archiwizacji zrealizowanych zamówień |

**Przepływ pracy:**

1. Zamówienia pojawiają się automatycznie po zapisaniu z zakładki 6
2. Śledź postęp dostawy przez liczbę dni
3. Gdy zamówienie nadejdzie (>= dni progowe), status pokazuje "Gotowe do dostawy"
4. Archiwizuj zamówienia, aby usunąć z listy aktywnych

---

### Zakładka 8: Dokładność prognozy

**Cel:** Pomiar dokładności zewnętrznej prognozy w porównaniu z rzeczywistą sprzedażą. Odpowiada na pytanie:
*"Jak dobra była nasza prognoza?"*

**Kiedy używać:**

- Miesięczny przegląd jakości prognozy
- Po zakończeniu sezonu do oceny dokładności przewidywań
- Przy badaniu przyczyn braków magazynowych lub nadstanów

**Kluczowa koncepcja:**
Ta zakładka patrzy **wstecz w czasie**. Porównuje **przeszłą prognozę** z **faktyczną sprzedażą, która już się odbyła**.
Mierzysz historyczną dokładność, nie przewidujesz przyszłości.

#### Przepływ pracy krok po kroku

1. **Ustaw okres analizy** (zakres czasu do oceny):
    - Przykład: Jeśli dziś jest 15 stycznia 2025, możesz analizować 1 października - 31 grudnia 2024
    - To okres, w którym porównasz prognozę z rzeczywistą sprzedażą
    - Minimum zalecane: co najmniej 30 dni dla znaczących wyników

2. **Ustaw przesunięcie prognozy** (jak daleko wstecz szukać pliku prognozy):
    - Domyślnie: 4 miesiące przed rozpoczęciem analizy
    - System szuka pliku prognozy wygenerowanego przed okresem analizy
    - Przykład: Dla analizy od 1 października szuka prognozy z ~czerwca 2024
    - Symuluje to warunki rzeczywiste, gdzie prognozy tworzy się miesiące wcześniej

3. **Wybierz poziom widoku**:
    - **SKU**: Szczegółowa analiza każdego wariantu rozmiar/kolor
    - **Model**: Zagregowana analiza na poziomie rodziny produktów (zalecana dla przeglądu)

4. **Kliknij "Generuj raport dokładności"**

#### Zrozumienie wyników

**Metryki ogólne (góra strony):**

| Metryka             | Co oznacza                                         | Cel            |
|---------------------|----------------------------------------------------|----------------|
| MAPE                | Średni błąd jako procent                           | < 20% = Dobrze |
| BIAS                | Dodatni = za wysoka prognoza, Ujemny = za niska    | Blisko 0%      |
| Utracone szanse     | Jednostki, które mogły się sprzedać podczas braków | Minimalizować  |
| Dokładność wolumenu | Łączna prognoza vs łączna rzeczywistość            | Blisko 100%    |

**Wskaźniki kolorowe:**

- 🟢 Zielony (MAPE < 20%): Doskonale — prognoza jest wiarygodna
- 🟡 Żółty (MAPE 20—40%): Akceptowalne — jest miejsce na poprawę
- 🔴 Czerwony (MAPE > 40%): Słabo — zbadaj przyczynę

**Wykres dokładności według typu produktu:**
Pokazuje, które kategorie produktów prognozują dobrze vs słabo. Typowe wzorce:

- Produkty podstawowe zwykle mają najniższy MAPE (stabilny popyt)
- Nowe produkty często mają najwyższy MAPE (ograniczona historia)
- Produkty sezonowe różnią się w zależności od timingu

**Wykres trendu:**
Pokazuje jak dokładność zmieniała się w czasie podczas okresu analizy. Szukaj:

- Stale niski MAPE = wiarygodne prognozowanie
- Skoki = zbadaj konkretne tygodnie/wydarzenia
- Trend poprawy = proces prognozowania się poprawia

**Tabela szczegółowa:**
Kliknij dowolny SKU/Model, aby zobaczyć:

- Rzeczywistą sprzedaż vs prognozę per okres
- Kiedy wystąpiły braki
- Rozbicie MAPE według tygodnia/miesiąca

#### Praktyczny przykład

*Scenariusz: Przegląd Q4 2024 (paź – gru)*

1. Ustaw początek analizy: 1 października 2024
2. Ustaw koniec analizy: 31 grudnia 2024
3. Przesunięcie: 4 miesiące (znajduje prognozę z ~czerwca 2024)
4. Wygeneruj raport

*Interpretacja wyników:*

- Ogólny MAPE: 28% → Akceptowalny, ale może być lepiej
- BIAS: +15% → Stale za wysoka prognoza (zamówiono za dużo)
- Produkty podstawowe: 18% MAPE → Dobrze
- Produkty sezonowe: 45% MAPE → Słabo (niedoszacowany skok świąteczny)

*Działanie: Dostosuj Z-scores sezonowe i przejrzyj parametry wykrywania sezonowości*

---

### Zakładka 9: Porównanie prognoz

**Cel:** Generowanie własnych prognoz statystycznych i porównanie ich z zewnętrznymi/dostawcy prognozami. Odpowiada:
*"Czy moglibyśmy prognozować lepiej wewnętrznie?"*

**Kiedy używać:**

- Ocena czy zmienić dostawcę prognoz
- Testowanie czy modele wewnętrzne przewyższają prognozy dostawcy
- Budowanie historycznego zapisu eksperymentów prognozowania
- Identyfikacja, które typy produktów najlepiej działają, z którymi metodami

**Kluczowa koncepcja:**
Ta zakładka generuje **nowe prognozy patrząc w przyszłość**, następnie porównuje je z zewnętrznymi prognozami.
Używa metod statystycznych (Średnia Ruchoma, Wygładzanie Wykładnicze, Holt-Winters, SARIMA) automatycznie
wybieranych na podstawie typu produktu.

#### Dwie pod-zakładki

**1. Generuj nowe** — Twórz świeże wewnętrzne prognozy
**2. Historyczne prognozy** — Przeglądaj wcześniej zapisane eksperymenty prognozowania

---

#### Zakładka Generuj nowe: Krok po kroku

1. **Ustaw horyzont prognozy**:
    - Ile miesięcy do przodu prognozować (1–12)
    - Domyślnie: odpowiada ustawieniu lead time
    - Zalecenie: Dopasuj do typowego horyzontu planowania (np. 2–3 miesiące)

2. **Wybierz poziom jednostki**:
    - **Model** (zalecany): Szybsze, bardziej stabilne wyniki, agreguje według rodziny produktów
    - **SKU**: Szczegółowe, ale wolniejsze, może mieć rzadkie dane dla pozycji nisko-wolumenowych

3. **Ustaw Top N**:
    - Ogranicz analizę do top N jednostek według wolumenu sprzedaży
    - Zalecenie: Zacznij od 50 do 100 dla szybkiej analizy, zwiększ dla kompleksowego przeglądu
    - Pełna analiza wszystkich pozycji może zająć kilka minut

4. **Kliknij "Generuj porównanie"**

#### Zrozumienie wyników porównania

**Pole podsumowania ogólnego:**

```
Wygrane wewnętrzne: 45 (45%)
Wygrane zewnętrzne: 38 (38%)
Remisy: 17 (17%)
```

Wyższy % wygranych wewnętrznych sugeruje, że twoje modele statystyczne przewyższają prognozę dostawcy.

**Tabela rozbicia według typu produktu:**

| Typ        | Łącznie | Wygrane wewn. | Wygrane zewn. | % wewn. | Śr. MAPE wewn. | Śr. MAPE zewn. |
|------------|---------|---------------|---------------|---------|----------------|----------------|
| podstawowy | 30      | 20            | 8             | 67%     | 15%            | 22%            |
| regularny  | 40      | 18            | 18            | 45%     | 25%            | 26%            |
| sezonowy   | 20      | 5             | 12            | 25%     | 38%            | 28%            |
| nowy       | 10      | 2             | 0             | 20%     | 45%            | 52%            |

*Interpretacja: Modele wewnętrzne świetne dla produktów podstawowych, ale mają trudności z sezonowymi.*

**Szczegółowa tabela porównania:**
Każdy wiersz pokazuje jedną jednostkę (SKU lub Model) z:

- Wewnętrzny MAPE vs Zewnętrzny MAPE
- Wskaźnik zwycięzcy
- % poprawy (o ile lepszy był zwycięzca)
- Użyte metody (jaka metoda statystyczna została zastosowana)

**Wykres porównania:**
Wybierz dowolną jednostkę, aby zobaczyć wizualne porównanie:

- Szara linia: Faktyczna historyczna sprzedaż
- Niebieska linia: Prognoza wewnętrzna
- Czerwona linia: Prognoza zewnętrzna
- Zacieniowany obszar: Okres prognozy

#### Zapisywanie prognoz do historii

Po wygenerowaniu możesz zapisać wyniki do przyszłego odniesienia:

1. Dodaj opcjonalne notatki (np. "Q1 2025 baseline", "Po dostrojeniu parametrów")
2. Kliknij "Zapisz prognozę do historii"
3. Zapisane prognozy zawierają:
    - Wszystkie wygenerowane wartości prognozy
    - Użyte parametry
    - Metryki porównania
    - Znacznik czasu

**Dlaczego zapisywać?**

- Śledzenie poprawy w czasie
- Porównanie przed/po zmianach parametrów
- Budowanie dowodów do decyzji o dostawcy prognoz
- Ślad audytowy eksperymentów prognozowania

---

#### Zakładka Historyczne prognozy: Krok po kroku

1. **Wybierz zapisaną prognozę** z listy rozwijanej (sortowane według daty, najnowsze pierwsze)

2. **Przejrzyj informacje o partii:**
    - Data/czas wygenerowania
    - Typ jednostki (SKU/Model)
    - Horyzont prognozy
    - Liczba sukcesów/niepowodzeń
    - Rozbicie użytych metod

3. **Kliknij "Załaduj i porównaj"** aby przeliczyć metryki względem aktualnych rzeczywistych danych

4. **Lub "Usuń"** aby usunąć historyczną prognozę

**Dlaczego przeładować?**
W miarę dostępności większej ilości rzeczywistych danych sprzedażowych możesz przeliczyć dokładność starych prognoz,
aby zobaczyć prawdziwą wydajność.

---

#### Objaśnienie metod prognozowania

System automatycznie wybiera najlepszą metodę dla każdej jednostki:

| Metoda                      | Kiedy używana                       | Jak działa                         | Najlepsza dla                   |
|-----------------------------|-------------------------------------|------------------------------------|---------------------------------|
| **Średnia Ruchoma**         | Nowe produkty (< 6 mies. historii)  | Ważona średnia ostatniej sprzedaży | Sytuacje z ograniczonymi danymi |
| **Wygładzanie Wykładnicze** | Produkty podstawowe (CV < 0.6)      | Śledzenie trendu z wygaszaniem     | Stabilne, trendowe produkty     |
| **Holt-Winters**            | Produkty regularne (0.6 ≤ CV ≤ 1.0) | Trend + sezonowość                 | Produkty z wyraźnymi wzorcami   |
| **SARIMA**                  | Produkty sezonowe (CV > 1.0)        | Pełny sezonowy model ARIMA         | Złożone wzorce sezonowe         |

*Zachowanie awaryjne: Jeśli złożona metoda zawiedzie (niewystarczające dane), system automatycznie próbuje
prostszych metod.*

---

#### Praktyczne przykłady

**Przykład 1: Kwartalna ocena dostawcy**

*Cel: Czy powinniśmy odnowić umowę z dostawcą prognoz?*

1. Generuj nowe → Poziom Model → Top 200 → Horyzont: 3 miesiące
2. Przejrzyj podsumowanie ogólne: Wygrane wewnętrzne 55%, Wygrane zewnętrzne 35%
3. Sprawdź według typu produktu: Wewnętrzne dużo lepsze dla podstawowych/regularnych
4. Zapisz z notatką: "Q4 2024 ocena dostawcy"
5. Decyzja: Rozważ przeniesienie prognozowania wewnętrznie dla stabilnych produktów

**Przykład 2: Przed/po dostrojeniu parametrów**

*Cel: Czy dostosowanie Z-scores sezonowych poprawiło prognozowanie?*

1. Przed zmianami: Zapisz prognozę z notatką "Przed dostrojeniem sezonowym"
2. Dostosuj parametry w panelu bocznym
3. Po zmianach: Wygeneruj nowe porównanie
4. Zapisz z notatką "Po dostrojeniu sezonowym"
5. Załaduj obie z historii i porównaj współczynniki wygranych

**Przykład 3: Analiza wydajności metod**

*Cel: Która metoda prognozowania działa najlepiej dla naszego asortymentu?*

1. Wygeneruj porównanie na poziomie Model → Top 500
2. Eksportuj szczegółową tabelę do CSV
3. Analizuj zewnętrznie: Grupuj według kolumny "Użyta metoda"
4. Znajdź: SARIMA ma najniższy MAPE dla pozycji sezonowych, Średnia Ruchoma ma trudności
5. Działanie: Zbadaj, dlaczego niektóre jednostki wracają do prostszych metod

---

#### Kluczowe różnice: Zakładka 8 vs Zakładka 9

| Aspekt                   | Zakładka 8: Dokładność prognozy             | Zakładka 9: Porównanie prognoz         |
|--------------------------|---------------------------------------------|----------------------------------------|
| **Kierunek**             | Patrzy wstecz                               | Patrzy do przodu                       |
| **Cel**                  | Pomiar przeszłej wydajności                 | Generowanie nowych prognoz             |
| **Porównuje**            | Zewnętrzną prognozę vs rzeczywistą sprzedaż | Wewnętrzną vs zewnętrzną prognozę      |
| **Odpowiada na pytanie** | "Jak dokładna była nasza prognoza?"         | "Czy moglibyśmy prognozować lepiej?"   |
| **Wynik**                | Metryki dokładności (MAPE, BIAS)            | Analiza zwycięzców + zapisane prognozy |
| **Typowe użycie**        | Przegląd miesięczny/kwartalny               | Ocena dostawcy, testowanie metod       |

---

### Zakładka 10: Prognoza ML

**Cel:** Trenowanie modeli uczenia maszynowego do generowania prognoz z automatyczną selekcją modelu per SKU/Model.
Używa walidacji krzyżowej do wyboru najlepszego modelu dla każdej jednostki.

**Kiedy używać:**

- Gdy masz wystarczającą historię danych (zalecane 12+ miesięcy)
- Do porównania prognoz ML z prognozami statystycznymi lub zewnętrznymi
- Do wykorzystania zaawansowanej inżynierii cech dla lepszych przewidywań
- Gdy wzorce popytu mogą być uchwycone przez cechy opóźnione i statystyki kroczące

**Kluczowa koncepcja:**
Ta zakładka trenuje wiele modeli ML (LightGBM, RandomForest, Ridge, Lasso) plus opcjonalne modele statystyczne
(SARIMA, Holt-Winters, Wygładzanie Wykładnicze) dla każdej jednostki i wybiera najlepszego wykonawcę przez
walidację krzyżową szeregów czasowych.

#### Trzy pod-zakładki

**1. Trenuj modele** — Trenuj i wybierz najlepsze modele per jednostka
**2. Generuj prognozy** — Użyj wytrenowanych modeli do generowania przewidywań
**3. Zarządzaj modelami** — Przeglądaj, porównuj i usuwaj zapisane modele

---

#### Zakładka Trenuj modele: Krok po kroku

1. **Wybierz poziom jednostki**:
    - **Model** (zalecany): Szybsze trenowanie, bardziej stabilne wyniki
    - **SKU**: Szczegółowe, ale wymaga więcej danych per jednostka

2. **Ustaw Top N**:
    - Ogranicz trenowanie do top N jednostek według wolumenu sprzedaży
    - Zacznij od 50 do 100 do testowania, zwiększ do użytku produkcyjnego

3. **Wybierz modele do trenowania**:
    - **LightGBM**: Gradient boosting, dobrze radzi sobie ze złożonymi wzorcami
    - **RandomForest**: Metoda zespołowa, odporna na wartości odstające
    - **Ridge/Lasso**: Regularyzowane modele liniowe, szybkie trenowanie
    - **Statystyczne**: Obejmuje SARIMA, Holt-Winters, ETS (opcjonalne)

4. **Skonfiguruj walidację krzyżową**:
    - **Podziały CV**: Liczba podziałów szeregów czasowych (domyślnie: 3)
    - **Rozmiar testu**: Miesiące na fold testowy (domyślnie: 3)
    - **Metryka**: MAPE (domyślnie) lub MAE/RMSE

5. **Kliknij "Trenuj modele"**

#### Inżynieria cech

System automatycznie tworzy cechy dla modeli ML:

| Typ cechy               | Opis                                                         |
|-------------------------|--------------------------------------------------------------|
| **Cechy czasowe**       | Miesiąc, kwartał, dzień tygodnia, koniec miesiąca            |
| **Cechy opóźnione**     | Sprzedaż z 1, 2, 3, 6, 12 miesięcy temu                      |
| **Statystyki kroczące** | 3-miesięczne i 6-miesięczne średnie ruchome i odchylenia std |
| **Cechy YoY**           | Zmiana i stosunek rok do roku                                |
| **Info o produkcie**    | Kodowanie typu produktu (podstawowy, sezonowy, itp.)         |

#### Zrozumienie wyników trenowania

**Postęp trenowania:**

- Pokazuje postęp jednostka po jednostce
- Wyświetla najlepszy model wybrany dla każdej jednostki
- Raportuje wynik CV (MAPE) dla zwycięskiego modelu

**Podsumowanie trenowania:**

- Łączna liczba wytrenowanych jednostek
- Rozkład modeli (ile wybrało każdy typ modelu)
- Średni CV MAPE dla wszystkich jednostek
- Czas trenowania

**Przechowywanie modeli:**

- Modele zapisywane w katalogu `data/ml_models/`
- Każdy model zawiera metadane (wynik CV, użyte cechy, data trenowania)
- Modele zachowywane między sesjami

---

#### Zakładka Generuj prognozy: Krok po kroku

1. **Wybierz wytrenowane modele**:
    - System pokazuje dostępne wytrenowane modele
    - Wybierz jednostki do prognozowania (lub wszystkie)

2. **Ustaw horyzont prognozy**:
    - Miesiące do przodu do przewidywania (domyślnie: odpowiada lead time)
    - Maksimum: 12 miesięcy

3. **Kliknij "Generuj prognozy"**

#### Wynik prognozy

**Tabela prognozy:**
| Kolumna | Opis |
|---------|------|
| Jednostka | Kod SKU lub Model |
| Miesiąc prognozy | Docelowy miesiąc przewidywania |
| Prognozowana ilość | Przewidywanie modelu |
| Dolna granica | Dolna granica 95% przedziału ufności |
| Górna granica | Górna granica 95% przedziału ufności |
| Użyty model | Który model ML dokonał przewidywania |

**Przedziały przewidywania:**

- Oparte na residuach walidacji krzyżowej
- Domyślnie poziom ufności 95% (konfigurowalny w ustawieniach)

---

#### Zakładka Zarządzaj modelami: Krok po kroku

1. **Przeglądaj zapisane modele**:
    - Lista wszystkich wytrenowanych modeli z metadanymi
    - Data trenowania, wynik CV, użyte cechy

2. **Statystyki modeli**:
    - Rozkład według typu modelu
    - Średnie metryki wydajności
    - Wiek modeli (dni od trenowania)

3. **Usuń modele**:
    - Usuń przestarzałe lub słabo działające modele
    - Wyczyść wszystkie modele, aby trenować od zera

---

#### Integracja z rekomendacjami zamówień

Prognozy ML mogą być używane w zakładce 5 (Rekomendacje zamówień):

1. Wytrenuj modele w zakładce 10
2. Idź do zakładki 5: Rekomendacje zamówień
3. Wybierz "ML" jako źródło prognozy (dropdown pokazuje liczbę dostępnych modeli)
4. Generuj rekomendacje używając przewidywań ML

**Zachowanie awaryjne:**

- Jeśli model ML niedostępny dla jednostki, wraca do zewnętrznej prognozy
- Mieszane źródła są wyraźnie wskazane w wyniku

---

#### Objaśnienie modeli ML

| Model            | Mocne strony                         | Najlepszy dla                        |
|------------------|--------------------------------------|--------------------------------------|
| **LightGBM**     | Szybki, radzi sobie z nieliniowością | Złożone wzorce, duże dane            |
| **RandomForest** | Odporny, ważność cech                | Ogólne użycie, odporność na outliers |
| **Ridge**        | Szybki, interpretowalny              | Liniowe trendy, szybka linia bazowa  |
| **Lasso**        | Wbudowana selekcja cech              | Rzadkie wzorce                       |
| **SARIMA**       | Jawnie ujmuje sezonowość             | Silne wzorce sezonowe                |
| **Holt-Winters** | Trend + sezonowość                   | Wyraźne trendy wzrostu/spadku        |
| **ExpSmoothing** | Gładkie przewidywania                | Stabilne wzorce popytu               |

#### Praktyczne przykłady

**Przykład 1: Początkowa konfiguracja ML**

*Cel: Wytrenuj modele ML dla najlepiej sprzedających się pozycji*

1. Trenuj modele → Poziom Model → Top 100
2. Wybierz: LightGBM + RandomForest (najszybsze, niezawodne)
3. Ustawienia CV: 3 podziały, 3-miesięczny rozmiar testu
4. Kliknij "Trenuj modele"
5. Przejrzyj podsumowanie: ~60% wygrywa LightGBM, ~30% RandomForest, ~10% Ridge
6. Generuj prognozy → Wszystkie wytrenowane modele → horyzont 3 miesiące

**Przykład 2: Porównaj ML vs Statystyczne**

*Cel: Czy modele ML są lepsze od metod statystycznych?*

1. Trenuj modele z metodami statystycznymi
2. Przejrzyj rozkład modeli:
    - Jeśli ML dominuje (>70%), ML dodaje wartość
    - Jeśli statystyczne konkurencyjne, rozważ hybrydę
3. Porównaj prognozy wewnętrzne z zakładki 9 vs prognozy ML z zakładki 10

**Przykład 3: Użyj ML do rekomendacji zamówień**

*Cel: Zastąp zewnętrzną prognozę przewidywaniami ML*

1. Upewnij się, że modele są wytrenowane dla odpowiednich jednostek
2. Zakładka 5 → Wybierz "ML (N modeli)" jako źródło prognozy
3. Generuj rekomendacje
4. Porównaj wyniki priorytetów z zewnętrznym źródłem prognozy
5. Monitoruj dokładność w czasie przez zakładkę 8

---

#### Kluczowe różnice: Zakładka 9 vs Zakładka 10

| Aspekt              | Zakładka 9: Porównanie prognoz      | Zakładka 10: Prognoza ML               |
|---------------------|-------------------------------------|----------------------------------------|
| **Metody**          | Tylko statystyczne                  | ML + Statystyczne                      |
| **Selekcja modelu** | Oparta na regułach wg typu produktu | Walidacja krzyżowa per jednostka       |
| **Inżynieria cech** | Brak (metody szeregów czasowych)    | Opóźnienia, stat. kroczące, YoY        |
| **Trwałość**        | Zapisywane partie prognoz           | Zapisywane indywidualne modele         |
| **Główne użycie**   | Porównanie wewnętrzne vs zewnętrzne | Prognozowanie produkcyjne              |
| **Najlepsze gdy**   | Ocena źródeł prognoz                | Maksymalizacja dokładności przewidywań |

---

### Zakładka 11: Zapytania w języku naturalnym

**Cel:** Zapytania do danych używając języka naturalnego zamiast nawigacji przez zakładki i filtry.
Obsługuje zapytania w języku angielskim i polskim.

**Kiedy używać:**

- Szybkie ad-hoc zapytania bez nawigowania wieloma zakładkami
- Gdy wiesz czego szukasz, ale nie wiesz, gdzie to znaleźć
- Dla użytkowników preferujących wpisywanie zapytań zamiast klikania przez filtry
- Do szybkiego sprawdzenia sprzedaży, stanów lub prognoz dla konkretnych modeli

**Kluczowa koncepcja:**
Ta zakładka używa parsera opartego na regułach do interpretacji zapytań w języku naturalnym i generowania SQL.
Zapytania wykonywane są przez DuckDB (tryb plikowy) lub PostgreSQL (tryb bazodanowy), zapewniając szybkie
wyniki na twoich danych.

#### Obsługiwane typy zapytań

| Typ zapytania        | Przykładowe zapytania                                        |
|----------------------|--------------------------------------------------------------|
| **Dane sprzedażowe** | "sales of model CH086 last 2 years", "sprzedaz modelu JU386" |
| **Dane o stanach**   | "stock below rop", "stan ponizej rop", "zero stock"          |
| **Dane prognozowe**  | "forecast for model DO322"                                   |
| **Agregacje**        | "sales by month for model CH086", "top 10 models by sales"   |
| **Filtry**           | "stock type = seasonal", "bestseller items"                  |

#### Wsparcie językowe

Parser obsługuje słowa kluczowe w języku angielskim i polskim:

| Angielski | Polski            |
|-----------|-------------------|
| sales     | sprzedaz          |
| stock     | stan, zapas       |
| forecast  | prognoza          |
| model     | model             |
| last      | ostatnie          |
| year(s)   | rok, lat, lata    |
| month(s)  | miesiac, miesiace |
| below     | ponizej           |
| top       | top, najlepsze    |

#### Przepływ pracy krok po kroku

1. **Wprowadź zapytanie** w polu tekstowym
2. **Kliknij "Wykonaj"** aby uruchomić zapytanie
3. **Przejrzyj wyniki**:
    - Wynik ufności pokazuje jak dobrze system zrozumiał twoje zapytanie
    - Wygenerowany SQL wyświetlany jest dla przejrzystości
    - Tabela wyników z liczbą wierszy/kolumn
    - Przycisk pobierania do eksportu CSV

#### Zrozumienie wyniku

**Sekcja interpretacji zapytania:**

- **Ufność**: 0–100% wskazuje jak dobrze zapytanie zostało sparsowane
    - 70%+ = Wysoka ufność, wyniki prawdopodobnie odpowiadają intencji
    - 50-70% = Średnia ufność, przejrzyj wyniki uważnie
    - <50% = Niska ufność, rozważ przeformułowanie

- **Wygenerowany SQL**: Faktyczne zapytanie SQL wykonane na twoich danych
    - Przydatne do debugowania lub nauki wzorców SQL
    - Można skopiować do użycia w zewnętrznych narzędziach

**Sekcja wyników:**

- Liczby wierszy i kolumn
- Interaktywna tabela danych
- Przycisk pobierania CSV

#### Przykładowe zapytania

**Zapytania o sprzedaż:**

```
sales of model CH086 last 4 years
sales by month for model CH086
top 10 models by sales
sprzedaz modelu JU386 ostatnie 2 lata
top 5 modeli wg sprzedazy
```

**Zapytania o stany:**

```
stock below rop
stock type = seasonal
zero stock
stan ponizej rop
```

**Zapytania o prognozy:**

```
forecast for model DO322
prognoza dla modelu CH086
```

#### Wskazówki dotyczące składni zapytań

1. **Identyfikatory modeli**: Używaj 5-znakowych kodów modeli (np. "CH086", "JU386")
2. **Zakresy czasowe**: Określ "last N years/months" dla filtrowania czasowego
3. **Agregacje**: Używaj "by month", "by year", "by model" do grupowania
4. **Limity**: Używaj "top N" do ograniczania wyników
5. **Filtry**: Używaj słów kluczowych jak "below rop", "seasonal", "bestseller"

#### Ograniczenia

- Złożone joiny wielu tabel nieobsługiwane
- Niestandardowe zakresy dat (konkretne daty) jeszcze nie zaimplementowane
- Kombinacje logiczne (AND/OR) ograniczone
- Podzapytania nieobsługiwane

#### Rozwiązywanie problemów

**"Nie można zrozumieć zapytania":**

- Spróbuj przeformułować używając prostszych słów kluczowych
- Sprawdź przykładowe zapytania jako odniesienie
- Używaj angielskiego lub polskiego konsekwentnie (nie mieszaj)

**Ostrzeżenie o niskiej ufności:**

- Wyniki mogą nie odpowiadać twojej intencji
- Spróbuj być bardziej konkretny
- Używaj dokładnych kodów modeli

**Brak wyników:**

- Zweryfikuj czy dane są załadowane (sprzedaż/stany/prognoza)
- Sprawdź, czy kod modelu istnieje w danych
- Dostosuj zakres czasowy (dane mogą nie istnieć dla żądanego okresu)

---

## Objaśnienie obliczeń statystycznych

### Klasyfikacja typu produktu

Produkty są klasyfikowane na cztery typy na podstawie ich charakterystyki sprzedażowej:

| Typ            | Kryteria                             | Opis                              |
|----------------|--------------------------------------|-----------------------------------|
| **Nowy**       | Pierwsza sprzedaż < 12 miesięcy temu | Niedawno wprowadzone produkty     |
| **Podstawowy** | CV < 0.6                             | Stabilny, przewidywalny popyt     |
| **Sezonowy**   | CV > 1.0                             | Wysoka zmienność, wzorce sezonowe |
| **Regularny**  | 0.6 ≤ CV ≤ 1.0                       | Umiarkowana zmienność             |

**Kolejność klasyfikacji:** Najpierw sprawdzany Nowy, potem Podstawowy/Sezonowy, Regularny jako domyślny.

### Współczynnik Zmienności (CV)

Mierzy zmienność popytu względem średniej:

```
CV = Odchylenie Standardowe / Średnia Miesięczna Sprzedaż
```

- **Niski CV (< 0.6)**: Stabilny popyt, łatwy do prognozowania
- **Średni CV (0.6 - 1.0)**: Umiarkowana zmienność
- **Wysoki CV (> 1.0)**: Bardzo zmienny, często sezonowy

### Zapas Bezpieczeństwa (SS)

Bufor zapasów zapobiegający brakom podczas zmienności popytu:

```
SS = Z-score × Odchylenie Standardowe × √(Lead Time)
```

**Składniki:**

- **Z-score**: Współczynnik poziomu obsługi (wyższy = więcej zapasu bezpieczeństwa)
    - Podstawowy: 2.5 (99.38% poziomu obsługi)
    - Regularny: 1.645 (95% poziomu obsługi)
    - Sezonowy w sezonie: 1.85 (96.8% poziomu obsługi)
    - Sezonowy poza sezonem: 1.5 (93.3% poziomu obsługi)
    - Nowy: 1.8 (96.4% poziomu obsługi)
- **Odchylenie Standardowe**: Zmienność miesięcznego popytu
- **Lead Time**: Czas w miesiącach od zamówienia do otrzymania (domyślnie: 1.36 miesiąca)

**Przykład:**

```
SD = 50 jednostek/miesiąc
Z-score = 1.645 (produkt regularny)
Lead Time = 1.36 miesiąca

SS = 1.645 × 50 × √1.36
SS = 1.645 × 50 × 1.166
SS = 95.9 jednostek
```

### Punkt Zamówienia (ROP)

Poziom zapasów uruchamiający nowe zamówienie:

```
ROP = (Średnia Sprzedaż × Lead Time) + Zapas Bezpieczeństwa
```

**Przykład:**

```
Średnia Sprzedaż = 200 jednostek/miesiąc
Lead Time = 1.36 miesiąca
Zapas Bezpieczeństwa = 95.9 jednostek

ROP = (200 × 1.36) + 95.9
ROP = 272 + 95.9
ROP = 367.9 jednostek
```

**Interpretacja:** Gdy stan spadnie do 368 jednostek, złóż nowe zamówienie.

### Wykrywanie sezonowości

Dla produktów sezonowych system określa czy bieżący miesiąc jest "w sezonie":

```
Indeks Sezonowości = Średnia Miesięczna Sprzedaż / Średnia Ogólna Sprzedaż
W Sezonie = Indeks Sezonowości > 1.2
```

**Przykład:**

```
Średnia Ogólna = 100 jednostek/miesiąc
Średnia Grudzień = 180 jednostek/miesiąc

Indeks Sezonowości = 180 / 100 = 1.8
W Sezonie = Prawda (1.8 > 1.2)
```

Produkty sezonowe używają różnych Z-scores:

- **W Sezonie**: Wyższy Z-score (1.85) dla większego zapasu bezpieczeństwa
- **Poza Sezonem**: Niższy Z-score (1.5) dla mniejszego zamrożonego kapitału

### Metryki prognozy

System oblicza prognozę popytu dla okresu lead time:

```
FORECAST_LEADTIME = Suma dziennych prognoz od dziś do (dziś + lead time)
```

Jeśli lead time = 1.36 miesiąca (~41 dni), system sumuje prognozę na następne 41 dni.

### Projekcja stanów

Symuluje przyszłe poziomy zapasów na podstawie prognozy:

```
Dla każdego przyszłego okresu:
    Prognozowany Stan = Poprzedni Stan - Prognozowany Popyt
    Sprawdź czy Prognozowany Stan ≤ ROP → Osiągnięto ROP
    Sprawdź czy Prognozowany Stan ≤ 0 → Brak towaru
```

Tworzy to wizualizację szeregów czasowych pokazującą:

- Kiedy stan przekroczy próg ROP
- Kiedy stan osiągnie zero (brak towaru)

---

## Algorytm optymalizacji wzorców

Optymalizator wzorców znajduje najlepszą alokację wzorców cięcia, aby zaspokoić popyt na rozmiary
minimalizując odpady.

### Tryby algorytmu

**1. Greedy Overshoot (Domyślny)**

- Priorytetyzuje pełne pokrycie
- Pozwala na pewną nadprodukcję
- Lepszy dla pozycji krytycznych

**2. Greedy Classic**

- Minimalizuje nadprodukcję
- Może nie pokryć niektórych rozmiarów
- Lepszy dla pozycji wrażliwych na koszty

### Funkcja punktacji

Każdy wzorzec jest punktowany na podstawie tego, jak dobrze wypełnia pozostały popyt:

```
Wynik = Σ(min(wzorzec_produkuje, pozostała_potrzeba) × 10 + bonus_priorytetu) - kara_nadmiaru

Gdzie:
- bonus_priorytetu = priorytet_rozmiaru × wzorzec_produkuje × 5
- kara_nadmiaru = jednostki_niepotrzebne × 1
```

### Proces optymalizacji

1. Oblicz minimalną liczbę wzorców: `max(ilości) / 2`
2. Dla każdej łącznej liczby wzorców od minimum do `min + 100`:
   a. Spróbuj alokować wzorce, aby pokryć wszystkie rozmiary
   b. Jeśli sukces, oblicz łączny nadmiar
   c. Śledź najlepsze rozwiązanie (najniższy nadmiar przy pokryciu wszystkich rozmiarów)
3. Jeśli nie znaleziono idealnego rozwiązania, użyj algorytmu zachłannego

### Ograniczenie minimalnego zamówienia

Wzorce muszą być zamawiane w minimalnych ilościach (domyślnie: 5):

- Pierwsza alokacja wzorca: minimalne zamówienie
- Kolejne alokacje: pojedyncze jednostki

### Objaśnienie wyniku

| Pole                   | Opis                                                         |
|------------------------|--------------------------------------------------------------|
| `allocation`           | {id_wzorca: liczba} - Ile każdego wzorca zamówić             |
| `produced`             | {rozmiar: ilość} - Łączne jednostki wyprodukowane na rozmiar |
| `excess`               | {rozmiar: ilość} - Nadprodukcja na rozmiar                   |
| `total_patterns`       | Suma wszystkich zamówień wzorców                             |
| `total_excess`         | Łączne jednostki nadprodukcji                                |
| `all_covered`          | Prawda jeśli wszystkie żądane rozmiary są w pełni pokryte    |
| `min_order_violations` | Wzorce zamówione poniżej minimalnej ilości                   |

---

## System punktacji priorytetów

System rekomendacji zamówień używa wieloczynnikowego wyniku priorytetu.

### Formuła wyniku priorytetu

```
Wynik Priorytetu = (Ryzyko Braku × W₁ + Wpływ Przychodu × W₂ + Popyt × W₃) × Mnożnik Typu
```

**Domyślne wagi:**

- W₁ (Ryzyko Braku): 0.5
- W₂ (Wpływ Przychodu): 0.3
- W₃ (Prognoza Popytu): 0.2

### Obliczenie ryzyka braku

```
Jeśli Stan = 0 I Prognoza > 0:
    Ryzyko Braku = 100 (kara_zerowy_stan)

Jeśli 0 < Stan < ROP:
    Ryzyko Braku = ((ROP - Stan) / ROP) × 80 (max_kara_ponizej_rop)

W przeciwnym razie:
    Ryzyko Braku = 0
```

**Przykład:**

```
ROP = 100 jednostek
Stan = 30 jednostek

Ryzyko Braku = ((100 - 30) / 100) × 80
Ryzyko Braku = 0.7 × 80
Ryzyko Braku = 56
```

### Obliczenie wpływu przychodu

```
Jeśli dostępna cena:
    Przychód Zagrożony = Prognoza × Cena
    Wpływ Przychodu = (Przychód Zagrożony / Max Przychód Zagrożony) × 100

Jeśli cena niedostępna:
    Wpływ Przychodu = (Prognoza / Max Prognoza) × 100
```

### Mnożniki typu

Zwiększają priorytet na podstawie typu produktu:

| Typ        | Mnożnik | Efekt                                    |
|------------|---------|------------------------------------------|
| Nowy       | 1.2     | +20% priorytet (chroń nowe wprowadzenia) |
| Sezonowy   | 1.3     | +30% priorytet (czas jest krytyczny)     |
| Regularny  | 1.0     | Linia bazowa                             |
| Podstawowy | 0.9     | -10% priorytet (stabilny, mniej pilny)   |

### Kompletny przykład

```
Stan = 0 jednostek (zerowy stan)
Prognoza = 80 jednostek
Cena = 25 zł
Max Przychód Zagrożony = 10,000 zł
Typ = Sezonowy

Ryzyko Braku = 100 (zerowy stan z popytem)
Przychód Zagrożony = 80 × 25 zł = 2,000 zł
Wpływ Przychodu = (2,000 zł / 10,000 zł) × 100 = 20
Popyt = min(80, 100) = 80 (ograniczony przez demand_cap)

Surowy Wynik = (100 × 0.5) + (20 × 0.3) + (80 × 0.2)
Surowy Wynik = 50 + 6 + 16 = 72

Wynik Priorytetu = 72 × 1.3 (mnożnik sezonowy)
Wynik Priorytetu = 93.6
```

### Agregacja według Model+Kolor

Priorytety na poziomie SKU są agregowane do poziomu MODEL+KOLOR:

```
Wynik Priorytetu = Średnia wyników SKU
Deficyt = Suma deficytów SKU
Prognoza = Suma prognoz SKU
Luka Pokrycia = max(0, Prognoza - Stan)
Pilne = Jakiekolwiek SKU jest pilne
```

---

## Parametry konfiguracyjne

### settings.json

Znajduje się w `src/settings.json`, wszystkie parametry można dostosować w panelu bocznym UI.

```json
{
  "data_source": {
    "mode": "database",
    "fallback_to_file": true,
    "pool_size": 10,
    "pool_recycle": 3600,
    "echo_sql": false
  },
  "lead_time": 1.36,
  "forecast_time": 5,
  "sync_forecast_with_lead_time": false,
  "cv_thresholds": {
    "basic": 0.6,
    "seasonal": 1.0
  },
  "z_scores": {
    "basic": 2.5,
    "regular": 1.645,
    "seasonal_in": 1.85,
    "seasonal_out": 1.5,
    "new": 1.8
  },
  "new_product_threshold_months": 12,
  "weekly_analysis": {
    "lookback_days": 60
  },
  "optimizer": {
    "min_order_per_pattern": 5,
    "algorithm_mode": "greedy_overshoot"
  },
  "order_recommendations": {
    "stockout_risk": {
      "zero_stock_penalty": 100,
      "below_rop_max_penalty": 80
    },
    "priority_weights": {
      "stockout_risk": 0.5,
      "revenue_impact": 0.3,
      "demand_forecast": 0.2
    },
    "type_multipliers": {
      "new": 1.2,
      "seasonal": 1.3,
      "regular": 1.0,
      "basic": 0.9
    },
    "demand_cap": 100
  }
}
```

### Opisy parametrów

| Parametr                        | Domyślnie        | Opis                                                  |
|---------------------------------|------------------|-------------------------------------------------------|
| `data_source.mode`              | database         | Tryb źródła danych: "file" lub "database"             |
| `data_source.fallback_to_file`  | true             | Powrót do trybu plikowego jeśli baza niedostępna      |
| `lead_time`                     | 1.36             | Miesiące między złożeniem zamówienia a otrzymaniem    |
| `forecast_time`                 | 5                | Miesiące do przodu dla popytu                         |
| `cv_thresholds.basic`           | 0.6              | CV poniżej = produkt podstawowy                       |
| `cv_thresholds.seasonal`        | 1.0              | CV powyżej = produkt sezonowy                         |
| `z_scores.*`                    | różne            | Współczynniki poziomu obsługi według typu produktu    |
| `new_product_threshold_months`  | 12               | Produkty młodsze są "nowe"                            |
| `weekly_analysis.lookback_days` | 60               | Dni wstecz dla monitora nowych produktów              |
| `min_order_per_pattern`         | 5                | Minimalne jednostki na zamówienie wzorca              |
| `algorithm_mode`                | greedy_overshoot | Algorytm optymalizatora: greedy_overshoot lub classic |
| `demand_cap`                    | 100              | Maksymalna wartość popytu do punktacji                |

---

## Wymagania dotyczące danych

### Dane sprzedażowe

**Wymagane kolumny:**
| Kolumna | Typ | Opis |
|---------|-----|------|
| `order_id` | string | Identyfikator zamówienia |
| `data` | datetime | Data sprzedaży |
| `sku` | string | 9-znakowy kod SKU |
| `ilosc` | numeric | Sprzedana ilość |
| `cena` | numeric | Cena jednostkowa |
| `razem` | numeric | Łączna kwota |

### Dane o stanach

**Wymagane kolumny:**
| Kolumna | Typ | Opis |
|---------|-----|------|
| `sku` | string | 9-znakowy kod SKU |
| `nazwa` | string | Opis produktu |
| `stock` | numeric | Łączny stan |
| `available_stock` | numeric | Dostępny stan (używany do obliczeń) |
| `aktywny` | 0/1 | Flaga aktywności (tylko aktywne pozycje są ładowane) |

### Dane prognozowe

**Wymagane kolumny:**
| Kolumna | Typ | Opis |
|---------|-----|------|
| `data` | datetime | Data prognozy |
| `sku` | string | 9-znakowy kod SKU |
| `forecast` | numeric | Prognozowana ilość |

### Struktura SKU

Wszystkie SKU muszą mieć 9 znaków:

```
XXXXXCCSS
│││││││││
├────┴ MODEL (znaki 1-5): Rodzina produktów
│    ├─┴ KOLOR (znaki 6-7): Kod koloru
│       └─┴ ROZMIAR (znaki 8-9): Numeryczny kod rozmiaru
```

**Przykład:** `ABC12BL03`

- Model: ABC12
- Kolor: BL
- Rozmiar: 03

---

## Architektura

### Struktura modułów

```
src/
├── app.py                      # Główna aplikacja Streamlit
├── settings.json               # Konfiguracja użytkownika
│
├── sales_data/                 # Warstwa danych
│   ├── analyzer.py             # Klasa opakowująca SalesAnalyzer
│   ├── data_source.py          # Abstrakcyjny interfejs DataSource
│   ├── file_source.py          # Implementacja plikowa
│   ├── db_source.py            # Implementacja bazodanowa
│   ├── data_source_factory.py  # Wzorzec fabryki
│   ├── loader.py               # Operacje I/O plików
│   ├── validator.py            # Walidacja schematu danych
│   └── analysis/               # Moduły analizy
│       ├── aggregation.py      # Agregacja SKU/Model
│       ├── classification.py   # Klasyfikacja typu produktu
│       ├── forecast_accuracy.py # Metryki dokładności prognozy
│       ├── forecast_comparison.py # Porównanie wewnętrznej vs zewnętrznej
│       ├── internal_forecast.py # Generowanie wewnętrznych prognoz
│       ├── inventory_metrics.py # Obliczenia SS, ROP
│       ├── order_priority.py   # Punktacja priorytetów
│       ├── pattern_helpers.py  # Pomocnicy optymalizacji wzorców
│       ├── projection.py       # Projekcja stanów
│       ├── reports.py          # Analiza tygodniowa/miesięczna
│       ├── ml_feature_engineering.py  # Tworzenie cech ML
│       ├── ml_model_selection.py      # Selekcja modelu CV
│       ├── ml_forecast.py             # Trenowanie i przewidywanie ML
│       └── utils.py            # Współdzielone narzędzia
│
├── ui/                         # Warstwa prezentacji
│   ├── sidebar.py              # Konfiguracja panelu bocznego
│   ├── constants.py            # Stałe i konfiguracja UI
│   ├── tab_sales_analysis.py
│   ├── tab_pattern_optimizer.py
│   ├── tab_weekly_analysis.py
│   ├── tab_monthly_analysis.py
│   ├── tab_order_recommendations.py
│   ├── tab_order_creation.py
│   ├── tab_order_tracking.py
│   ├── tab_forecast_accuracy.py
│   ├── tab_forecast_comparison.py
│   ├── tab_ml_forecast.py      # UI prognozy ML
│   ├── tab_nlq.py              # UI zapytań w języku naturalnym
│   └── shared/                 # Współdzielone komponenty UI
│       ├── data_loaders.py     # Cachowane ładowanie danych
│       ├── display_helpers.py  # Narzędzia wyświetlania
│       ├── forecast_accuracy_loader.py
│       ├── session_manager.py  # Zarządzanie stanem sesji
│       ├── sku_utils.py        # Narzędzia parsowania SKU
│       └── styles.py           # Style CSS
│
├── nlq/                        # Zapytania w języku naturalnym
│   ├── __init__.py             # Eksporty pakietu
│   ├── vocabulary.py           # Tłumaczenia polsko-angielskie
│   ├── patterns.py             # Definicje wzorców do parsowania
│   ├── intent.py               # Dataclass QueryIntent
│   ├── parser.py               # Klasa QueryParser
│   ├── sql_generator.py        # Generowanie SQL z intencji
│   ├── executor.py             # Legacy executor (przestarzały)
│   ├── duckdb_executor.py      # Wykonywanie DuckDB (tryb plikowy)
│   └── postgres_executor.py    # Wykonywanie PostgreSQL (tryb bazodanowy)
│
├── utils/                      # Narzędzia
│   ├── pattern_optimizer.py    # Optymalizacja wzorców
│   ├── settings_manager.py     # Zarządzanie konfiguracją
│   ├── order_manager.py        # Fasada trwałości zamówień
│   ├── order_repository.py     # Wzorzec repozytorium (abstrakcyjny)
│   ├── order_repository_factory.py # Fabryka repozytorium
│   ├── internal_forecast_repository.py # Przechowywanie wewnętrznych prognoz
│   ├── ml_model_repository.py  # Trwałość modeli ML
│   ├── import_utils.py         # Pomocnicy importu
│   └── logging_config.py       # Konfiguracja logowania (LOG_LEVEL z .env)
│
└── migration/                  # Konfiguracja bazy danych (opcjonalna)
    ├── setup_database.py
    ├── import_all.py
    ├── populate_cache.py
    └── sql/                    # Skrypty SQL
```

### Przepływ danych

```
Pliki Sprzedażowe         Pliki Stanów              Pliki Prognozowe
     │                           │                          │
     ▼                           ▼                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DataSource (Abstrakcyjny)                     │
│         FileSource (domyślny) │ DatabaseSource (opcjonalny)      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SalesAnalyzer                               │
│  Agregacja → Klasyfikacja → SS/ROP → Integracja Prognozy         │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        Zakł. 1: Analiza  Zakł. 3-4: Raporty  Zakł. 5: Rekomendacje
                                                  │
                                                  ▼
                                          Zakł. 6: Tworzenie zamówień
                                                  │
                                                  ▼
                                          Optymalizator wzorców
```

### Przełączanie źródła danych

Aplikacja obsługuje dwa tryby źródła danych:

**Tryb plikowy (Domyślny):**

- Czyta z plików Excel/CSV
- Konfiguruj przez `paths_to_files.txt`
- Nie wymaga dodatkowej konfiguracji

**Tryb bazodanowy:**

- PostgreSQL z widokami zmaterializowanymi
- Lepsza wydajność dla dużych zbiorów danych
- Konfiguruj przez plik `.env`
- Wymaga skryptów migracyjnych do konfiguracji

Przełączaj tryby ustawiając `DATA_SOURCE_MODE` w `.env`:

```bash
DATA_SOURCE_MODE=file      # Używaj plików Excel/CSV
DATA_SOURCE_MODE=database  # Używaj PostgreSQL
LOG_LEVEL=INFO             # Poziom logowania: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

## Przewodnik biznesowy

Ta sekcja wyjaśnia jak używać Stock Monitor 3 z perspektywy biznesowej, bez wymagania wiedzy technicznej.

### Zrozumienie kondycji zapasów

#### Co oznaczają liczby

**Zapas Bezpieczeństwa (SS)** - Twoja polisa ubezpieczeniowa przed wyczerpaniem zapasów

- Pomyśl o tym jako o buforze chroniącym przed nieoczekiwanymi skokami popytu
- Wyższy SS = mniej braków, ale więcej pieniędzy zamrożonych w zapasach
- Niższy SS = mniej wymaganego kapitału, ale wyższe ryzyko utraty sprzedaży

**Punkt Zamówienia (ROP)** - Twój alarm "zamów teraz"

- Gdy zapasy spadną do tego poziomu, czas złożyć zamówienie
- Uwzględnia zarówno lead time, JAK I bufor bezpieczeństwa
- Pozycje poniżej ROP wymagają natychmiastowej uwagi

**Współczynnik Zmienności (CV)** - Jak przewidywalny jest popyt?

- Niski CV (poniżej 0.6): Bardzo przewidywalny, stali sprzedawcy — twój "chleb powszedni"
- Średni CV (0.6 — 1.0): Nieco zmienny — normalne produkty
- Wysoki CV (powyżej 1.0): Bardzo nieprzewidywalny — często pozycje sezonowe

### Objaśnienie kategorii produktów

| Kategoria      | Co oznacza                             | Implikacja biznesowa                                 |
|----------------|----------------------------------------|------------------------------------------------------|
| **Podstawowy** | Stałe, przewidywalne sprzedawcy        | Utrzymuj stały zapas; niskie ryzyko nadstanu         |
| **Regularny**  | Normalna zmienność                     | Standardowe zarządzanie zapasami                     |
| **Sezonowy**   | Skoki sprzedaży w określonych okresach | Buduj zapas przed sezonem; redukuj po                |
| **Nowy**       | Mniej niż 12 miesięcy historii         | Monitoruj uważnie; ograniczone dane do prognozowania |

### Zalecenia codziennego przepływu pracy

#### Poranna kontrola (5 minut)

1. Otwórz **Zakładkę 1: Analiza sprzedaży**
2. Filtruj "Poniżej ROP" aby zobaczyć krytyczne pozycje
3. Zanotuj pilne pozycje (zerowy stan z popytem)
4. Sprawdź **Zakładkę 7: Śledzenie zamówień** dla zamówień gotowych do dostawy

#### Tygodniowe planowanie (30 minut)

1. **Zakładka 5: Rekomendacje zamówień** — Wygeneruj top 20—30 priorytetów
2. Użyj filtrów zakładów, aby skupić się na konkretnych zakładach produkcyjnych
3. Przejrzyj listę priorytetów — najwyższe wyniki wymagają działania pierwsze
4. Wybierz pozycje i przejdź do **Zakładki 6: Tworzenie zamówień**
5. Przejrzyj alokacje wzorców i zapisz zamówienia
6. Archiwizuj dostarczone zamówienia w **Zakładce 7**

#### Miesięczny przegląd (1 godzina)

1. **Zakładka 3: Analiza tygodniowa** — Zidentyfikuj rosnące i spadające produkty
2. **Zakładka 4: Analiza miesięczna** — Sprawdź wydajność kategorii vs rok temu
3. **Zakładka 8: Dokładność prognozy** — Przejrzyj jakość prognozy (cel < 20% MAPE)
4. Przejrzyj i dostosuj ustawienia w razie potrzeby (lead time, Z-scores)

### Odczytywanie wyniku priorytetu

Wynik priorytetu (0–150+) mówi co zamawiać najpierw:

| Zakres wyniku  | Pilność   | Działanie                                 |
|----------------|-----------|-------------------------------------------|
| **80+**        | Krytyczna | Zamów natychmiast - wysokie ryzyko braku  |
| **50-80**      | Wysoka    | Zamów w tym tygodniu                      |
| **30-50**      | Średnia   | Zaplanuj na następny cykl zamówień        |
| **Poniżej 30** | Niska     | Monitoruj, bez natychmiastowego działania |

**Co napędza wysokie wyniki:**

- Zerowy stan z oczekiwanym popytem = najwyższa pilność
- Stan poniżej ROP = umiarkowana pilność
- Wysoki prognozowany popyt = rosnący wynik
- Produkty sezonowe/nowe = podwyższony priorytet (czas jest krytyczny)

### Podejmowanie mądrzejszych decyzji zakupowych

#### Kiedy zwiększyć zapas bezpieczeństwa

- Produkty z częstymi brakami
- Pozycje wysokomarżowe gdzie utracona sprzedaż boli
- Pozycje sezonowe wchodzące w szczyt sezonu
- Niewiarygodni dostawcy ze zmiennym lead time

#### Kiedy zmniejszyć zapas bezpieczeństwa

- Wolno rotujące pozycje zamrażające kapitał
- Produkty wycofywane
- Pozycje z bardzo stabilnym, przewidywalnym popytem
- Pozycje sezonowe wychodzące ze szczytu sezonu

#### Zrozumienie kompromisów

| Więcej zapasu bezpieczeństwa | Mniej zapasu bezpieczeństwa |
|------------------------------|-----------------------------|
| Mniej braków                 | Więcej braków               |
| Wyższy poziom obsługi        | Niższy poziom obsługi       |
| Więcej zamrożonego kapitału  | Mniej wymaganego kapitału   |
| Ryzyko przestarzałości       | Ryzyko utraconej sprzedaży  |

### Planowanie sezonowe

System automatycznie wykrywa wzorce sezonowe, ale oto jak wykorzystać te informacje:

**Przed szczytem sezonu:**

1. Sprawdź, które pozycje są sklasyfikowane jako "Sezonowe"
2. Zanotuj ich miesiące w sezonie (widoczne w szczegółowej analizie)
3. Zbuduj zapasy 1–2 miesiące przed rozpoczęciem sezonu
4. Używaj wyższego Z-score (ustawienie w sezonie) podczas szczytu

**Po szczycie sezonu:**

1. System automatycznie przełącza na Z-score poza sezonem
2. Niższy zapas bezpieczeństwa zmniejsza zamrożony kapitał
3. Monitoruj nadmierny zapas, który może wymagać promocji

### Optymalizator wzorców dla produkcji

Jeśli produkujesz lub zamawiasz we wzorcach cięcia:

**Konfiguracja wzorców:**

1. Utwórz zestaw wzorców dla każdego typu produktu (np. "Dorośli", "Dzieci")
2. Zdefiniuj dostępne rozmiary (XL, L, M, S, XS)
3. Dodaj wzorce odpowiadające twoim możliwościom produkcyjnym

**Odczytywanie wyników optymalizacji:**

- **Alokacja**: Ile każdego wzorca wyprodukować
- **Nadmiar**: Nadprodukcja na rozmiar (minimalizuj to)
- **Wszystko pokryte**: Zielony = wszystkie rozmiary zrealizowane; Czerwony = niektóre rozmiary brakuje

**Wskazówka:** Nazywaj zestawy wzorców tak, aby pasowały do kodów modeli dla automatycznego dopasowania
podczas tworzenia zamówień.

### Kluczowe wskaźniki wydajności do monitorowania

| KPI                 | Co monitorować                         | Cel           | Gdzie sprawdzić |
|---------------------|----------------------------------------|---------------|-----------------|
| Pozycje poniżej ROP | Liczba krytycznych pozycji             | Minimalizować | Filtr Zakł. 1   |
| Wskaźnik braków     | Pozycje na zerze z popytem             | Poniżej 5%    | Pilne Zakł. 5   |
| Pozycje z nadstanem | Stan > 6 miesięcy popytu               | Poniżej 10%   | Filtr Zakł. 1   |
| MAPE prognozy       | Średni absolutny błąd procentowy       | Poniżej 20%   | Zakł. 8         |
| BIAS prognozy       | Tendencja do nad/niedoszacowania       | Blisko 0%     | Zakł. 8         |
| Wewnętrzny vs zewn. | Współczynnik wygranych wewnętrznych    | Śledzić       | Zakł. 9         |
| MAPE modeli ML      | Średni CV MAPE modeli ML               | Poniżej 25%   | Zakł. 10        |
| Aktywne zamówienia  | Zamówienia w produkcji                 | Śledzić       | Zakł. 7         |
| Zamówienia gotowe   | Zamówienia przekraczające próg dostawy | Przetwarzać   | Zakł. 7         |

### Typowe scenariusze biznesowe

#### Scenariusz 1: Wprowadzenie nowego produktu

1. System klasyfikuje jako "Nowy" (wyższy mnożnik priorytetu)
2. Ograniczona historia oznacza mniej wiarygodne prognozy
3. **Działanie:** Monitoruj tygodniowo, dostosowuj zamówienia na podstawie faktycznej sprzedaży

#### Scenariusz 2: Nadchodzący skok sezonowy

1. Sprawdź które pozycje mają nadchodzące miesiące "w sezonie"
2. Przejrzyj aktualny stan vs zwiększony ROP (kalkulacja w sezonie)
3. **Działanie:** Zamów z wyprzedzeniem, aby zbudować zapasy przed szczytem

#### Scenariusz 3: Wolno rotujące zapasy

1. Filtruj Zakł. 1 przez "Nadstan" aby znaleźć nadmiar
2. Sprawdź, czy pozycje są Podstawowe (przewidywalne) czy spadające
3. **Działanie:** Rozważ promocje, zmniejsz przyszłe zamówienia

#### Scenariusz 4: Opóźnienie dostawcy

1. Tymczasowo zwiększ ustawienie lead time
2. System przelicza wyższy SS i ROP
3. **Działanie:** Zamawiaj wcześniej, aby skompensować dłuższą dostawę

#### Scenariusz 5: Słaba dokładność prognozy

1. Otwórz **Zakładkę 8: Dokładność prognozy**
2. Ustaw okres analizy: ostatnie 90 dni (lub ostatni zamknięty kwartał)
3. Ustaw przesunięcie: 4 miesiące (aby znaleźć prognozę, która była używana)
4. Wygeneruj raport i przejrzyj ogólny MAPE
5. Sprawdź MAPE według typu produktu — zidentyfikuj problematyczne kategorie
6. Przejrzyj BIAS:
    - Dodatni (+) = za wysoka prognoza = zamówiono za dużo = nadmiar zapasów
    - Ujemny (-) = za niska prognoza = zamówiono za mało = braki
7. **Działanie:** Dla kategorii z wysokim MAPE:
    - Sezonowe ze słabą dokładnością → Przejrzyj parametry wykrywania sezonowości
    - Nowe produkty ze słabą dokładnością → Oczekiwane, monitoruj bliżej
    - Produkty podstawowe ze słabą dokładnością → Zbadaj problemy z jakością danych

#### Scenariusz 6: Śledzenie dostawy zamówienia

1. Otwórz **Zakładkę 7: Śledzenie zamówień**
2. Przejrzyj zamówienia ze statusem "Gotowe do dostawy"
3. Zweryfikuj przybycie dostawy i zaktualizuj stan
4. Archiwizuj przetworzone zamówienia, aby utrzymać czystą listę
5. **Działanie:** Sprawdź Zakł. 5 - zarchiwizowane modele pojawią się ponownie w rekomendacjach, jeśli potrzebne

#### Scenariusz 7: Ocena źródeł prognoz (Przegląd Kwartalny)

*Cel: Czy powinniśmy używać zewnętrznych prognoz dostawcy, czy budować modele wewnętrzne?*

1. Otwórz **Zakładkę 9: Porównanie prognoz**
2. Ustaw parametry: Poziom Model, Top 200, Horyzont = lead time
3. Kliknij "Generuj porównanie" i poczekaj na analizę
4. Przejrzyj podsumowanie ogólne:
    - Wygrane wewnętrzne > 50%? → Modele wewnętrzne mogą być lepsze
    - Wygrane zewnętrzne > 50%? → Prognoza dostawcy dodaje wartość
5. Sprawdź rozbicie według typu produktu:
    - Wewnętrzne często wygrywają dla produktów podstawowych (stabilne wzorce)
    - Zewnętrzne mogą wygrywać dla sezonowych (dostawca może mieć wiedzę rynkową)
6. Zapisz z notatką: "Q4 2024 przegląd dostawcy"
7. **Działanie:** Rozważ podejście hybrydowe — używaj wewnętrznych dla podstawowych, zewnętrznych dla sezonowych

#### Scenariusz 8: Śledzenie poprawy prognozowania w czasie

*Cel: Czy nasze dostosowania prognozowania poprawiają sytuację?*

1. Otwórz **Zakładkę 9: Porównanie prognoz** → zakładka Historyczne prognozy
2. Załaduj najstarszą zapisaną prognozę
3. Zanotuj współczynnik wygranych wewnętrznych i średni MAPE
4. Załaduj najnowszą zapisaną prognozę
5. Porównaj współczynniki wygranych i wartości MAPE
6. **Działanie:** Jeśli się poprawia, kontynuuj obecne podejście; jeśli nie, przejrzyj zmiany parametrów

#### Scenariusz 9: Konfiguracja prognozowania ML

*Cel: Zacznij używać modeli ML do prognozowania*

1. Otwórz **Zakładkę 10: Prognoza ML** → zakładka Trenuj modele
2. Wybierz poziom Model (szybsze), Top 100 jednostek
3. Wybierz LightGBM + RandomForest (najlepsza kombinacja)
4. Zachowaj domyślne ustawienia CV (3 podziały, 3-miesięczny test)
5. Kliknij "Trenuj modele" i poczekaj na ukończenie
6. Przejrzyj rozkład modeli: które typy modeli wygrały najczęściej
7. Idź do zakładki Generuj prognozy → wygeneruj horyzont 3 miesiące
8. **Działanie:** Porównaj prognozy ML z zewnętrznymi prognozami w Zakł. 9

#### Scenariusz 10: Używanie prognoz ML do rekomendacji zamówień

*Cel: Zastąp zewnętrzną prognozę przewidywaniami ML*

1. Upewnij się, że modele są wytrenowane dla odpowiednich jednostek
2. Zakładka 5 → Wybierz "ML (N modeli)" jako źródło prognozy
3. Wygeneruj rekomendacje
4. Porównaj wyniki priorytetów z zewnętrznym źródłem prognozy
5. **Działanie:** Jeśli rekomendacje ML lepiej pasują do intuicji biznesowej, przełącz na stałe

### Dostosowywanie ustawień do twojego biznesu

**Podejście konserwatywne** (mniej braków, więcej zapasów):

- Wyższe Z-scores (2.0+ dla podstawowych, 2.5+ dla sezonowych)
- Wyższa waga ryzyka braku (0.6–0.7)
- Niższy limit popytu

**Podejście agresywne** (mniej zapasów, akceptacja niektórych braków):

- Niższe Z-scores (1.5 dla podstawowych, 1.8 dla sezonowych)
- Wyższa waga prognozy popytu (0.3–0.4)
- Wyższy limit popytu

**Podejście zbalansowane** (domyślne):

- Standardowe Z-scores jak skonfigurowane
- Równomierny rozkład wag
- Odpowiednie dla większości firm

### Szybka karta referencyjna

| Chcę...                                    | Idź do... | Zrób to...                                             |
|--------------------------------------------|-----------|--------------------------------------------------------|
| Zobaczyć co trzeba zamówić                 | Zakł. 5   | Wygeneruj rekomendacje, użyj filtrów zakładów          |
| Sprawdzić konkretny produkt                | Zakł. 1   | Szukaj po SKU/Modelu, zobacz wykres projekcji          |
| Znaleźć trendujące produkty                | Zakł. 3   | Sprawdź Wschodzące/Spadające Gwiazdy                   |
| Porównać z rokiem ubiegłym                 | Zakł. 4   | Przejrzyj wydajność kategorii YoY                      |
| Utworzyć zamówienie produkcyjne            | Zakł. 6   | Wybierz pozycje z Zakł. 5 lub wprowadź model ręcznie   |
| Skonfigurować wzorce cięcia                | Zakł. 2   | Utwórz zestaw wzorców, zdefiniuj rozmiary i wzorce     |
| Załadować historię sprzedaży dla rozmiarów | Zakł. 2   | Wprowadź kod modelu, kliknij Załaduj                   |
| Śledzić dostawę zamówienia                 | Zakł. 7   | Przeglądaj aktywne zamówienia, sprawdź dni od złożenia |
| Dodać ręczne zamówienie                    | Zakł. 7   | Wprowadź kod modelu i datę                             |
| Archiwizować zrealizowane zamówienie       | Zakł. 7   | Zaznacz checkbox archiwum, kliknij Archiwizuj          |
| Sprawdzić jakość prognozy                  | Zakł. 8   | Ustaw okres analizy + przesunięcie, wygeneruj raport   |
| Zobaczyć trend dokładności prognozy        | Zakł. 8   | Wygeneruj raport, przewiń do Wykresu Trendu            |
| Porównać wewnętrzne vs zewnętrzne          | Zakł. 9   | Generuj nowe → ustaw horyzont → Generuj porównanie     |
| Zapisać prognozę do historii               | Zakł. 9   | Po wygenerowaniu, dodaj notatki, Zapisz do historii    |
| Załadować historyczną prognozę             | Zakł. 9   | Zakładka Historyczne prognozy → wybierz → Załaduj      |
| Wytrenować modele ML                       | Zakł. 10  | Zakładka Trenuj modele → wybierz modele → Trenuj       |
| Wygenerować prognozy ML                    | Zakł. 10  | Zakładka Generuj prognozy → wybierz horyzont           |
| Użyć ML do rekomendacji                    | Zakł. 5   | Wybierz "ML" jako źródło prognozy                      |
| Filtrować według zakładu produkcyjnego     | Zakł. 5   | Użyj filtrów Uwzględnij/Wyklucz zakład                 |
| Zapytać dane językiem naturalnym           | Zakł. 11  | Wpisz zapytanie po polsku/angielsku, kliknij Wykonaj   |
| Uzyskać sprzedaż dla konkretnego modelu    | Zakł. 11  | "sprzedaz modelu CH086 ostatnie 2 lata"                |
| Znaleźć pozycje poniżej ROP                | Zakł. 11  | "stan ponizej rop"                                     |

---

## Wskazówki dla najlepszych wyników

1. **Dokładny lead time**: Ustaw lead time odpowiadający twojemu faktycznemu łańcuchowi dostaw
2. **Dostrajaj Z-scores**: Wyższe Z-scores = więcej zapasu bezpieczeństwa = mniej braków, ale więcej kapitału
3. **Obserwuj progi CV**: Dostosuj na podstawie charakterystyki twojego asortymentu
4. **Przeglądaj produkty sezonowe**: Weryfikuj czy pozycje sezonowe są prawidłowo sklasyfikowane
5. **Zestawy wzorców**: Twórz zestawy pasujące do twoich możliwości produkcyjnych (nazwa = kod modelu)
6. **Tygodniowy przegląd**: Sprawdzaj rekomendacje zamówień tygodniowo dla optymalnych zapasów
7. **Używaj filtrów zakładów**: Skupiaj się na jednym zakładzie na raz dla efektywnego zamawiania
8. **Śledź zamówienia**: Utrzymuj Zakł. 7 aktualną — archiwizuj dostarczone zamówienia
9. **Monitoruj dokładność prognozy**: Sprawdzaj Zakł. 8 miesięcznie — cel MAPE poniżej 20%
10. **Ręczne zamówienia**: Używaj Zakł. 7 dla zamówień złożonych poza systemem
11. **Porównuj prognozy**: Używaj Zakł. 9, aby ocenić czy modele wewnętrzne mogą poprawić dokładność
12. **Zapisuj historię prognoz**: Regularnie zapisuj wewnętrzne prognozy do śledzenia poprawy
13. **Trenowanie ML**: Trenuj modele ML miesięcznie, aby uchwycić ostatnie wzorce popytu
14. **Selekcja modeli ML**: Zacznij od LightGBM + RandomForest dla najlepszych wyników

---

## Rozwiązywanie problemów

**Błąd "Brak załadowanych danych":**

- Zweryfikuj, że `paths_to_files.txt` wskazuje na prawidłowe pliki danych
- Upewnij się, że pliki danych mają wymagane kolumny i formaty

**Puste rekomendacje:**

- Zarówno dane o stanach, JAK I prognozowe muszą być załadowane
- Sprawdź, czy SKU w prognozie pasują do SKU w danych sprzedażowych
- Sprawdź, czy filtry zakładów nie wykluczają wszystkich pozycji

**Brakujące pozycje w rekomendacjach:**

- Model może mieć aktywne zamówienie w Zakł. 7 - archiwizuj, jeśli dostarczone
- Sprawdź filtry zakładów — model może być wykluczony

**Optymalizacja wzorców nie działa:**

- Upewnij się, że zestaw wzorców istnieje z pasującą nazwą modelu
- Zweryfikuj, że nazwy rozmiarów w zestawie pasują do twoich danych

**Wysokie/niskie wyniki priorytetów:**

- Dostosuj wagi w panelu bocznym (powinny sumować się do ~1.0)
- Przejrzyj mnożniki typów dla twojego kontekstu biznesowego

**Dokładność prognozy nie pokazuje danych:**

- Upewnij się, że okres analizy jest co najmniej tak długi, jak lead time
- Sprawdź, czy plik prognozy istnieje dla okresu przesunięcia
- Zweryfikuj, że SKU pasują między danymi sprzedażowymi a prognozowymi

**Problemy ze śledzeniem zamówień:**

- Zamówienia filtrują rekomendacje tylko według kodu modelu
- Archiwizuj zamówienia, gdy towary zostaną odebrane, aby ponownie włączyć rekomendacje

**Problemy z porównaniem prognoz:**

- Upewnij się, że zarówno dane sprzedażowe, jak i zewnętrzne prognozowe są załadowane
- Wewnętrzne prognozy wymagają co najmniej 3 miesiące historii sprzedaży per jednostka
- Metoda SARIMA może zawieść dla jednostek z rzadkimi danymi — system wraca do prostszych metod
- Historyczne prognozy wymagają trybu bazodanowego lub dostępu do zapisu do katalogu data/internal_forecasts/

**Problemy z prognozą ML:**

- Wymaga pakietów lightgbm i scikit-learn
- Trenowanie wymaga co najmniej 12 miesięcy historii sprzedaży dla wiarygodnych cech
- Modele zapisywane w katalogu data/ml_models/
- Walidacja krzyżowa może zawieść dla rzadkich danych — zwiększ minimalne wymagania danych

**Historia sprzedaży optymalizatora wzorców nie ładuje się:**

- Upewnij się, że kod modelu istnieje w danych sprzedażowych
- System agreguje wszystkie kolory dla modelu
- Wymaga co najmniej 4 miesiące historii sprzedaży

**Problemy z zapytaniami w języku naturalnym:**

- Wymaga pakietu duckdb (tryb plikowy)
- Zapytanie nie jest rozumiane: spróbuj przeformułować z prostszymi słowami kluczowymi
- Niska ufność: używaj dokładnych kodów modeli i standardowych słów kluczowych
- Brak wyników: zweryfikuj, że dane są załadowane i model/SKU istnieje
- Zapytania z mieszanym językiem mogą zawieść — używaj angielskiego lub polskiego konsekwentnie

---

## Licencja

Własność prywatna – Wszelkie prawa zastrzeżone.
