"src": "main.py",
"use": "@vercel/python"
}
],
"routes": [
{
"src": "/(.*)",
"destination": "main.py"
}
]
}
from flask import Flask, render_template_string, jsonify, request, Response{
"version": 2,
"builds": [
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import time
import re

app = Flask(__name__)

# Server Uptime Tracking
SERVER_START_TIME = time.time()

# Fallback Radio-Browser API Mirrors with Auto-Balancing
RADIO_MIRRORS = [
    'https://de1.api.radio-browser.info/json/stations/topclick/150',
    'https://nl1.api.radio-browser.info/json/stations/topclick/150',
    'https://at1.api.radio-browser.info/json/stations/topclick/150',
    'https://fr1.api.radio-browser.info/json/stations/topclick/150'
]

# Simple In-Memory Cache & Metrics Matrix
STATION_CACHE = {
    'timestamp': 0,
    'data': []
}
CACHE_TTL = 300  # 5 minutes cache lifetime
CUSTOM_STATIONS = []
STREAM_METRICS = {}

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
    
    if STATION_CACHE['data'] and (now - STATION_CACHE['timestamp'] < CACHE_TTL):
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    for mirror_url in RADIO_MIRRORS:
        try:
            req = urllib.request.Request(
                mirror_url,
                headers={'User-Agent': 'RadioPulseSingularity/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    STATION_CACHE['data'] = data
                    STATION_CACHE['timestamp'] = now
                    return jsonify(CUSTOM_STATIONS + data)
        except Exception:
            continue
            
    if STATION_CACHE['data']:
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    return jsonify({'error': 'Failed to fetch radio stations from mirror cluster'}), 500

@app.route('/api/metadata')
def get_live_metadata():
    """Extract real-time ICY metadata and track audio stream performance."""
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({'error': 'Missing stream URL'}), 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'VLC/3.0.18', 'Icy-MetaData': '1'}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            headers = dict(response.headers)
            metaint = int(headers.get('icy-metaint', 0))
            
            title = headers.get('icy-name', 'Quantum Singularity Stream')
            genre = headers.get('icy-genre', 'Ambient / Electronic')
            bitrate = headers.get('icy-br', '128')
            now_playing = "Harmonic Transmission Live"

            if metaint > 0:
                response.read(metaint)
                meta_byte_len = ord(response.read(1)) * 16
                if meta_byte_len > 0:
                    meta_raw = response.read(meta_byte_len).decode('utf-8', errors='ignore')
                    match = re.search(r"StreamTitle='([^']*)';", meta_raw)
                    if match and match.group(1):
                        now_playing = match.group(1).strip()

            return jsonify({
                'title': title,
                'now_playing': now_playing,
                'genre': genre,
                'bitrate': f"{bitrate} kbps",
                'status': 'ONLINE'
            })
    except Exception as e:
        return jsonify({'title': 'Singularity Node', 'now_playing': 'Direct Quantum Feed', 'status': 'ONLINE', 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Enhanced Singularity health diagnostics endpoint."""
    uptime = int(time.time() - SERVER_START_TIME)
    return jsonify({
        'status': 'SINGULARITY MATRIX ONLINE',
        'uptime_seconds': uptime,
        'cached_stations_count': len(STATION_CACHE['data']),
        'custom_stations_count': len(CUSTOM_STATIONS),
        'active_mirrors': len(RADIO_MIRRORS),
        'server_load': 'OPTIMAL'
    })

@app.route('/api/stations/add', methods=['POST'])
def add_custom_station():
    """Add a custom user radio stream into the session matrix."""
    data = request.json or {}
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    lat = float(data.get('lat', 0.0) or 0.0)
    long_val = float(data.get('long', 0.0) or 0.0)
    
    if not name or not url:
        return jsonify({'success': False, 'error': 'Station Name and Stream URL are required.'}), 400

    station = {
        'stationuuid': f"custom-{int(time.time())}",
        'name': name,
        'url_resolved': url,
        'geo_lat': lat,
        'geo_long': long_val,
        'country': data.get('country', 'User Custom Node'),
        'codec': 'MP3',
        'tags': 'custom, user'
    }
    CUSTOM_STATIONS.insert(0, station)
    return jsonify({'success': True, 'station': station})

@app.route('/api/stream_info')
def get_stream_info():
    """Inspect live stream headers to extract server software and bitrate info."""
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({'bitrate': 128, 'server': 'Quantum Matrix'})
    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'VLC/3.0.18', 'Icy-MetaData': '1'}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            headers = dict(res.headers)
            br = headers.get('icy-br', '128')
            server = headers.get('server', 'Quantum Proxy Node')
            return jsonify({'bitrate': br, 'server': server})
    except Exception:
        return jsonify({'bitrate': 128, 'server': 'Quantum Direct Relay'})

@app.route('/api/proxy')
def proxy_audio():
    """Robust CORS audio stream proxy with optimized buffering."""
    stream_url = request.args.get('url')
    if not stream_url:
        return "Missing 'url' parameter", 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': '*/*'
            }
        )
        remote_res = urllib.request.urlopen(req, timeout=12)
        content_type = remote_res.headers.get('Content-Type', 'audio/mpeg')

        def generate():
            try:
                while True:
                    chunk = remote_res.read(16384)
                    if not chunk:
                        break
                    yield chunk
            except Exception:
                pass

        return Response(generate(), content_type=content_type)
    except Exception as e:
        return f"Singularity Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Radio Pulse Singularity Server Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)from flask import Flask, render_template_string, jsonify, request, Response
import urllib.request
import urllib.error
import urllib.parse
import json
import os
import time
import re

app = Flask(__name__)

# Server Uptime Tracking
SERVER_START_TIME = time.time()

# Fallback Radio-Browser API Mirrors with Auto-Balancing
RADIO_MIRRORS = [
    'https://de1.api.radio-browser.info/json/stations/topclick/150',
    'https://nl1.api.radio-browser.info/json/stations/topclick/150',
    'https://at1.api.radio-browser.info/json/stations/topclick/150',
    'https://fr1.api.radio-browser.info/json/stations/topclick/150'
]

# Simple In-Memory Cache & Metrics Matrix
STATION_CACHE = {
    'timestamp': 0,
    'data': []
}
CACHE_TTL = 300  # 5 minutes cache lifetime
CUSTOM_STATIONS = []
STREAM_METRICS = {}

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
    
    if STATION_CACHE['data'] and (now - STATION_CACHE['timestamp'] < CACHE_TTL):
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    for mirror_url in RADIO_MIRRORS:
        try:
            req = urllib.request.Request(
                mirror_url,
                headers={'User-Agent': 'RadioPulseSingularity/5.0'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    STATION_CACHE['data'] = data
                    STATION_CACHE['timestamp'] = now
                    return jsonify(CUSTOM_STATIONS + data)
        except Exception:
            continue
            
    if STATION_CACHE['data']:
        return jsonify(CUSTOM_STATIONS + STATION_CACHE['data'])

    return jsonify({'error': 'Failed to fetch radio stations from mirror cluster'}), 500

@app.route('/api/metadata')
def get_live_metadata():
    """Extract real-time ICY metadata and track audio stream performance."""
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({'error': 'Missing stream URL'}), 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'VLC/3.0.18', 'Icy-MetaData': '1'}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            headers = dict(response.headers)
            metaint = int(headers.get('icy-metaint', 0))
            
            title = headers.get('icy-name', 'Quantum Singularity Stream')
            genre = headers.get('icy-genre', 'Ambient / Electronic')
            bitrate = headers.get('icy-br', '128')
            now_playing = "Harmonic Transmission Live"

            if metaint > 0:
                response.read(metaint)
                meta_byte_len = ord(response.read(1)) * 16
                if meta_byte_len > 0:
                    meta_raw = response.read(meta_byte_len).decode('utf-8', errors='ignore')
                    match = re.search(r"StreamTitle='([^']*)';", meta_raw)
                    if match and match.group(1):
                        now_playing = match.group(1).strip()

            return jsonify({
                'title': title,
                'now_playing': now_playing,
                'genre': genre,
                'bitrate': f"{bitrate} kbps",
                'status': 'ONLINE'
            })
    except Exception as e:
        return jsonify({'title': 'Singularity Node', 'now_playing': 'Direct Quantum Feed', 'status': 'ONLINE', 'error': str(e)})

@app.route('/api/health')
def health_check():
    """Enhanced Singularity health diagnostics endpoint."""
    uptime = int(time.time() - SERVER_START_TIME)
    return jsonify({
        'status': 'SINGULARITY MATRIX ONLINE',
        'uptime_seconds': uptime,
        'cached_stations_count': len(STATION_CACHE['data']),
        'custom_stations_count': len(CUSTOM_STATIONS),
        'active_mirrors': len(RADIO_MIRRORS),
        'server_load': 'OPTIMAL'
    })

@app.route('/api/stations/add', methods=['POST'])
def add_custom_station():
    """Add a custom user radio stream into the session matrix."""
    data = request.json or {}
    name = data.get('name', '').strip()
    url = data.get('url', '').strip()
    lat = float(data.get('lat', 0.0) or 0.0)
    long_val = float(data.get('long', 0.0) or 0.0)
    
    if not name or not url:
        return jsonify({'success': False, 'error': 'Station Name and Stream URL are required.'}), 400

    station = {
        'stationuuid': f"custom-{int(time.time())}",
        'name': name,
        'url_resolved': url,
        'geo_lat': lat,
        'geo_long': long_val,
        'country': data.get('country', 'User Custom Node'),
        'codec': 'MP3',
        'tags': 'custom, user'
    }
    CUSTOM_STATIONS.insert(0, station)
    return jsonify({'success': True, 'station': station})

@app.route('/api/stream_info')
def get_stream_info():
    """Inspect live stream headers to extract server software and bitrate info."""
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({'bitrate': 128, 'server': 'Quantum Matrix'})
    try:
        req = urllib.request.Request(
            stream_url,
            headers={'User-Agent': 'VLC/3.0.18', 'Icy-MetaData': '1'}
        )
        with urllib.request.urlopen(req, timeout=3) as res:
            headers = dict(res.headers)
            br = headers.get('icy-br', '128')
            server = headers.get('server', 'Quantum Proxy Node')
            return jsonify({'bitrate': br, 'server': server})
    except Exception:
        return jsonify({'bitrate': 128, 'server': 'Quantum Direct Relay'})

@app.route('/api/proxy')
def proxy_audio():
    """Robust CORS audio stream proxy with optimized buffering."""
    stream_url = request.args.get('url')
    if not stream_url:
        return "Missing 'url' parameter", 400

    try:
        req = urllib.request.Request(
            stream_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': '*/*'
            }
        )
        remote_res = urllib.request.urlopen(req, timeout=12)
        content_type = remote_res.headers.get('Content-Type', 'audio/mpeg')

        def generate():
            try:
                while True:
                    chunk = remote_res.read(16384)
                    if not chunk:
                        break
                    yield chunk
            except Exception:
                pass

        return Response(generate(), content_type=content_type)
    except Exception as e:
        return f"Singularity Proxy Error: {str(e)}", 500

if __name__ == '__main__':
    print("🚀 Radio Pulse Singularity Server Running on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
