from bson.codec_options import CodecOptions
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi
import os
from datetime import datetime, timedelta
import pytz
from utils import parse_date

MONGO_URI = os.getenv('MONGO_URI')

if not MONGO_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['NewsAPI']
collection = db['All_News']



def check_connection():
    try:
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        print("MongoDB connection successful")
        print(f"Connected to database: {db.name}")
        print(f"Collections: {db.list_collection_names()}")
    except Exception as e:
        print(f"MongoDB connection failed: {e}")

def insert_articles_bulk(articles):
    # Get all links from the incoming articles
    new_links = set(article['link'] for article in articles)

    # Check which links already exist in the database
    existing_articles = list(collection.find(
        {"link": {"$in": list(new_links)}},
        projection={"link": 1, "published": 1, "_id": 0}
    ))

    existing_links = {doc['link']: doc['published'] for doc in existing_articles}

    # Filter out articles that already exist or are older
    new_articles = []
    for article in articles:
            existing_date = parse_date(existing_links.get(article['link']))
            new_date = parse_date(article.get('published'))

            if article['link'] not in existing_links:
                new_articles.append(article)
            elif new_date and existing_date:
                if new_date > existing_date:
                    new_articles.append(article)
            elif new_date and not existing_date:
                new_articles.append(article)

    if new_articles:
        # Prepare bulk insert operation
        operations = [UpdateOne(
            {"link": article["link"]},
            {"$set": article},
            upsert=True
        ) for article in new_articles]

        # Perform bulk insert
        result = collection.bulk_write(operations)
        return result.upserted_count, result.modified_count

    return 0, 0

def cleanup_old_articles(collection, days=30):
    collection = db[collection].with_options(codec_options=CodecOptions(tz_aware=True))
    cutoff_date = datetime.now(pytz.utc) - timedelta(days=days)
    result = collection.delete_many({"published": {"$lt": cutoff_date}})
    return result.deleted_count


check_connection()
