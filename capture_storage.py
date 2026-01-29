"""
Захопити cookies + localStorage після вибору валюти вручну.
Запускати у PowerShell/Command Prompt (не Git Bash).
"""

import argparse
import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def main(label: str) -> None:
    url = "https://gameboost.com/keys"
    output_dir = Path("storage_dumps")
    output_dir.mkdir(exist_ok=True)

    stealth = Stealth()
    async with stealth.use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        print("\nПереключи валюту у хедері, потім натисни Enter тут...")
        input()

        cookies = await context.cookies()
        local_storage = await page.evaluate(
            "() => { const o = {}; for (let i=0; i<localStorage.length; i++) { const k = localStorage.key(i); o[k] = localStorage.getItem(k); } return o; }"
        )
        session_storage = await page.evaluate(
            "() => { const o = {}; for (let i=0; i<sessionStorage.length; i++) { const k = sessionStorage.key(i); o[k] = sessionStorage.getItem(k); } return o; }"
        )

        data = {
            "url": url,
            "cookies": cookies,
            "localStorage": local_storage,
            "sessionStorage": session_storage,
        }

        out_file = output_dir / f"state_{label}.json"
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Збережено: {out_file}")

        await browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, help="Мітка стану, наприклад eur або usd")
    args = parser.parse_args()

    asyncio.run(main(args.label))
