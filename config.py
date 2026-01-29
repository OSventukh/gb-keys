"""
Конфігурація парсера
"""

# URL для парсингу
TARGET_URL = "https://gameboost.com/keys"

# Налаштування Playwright
PLAYWRIGHT_CONFIG = {
    "headless": False,  # True для безголового режиму
    "timeout": 60000,  # Таймаут завантаження сторінки (мс)
    "wait_after_load": 8,  # Час очікування після завантаження (сек)
    "viewport": {
        "width": 1920,
        "height": 1080
    },
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Налаштування Cloudscraper
CLOUDSCRAPER_CONFIG = {
    "timeout": 30,
    "browser": {
        "browser": "chrome",
        "platform": "windows",
        "desktop": True
    }
}

# Налаштування Selenium
SELENIUM_CONFIG = {
    "timeout": 30,
    "wait_after_load": 5
}

# Налаштування парсингу
PARSING_CONFIG = {
    "max_items": 50,  # Максимальна кількість елементів для парсингу
    "save_html": True,  # Зберігати HTML сторінки
    "save_screenshot": True,  # Зберігати скріншот (тільки Playwright)
}

# Файли виводу
OUTPUT_FILES = {
    "results": "results.json",
    "html": "page_content.html",
    "screenshot": "page_screenshot.png"
}
