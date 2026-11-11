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

# User-added custom stations storage
CUSTOM_STATIONS = []

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
    
    # Return cached station data combined with custom stations
    if STATION_CACHE['data'] and (now - STATION_CACHE['timestamp'] < CACHE_TTL):
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    for mirror_url in RADIO_MIRRORS:
        try:
            req = urllib.request.Request(
                mirror_url,
                headers={'User-Agent': 'RadioPulseQuantumNexus/3.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    STATION_CACHE['data'] = data
                    STATION_CACHE['timestamp'] = now
                    return jsonify(CUSTOM_STATIONS + data)
        except Exception:
            continue
            
    # Fallback to stale cache if mirrors fail
    if STATION_CACHE['data']:
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    return jsonify({'error': 'Failed to fetch radio stations from mirror cluster'}), 500

@app.route('/api/stations/add', methods=['POST'])
def add_custom_station():
    """Endpoint for adding user-defined radio stream URLs."""
    try:
        body = request.get_json() or {}
        name = body.get('name', 'Custom Cyber Stream').strip()
        url = body.get('url', '').strip()
        country = body.get('country', 'Custom Node').strip()
        lat = float(body.get('lat', 0.0))
        long_val = float(body.get('long', 0.0))

        if not url:
            return jsonify({'error': 'Stream URL is required'}), 400

        custom_entry = {
            'stationuuid': f'custom-{int(time.time()*1000)}',
            'name': name,
            'url_resolved': url,
            'country': country,
            'codec': 'STREAM',
            'geo_lat': lat if lat != 0 else None,
            'geo_long': long_val if long_val != 0 else None,
            'tags': 'custom,user-stream'
        }
        CUSTOM_STATIONS.insert(0, custom_entry)
        return jsonify({'success': True, 'station': custom_entry})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stream_info')
def stream_info():
    """Server-side inspection of audio stream headers to return real-time stream metadata."""
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({'error': 'Missing stream URL'}), 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'Mozilla/5.0', 'Icy-MetaData': '1'}
        )
        with urllib.request.urlopen(req, timeout=4) as res:
            headers = dict(res.headers)
            bitrate = headers.get('icy-br', headers.get('content-bitrate', '128'))
            server = headers.get('icy-name', headers.get('Server', 'Cyber Audio Matrix'))
            content_type = headers.get('Content-Type', 'audio/mpeg')
            return jsonify({
                'bitrate': bitrate,
                'server': server,
                'content_type': content_type,
                'status': 'ONLINE'
            })
    except Exception as e:
        return jsonify({'status': 'UNCHECKED', 'error': str(e)})

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
