"""
Text Processor - NLTK-based text processing for news articles

Handles tokenization, stop-word removal, and word frequency counting.
"""

import string
from collections import Counter

# Lazy NLTK imports to avoid slow startup
_word_tokenize = None
_stopwords = None


def _load_nltk():
    """Load NLTK modules lazily"""
    global _word_tokenize, _stopwords
    if _word_tokenize is None:
        from consumer import ensure_nltk_data
        ensure_nltk_data()
        from nltk.tokenize import word_tokenize as wt
        from nltk.corpus import stopwords as sw
        _word_tokenize = wt
        _stopwords = sw


class TextProcessor:
    """Processes text content from news articles using NLTK"""

    def __init__(self):
        """Initialize with English stop words"""
        _load_nltk()
        # Load English stop words
        self.stop_words = set(_stopwords.words('english'))

        # Add custom stop words common in news content
        self.custom_stop_words = {
            'said', 'would', 'could', 'also', 'one', 'two', 'three',
            'new', 'like', 'get', 'may', 'might', 'know', 'way',
            'chars', 'say', 'says', 'year', 'years', 'make', 'made',
            'wed', 'thu', 'fri', 'sat', 'sun', 'mon', 'tue',  # Day abbreviations
            'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',  # Month abbrevs
            'com', 'www', 'http', 'https'  # URL fragments
        }
        self.stop_words.update(self.custom_stop_words)

        # Punctuation set for filtering
        self.punctuation = set(string.punctuation)

    def extract_text(self, article: dict) -> str:
        """
        Combine title, description, and content into one text

        Args:
            article: Article dictionary with title, description, content

        Returns:
            Combined text string
        """
        title = article.get('title') or ''
        description = article.get('description') or ''
        content = article.get('content') or ''

        # Combine all text fields
        combined = f"{title} {description} {content}"
        return combined

    def tokenize(self, text: str) -> list:
        """
        Tokenize text into words using NLTK word_tokenize

        Args:
            text: Input text string

        Returns:
            List of tokens
        """
        if not text:
            return []

        try:
            tokens = _word_tokenize(text.lower())
            return tokens
        except Exception:
            # Fallback to simple split if NLTK fails
            return text.lower().split()

    def clean_tokens(self, tokens: list) -> list:
        """
        Remove stop words, punctuation, and normalize tokens

        Args:
            tokens: List of raw tokens

        Returns:
            List of cleaned tokens
        """
        cleaned = []
        for token in tokens:
            # Skip if too short (less than 3 chars)
            if len(token) < 3:
                continue

            # Skip if it's punctuation
            if token in self.punctuation:
                continue

            # Skip if it contains only punctuation/numbers
            if not any(c.isalpha() for c in token):
                continue

            # Skip tokens with special characters (HTML artifacts like /li, &amp, etc.)
            if any(c in token for c in '/<>&[]{}'):
                continue

            # Skip stop words
            if token in self.stop_words:
                continue

            cleaned.append(token)

        return cleaned

    def count_words(self, tokens: list) -> dict:
        """
        Count word frequencies

        Args:
            tokens: List of cleaned tokens

        Returns:
            Dictionary of word counts
        """
        return dict(Counter(tokens))

    def process_article(self, article: dict) -> dict:
        """
        Full processing pipeline: extract -> tokenize -> clean -> count

        Args:
            article: Article dictionary

        Returns:
            Dictionary of word frequencies
        """
        try:
            # Extract text from article
            text = self.extract_text(article)

            # Tokenize
            tokens = self.tokenize(text)

            # Clean tokens
            cleaned = self.clean_tokens(tokens)

            # Count frequencies
            word_counts = self.count_words(cleaned)

            return word_counts

        except Exception as e:
            print(f"[ERROR] Text processing failed: {e}")
            return {}
