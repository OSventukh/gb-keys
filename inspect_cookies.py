"""
Дослідження валютних кук та фактичної валюти у data-page.
"""

import json
import html as html_lib
from typing import Optional, Dict

import cloudscraper
from bs4 import BeautifulSoup


def extract_page_currency(html: str) -> Optional[Dict]:
    soup = BeautifulSoup(html, "lxml")
    app_div = soup.find("div", id="app")
    if not app_div or not app_div.has_attr("data-page"):
        return None
    try:
        raw = html_lib.unescape(app_div["data-page"])
        data = json.loads(raw)
    except Exception:
        return None

    props = data.get("props", {})
    return {
        "currency": props.get("currency"),
        "session_currency": props.get("session", {}).get("currency_id"),
        "ip_country": props.get("session", {}).get("ip_country", {}).get("code_2"),
    }


def inspect(currency: str) -> None:
    url = "https://gameboost.com/keys"
    currency = currency.upper()

    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "desktop": True}
    )

    headers = {"X-Currency": currency}
    cookies = {"currency": currency, "currency_id": currency.lower()}
    url_with_param = f"{url}?currency={currency}"

    print("=" * 60)
    print(f"Запит валюти: {currency}")
    resp = scraper.get(url_with_param, headers=headers, cookies=cookies, timeout=30)
    print(f"Status: {resp.status_code}")

    # Set-Cookie з відповіді
    set_cookie = resp.headers.get("set-cookie")
    if set_cookie:
        print("Set-Cookie:", set_cookie[:300], "..." if len(set_cookie) > 300 else "")
    else:
        print("Set-Cookie: <немає>")

    # Куки в сесії
    print("Response cookies:", resp.cookies.get_dict())
    print("Session cookies:", scraper.cookies.get_dict())

    # Валюта з data-page
    page_info = extract_page_currency(resp.text)
    print("data-page currency:", page_info)


if __name__ == "__main__":
    for cur in ["USD", "EUR", "UAH"]:
        inspect(cur)
