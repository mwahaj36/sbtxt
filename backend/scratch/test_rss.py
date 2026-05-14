import httpx
import asyncio

async def test_rss():
    username = "chamkadar1234"
    urls = [
        f"https://letterboxd.com/{username}/rss/",
        f"https://letterboxd.com/{username}/watchlist/rss/"
    ]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                resp = await client.get(url, headers=headers)
                print(f"URL: {url} | Status: {resp.status_code}")
            except Exception as e:
                print(f"URL: {url} | Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_rss())
