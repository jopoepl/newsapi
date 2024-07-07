import asyncio
import logging
from database import insert_articles_bulk
from utils import ReadRss, get_domain, find_image_and_content, parse_date, find_image, find_article_content
import time
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def process_feed(url):
    try:
        feed = ReadRss(url)
        source = get_domain(url)
        articles = []
        for entry in feed.feed.entries:
            try:
                title = entry.title
                link = entry.link
                published = parse_date(entry.published)
                if source == 'gizmochina':
                    image = find_image(link)
                    description = find_article_content(link)
                else:
                    image = ''
                    description = ''
                articles.append({
                    "title": title,
                    "link": link,
                    "published": published,
                    "source": source,
                    "image": image,
                    "description": description
                })
            except Exception as e:
                logging.error(f"Error processing entry from {source}: {str(e)}")
        return articles
    except Exception as e:
        logging.error(f"Error processing feed {url}: {str(e)}")
        return []

async def main():
    urls = [
        "https://pandaily.com/feed/",
        'https://www.phonearena.com/feed',
        'https://www.sammobile.com/feed/',
        "https://www.androidpolice.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://wccftech.com/feed/",
        "https://www.androidauthority.com/feed/",
        "https://www.reutersagency.com/feed/?best-topics=tech&post_type=best",
        "https://www.scmp.com/rss/36/feed",
        "https://rss.cnbeta.com.tw/",
        "https://www.ithome.com/rss/",
        "https://hk.news.yahoo.com/tech/rss.xml",
        "https://www.gizmochina.com/feed/"
    ]

    while True:
        run_id = uuid.uuid4()
        logging.info(f"Starting new run. Run ID: {run_id}")

        try:
            tasks = [process_feed(url) for url in urls]
            results = await asyncio.gather(*tasks)
            all_articles = [article for result in results for article in result]

            inserted, updated = insert_articles_bulk(all_articles)
            logging.info(f"Run ID {run_id}: Inserted {inserted} new articles, updated {updated} existing articles")

        except Exception as e:
            logging.error(f"Run ID {run_id}: Error during processing: {str(e)}")

        logging.info(f"Run ID {run_id}: Waiting for 30 minutes before next run")


if __name__ == '__main__':
    asyncio.run(main())
