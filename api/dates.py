"""
Vercel Serverless Function - Manage Dates
"""
from http.server import BaseHTTPRequestHandler
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db import get_dates, add_date, remove_date


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            dates = get_dates()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'dates': dates}).encode())
        except Exception as e:
            self._error(str(e))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            date = data.get('date', '').strip()
            if not date:
                self._error('Fecha requerida', 400)
                return

            # Validate format DD/MM/YYYY
            import re
            if not re.match(r'^\d{2}/\d{2}/\d{4}$', date):
                self._error('Formato invalido. Use DD/MM/YYYY', 400)
                return

            dates = get_dates()
            if date in dates:
                self._error('Fecha ya existe', 400)
                return

            add_date(date)
            dates = get_dates()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'dates': dates}).encode())

        except Exception as e:
            self._error(str(e))

    def do_DELETE(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)

            date = data.get('date', '').strip()
            if not date:
                self._error('Fecha requerida', 400)
                return

            remove_date(date)
            dates = get_dates()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True, 'dates': dates}).encode())

        except Exception as e:
            self._error(str(e))

    def _error(self, message, code=500):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode())
