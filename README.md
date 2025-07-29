# FT News Scraper 🕷️

Scrapes Financial Times **World** headlines with Scrapy + Playwright and saves structured articles to a Postgres database (running in Docker).

---

## Prerequisites

| Tool | Version (tested) |
|------|------------------|
| **Docker Engine** | ≥ 24 CE |
| **Docker Compose** | v2 plugin (bundled with Docker Desktop) |
| **Python** | 3.11 (only if you run helper scripts outside Docker) |

---

## 1. Clone & install

```bash
git clone git@github.com:your-org/ft_scraper.git
cd ft_scraper
cp .env.example .env          # fill in secrets – see next section
```

---

## 2. Configure secrets (`.env`)

```dotenv
# Postgres
POSTGRES_DB=ft_scraper
POSTGRES_USER=scraper_user
POSTGRES_PASSWORD=scraper_pass
POSTGRES_HOST=db
POSTGRES_PORT=5432

# FT credentials for Playwright cookie harvester
EMAIL=you@example.com
PASSWORD=********
```

*Never commit real credentials – `.env` is git‑ignored.*

---

## 3. Harvest FT cookies (once)

```bash
# runs Playwright, logs in, saves ft_cookies.json
docker compose run --rm scraper python ft_scraper/ft_cookies_farming.py
```

A file `ft_scraper/ft_cookies.json` is created and will be picked up by the spider.

---

## 4. Bootstrap run (30 days history)

```bash
FIRST_RUN=yes docker compose up --build         # first time only
```

* The flag `FIRST_RUN=yes` tells the spider to crawl the last **30 days**.
* Data land in the Postgres table `articles`; duplicates are ignored.

When the bootstrap finishes, **remove** or set `FIRST_RUN=no` in
`docker-compose.yml` / your CI environment.

---

## 5. Incremental runs (hourly news)

```bash
docker compose up -d db           # ensure DB container is running
docker compose up -d scraper      # spider now scrapes only the last hour
```

To keep it continuous you can:

* wrap the scraper container in a `while true; sleep 3600; ...`
  entrypoint **or**
* schedule `docker compose run --rm scraper scrapy crawl ftSpider` via cron.

---

## 6. Querying the database

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB   -c "SELECT COUNT(*), MIN(published_at), MAX(published_at) FROM articles;"
```

---

## Project layout

```
ft_scraper/
├── ft_scraper/
│   ├── spiders/           # FtSpider lives here
│   ├── pipelines.py       # Postgres upsert, table auto‑create
│   ├── ft_cookies_farming.py
│   └── data/              # scraped JSON feeds (git‑ignored)
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```


