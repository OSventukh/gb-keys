"""
Швидкий тест парсера
"""

import asyncio
from parser import GameBoostParser

async def test():
    parser = GameBoostParser()
    
    print("Тестування парсера...")
    print("Оберіть метод:")
    print("1. Playwright (рекомендовано)")
    print("2. Cloudscraper")
    print("3. Selenium")
    print("4. Автоматичний вибір")
    
    choice = input("\nВведіть номер (1-4, за замовчуванням 4): ").strip() or "4"
    
    method_map = {
        "1": "playwright",
        "2": "cloudscraper",
        "3": "selenium",
        "4": "auto"
    }
    
    method = method_map.get(choice, "auto")
    
    results = await parser.parse(method=method)
    
    if results:
        print(f"\n✅ Успіх! Знайдено {len(results)} записів")
        parser.save_results()
    else:
        print("\n⚠️ Дані не знайдено")
        print("💡 Перевірте файли page_content.html та page_screenshot.png для аналізу")

if __name__ == "__main__":
    asyncio.run(test())
