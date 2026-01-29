"""
Stats Producer - Publishes word statistics to Kafka word-stats topic
"""

import json
from datetime import datetime
from kafka import KafkaProducer

from config import KAFKA_BROKER, KAFKA_TOPIC_STATS


class StatsProducer:
    """Publishes word statistics to Kafka word-stats topic"""

    def __init__(self):
        """Initialize Kafka producer for stats topic"""
        print(f"[INFO] Connecting stats producer to Kafka: {KAFKA_BROKER}")

        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BROKER,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        print(f"[INFO] Stats producer will publish to: {KAFKA_TOPIC_STATS}")

    def publish_stats(self, word_counts: dict, metadata: dict):
        """
        Publish individual article word statistics

        Args:
            word_counts: Dictionary of word frequencies
            metadata: Article metadata (source, title, etc.)
        """
        message = {
            'type': 'article_stats',
            'word_counts': word_counts,
            'source': metadata.get('source', 'Unknown'),
            'article_title': metadata.get('title', 'Unknown'),
            'processed_at': datetime.now().isoformat(),
            'total_words': sum(word_counts.values())
        }

        try:
            self.producer.send(KAFKA_TOPIC_STATS, value=message)
        except Exception as e:
            print(f"[ERROR] Failed to publish stats: {e}")

    def publish_aggregated_stats(self, aggregated_counts: dict, article_count: int):
        """
        Publish batch aggregated statistics

        Args:
            aggregated_counts: Dictionary of aggregated word frequencies
            article_count: Number of articles in this aggregation
        """
        message = {
            'type': 'aggregated_stats',
            'word_counts': aggregated_counts,
            'articles_processed': article_count,
            'processed_at': datetime.now().isoformat(),
            'total_words': sum(aggregated_counts.values())
        }

        try:
            self.producer.send(KAFKA_TOPIC_STATS, value=message)
            self.producer.flush()
            print(f"[STATS] Published aggregated stats for {article_count} articles")
        except Exception as e:
            print(f"[ERROR] Failed to publish aggregated stats: {e}")

    def flush(self):
        """Flush pending messages"""
        self.producer.flush()

    def close(self):
        """Flush and close producer connection"""
        self.producer.flush()
        self.producer.close()
        print("[INFO] Stats producer closed")
