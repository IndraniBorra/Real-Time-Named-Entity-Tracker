"""
Consumer Package - Processes news articles from Kafka

NLTK data is downloaded lazily when first needed.
"""

_nltk_ready = False

def ensure_nltk_data():
    """Download required NLTK datasets if not already done"""
    global _nltk_ready
    if _nltk_ready:
        return

    try:
        import nltk
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('stopwords', quiet=True)
        _nltk_ready = True
    except Exception as e:
        print(f"[WARNING] Failed to download NLTK data: {e}")
