# Verejná doprava – vyhľadávanie spojení

Webová aplikácia vytvorená ako bakalárska práca. Projekt slúži na správu údajov o verejnej doprave a vyhľadávanie spojení medzi zastávkami.

## Prehľad

Aplikácia je postavená na frameworku Django a používa MySQL databázu. Umožňuje:

- vyhľadávať spojenia verejnej dopravy,
- pracovať s údajmi o dopravných podnikoch, linkách, spojoch, zastávkach a časoch odchodov,
- načítavať dopravné údaje do databázy,
- zobrazovať trasu a súradnice spojenia,
- vypočítať vzdialenosť medzi bodmi,
- prevádzať adresu na súradnice,
- prihlasovať používateľov a chrániť funkcie určené pre prihlásených používateľov.

## Technológie

- **Python 3.10**
- **Django 4.2**
- **MySQL 8.0**
- **Django Tailwind**
- **HTML, CSS a JavaScript**
- **Docker a Docker Compose**
- **OpenRouteService API** – pre vybrané geografické a mapové funkcie

## Štruktúra projektu

```text
.
├── backend/                 # Pomocné/backendové súbory
├── data_management/         # Modely, import údajov a logika vyhľadávania
├── frontend/                # Používateľské rozhranie a Django views
├── theme/                   # Tailwind CSS téma
├── verejna_doprava/        # Hlavná konfigurácia Django projektu
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Spustenie pomocou Dockeru

### Požiadavky

- Docker
- Docker Compose
- API kľúč pre OpenRouteService, ak chcete používať geografické funkcie

### Inštalácia a spustenie

1. Naklonujte repozitár:

   ```bash
   git clone https://github.com/ZiakovaKatarina/bakalarska-praca.git
   cd bakalarska-praca
   ```

2. Voliteľne vytvorte súbor `.env` a doplňte API kľúč:

   ```env
   OPEN_ROUTE_SERVICE_API_KEY=vas_api_kluc
   ```

3. Spustite databázu a webovú aplikáciu:

   ```bash
   docker compose up --build
   ```

4. V samostatnom termináli aplikujte migrácie:

   ```bash
   docker compose exec web python manage.py migrate
   ```

5. Aplikáciu otvorte v prehliadači:

   ```text
   http://localhost:8000
   ```

## Lokálne spustenie bez Dockeru

1. Vytvorte a aktivujte virtuálne prostredie:

   ```bash
   python -m venv .venv
   ```

   Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

   Linux/macOS:

   ```bash
   source .venv/bin/activate
   ```

2. Nainštalujte závislosti:

   ```bash
   pip install -r requirements.txt
   ```

3. Nastavte pripojenie k MySQL databáze a potrebné premenné prostredia.

4. Spustite migrácie a vývojový server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Hlavné dátové entity

Databázová vrstva obsahuje modely pre:

- používateľov,
- dopravné podniky,
- linky,
- trasy a ich geometrické body,
- kalendáre platnosti spojov,
- zastávky,
- spoje,
- časy príchodov a odchodov.

Štruktúra dát vychádza z údajov potrebných na reprezentáciu cestovných poriadkov a trás verejnej dopravy.

## Konfigurácia a bezpečnosť

Pred nasadením do produkcie je potrebné:

- uložiť tajné údaje do premenných prostredia,
- zmeniť vývojový `SECRET_KEY`,
- vypnúť `DEBUG`,
- nastaviť `ALLOWED_HOSTS`,
- použiť bezpečné heslo databázy,
- necommitovať súbor `.env` ani API kľúče.

## Stav projektu

Projekt je vyvíjaný ako bakalárska práca a slúži na vývoj a overenie webovej aplikácie pre vyhľadávanie spojení verejnej dopravy.

## Autorka

**Katarína Žiaková**  
GitHub: [ZiakovaKatarina](https://github.com/ZiakovaKatarina)
