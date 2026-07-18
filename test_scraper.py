import sys
from core.scraper import scrape_url

if __name__ == "__main__":
    url = "https://www.amazon.in/dp/B0B7CKVCCV"
    try:
        res = scrape_url(url)
        print("Success:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()
