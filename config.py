import os
from dotenv import load_dotenv

load_dotenv()

# Kafka Configuration
KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC_NEWS = 'news-articles'
KAFKA_TOPIC_STATS = 'word-stats'

# NewsAPI Configuration  
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
NEWS_API_URL = 'https://newsapi.org/v2/top-headlines'
NEWS_API_COUNTRY = 'us'  # Can change to: in, gb, ca, etc.
NEWS_API_CATEGORY = 'business'  # Can be: business, sports, health, etc.

# Processing Configuration
FETCH_INTERVAL = 300  # Fetch news every 5 minutes (300 seconds)
TOP_WORDS_COUNT = 20  # Show top 20 words in dashboard
