"""
Dashboard Flask Application - Real-time news analytics visualization

Routes:
- GET /           : Main dashboard page
- GET /api/stats  : JSON API endpoint for AJAX polling
- GET /health     : Health check endpoint
"""

from flask import Flask, render_template, jsonify
from dashboard.kafka_consumer import stats_consumer


def create_app():
    """Flask application factory"""
    app = Flask(__name__)

    # Configuration
    app.config['REFRESH_INTERVAL'] = 3000  # milliseconds

    # Start background Kafka consumer
    stats_consumer.start()

    # Routes
    @app.route('/')
    def dashboard():
        """Main dashboard page"""
        data = stats_consumer.get_dashboard_data()
        return render_template(
            'dashboard.html',
            data=data,
            refresh_interval=app.config['REFRESH_INTERVAL']
        )

    @app.route('/api/stats')
    def api_stats():
        """JSON API for AJAX polling"""
        data = stats_consumer.get_dashboard_data()
        return jsonify(data)

    @app.route('/health')
    def health():
        """Health check endpoint"""
        data = stats_consumer.get_dashboard_data()
        return jsonify({
            'status': 'healthy' if data['is_connected'] else 'degraded',
            'kafka_connected': data['is_connected'],
            'articles_processed': data['articles_processed']
        })

    return app


# Entry point for running directly
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=True)
