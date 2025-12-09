"""
Vercel Serverless Function - Get Status
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db import get_status, get_dates


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            status = get_status()
            dates = get_dates()

            response = {
                'running': True,
                'check_count': status.get('check_count', 0),
                'alerts_sent': status.get('alerts_sent', 0),
                'last_check': status.get('last_check'),
                'last_results': status.get('last_results', {}),
                'target_dates': dates,
                'visit_tag': os.environ.get('VISIT_TAG', 'MV-Biglietti'),
                'visitor_num': int(os.environ.get('VISITOR_NUM', 1)),
                'product_filter': os.environ.get('PRODUCT_FILTER', ''),
                'interval_seconds': int(os.environ.get('CHECK_INTERVAL_SECONDS', 1800))
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'max-age=5')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
