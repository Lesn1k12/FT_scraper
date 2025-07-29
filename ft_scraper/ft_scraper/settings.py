import os

BOT_NAME = "ft_scraper"

SPIDER_MODULES = ["ft_scraper.spiders"]
NEWSPIDER_MODULE = "ft_scraper.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "ft_scraper (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
#CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "ft_scraper.middlewares.FtScraperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    "ft_scraper.middlewares.FtScraperDownloaderMiddleware": 543,
#}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   # "ft_scraper.pipelines.FtScraperPipeline": 300,
    'ft_scraper.pipelines.PostgresPipeline': 300,
}

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
FEED_EXPORT_ENCODING = "utf-8"

FEEDS = {
    "ft_scraper/data/articles.json": {
        "format": "json",
        "overwrite": True,  # перезаписувати при кожному запуску
    }
}

# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
#     "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
# }
#
# TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
#
# PLAYWRIGHT_BROWSER_TYPE = "chromium"
#
# PLAYWRIGHT_LAUNCH_OPTIONS = {
#     "headless": False,
# }


LOG_FILE = os.path.join(os.path.dirname(__file__), 'rich.log')
LOG_LEVEL = 'INFO'
LOG_STDOUT = True

import logging
from scrapy.utils.log import configure_logging
configure_logging(install_root_handler=False)
logging.basicConfig(
    filename=LOG_FILE,
    filemode='w',
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    level=LOG_LEVEL,
)