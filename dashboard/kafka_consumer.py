"""
Dashboard Kafka Consumer - Background consumer for word-stats topic

Maintains in-memory state of:
- Latest aggregated word counts
- Recent articles processed
- Connection status
"""

import json
import threading
from collections import deque
from datetime import datetime
from kafka import KafkaConsumer

from config import KAFKA_BROKER, KAFKA_TOPIC_STATS, TOP_WORDS_COUNT


class DashboardStatsConsumer:
    """Background consumer that maintains dashboard state"""

    def __init__(self, max_recent_articles=10):
        """
        Initialize consumer state

        Args:
            max_recent_articles: Number of recent articles to keep
        """
        # In-memory data stores
        self.word_counts = {}
        self.recent_articles = deque(maxlen=max_recent_articles)
        self.articles_processed = 0
        self.last_update = None
        self.is_connected = False

        # Thread management
        self._consumer = None
        self._thread = None
        self._running = False
        self._lock = threading.Lock()

    def start(self):
        """Start background consumer thread"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._thread.start()
        print("[DASHBOARD] Background Kafka consumer started")

    def stop(self):
        """Stop background consumer thread"""
        self._running = False
        if self._consumer:
            self._consumer.close()
        print("[DASHBOARD] Background Kafka consumer stopped")

    def _consume_loop(self):
        """Main consumer loop running in background thread"""
        try:
            self._consumer = KafkaConsumer(
                KAFKA_TOPIC_STATS,
                bootstrap_servers=KAFKA_BROKER,
                group_id='dashboard-consumer',
                auto_offset_reset='latest',
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            self.is_connected = True
            print(f"[DASHBOARD] Connected to Kafka topic: {KAFKA_TOPIC_STATS}")

            while self._running:
                messages = self._consumer.poll(timeout_ms=1000)

                for topic_partition, records in messages.items():
                    for record in records:
                        self._process_message(record.value)

        except Exception as e:
            print(f"[DASHBOARD] Kafka consumer error: {e}")
            self.is_connected = False

    def _process_message(self, message):
        """Process incoming message and update state"""
        msg_type = message.get('type')

        with self._lock:
            if msg_type == 'aggregated_stats':
                # Update aggregated word counts
                self.word_counts = message.get('word_counts', {})
                self.articles_processed = message.get('articles_processed', 0)
                self.last_update = datetime.now()

            elif msg_type == 'article_stats':
                # Add to recent articles
                article_info = {
                    'title': message.get('article_title', 'Unknown'),
                    'source': message.get('source', 'Unknown'),
                    'total_words': message.get('total_words', 0),
                    'processed_at': message.get('processed_at', '')
                }
                self.recent_articles.append(article_info)

                # Also update word counts from individual articles
                new_counts = message.get('word_counts', {})
                for word, count in new_counts.items():
                    self.word_counts[word] = self.word_counts.get(word, 0) + count

                self.last_update = datetime.now()

    def get_dashboard_data(self):
        """
        Get current dashboard data (thread-safe)

        Returns:
            Dictionary with top words, recent articles, and metadata
        """
        with self._lock:
            # Get top N words sorted by count
            sorted_words = sorted(
                self.word_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:TOP_WORDS_COUNT]

            return {
                'top_words': dict(sorted_words),
                'recent_articles': list(self.recent_articles),
                'articles_processed': self.articles_processed,
                'last_update': self.last_update.isoformat() if self.last_update else None,
                'is_connected': self.is_connected
            }


# Singleton instance for the dashboard
stats_consumer = DashboardStatsConsumer()
