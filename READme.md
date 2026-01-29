## Project Overview:
Build a streaming data pipeline that fetches real-time news articles, processes them to extract trending keywords/topics, and displays the results on a live dashboard.

## Project Outline: (Real-Time Analytics/Stream Processing)
- Fectching the real-time data from NewsAPI : "https://newsapi.org/v2/everything?q=tesla&from=2025-11-29&sortBy=publishedAt&apiKey=198ecb4d47b14bfbb3799d8568271fcc"
- Performing word count on tg econtent
- visulization

## Project Flow:

NewsAPI -> Producer(fetches api) -> Topic(content of api) -> Processor(python file : word count) -> Consumer:resultant topic(excuted data) -> Visualization(Dashboard)

## SetUP:

- Producer: Python (requests + kafka-python)
- Processing: Kafka Streams or Apache Flink
- Storage: Elasticsearch 
- Visualization: Kibana
- Deployment: Docker Compose


Learning Points:
- Kafka is used for real time streaming content, verstile on CRUD operation, stored data default by 7 days.
- Docker: custom envirnment to run the desried custom services together for the project
- Zookeeper: manages kafka brokers like a coordinator who manages everything, health status 
- Kafka Brokers: actual message storage/distribution system
- topic: channel/category for messages
- we need curser in the next line to get the last senetnce in consumer side (real -time): message boundaries(each line = one message):  The console producer sends a message when you press Enter (newline character).
- --from-beginning lets you re-read old messages in consumer side.
- kafka uses binary protocol over TCP, python doesnt speak this and can be handled by "kafka-python" library.
    - connecting to the kafka broker(localhpst:9092)
    - serializing data (Python objects -> bytes)
    - Handling retries and acknowledgements
    - Managing connection
- 



## docker file explanation:

#### Zookeeper Section:
- image: confluentinc/cp-zookeeper:7.5.0 - Pre-built Zookeeper image
- ZOOKEEPER_CLIENT_PORT: 2181 - Port where Kafka connects to Zookeeper
- ZOOKEEPER_TICK_TIME: 2000 - Heartbeat interval (2 seconds)
- ports: "2181:2181" - Expose port to your machine
#### Kafka Section:
- depends_on: zookeeper - Start Kafka AFTER Zookeeper is ready
- ports: "9092:9092" - IMPORTANT: Your Python code connects here!
- KAFKA_BROKER_ID: 1 - Unique ID (useful when multiple brokers)
- KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181 - How Kafka finds Zookeeper
- KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092 - Address clients use to connect
- KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1 - No replication (we have 1 broker)


