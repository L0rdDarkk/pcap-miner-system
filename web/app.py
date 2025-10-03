#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, send_file
import os
import json
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

RESULTS_DIR = os.getenv('RESULTS_DIR', '/data/results')
PCAP_DIR = os.getenv('PCAP_DIR', '/data/pcaps')

print("=" * 50)
print("PCAP WEB UI STARTING")
print("=" * 50)
print(f"Results directory: {RESULTS_DIR}")
print(f"PCAP directory: {PCAP_DIR}")
print("=" * 50)

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/api/analyses')
def get_analyses():
    """Get list of all PCAP analyses"""
    analyses = []
    
    try:
        for result_file in Path(RESULTS_DIR).glob('*.json'):
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    
                    timestamp = data.get('timestamp', 0)
                    analyses.append({
                        'id': result_file.stem,
                        'filename': data.get('filename', 'Unknown'),
                        'timestamp': timestamp,
                        'status': data.get('status', 'unknown'),
                        'date': datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else 'N/A',
                        'exit_code': data.get('exit_code', -1)
                    })
            except Exception as e:
                print(f"Error reading {result_file}: {e}")
        
        # Sort by timestamp, newest first
        analyses.sort(key=lambda x: x['timestamp'], reverse=True)
        
    except Exception as e:
        print(f"Error scanning results directory: {e}")
    
    return jsonify(analyses)

@app.route('/api/analysis/<analysis_id>')
def get_analysis_detail(analysis_id):
    """Get detailed analysis results"""
    result_file = Path(RESULTS_DIR) / f"{analysis_id}.json"
    
    if not result_file.exists():
        return jsonify({'error': 'Analysis not found'}), 404
    
    try:
        with open(result_file, 'r') as f:
            data = json.load(f)
        
        return jsonify({
            'filename': data.get('filename'),
            'timestamp': data.get('timestamp'),
            'status': data.get('status'),
            'exit_code': data.get('exit_code'),
            'error': data.get('error'),
            'raw_output': data.get('pcap_miner_output', ''),
            'stderr': data.get('pcap_miner_stderr', '')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/<pcap_name>')
def download_pcap(pcap_name):
    """Download original PCAP file"""
    pcap_path = Path(PCAP_DIR) / pcap_name
    
    if not pcap_path.exists():
        return jsonify({'error': 'PCAP not found'}), 404
    
    return send_file(pcap_path, as_attachment=True)

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🌐 Starting web server on port 8080...")
    app.run(host='0.0.0.0', port=8080, debug=False)
