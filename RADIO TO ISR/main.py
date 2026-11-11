from flask import Flask, render_template_string, jsonify, request, Response
import urllib.request
import urllib.error
import json
import os
import time

app = Flask(__name__)

# Fallback Radio-Browser API Mirrors
RADIO_MIRRORS = [
    'https://de1.api.radio-browser.info/json/stations/topclick/100',
    'https://nl1.api.radio-browser.info/json/stations/topclick/100',
    'https://at1.api.radio-browser.info/json/stations/topclick/100'
]

# Simple In-Memory Cache
STATION_CACHE = {
    'timestamp': 0,
    'data': []
}
CACHE_TTL = 300  # 5 minutes cache lifetime

@app.route('/')
def index():
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return render_template_string(html_content)
    return "<h1>Error: index.html not found</h1>", 404

@app.route('/api/stations')
def get_stations():
    """Backend endpoint to reliably fetch top radio stations with server-side mirror failover and in-memory caching."""
    now = time.time()
    
    # Return cached station data if valid
    if STATION_CACHE['data'] and (now - STATION_CACHE['timestamp'] < CACHE_TTL):
        return jsonify(STATION_CACHE['data'])

    for mirror_url in RADIO_MIRRORS:
        try:
            req = urllib.request.Request(
                mirror_url,
                headers={'User-Agent': 'RadioPulseQuantumNexus/2.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    STATION_CACHE['data'] = data
                    STATION_CACHE['timestamp'] = now
                    return jsonify(data)
        except Exception:
            continue
            
    # Fallback to stale cache if mirrors fail
    if STATION_CACHE['data']:
        return jsonify(STATION_CACHE['data'])

    return jsonify({'error': 'Failed to fetch radio stations from mirror cluster'}), 500

@app.route('/api/search')
def search_stations():
    """Server-side station search endpoint across Radio-Browser API cluster."""
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    search_url = f"https://de1.api.radio-browser.info/json/stations/byname/{urllib.parse.quote(query)}?limit=40"
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'RadioPulseQuantumNexus/2.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/proxy')
def proxy_audio():
    """CORS audio stream proxy to bypass browser restriction policies on HTTP radio streams."""
    stream_url = request.args.get('url')
    if not stream_url:
        return "Missing 'url' parameter", 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        remote_res = urllib.request.urlopen(req, timeout=8)
        content_type = remote_res.headers.get('Content-Type', 'audio/mpeg')

        def generate():
            while True:
                chunk = remote_res.read(4096)
                if not chunk:
                    break
                yield chunk

        return Response(generate(), content_type=content_type)
    except Exception as e:
        return f"Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Radio Pulse Server Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
