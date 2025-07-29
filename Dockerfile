FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential libpq-dev \
        wget ca-certificates \
        libnss3 libatk-bridge2.0-0 libgtk-3-0 \
        libxss1 libasound2 libgbm-dev \
        libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        libpangocairo-1.0-0 libcups2 fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

# Встановлюємо Chromium + deps
RUN playwright install --with-deps chromium

# Робочий каталог — саме корінь Scrapy‑проєкту
WORKDIR /app/ft_scraper

CMD ["scrapy", "crawl", "ftSpider"]
