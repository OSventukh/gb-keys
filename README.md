# GameBoost Keys Parser

Веб-парсер для сторінки [gameboost.com/keys](https://gameboost.com/keys) з обходом захисту від ботів.

## Особливості

- ✅ Підтримка кількох методів обходу захисту від ботів
- ✅ Playwright з stealth режимом
- ✅ Cloudscraper для Cloudflare захисту
- ✅ Selenium з undetected-chromedriver
- ✅ Автоматичний вибір найкращого методу

## Встановлення

1. Встановіть Python 3.8 або новіший

2. Встановіть залежності:
```bash
pip install -r requirements.txt
```

3. Встановіть браузери для Playwright:
```bash
playwright install chromium
```

4. Для Selenium (опціонально):
   - Переконайтеся, що у вас встановлений Chrome браузер
   - undetected-chromedriver встановить потрібний драйвер автоматично

## Використання

### Базове використання:
```bash
python parser.py
```

### Інтерактивне тестування:
```bash
python test_parser.py
```

### Перевірити валюти/куки:
```bash
python inspect_cookies.py
```

### Визначити конкретну валютну куку (manual)
1) Запусти:
```bash
python capture_storage.py --label eur
```
2) У браузері вибери EUR у хедері, повернись у консоль і натисни Enter.
3) Повтори для USD:
```bash
python capture_storage.py --label usd
```
4) Порівняй:
```bash
python diff_storage.py --a storage_dumps/state_eur.json --b storage_dumps/state_usd.json
```

### Альтернатива (Puppeteer + stealth)
```bash
npm install
node capture_storage_puppeteer.js --label=eur
node capture_storage_puppeteer.js --label=usd
node diff_storage.py --a storage_dumps/state_eur.json --b storage_dumps/state_usd.json
```

### Запуск API:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

## Деплой (Docker / Coolify)

1) Використай `Dockerfile` (вже доданий).
2) В Coolify створюй сервіс з Git‑репозиторію.
3) Команда старту не потрібна — використовується `CMD` з Dockerfile.

### Важливо
- `storage_dumps/` не комітиться. Додай ці файли в volume або заливай на сервер вручну.
- Для USD/EUR передавай `storage_file`, наприклад:
```bash
curl "http://your-domain/trending?refresh=true&method=cloudscraper&storage_file=storage_dumps/state_usd.json"
```
### Отримати дані:
```bash
curl "http://localhost:8000/trending?currency=USD"
```

### Отримати дані з реальними куками (з browser dump):
```bash
curl "http://localhost:8000/trending?refresh=true&method=cloudscraper&storage_file=storage_dumps/state_usd.json"
```

### Оновити дані вручну:
```bash
curl -X POST "http://localhost:8000/refresh?method=cloudscraper&currency=EUR"
```

### Програмне використання:
```python
from parser import GameBoostParser
import asyncio

async def main():
    parser = GameBoostParser()
    results = await parser.parse(method='playwright')  # або 'cloudscraper', 'selenium', 'auto'
    parser.save_results('my_results.json')

asyncio.run(main())
```

## Методи парсингу

1. **Playwright** (рекомендовано) - найнадійніший метод для складних захистів
2. **Cloudscraper** - швидкий метод для Cloudflare захисту
3. **Selenium** - альтернативний метод з повноцінним браузером

## Налаштування

У файлі `parser.py` можна змінити:
- `headless=False` на `True` для безголового режиму браузера
- Таймаути завантаження
- User-Agent та інші заголовки

## Структура даних

Результати зберігаються у форматі JSON:
```json
[
  {
    "title": "Назва ключа",
    "price_current": "Поточна ціна",
    "price_old": "Стара ціна (якщо є)",
    "discount": "Знижка (якщо є)",
    "region": "Регіон",
    "platform": "Платформа",
    "link": "Посилання на товар",
    "cover_image": "Обкладинка",
    "cover_srcset": "Srcset (якщо є)",
    "drm_icon": "Іконка DRM"
  }
]
```

## Примітки

- Якщо парсер не знаходить дані, він зберігає HTML сторінки у файл `page_content.html` для аналізу
- Скріншот сторінки зберігається у `page_screenshot.png` (тільки для Playwright)
- API кешує дані у `latest.json` та оновлює їх кожні 15 хвилин або вручну
- Можливо знадобиться адаптувати селектори у методі `_parse_html()` під реальну структуру сторінки
- Для обходу CAPTCHA може знадобитися:
  - Запуск з `headless=False` для ручного проходження CAPTCHA
  - Використання сервісів типу 2captcha або AntiCaptcha
  - Використання проксі-серверів з резидентними IP

## Розв'язання проблем

### Помилка "Navigation timeout"
- Збільште timeout у коді або перевірте інтернет-з'єднання
- Спробуйте використати інший метод парсингу

### Сторінка блокує запити
- Спробуйте запустити з `headless=False` для імітації реального браузера
- Використайте проксі-сервер
- Збільште час очікування після завантаження сторінки

### Дані не знаходяться
- Перевірте файл `page_content.html` для аналізу структури сторінки
- Адаптуйте селектори у методі `_parse_html()` під реальну структуру
- Переконайтеся, що сторінка повністю завантажилася (перевірте скріншот)
