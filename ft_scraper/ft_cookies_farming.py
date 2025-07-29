import json, os
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
load_dotenv()

EMAIL = os.getenv("EMAIL", "example.com")
PASSWORD = os.getenv("PASSWORD", "<PASSWORD>")

def auto_login_and_save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=150,
            args=[
                "--window-size=1200,800",
                "--lang=en-US,en",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            locale="en-US"
        )
        page = context.new_page()

        # 🔗 Перехід на сторінку логіну
        page.goto("https://accounts.ft.com/login", wait_until="domcontentloaded")

        # 🔐 Вводимо email
        page.click('input[name="email"]')
        page.keyboard.type(EMAIL, delay=100)
        page.click('button:has-text("Next")')
        page.wait_for_selector('input[name="password"]', timeout=10000)

        # 🔐 Вводимо пароль
        page.keyboard.type(PASSWORD, delay=100)
        page.click('button:has-text("Sign in")')

        # ✅ Очікуємо навігацію (успішний вхід)
        page.wait_for_url("https://www.ft.com/", timeout=15000)

        # 💾 Зберігаємо cookies
        cookies = context.cookies()
        with open("ft_cookies.json", "w") as f:
            json.dump(cookies, f, indent=2)
        print("✅ Cookies збережено!")

        browser.close()

auto_login_and_save_cookies()
