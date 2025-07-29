import os
from datetime import datetime, timedelta, timezone
import psycopg2
from psycopg2.extras import execute_values
from dateutil import parser as dtparse
from dotenv import load_dotenv
load_dotenv()

class FtScraperPipeline:
    def process_item(self, item, spider):
        return item

class PostgresPipeline:
    BULK_SIZE = 50

    buffer: list[tuple]

    anchor_utc: datetime | None = None

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS articles (
        url             TEXT PRIMARY KEY,
        title           TEXT,
        content         TEXT,
        author          TEXT,
        subtitle        TEXT,
        tags            TEXT[],
        image_url       TEXT,
        word_count      INT,
        published_at    TIMESTAMPTZ,
        scraped_at      TIMESTAMPTZ,
        reading_time    TEXT,
        related_articles TEXT[]
    );
    """

    def open_spider(self, spider):
        self.buffer = []

        self.connection = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", "5432"),
        )
        self.cursor = self.connection.cursor()
        self.cursor.execute(self.CREATE_TABLE_SQL)
        self.connection.commit()

        self.cursor.execute("SELECT MAX(published_at) FROM articles;")
        latest: datetime | None = self.cursor.fetchone()[0]

        if latest is None:
            PostgresPipeline.anchor_utc = (
                datetime.now(timezone.utc) - timedelta(days=30)
            )
        else:
            PostgresPipeline.anchor_utc = (
                datetime.now(timezone.utc) - timedelta(hours=1)
            )

        spider.logger.info(f"[PIPELINE] Anchor datetime set to: {self.anchor_utc}")

    def close_spider(self, spider):
        if self.buffer:
            self.flush()
        self.cursor.close()
        self.connection.close()

    def process_item(self, item, spider):
        pub = item["published_at"]
        if isinstance(pub, str):
            try:
                pub = dtparse.isoparse(pub)
            except Exception:
                spider.logger.warning("Cannot parse published_at=%s, fallback to now()", pub)
                pub = datetime.now(timezone.utc)
        if pub.tzinfo is None:
            pub = pub.replace(tzinfo=timezone.utc)
        pub = pub.astimezone(timezone.utc)
        item["published_at"] = pub.astimezone(timezone.utc)
        item["scraped_at"]   = datetime.now(timezone.utc)
        item["tags"]         = item.get("tags") or []
        item["related_articles"] = item.get("related_articles") or []

        self.buffer.append((
            item["url"],
            item["title"],
            item["content"],
            item["author"],
            item["subtitle"],
            item["tags"],
            item["image_url"],
            item["word_count"],
            item["published_at"],
            item["scraped_at"],
            item["reading_time"],
            item["related_articles"],
        ))

        if len(self.buffer) >= self.BULK_SIZE:
            self.flush()

        return item

    def flush(self):
        query = """
        INSERT INTO articles (
            url, title, content, author, subtitle,
            tags, image_url, word_count, published_at,
            scraped_at, reading_time, related_articles
        )
        VALUES %s
        ON CONFLICT (url) DO NOTHING;
        """
        execute_values(self.cursor, query, self.buffer,
                       template=None, page_size=len(self.buffer))
        self.connection.commit()
        self.buffer.clear()

