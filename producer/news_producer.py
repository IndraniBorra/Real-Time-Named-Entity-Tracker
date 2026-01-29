"""
News Producer - Fetches news from NewsAPI and sends to Kafka

Flow:
1. Connect to NewsAPI
2. Fetch latest articles
3. Send each article to Kafka topic 'news-articles'
4. Wait 5 minutes
5. Repeat
"""



import json
import time
import requests
from kafka import KafkaProducer
from datetime import datetime

# Import our configuration
from config import (
    KAFKA_BROKER,
    KAFKA_TOPIC_NEWS,
    NEWS_API_KEY,
    NEWS_API_URL,
    NEWS_API_COUNTRY,
    NEWS_API_CATEGORY,
    FETCH_INTERVAL
)


class NewsProducer:
    """Fetches news and produces messages to Kafka"""
    
    def __init__(self):
        """Initialize Kafka Producer connection"""
        print(f"[INFO] Connecting to Kafka broker: {KAFKA_BROKER}")
        
        # Create Kafka Producer
        # value_serializer: Converts Python dict to JSON bytes
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        print(f"[SUCCESS] Connected to Kafka!")
        print(f"[INFO] Will publish to topic: {KAFKA_TOPIC_NEWS}")
    
    
    def fetch_news(self):
        """
        Fetch news articles from NewsAPI
        
        Returns:
            list: List of article dictionaries, or empty list if error
        """
        print(f"\n[INFO] Fetching news from NewsAPI...")
        print(f"       Category: {NEWS_API_CATEGORY}, Country: {NEWS_API_COUNTRY}")
        
        # Build API request parameters
        params = {
            'country': NEWS_API_COUNTRY,
            'category': NEWS_API_CATEGORY,
            'apiKey': NEWS_API_KEY
        }
        
        try:
            # Make HTTP GET request to NewsAPI
            response = requests.get(NEWS_API_URL, params=params)
            response.raise_for_status()  # Raise error if status code is 4xx or 5xx
            
            # Parse JSON response
            data = response.json()
            
            # Check if request was successful
            if data.get('status') == 'ok':
                articles = data.get('articles', [])
                print(f"[SUCCESS] Fetched {len(articles)} articles")
                return articles
            else:
                print(f"[ERROR] API returned error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to fetch news: {e}")
            return []
    
    
    def send_to_kafka(self, article):
        """
        Send a single article to Kafka
        
        Args:
            article (dict): Article data from NewsAPI
        """
        # Prepare message with essential fields
        message = {
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'content': article.get('content', ''),
            'source': article.get('source', {}).get('name', 'Unknown'),
            'author': article.get('author', 'Unknown'),
            'publishedAt': article.get('publishedAt', ''),
            'url': article.get('url', ''),
            'timestamp': datetime.now().isoformat()  # When we processed it
        }
        
        # Send message to Kafka topic
        # This is ASYNCHRONOUS by default - doesn't wait for confirmation
        future = self.producer.send(KAFKA_TOPIC_NEWS, value=message)
        
        # Optional: Wait for confirmation (makes it synchronous)
        # Uncomment next line if you want to ensure message was received
        # record_metadata = future.get(timeout=10)
        
        print(f"[SENT] {message['title'][:60]}...")
    
    
    def run(self):
        """
        Main loop - continuously fetch and send news
        """
        print("\n" + "="*70)
        print("NEWS PRODUCER STARTED")
        print("="*70)
        print(f"Fetch interval: {FETCH_INTERVAL} seconds ({FETCH_INTERVAL//60} minutes)")
        print("Press Ctrl+C to stop")
        print("="*70 + "\n")
        
        try:
            while True:
                # Fetch news articles
                articles = self.fetch_news()
                
                # Send each article to Kafka
                for article in articles:
                    self.send_to_kafka(article)
                
                # Flush any pending messages
                self.producer.flush()
                print(f"[INFO] All messages sent. Sleeping for {FETCH_INTERVAL} seconds...")
                
                # Wait before next fetch
                time.sleep(FETCH_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n[INFO] Stopping producer...")
        finally:
            # Close Kafka connection gracefully
            self.producer.close()
            print("[INFO] Producer stopped. Goodbye!")


# Entry point - runs when you execute this file
if __name__ == "__main__":
    producer = NewsProducer()
    producer.run()
