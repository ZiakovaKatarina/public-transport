# Public Transport Connection Finder

[English](#english) | [Slovenčina](#slovenčina)

<a id="english"></a>

## English

A web application developed as a bachelor’s thesis for managing public transport data and searching for connections between stops.

## Overview

The application is built with Django and uses MySQL as its database. It supports:

- searching for public transport connections,
- managing transport agencies, routes, trips, stops, and departure times,
- importing public transport data into the database,
- displaying route coordinates and shapes,
- calculating distances between points,
- converting addresses into coordinates,
- user authentication and protected data-management features.

## Technologies

- **Python 3.10**
- **Django 4.2**
- **MySQL 8.0**
- **Django Tailwind**
- **HTML, CSS, and JavaScript**
- **Docker and Docker Compose**
- **OpenRouteService API** for selected geographic and routing features

## Project structure

```text
.
├── backend/                 # Supporting backend files
├── data_management/         # Models, data import, and connection-search logic
├── frontend/                # User interface and Django views
├── theme/                   # Tailwind CSS theme
├── verejna_doprava/         # Main Django project configuration
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Running with Docker

### Requirements

- Docker
- Docker Compose
- An OpenRouteService API key for geographic features

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/ZiakovaKatarina/public-transport-connection-finder.git
   cd public-transport-connection-finder
   ```

2. Optionally create a `.env` file and add the API key:

   ```env
   OPEN_ROUTE_SERVICE_API_KEY=your_api_key
   ```

3. Start the database and web application:

   ```bash
   docker compose up --build
   ```

4. In a separate terminal, apply the database migrations:

   ```bash
   docker compose exec web python manage.py migrate
   ```

5. Open the application in your browser:

   ```text
   http://localhost:8000
   ```

## Running locally without Docker

1. Create and activate a virtual environment:

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

2. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure the MySQL database connection and required environment variables.

4. Run the migrations and development server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Main data entities

The database layer contains models for:

- users,
- transport agencies,
- routes,
- route shapes and geographic points,
- service calendars,
- stops,
- trips,
- arrival and departure times.

## Configuration and security

Before deploying to production:

- store secrets in environment variables,
- replace the development `SECRET_KEY`,
- set `DEBUG` to `False`,
- configure `ALLOWED_HOSTS`,
- use a secure database password,
- never commit `.env` files or API keys.

## Project status

This project is being developed as a bachelor’s thesis and is intended for the development and evaluation of a web application for searching public transport connections.

## Author

**Katarína Žiaková**  
GitHub: [ZiakovaKatarina](https://github.com/ZiakovaKatarina)

---

<a id="slovenčina"></a>

## Slovenčina

Webová aplikácia vytvorená ako bakalárska práca na správu údajov o verejnej doprave a vyhľadávanie spojení medzi zastávkami.

## Prehľad

Aplikácia je postavená na frameworku Django a používa MySQL databázu. Umožňuje:

- vyhľadávať spojenia verejnej dopravy,
- spravovať dopravné podniky, linky, spoje, zastávky a časy odchodov,
- načítavať dopravné údaje do databázy,
- zobrazovať súradnice a tvary trás,
- vypočítať vzdialenosť medzi bodmi,
- prevádzať adresy na súradnice,
- prihlasovať používateľov a chrániť funkcie určené pre správu údajov.

## Technológie

- **Python 3.10**
- **Django 4.2**
- **MySQL 8.0**
- **Django Tailwind**
- **HTML, CSS a JavaScript**
- **Docker a Docker Compose**
- **OpenRouteService API** pre vybrané geografické a smerovacie funkcie

## Štruktúra projektu

```text
.
├── backend/                 # Pomocné backendové súbory
├── data_management/         # Modely, import údajov a logika vyhľadávania spojení
├── frontend/                # Používateľské rozhranie a Django views
├── theme/                   # Tailwind CSS téma
├── verejna_doprava/         # Hlavná konfigurácia Django projektu
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
   git clone https://github.com/ZiakovaKatarina/public-transport-connection-finder.git
   cd public-transport-connection-finder
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

5. Aplikáciu otvorte v prehliadači na adrese `http://localhost:8000`.

## Lokálne spustenie bez Dockeru

1. Vytvorte a aktivujte virtuálne prostredie.
2. Nainštalujte závislosti pomocou `pip install -r requirements.txt`.
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
- tvary trás a geografické body,
- kalendáre platnosti spojov,
- zastávky,
- spoje,
- časy príchodov a odchodov.

## Konfigurácia a bezpečnosť

Pred nasadením do produkcie je potrebné:

- uložiť tajné údaje do premenných prostredia,
- zmeniť vývojový `SECRET_KEY`,
- nastaviť `DEBUG = False`,
- nastaviť `ALLOWED_HOSTS`,
- použiť bezpečné heslo databázy,
- necommitovať súbory `.env` ani API kľúče.

## Stav projektu

Projekt je vyvíjaný ako bakalárska práca a slúži na vývoj a overenie webovej aplikácie pre vyhľadávanie spojení verejnej dopravy.

## Autorka

**Katarína Žiaková**  
GitHub: [ZiakovaKatarina](https://github.com/ZiakovaKatarina)
