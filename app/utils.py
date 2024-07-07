import feedparser
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import aiohttp
import asyncio
from dateutil import parser
import pytz
import cloudscraper
import re



headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def parse_date(date_string):
    if isinstance(date_string, str):
        try:
            date = parser.parse(date_string)
            if date.tzinfo is None:
                date = pytz.utc.localize(date)
            return date.astimezone(pytz.utc)
        except ValueError:
                    return None
        return date_str

def get_domain(url):
    parsed_url = urlparse(url)
    hostname = parsed_url.hostname
    parts = hostname.split('.')
    if len(parts) >= 2 and parts[-1] in ['com', 'net', 'org', 'edu', 'gov', 'co', 'uk', 'de', 'jp', 'fr', 'au', 'us', 'ru', 'ch', 'it', 'nl', 'se', 'no', 'es', 'mil']:
        return parts[-2]
    elif len(parts) >= 3:
        return parts[-3]
    else:
        return parts[0]

class ReadRss:
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers if headers else {}
        self.feed = self.fetch_feed()

    def fetch_feed(self):
        return feedparser.parse(self.url, request_headers=self.headers)

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

async def find_image_and_content(url):
    async with aiohttp.ClientSession() as session:
        html = await fetch(session, url)
        soup = BeautifulSoup(html, 'html.parser')
        img = soup.find('meta', property='og:image')
        image_url = img['content'] if img else "Not Found"

        paragraphs = soup.find_all('p')
        content = ' '.join([p.text for p in paragraphs])
        content = content[:500] + '...' if len(content) > 500 else content

        return image_url, content

def find_article_content(url):
    scraper = cloudscraper.create_scraper()  # Create a CloudScraper instance
    response = scraper.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    article_content = soup.find('div', class_='td-post-content')
    # print(article_content, "soup check")
    if article_content:
           # If you want the text content inside the div
           article_text = article_content.get_text(strip=True)
        #    print(article_content.get_text(strip=True), "content found")
           return article_text
    else:
        print("No Content found")
    return None

def find_og_image(soup):
    """Find the Open Graph image in the HTML."""
    og_image = soup.find('meta', attrs={'property': re.compile(r'^\s*og:image\s*$', re.IGNORECASE)})
    if og_image and og_image.get('content'):
        return og_image['content']
    return None


def find_twitter_image(soup):
    """Find the Twitter image in the HTML."""
    twitter_image = soup.find('meta', attrs={'name': re.compile(r'^\s*twitter:image\s*$', re.IGNORECASE)})
    if twitter_image and twitter_image.get('content'):
        return twitter_image['content']
    return None

def find_main_image(soup):
    """Find the main image in the article content."""
    main_image = soup.find('img')
    if main_image and main_image.get('src'):
        return main_image['src']
    return None

def find_image(url):
    """Fetch the URL and scrape the main or featured image."""
    scraper = cloudscraper.create_scraper()  # Create a CloudScraper instance
    response = scraper.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Print HTML content for debugging
    # print(soup.prettify())  # Uncomment this line to see the parsed HTML

    # Try to find the Open Graph image
    image_url = find_og_image(soup)
    if image_url:
        return image_url

    # Try to find the Twitter image
    image_url = find_twitter_image(soup)
    if image_url:
        return image_url

    # Try to find the main image in the article content
    image_url = find_main_image(soup)
    if image_url:
        return image_url

    return None