## Docker commands:
- docker-compose up: start the service i.e., docker-compose.yml 
- "-d": runs in background, doesnt block my terminal
- docker-compose ps: checks if its running
- docker-compose logs kafka | tail 20: check first 20 logs 
- docker exec -it kafka: run command inside kafka container
- kafka-topics --create : Create a new topic
- bootstrap-server localhost:9092 : Connect to Kafka broker
- topic test-topic : Name of the topic
- partitions 1 : One partition (we'll learn this later)
- replication-factor 1 : No copies (we have only 1 broker)
- --list : list the all topics

## Topic

- to create topic: 
```
kafka-topics --create 
  --topic test-topic 

```
- list all topics:
```
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
```
- send messages
```
docker exec -it kafka kafka-console-producer \
  --bootstrap-server localhost:9092 \
  --topic test-topic
```
- recieve messages
```
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test-topic \
  --from-beginning
```


## Producer

1. Connect to Kafka broker (localhost:9092)
2. Fetch news from NewsAPI
3. For each article:
   - Convert article to JSON
   - Send to Kafka topic 'news-articles'
4. Sleep for 5 minutes
5. Repeat


## Consumer

1. Connect to Kafka broker (localhost:9092)
2. Read messages from 'news-articles' topic
3. For each article:
   - Extract text (title + description + content)
   - Use NLTK to tokenize words
   - Remove stop words (the, is, and, etc.)
   - Count word frequencies
4. Send results to 'word-stats' topic
5. Repeat for each new message

Learning Points:
- NLTK: Natural Language Toolkit - library for text processing
- Tokenization: breaking text into individual words
- Stop words: common words that don't add meaning (the, is, and, for, etc.)
- We filter HTML artifacts like "/li", "&amp" using special character detection
- Consumer uses consumer group 'news-analytics-consumer' so multiple consumers can share work
- auto_offset_reset='earliest' means start from beginning if first time


## Dashboard

Real-time web interface showing trending keywords

1. Background thread connects to 'word-stats' topic
2. Updates in-memory data (word counts, recent articles)
3. Flask serves web page at http://localhost:8000
4. JavaScript auto-refreshes every 3 seconds
5. Shows:
   - Trending keywords with bar chart
   - Recent articles processed
   - Total statistics

Learning Points:
- Flask: Python web framework - creates the web server
- Background thread: runs Kafka consumer separately so web page stays responsive
- AJAX polling: JavaScript fetches new data every few seconds without page reload
- threading.Lock: makes sure data updates are thread-safe (no conflicts between background thread and web requests)
- daemon thread: automatically stops when main program stops


## How to Run Everything

### Step 1: Start Kafka (Docker)
```bash
cd kafka-news-analytics
docker-compose up -d
```
Check if running:
```bash
docker-compose ps
```

### Step 2: Create .env file
Create file named `.env` in project root:
```
NEWS_API_KEY=your_api_key_here
```
Get free API key from: https://newsapi.org

### Step 3: Install Python dependencies
```bash
python -m venv venv
source venv/bin/activate  
pip install -r requirements.txt
```

### Step 4: Run Producer (Terminal 1)
```bash
cd kafka-news-analytics
source venv/bin/activate
python -m producer.news_producer
```
You'll see: "[SENT] Article title..."

### Step 5: Run Consumer (Terminal 2)
```bash
cd kafka-news-analytics
source venv/bin/activate
python -m consumer.news_consumer
```
You'll see: "[PROCESSED] Article title..."

### Step 6: Run Dashboard (Terminal 3)
```bash
cd kafka-news-analytics
source venv/bin/activate
python -m dashboard.app
```
Open browser: http://localhost:8000


## Verifying Data Flow

Check messages in Kafka topics:

**news-articles topic:**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic news-articles \
  --from-beginning \
  --max-messages 5
```

**word-stats topic:**
```bash
docker exec -it kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic word-stats \
  --from-beginning \
  --max-messages 5
```


## Project Structure

```
kafka-news-analytics/
├── producer/
│   └── news_producer.py       # Fetches news from API
├── consumer/
│   ├── news_consumer.py       # Main consumer loop
│   ├── text_processor.py      # NLTK word processing
│   ├── stats_producer.py      # Publishes to word-stats
│   └── utils.py               # Helper functions
├── dashboard/
│   ├── app.py                 # Flask web server
│   ├── kafka_consumer.py      # Background Kafka consumer
│   ├── templates/
│   │   ├── base.html          # Base template
│   │   └── dashboard.html     # Main dashboard
│   └── static/css/
│       └── style.css          # Styling
├── config.py                  # Shared configuration
├── docker-compose.yml         # Kafka + Zookeeper setup
├── requirements.txt           # Python dependencies
└── .env                       # API keys (not in git!)
```


## Troubleshooting


**NLTK data not found?**
- Downloads automatically on first run
- Or manually: `python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"`

**Kafka not starting?**
- Check Docker is running: `docker ps`
- Check logs: `docker-compose logs kafka`
- Restart: `docker-compose down && docker-compose up -d`

**No data in dashboard?**
- Make sure producer is running (fetches news)
- Make sure consumer is running (processes news)
- Check Kafka topics have messages (use verification commands above)


## Future Ideas to Try

**Better NLP - spaCy + BERT instead of NLTK:**
- Want to test what difference it makes using spaCy NER vs simple word count
- Try fine-tuned BERT for entity recognition
- See if accuracy improves for finding companies, people, locations

**Real streaming data with high volume:**
- Twitter API or Reddit API instead of just NewsAPI
- Want to see how pipeline handles 500K+ messages/day
- Test if current setup breaks or works fine with real stream

**PySpark for parallel processing:**
- Replace single consumer with PySpark Structured Streaming
- Try batch processing instead of one-by-one
- See performance difference with distributed processing

**ELK Stack (Elasticsearch + Kibana):**
- Store data in Elasticsearch instead of in-memory
- Use Kibana for dashboard instead of Flask
- Try different visualizations - word clouds, time series, heatmaps

**Sentiment Analysis:**
- Add sentiment to tweets/news - positive or negative?
- See which topics are getting positive vs negative coverage
- Track sentiment changes over time

**Different representations:**
- Try various chart types - bar, pie, scatter, network graphs
- Geographic maps showing where news is coming from
- Time-series showing keyword trends by hour/day

Just rough ideas to experiment with and see what works better


## What I Learned

- Kafka: real-time message streaming between services
- Producer-Consumer pattern: decoupled services communicate via topics
- Docker: run Kafka+Zookeeper without installing them
- NLTK: process natural language text in Python
- Flask: build web dashboards quickly
- Threading: run background tasks while serving web requests
- Message serialization: converting Python objects to bytes for Kafka

