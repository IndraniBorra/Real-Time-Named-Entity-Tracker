"""
News Consumer - Consumes news articles from Kafka and processes them

Flow:
1. Connect to Kafka consumer on 'news-articles' topic
2. Poll for messages
3. Deserialize JSON message
4. Process text with TextProcessor (NLTK)
5. Aggregate word counts
6. Publish stats via StatsProducer
7. Handle graceful shutdown
"""

import json
import signal
from collections import Counter
from kafka import KafkaConsumer

from config import KAFKA_BROKER, KAFKA_TOPIC_NEWS, TOP_WORDS_COUNT
from consumer.text_processor import TextProcessor
from consumer.stats_producer import StatsProducer


class NewsConsumer:
    """Consumes news articles from Kafka, processes them, and publishes stats"""

    def __init__(self, group_id: str = 'news-analytics-consumer'):
        """
        Initialize Kafka Consumer and processing components

        Args:
            group_id: Kafka consumer group ID
        """
        print(f"[INFO] Connecting to Kafka broker: {KAFKA_BROKER}")

        # Initialize Kafka Consumer
        self.consumer = KafkaConsumer(
            KAFKA_TOPIC_NEWS,
            bootstrap_servers=KAFKA_BROKER,
            group_id=group_id,
            auto_offset_reset='earliest',  # Start from beginning if no offset
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )

        print(f"[SUCCESS] Connected to Kafka!")
        print(f"[INFO] Listening on topic: {KAFKA_TOPIC_NEWS}")

        # Initialize processing components
        self.text_processor = TextProcessor()
        self.stats_producer = StatsProducer()

        # Aggregation state
        self.aggregated_counts = Counter()
        self.articles_processed = 0

        # Shutdown flag
        self.running = True

    def setup_signal_handlers(self):
        """Register signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)

    def _shutdown_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\n[INFO] Shutdown signal received...")
        self.running = False

    def process_message(self, message) -> dict:
        """
        Process a single Kafka message

        Args:
            message: Kafka message object

        Returns:
            Dictionary of word counts
        """
        article = message.value
        word_counts = self.text_processor.process_article(article)
        return word_counts

    def aggregate_counts(self, word_counts: dict):
        """
        Add word counts to running aggregation

        Args:
            word_counts: Dictionary of word frequencies
        """
        self.aggregated_counts.update(word_counts)
        self.articles_processed += 1

    def get_top_words(self) -> dict:
        """
        Get top N words from aggregated counts

        Returns:
            Dictionary of top words and their counts
        """
        return dict(self.aggregated_counts.most_common(TOP_WORDS_COUNT))

    def run(self):
        """Main consumer loop"""
        self.setup_signal_handlers()

        print("\n" + "=" * 70)
        print("NEWS CONSUMER STARTED")
        print("=" * 70)
        print(f"Consumer group: news-analytics-consumer")
        print(f"Publishing stats to: word-stats")
        print("Press Ctrl+C to stop")
        print("=" * 70 + "\n")

        try:
            while self.running:
                # Poll with timeout (returns dict of topic-partition -> messages)
                message_batch = self.consumer.poll(timeout_ms=1000)

                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Process message
                            word_counts = self.process_message(message)

                            # Aggregate
                            self.aggregate_counts(word_counts)

                            # Prepare metadata for stats
                            article = message.value
                            metadata = {
                                'source': article.get('source', 'Unknown'),
                                'title': article.get('title', 'Unknown')
                            }

                            # Publish individual stats
                            self.stats_producer.publish_stats(word_counts, metadata)

                            # Print progress
                            title = article.get('title', 'Unknown')[:50]
                            print(f"[PROCESSED] {title}...")

                        except json.JSONDecodeError as e:
                            print(f"[ERROR] Failed to deserialize message: {e}")
                            continue
                        except Exception as e:
                            print(f"[ERROR] Failed to process message: {e}")
                            continue

                # Periodically publish aggregated stats (every 10 articles)
                if self.articles_processed > 0 and self.articles_processed % 10 == 0:
                    top_words = self.get_top_words()
                    self.stats_producer.publish_aggregated_stats(
                        top_words,
                        self.articles_processed
                    )

        except Exception as e:
            print(f"[ERROR] Consumer error: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Clean up resources"""
        print("\n[INFO] Shutting down consumer...")

        # Publish final aggregated stats
        if self.articles_processed > 0:
            print(f"[INFO] Publishing final stats for {self.articles_processed} articles...")
            top_words = self.get_top_words()
            self.stats_producer.publish_aggregated_stats(
                top_words,
                self.articles_processed
            )

        # Close connections
        self.stats_producer.close()
        self.consumer.close()

        print(f"[INFO] Processed {self.articles_processed} articles total")
        print("[INFO] Consumer stopped. Goodbye!")


# Entry point - runs when you execute this file
if __name__ == "__main__":
    consumer = NewsConsumer()
    consumer.run()
