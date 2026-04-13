from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json
from urllib.parse import urljoin

BASE_URL = "https://ekantipur.com"
ENTERTAINMENT_URL = "https://ekantipur.com/entertainment"
CARTOON_URL = "https://ekantipur.com/cartoon"
CATEGORY_LABEL = "मनोरञ्जन"
TOP_N = 5
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"

def abs_url(href):
    if not href:
        return None
    return href if href.startswith("http") else "https://ekantipur.com" + href

def scrape_entertainment(page):
    articles = []
    print("[Task 1] Loading entertainment page...")
    page.goto(ENTERTAINMENT_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector("div.category-wrapper div.category", timeout=15000)
    cards = page.query_selector_all("div.category-wrapper div.category")
    print(f"Found {len(cards)} cards")
    for card in cards:
        if len(articles) >= TOP_N:
            break
        title_el = card.query_selector("div.category-description h2")
        title = title_el.inner_text().strip() if title_el else None
        if not title:
            continue
        author_el = card.query_selector("div.category-description div.author-name")
        author = author_el.inner_text().strip() if author_el else None
        img_el = card.query_selector("div.category-image figure img")
        image_url = None
        if img_el:
            raw = img_el.get_attribute("data-src") or img_el.get_attribute("src")
            image_url = abs_url(raw)
        articles.append({
            "title": title,
            "image_url": image_url,
            "category": CATEGORY_LABEL,
            "author": author,
        })
        print(f"  [{len(articles)}] {title[:60]}")
    return articles

def scrape_cartoon(page):
    print("[Task 2] Loading cartoon page...")
    page.goto(CARTOON_URL, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)
    card = (
        page.query_selector("section.cartoon-main-wrapper div.col-lg-4")
        or page.query_selector("div.cartoon-main-wrapper div.col-lg-4")
        or page.query_selector("div.cartoon-wrapper")
    )
    if not card:
        print("Cartoon card not found")
        return None
    image_url = None
    link_el = card.query_selector("div.cartoon-image figure a")
    if link_el:
        raw = link_el.get_attribute("data-thumb") or link_el.get_attribute("href")
        image_url = abs_url(raw)
    if not image_url:
        img_el = card.query_selector("div.cartoon-image figure img")
        if img_el:
            raw = img_el.get_attribute("data-src") or img_el.get_attribute("src")
            image_url = abs_url(raw)
    title = None
    author = None
    desc_el = card.query_selector("div.cartoon-description p")
    if desc_el:
        full_text = desc_el.inner_text().strip()
        print(f"  Cartoon text: {full_text}")
        if " - " in full_text:
            parts = full_text.rsplit(" - ", 1)
            title = parts[0].strip()
            author = parts[1].strip()
        else:
            title = full_text
    print(f"  Title: {title}")
    print(f"  Author: {author}")
    print(f"  Image: {image_url}")
    return {"title": title, "image_url": image_url, "author": author}

def main():
    output = {"entertainment_news": [], "cartoon_of_the_day": None}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="ne-NP",
        )
        page = context.new_page()
        page.route("**/*", lambda route: route.abort()
            if route.request.resource_type in ("font", "media")
            else route.continue_())
        try:
            output["entertainment_news"] = scrape_entertainment(page)
            output["cartoon_of_the_day"] = scrape_cartoon(page)
        except PlaywrightTimeoutError as e:
            print(f"Timeout: {e}")
        except Exception as e:
            print(f"Error: {e}")
            raise
        finally:
            browser.close()
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    with open("output.json", "r", encoding="utf-8") as f:
        saved = json.load(f)
    print(f"\nSaved output.json")
    print(f"Entertainment: {len(saved['entertainment_news'])} articles")
    print(f"Cartoon: {'found' if saved['cartoon_of_the_day'] else 'not found'}")
    print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()