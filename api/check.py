"""
Vercel Serverless Function - Check Availability
This is the main endpoint that checks Vatican ticket availability.
Can be triggered manually or via Vercel Cron.
"""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.db import (
    get_dates, get_status, update_status, increment_check_count,
    increment_alerts_sent, get_alerted_products, add_alerted_product
)
from vatican_client import VaticanClient
from telegram_notifier import TelegramNotifier


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET request (for Vercel Cron)"""
        self._check_availability()

    def do_POST(self):
        """Handle POST request (for manual trigger)"""
        self._check_availability()

    def _check_availability(self):
        try:
            # Get configuration from environment
            visit_tag = os.environ.get('VISIT_TAG', 'MV-Biglietti')
            visitor_num = int(os.environ.get('VISITOR_NUM', 1))
            who_id = os.environ.get('WHO_ID', '1')
            product_filter = os.environ.get('PRODUCT_FILTER', '')

            # Get target dates from database
            target_dates = get_dates()

            if not target_dates:
                self._send_response({
                    'success': True,
                    'message': 'No hay fechas configuradas',
                    'availability': {}
                })
                return

            # Initialize Vatican client
            client = VaticanClient()
            notifier = TelegramNotifier()

            # Check availability
            availability = {}
            for date in target_dates:
                if not date:
                    continue

                products = client.get_available_products(
                    visit_date=date,
                    visitor_num=visitor_num,
                    tag=visit_tag,
                    who_id=who_id,
                    product_filter=product_filter if product_filter else None
                )

                if products:
                    availability[date] = products

            # Increment check count
            check_count = increment_check_count()

            # Update last results
            update_status(
                last_check=datetime.now().isoformat(),
                last_results=availability
            )

            # Filter new availability (not alerted before)
            alerted = get_alerted_products()
            new_availability = {}

            for date, products in availability.items():
                new_products = []
                for product in products:
                    key = f"{date}_{product.get('id', 0)}"
                    if key not in alerted:
                        new_products.append(product)
                        add_alerted_product(key)

                if new_products:
                    new_availability[date] = new_products

            # Send Telegram alert for new availability
            alerts_sent = 0
            if new_availability and notifier.is_configured():
                success = notifier.send_availability_alert(new_availability)
                if success:
                    alerts_sent = increment_alerts_sent()

            self._send_response({
                'success': True,
                'check_count': check_count,
                'dates_checked': len(target_dates),
                'availability': availability,
                'new_availability': new_availability,
                'alerts_sent': alerts_sent
            })

        except Exception as e:
            self._send_response({
                'success': False,
                'error': str(e)
            }, 500)

    def _send_response(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
