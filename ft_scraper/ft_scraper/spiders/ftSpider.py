import json, os, time
from datetime import datetime, timedelta, timezone
from dateutil import parser as dtparse
from typing import List, Optional
import scrapy
import requests

class FtSpider(scrapy.Spider):
    name = "ftSpider"
    allowed_domains = ["ft.com"]
    start_urls = ["https://accounts.ft.com/login"]
    custom_settings = {"DOWNLOAD_DELAY": 0.5}

    cookies = None

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

        first_run = os.getenv("FIRST_RUN", "no").lower() in {"yes", "true", "1"}
        if first_run:
            self.anchor = datetime.now(timezone.utc) - timedelta(days=30)
        else:
            self.anchor = datetime.now(timezone.utc) - timedelta(hours=1)

        self.logger.info("🕰  Anchor datetime = %s  (FIRST_RUN=%s)",
                         self.anchor.isoformat(), first_run)

        try:
            cookies_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "ft_cookies.json")
            with open(cookies_path, "r") as f:
                raw_cookies = json.load(f)
            self.cookies = {c['name']: c['value'] for c in raw_cookies if '.ft.com' in c['domain']}
        except Exception as e:
            self.logger.error(f"💥 Помилка зчитування cookies: {e}")
            self.cookies = None


    def start_requests(self):
        self.logger.info("🔥 Стартуємо start_requests()...")

        url = "https://www.ft.com/world?page={}"
        for page in range(1):
            yield scrapy.Request(
                url=url.format(page),
                #cookies=cookies,
                callback=self.parse_page
            )

    def parse_page(self, response):
        self.logger.info("🔍  %s", response.url)

        for teaser in response.css("div.stream-item"):
            href = teaser.css("div.o-teaser__heading a::attr(href)").get()
            if not href:
                continue

            time_raw = teaser.css("div.o-teaser__meta time::attr(datetime)").get()
            if not time_raw:
                time_raw = teaser.css("div.o-teaser__meta::text").re_first(r"[A-Z]{3,9} \d{1,2} \d{4}")

            pub_dt = None
            if time_raw:
                pub_dt = dtparse.parse(time_raw)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                pub_dt = pub_dt.astimezone(timezone.utc)

                if pub_dt < self.anchor:
                    self.logger.info("🛑  %s < anchor → stop pagination", pub_dt.date())
                    return

            # self.logger.info(f"🔗 Знайдено статтю: {href} (опубліковано: {pub_dt}) on page {response.url}")
            yield response.follow(
                response.urljoin(href),
                self.parse_article,
                cookies=self.cookies,
                cb_kwargs={"list_date": pub_dt},  # може бути None, і це ок
            )

        # next / load‑more
        next_page = (
                response.css('a[data-trackable="next-page"]::attr(href)').get()
                or response.css('a[data-trackable="load-more"]::attr(href)').get()
        )
        if next_page:
            yield response.follow(next_page, self.parse_page)

    def parse_related_articles(self, article_id: str, timeout: int = 10) -> Optional[List[str]]:
        if not article_id or not isinstance(article_id, str):
            self.logger.warning("Invalid article_id: %s", article_id)
            return None

        url = f"https://www.ft.com/lure/v2/content/{article_id}?slots=onward%2Conward2"

        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            data = response.json()
            onward_data = data.get("onward")

            if not onward_data:
                self.logger.info("No 'onward' data found for article %s", article_id)
                return []

            items = onward_data.get("items", [])

            if not items:
                self.logger.info("No related articles found for %s", article_id)
                return []

            related_articles = [
                f"https://www.ft.com/content/{item.get('id')}"
                for item_id in items
                if item.get('id')
            ]

            self.logger.info("Found %d related articles for %s", len(related_articles), article_id)
            return related_articles

        except requests.exceptions.Timeout:
            self.logger.error("Timeout error for article %s", article_id)
            return None

        except requests.exceptions.RequestException as e:
            self.logger.error("HTTP request error for article %s: %s", article_id, e)
            return None

        except KeyError as e:
            self.logger.error("Missing expected keys in response for article %s: %s", article_id, e)
            return None

        except ValueError as e:
            self.logger.error("JSON parsing error for article %s: %s", article_id, e)
            return None

        except Exception as e:
            self.logger.error("Unexpected error for article %s: %s", article_id, e)
            return None

    def parse_article(self, response, list_date=None):
        self.logger.info(f"🔎 Парсимо статтю: {response.url}")

        article_id = response.url.split("/")[-1]

        json_ld_raw = response.css('script[type="application/ld+json"]::text').get()
        if json_ld_raw:
            try:
                data = json.loads(json_ld_raw)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        #drop paywall articles
        access_level = response.css("meta[property='ft.accessLevel']::attr(content)").get() or data.get("isAccessibleForFree")
        if access_level != "True":
            return

        # drop paywall articles
        title = response.css("title::text").get() or data.get("headline")
        if title and "subscribe" in title.lower():
            return

        #mail fields
        content = data.get("articleBody") or response.css("meta[name='description']::attr(content)").get()

        author = None
        if isinstance(data.get("author"), list) and data["author"]:
            author = data["author"][0].get("name")
        elif isinstance(data.get("author"), dict):
            author = data["author"].get("name")

        if not author:
            author = response.css('meta[property="article:author"]::attr(content)').get()

        published_at = data.get("datePublished")
        scraped_at = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        #additional fields
        subtitle = data.get("description") or response.css("meta[property='og:description']::attr(content)").get()
        tags = response.css('meta[property="article:tag"]::attr(content)').getall()
        image_url = data.get("image", {}).get("url") or response.css("meta[property='og:image']::attr(content)").get()
        word_count = len(content.split()) if content else 0
        reading_time = None
        related_articles = self.parse_related_articles(article_id)

        yield {
            "url": response.url,
            "title": title,
            "content": content,
            "author": author,
            "published_at": published_at,
            "scraped_at": scraped_at,
            "subtitle": subtitle,
            "tags": tags,
            "image_url": image_url,
            "word_count": word_count,
            "reading_time": reading_time,
            "related_articles": related_articles
        }

