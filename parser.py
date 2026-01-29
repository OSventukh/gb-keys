"""
Веб-парсер для gameboost.com/keys з обходом захисту від ботів
Використовує кілька методів для надійності
"""

import asyncio
import json
import time
import html as html_lib
from pathlib import Path
from typing import List, Dict, Optional

from bs4 import BeautifulSoup
import cloudscraper


class GameBoostParser:
    """Парсер для gameboost.com з обходом захисту від ботів"""
    
    def __init__(self):
        self.url = "https://gameboost.com/keys"
        self.results = []
        self.last_debug = {}
    
    async def parse_with_playwright(self) -> Optional[List[Dict]]:
        """
        Метод 1: Playwright з stealth режимом
        Найнадійніший метод для складних захистів
        """
        try:
            try:
                from playwright.async_api import async_playwright
            except Exception as import_error:
                print("❌ Playwright не встановлений.")
                print("💡 Встановіть playwright або використайте cloudscraper.")
                print(f"Деталі: {import_error}")
                return None

            async with async_playwright() as p:
                # Запускаємо браузер з налаштуваннями для обходу детекції
                browser = await p.chromium.launch(
                    headless=False,  # Можна змінити на True для безголового режиму
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-infobars',
                        '--window-size=1920,1080',
                    ]
                )
                
                # Створюємо контекст з реалістичними налаштуваннями
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York',
                    permissions=['geolocation'],
                    geolocation={'latitude': 40.7128, 'longitude': -74.0060},
                    color_scheme='light',
                )
                
                page = await context.new_page()
                
                # Додаємо скрипти для обходу детекції
                await page.add_init_script("""
                    // Приховуємо webdriver
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    
                    // Додаємо плагіни
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });
                    
                    // Мови
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en']
                    });
                    
                    // Chrome об'єкт
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // Permissions
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // Canvas fingerprinting
                    const getImageData = CanvasRenderingContext2D.prototype.getImageData;
                    CanvasRenderingContext2D.prototype.getImageData = function() {
                        const imageData = getImageData.apply(this, arguments);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                        }
                        return imageData;
                    };
                    
                    // WebGL fingerprinting
                    const getParameter = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        if (parameter === 37445) {
                            return 'Intel Inc.';
                        }
                        if (parameter === 37446) {
                            return 'Intel Iris OpenGL Engine';
                        }
                        return getParameter.apply(this, arguments);
                    };
                """)
                
                # Додаємо заголовки
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0',
                })
                
                print(f"Завантаження сторінки: {self.url}")
                
                # Спробуємо завантажити сторінку з різними стратегіями
                try:
                    await page.goto(self.url, wait_until='domcontentloaded', timeout=60000)
                except:
                    try:
                        await page.goto(self.url, wait_until='load', timeout=60000)
                    except:
                        await page.goto(self.url, timeout=60000)
                
                # Чекаємо на завантаження контенту та JavaScript
                await asyncio.sleep(8)
                
                # Прокручуємо сторінку для імітації поведінки користувача
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                await page.evaluate("window.scrollTo(0, 0)")
                await asyncio.sleep(1)
                
                # Перевіряємо, чи не показується CAPTCHA або блокування
                page_content = await page.content()
                page_text = await page.inner_text('body')
                
                if 'captcha' in page_content.lower() or 'cloudflare' in page_content.lower():
                    print("⚠️ Виявлено CAPTCHA або Cloudflare захист")
                    print("💡 Спробуйте запустити з headless=False для ручного проходження CAPTCHA")
                
                # Перевіряємо, чи сторінка завантажилася
                if len(page_text) < 100:
                    print("⚠️ Сторінка може бути порожньою або заблокованою")
                
                # Отримуємо HTML контент
                html = await page.content()
                
                # Зберігаємо скріншот для аналізу
                try:
                    await page.screenshot(path='page_screenshot.png', full_page=True)
                    print("📸 Скріншот збережено у page_screenshot.png")
                except:
                    pass
                
                await browser.close()
                
                return self._parse_html(html)
                
        except Exception as e:
            print(f"❌ Помилка при парсингу з Playwright: {e}")
            return None
    
    def parse_with_cloudscraper(
        self,
        currency: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Optional[List[Dict]]:
        """
        Метод 2: Cloudscraper для Cloudflare захисту
        Швидший метод для простих випадків
        """
        try:
            self.last_debug = {}
            scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'desktop': True
                }
            )
            
            headers = {}
            cookies = cookies or {}
            url = self.url

            if currency and not cookies:
                currency_code = currency.upper()
                cookies = {
                    "currency": currency_code,
                    "currency_id": currency_code.lower(),
                }
                headers["X-Currency"] = currency_code
                if "?" in url:
                    url = f"{url}&currency={currency_code}"
                else:
                    url = f"{url}?currency={currency_code}"

            print(f"Завантаження сторінки через cloudscraper: {url}")
            response = scraper.get(url, timeout=30, headers=headers, cookies=cookies)
            self.last_debug.update({
                "cloudscraper_status": response.status_code,
                "cloudscraper_url": url,
                "cloudscraper_response_url": response.url,
            })
            
            if response.status_code == 200:
                return self._parse_html(response.text)
            else:
                print(f"❌ Помилка HTTP {response.status_code}")
                self.last_debug["cloudscraper_body_snippet"] = response.text[:500]
                return []
                
        except Exception as e:
            print(f"❌ Помилка при парсингу з cloudscraper: {e}")
            self.last_debug["cloudscraper_error"] = str(e)
            return None
    
    def parse_with_selenium(self) -> Optional[List[Dict]]:
        """
        Метод 3: Selenium з undetected-chromedriver
        Альтернативний метод з повноцінним браузером
        """
        try:
            try:
                import undetected_chromedriver as uc
            except Exception as import_error:
                print("❌ Не вдалося імпортувати undetected-chromedriver.")
                print("💡 Спробуйте встановити setuptools або використайте метод playwright/cloudscraper.")
                print(f"Деталі: {import_error}")
                return None

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            options = uc.ChromeOptions()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-gpu')
            
            print(f"Завантаження сторінки через Selenium: {self.url}")
            driver = uc.Chrome(options=options, version_main=None)
            
            try:
                driver.get(self.url)
                
                # Чекаємо на завантаження сторінки
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                time.sleep(5)  # Додатковий час для завантаження JavaScript
                
                html = driver.page_source
                return self._parse_html(html)
                
            finally:
                driver.quit()
                
        except Exception as e:
            print(f"❌ Помилка при парсингу з Selenium: {e}")
            return None
    
    def _parse_html(self, html: str) -> List[Dict]:
        """
        Парсить HTML і витягує дані про ключі
        """
        soup = BeautifulSoup(html, 'lxml')
        keys_data = []
        self.last_debug = {}
        
        # Зберігаємо HTML для аналізу
        with open('page_content.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("📄 HTML збережено у файл page_content.html для аналізу")

        # Простий детект Cloudflare challenge
        cf_detected = bool(soup.find('script', src=lambda x: x and 'cdn-cgi/challenge' in x))
        if not cf_detected and "__CF$cv$params" in html:
            cf_detected = True
        self.last_debug["cloudflare_detected"] = cf_detected

        # 1) Спочатку пробуємо взяти Trending із data-page (JSON)
        data_page_items = self._parse_data_page_trending(soup)
        if data_page_items:
            return data_page_items

        # 2) Fallback: шукаємо секцію Trending у DOM
        trending_section = None
        for header in soup.find_all('h2'):
            if header.get_text(strip=True).lower() == 'trending':
                trending_section = header.find_parent(
                    'div',
                    class_=lambda x: x and 'flex' in x and 'flex-col' in x and 'relative' in x
                )
                if not trending_section:
                    trending_section = header.find_parent('div')
                break

        if not trending_section:
            print("⚠️ Секція Trending не знайдена. Перевірте page_content.html")
            return []

        slides = trending_section.find_all(
            'div',
            attrs={'role': 'group', 'aria-roledescription': 'slide'}
        )

        if not slides:
            print("⚠️ Не знайдено слайди Trending. Перевірте page_content.html")
            return []

        for slide in slides:
            try:
                link_elem = slide.find('a', href=True)
                title_elem = slide.find('p', class_=lambda x: x and 'font-medium' in x)
                region_platform_row = slide.find('div', class_=lambda x: x and 'text-xs' in x)

                # Ціни
                price_current_elem = slide.find(
                    'div',
                    class_=lambda x: x and 'font-bold' in x and 'text-transparent' in x
                )
                price_old_elem = slide.find('div', class_=lambda x: x and 'line-through' in x)
                discount_elem = slide.find('div', class_=lambda x: x and 'rounded-full' in x and 'bg-primary' in x)

                # Зображення
                images = slide.find_all('img')
                drm_icon = None
                cover_image = None
                cover_srcset = None
                for img in images:
                    src = img.get('src') or ''
                    srcset = img.get('srcset')
                    if '/drm/' in src and not drm_icon:
                        drm_icon = src
                    if ('igdb' in src or 'covers' in src) and not cover_image:
                        cover_image = src
                        cover_srcset = srcset

                region = None
                platform = None
                if region_platform_row:
                    spans = region_platform_row.find_all('span')
                    parts = [s.get_text(strip=True) for s in spans if s.get_text(strip=True) not in ('·', '')]
                    if parts:
                        region = parts[0]
                        platform = parts[-1] if len(parts) > 1 else None

                title = title_elem.get_text(strip=True) if title_elem else None
                price_current = price_current_elem.get_text(strip=True) if price_current_elem else None
                price_old = price_old_elem.get_text(strip=True) if price_old_elem else None
                discount = discount_elem.get_text(strip=True) if discount_elem else None
                link = link_elem['href'] if link_elem else None

                if title:
                    keys_data.append({
                        'title': title,
                        'price_current': price_current,
                        'price_old': price_old,
                        'discount': discount,
                        'region': region,
                        'platform': platform,
                        'link': link,
                        'cover_image': cover_image,
                        'cover_srcset': cover_srcset,
                        'drm_icon': drm_icon
                    })
            except Exception:
                continue

        return keys_data

    def _parse_data_page_trending(self, soup: BeautifulSoup) -> List[Dict]:
        app_div = soup.find('div', id='app')
        if not app_div or not app_div.has_attr('data-page'):
            self.last_debug.update({
                "data_page_found": False,
            })
            return []

        try:
            raw = html_lib.unescape(app_div['data-page'])
            page_data = json.loads(raw)
        except Exception:
            self.last_debug.update({
                "data_page_found": True,
                "data_page_parsed": False,
            })
            return []

        props = page_data.get("props", {})
        session = props.get("session", {})
        self.last_debug.update({
            "data_page_found": True,
            "data_page_parsed": True,
            "data_page_component": page_data.get("component"),
            "props_currency": props.get("currency"),
            "session_currency_id": session.get("currency_id"),
            "ip_country": (session.get("ip_country") or {}).get("code_2"),
            "props_keys": list(props.keys())[:30],
        })

        trending_lists = []

        def walk(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, list) and 'trending' in k.lower():
                        trending_lists.append(v)
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(page_data)

        candidates = [lst for lst in trending_lists if lst and isinstance(lst[0], dict)]
        if not candidates:
            # Fallback: знайти список об'єктів із полями ціни/назви
            def list_has_keys(lst):
                if not lst or not isinstance(lst[0], dict):
                    return False
                keys = set()
                for item in lst[:5]:
                    keys.update(item.keys())
                key_text = " ".join(keys).lower()
                return any(k in key_text for k in ['price', 'cost', 'title', 'name', 'local_price', 'retail_price'])

            def find_any_lists(obj):
                found = []
                if isinstance(obj, dict):
                    for v in obj.values():
                        found.extend(find_any_lists(v))
                elif isinstance(obj, list):
                    if list_has_keys(obj):
                        found.append(obj)
                    for v in obj:
                        found.extend(find_any_lists(v))
                return found

            candidates = find_any_lists(page_data)

        if not candidates:
            self.last_debug.update({
                "trending_candidates": 0,
            })
            return []

        items = candidates[0]
        sample_keys = []
        for item in items[:3]:
            if isinstance(item, dict):
                sample_keys.append(list(item.keys())[:20])
        self.last_debug.update({
            "trending_candidates": len(candidates),
            "candidate_sample_keys": sample_keys,
        })
        normalized = []
        for item in items:
            if not isinstance(item, dict):
                continue
            normalized_item = self._normalize_item(item)
            if normalized_item.get('title'):
                normalized.append(normalized_item)
        return normalized

    def load_cookies_from_dump(self, path: str) -> Dict[str, str]:
        """
        Завантажує cookies з storage_dumps/state_*.json (Puppeteer/Playwright dump).
        """
        dump = json.loads(Path(path).read_text(encoding="utf-8"))
        cookies = {}
        for c in dump.get("cookies", []):
            domain = c.get("domain", "")
            if "gameboost.com" in domain:
                name = c.get("name")
                value = c.get("value")
                if name and value is not None:
                    cookies[name] = value
        return cookies

    def _normalize_item(self, item: Dict) -> Dict:
        def pick(keys):
            for k in keys:
                if k in item and item[k] not in (None, ""):
                    return item[k]
            return None

        title = pick(['title', 'name', 'display_name', 'product_name'])

        link = pick(['url', 'link', 'href', 'permalink'])
        slug = pick(['slug', 'seo_slug', 'product_slug'])
        if not link and slug:
            link = f"https://gameboost.com/{str(slug).lstrip('/')}"

        price_current, price_old, currency_code = self._extract_prices(item)
        discount = pick(['discount', 'discount_percent', 'discount_pct', 'discountPercent', 'discount_value'])

        region = pick(['region', 'region_name', 'country', 'country_name'])
        platform = pick(['platform', 'platform_name', 'drm', 'drm_name'])
        if not platform and isinstance(item.get('sub_platform'), dict):
            platform = item['sub_platform'].get('name')

        cover_image = pick(['cover', 'cover_image', 'image', 'image_url', 'cover_url', 'cover_image_url'])
        cover_srcset = pick(['cover_srcset', 'image_srcset', 'srcset'])
        drm_icon = pick(['drm_icon', 'drm_logo', 'drm_image', 'drm_icon_url'])
        if not drm_icon and isinstance(item.get('sub_platform'), dict):
            drm_icon = item['sub_platform'].get('image_url')

        return {
            'title': title,
            'price_current': price_current,
            'price_old': price_old,
            'discount': discount,
            'region': region,
            'platform': platform,
            'link': link,
            'cover_image': cover_image,
            'cover_srcset': cover_srcset,
            'drm_icon': drm_icon,
            'currency': currency_code,
            'raw': item
        }

    def _extract_prices(self, item: Dict) -> (Optional[str], Optional[str], Optional[str]):
        # flat keys
        current = item.get('price') or item.get('price_current') or item.get('current_price')
        old = item.get('price_old') or item.get('old_price') or item.get('original_price')
        currency_code = None

        # Prefer local price if present (matches selected currency)
        local_price = item.get('local_price')
        if isinstance(local_price, dict):
            current = local_price.get('format') or local_price.get('value') or current
            currency = local_price.get('currency')
            if isinstance(currency, dict):
                currency_code = currency.get('code') or currency_code

        # local retail (old) price in selected currency
        local_retail = item.get('local_retail_price')
        if isinstance(local_retail, dict):
            old = local_retail.get('format') or local_retail.get('value') or old
            currency = local_retail.get('currency')
            if isinstance(currency, dict):
                currency_code = currency.get('code') or currency_code

        # retail/local price objects
        for key in ['retail_price', 'local_retail_price', 'sale_price', 'local_sale_price']:
            value = item.get(key)
            if isinstance(value, dict):
                current = current or value.get('format') or value.get('value')
                currency = value.get('currency')
                if isinstance(currency, dict):
                    currency_code = currency.get('code') or currency_code

        # nested price dicts
        for key in ['prices', 'price', 'price_info', 'price_data']:
            value = item.get(key)
            if isinstance(value, dict):
                current = current or value.get('current') or value.get('final') or value.get('discounted')
                old = old or value.get('old') or value.get('regular') or value.get('original')
                currency = value.get('currency')
                if isinstance(currency, dict):
                    currency_code = currency.get('code') or currency_code

        # stringify numbers
        if isinstance(current, (int, float)):
            current = str(current)
        if isinstance(old, (int, float)):
            old = str(old)

        return current, old, currency_code
    
    async def parse(
        self,
        method: str = 'auto',
        currency: Optional[str] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> List[Dict]:
        """
        Головний метод парсингу з автоматичним вибором методу
        """
        print(f"\n🚀 Початок парсингу {self.url}")
        print(f"📋 Метод: {method}")
        if currency:
            print(f"💱 Валюта: {currency}")
        print("")
        
        if method == 'playwright' or method == 'auto':
            print("=" * 50)
            print("Спроба 1: Playwright")
            print("=" * 50)
            result = await self.parse_with_playwright()
            if result:
                self.results = result
                return result
        
        if method == 'cloudscraper' or (method == 'auto' and not self.results):
            print("\n" + "=" * 50)
            print("Спроба 2: Cloudscraper")
            print("=" * 50)
            result = self.parse_with_cloudscraper(currency=currency, cookies=cookies)
            if result:
                self.results = result
                return result
        
        if method == 'selenium' or (method == 'auto' and not self.results):
            print("\n" + "=" * 50)
            print("Спроба 3: Selenium")
            print("=" * 50)
            result = self.parse_with_selenium()
            if result:
                self.results = result
                return result
        
        print("\n❌ Всі методи не вдалися")
        return []
    
    def save_results(self, filename: str = 'results.json'):
        """Зберігає результати у JSON файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Результати збережено у {filename}")


async def main():
    """Головна функція"""
    parser = GameBoostParser()
    
    # Спробуємо автоматично знайти найкращий метод
    results = await parser.parse(method='auto')
    
    if results:
        print(f"\n✅ Знайдено {len(results)} записів")
        for i, item in enumerate(results[:5], 1):  # Показуємо перші 5
            print(f"\n{i}. {item.get('title', 'N/A')}")
            print(f"   Ціна: {item.get('price', 'N/A')}")
        
        parser.save_results()
    else:
        print("\n⚠️ Дані не знайдено. Перевірте файл page_content.html для аналізу структури сторінки.")


if __name__ == "__main__":
    asyncio.run(main())
