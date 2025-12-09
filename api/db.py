"""
Supabase Database Client for Vatican Monitor
Using REST API directly to avoid async issues in serverless
"""
import os
import json
import requests
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')


def _headers():
    return {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }


def _api_url(table: str) -> str:
    return f"{SUPABASE_URL}/rest/v1/{table}"


# ============ DATES ============

def get_dates() -> list:
    """Get all target dates."""
    try:
        response = requests.get(
            _api_url('target_dates'),
            headers=_headers(),
            params={'select': 'date'}
        )
        if response.status_code == 200:
            return [row['date'] for row in response.json()]
        return []
    except Exception as e:
        print(f"Error getting dates: {e}")
        return []


def add_date(date: str) -> bool:
    """Add a date to monitor."""
    try:
        response = requests.post(
            _api_url('target_dates'),
            headers=_headers(),
            json={'date': date}
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error adding date: {e}")
        return False


def remove_date(date: str) -> bool:
    """Remove a date from monitoring."""
    try:
        response = requests.delete(
            _api_url('target_dates'),
            headers=_headers(),
            params={'date': f'eq.{date}'}
        )
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error removing date: {e}")
        return False


# ============ STATUS ============

def get_status() -> dict:
    """Get monitor status."""
    try:
        response = requests.get(
            _api_url('monitor_status'),
            headers=_headers(),
            params={'id': 'eq.1'}
        )
        if response.status_code == 200 and response.json():
            return response.json()[0]
        return {
            'check_count': 0,
            'alerts_sent': 0,
            'last_check': None,
            'last_results': {}
        }
    except Exception as e:
        print(f"Error getting status: {e}")
        return {
            'check_count': 0,
            'alerts_sent': 0,
            'last_check': None,
            'last_results': {}
        }


def update_status(check_count: int = None, alerts_sent: int = None,
                  last_check: str = None, last_results: dict = None) -> bool:
    """Update monitor status."""
    updates = {'id': 1}
    if check_count is not None:
        updates['check_count'] = check_count
    if alerts_sent is not None:
        updates['alerts_sent'] = alerts_sent
    if last_check is not None:
        updates['last_check'] = last_check
    if last_results is not None:
        updates['last_results'] = last_results
    updates['updated_at'] = datetime.now().isoformat()

    try:
        headers = _headers()
        headers['Prefer'] = 'resolution=merge-duplicates'
        response = requests.post(
            _api_url('monitor_status'),
            headers=headers,
            json=updates
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error updating status: {e}")
        return False


def increment_check_count() -> int:
    """Increment and return new check count."""
    status = get_status()
    new_count = status.get('check_count', 0) + 1
    update_status(check_count=new_count)
    return new_count


def increment_alerts_sent() -> int:
    """Increment and return new alerts count."""
    status = get_status()
    new_count = status.get('alerts_sent', 0) + 1
    update_status(alerts_sent=new_count)
    return new_count


def update_status_with_results(last_check: str, last_results: dict,
                                increment_check: bool = True,
                                increment_alert: bool = False) -> dict:
    """
    Update status with results and optionally increment counters in a single operation.
    Returns the updated status.
    """
    status = get_status()
    updates = {
        'id': 1,
        'last_check': last_check,
        'last_results': last_results,
        'updated_at': datetime.now().isoformat()
    }

    if increment_check:
        updates['check_count'] = status.get('check_count', 0) + 1
    if increment_alert:
        updates['alerts_sent'] = status.get('alerts_sent', 0) + 1

    try:
        headers = _headers()
        headers['Prefer'] = 'resolution=merge-duplicates'
        response = requests.post(
            _api_url('monitor_status'),
            headers=headers,
            json=updates
        )
        if response.status_code in [200, 201]:
            return updates
    except Exception as e:
        print(f"Error updating status with results: {e}")

    return status


# ============ ALERTED PRODUCTS ============

def get_alerted_products() -> set:
    """Get set of already alerted products."""
    try:
        response = requests.get(
            _api_url('alerted_products'),
            headers=_headers(),
            params={'select': 'product_key'}
        )
        if response.status_code == 200:
            return {row['product_key'] for row in response.json()}
        return set()
    except Exception as e:
        print(f"Error getting alerted products: {e}")
        return set()


def add_alerted_product(product_key: str) -> bool:
    """Add a product to alerted set."""
    try:
        response = requests.post(
            _api_url('alerted_products'),
            headers=_headers(),
            json={
                'product_key': product_key,
                'alerted_at': datetime.now().isoformat()
            }
        )
        return response.status_code in [200, 201]
    except:
        return False


def add_alerted_products_batch(product_keys: list) -> bool:
    """Add multiple products to alerted set in a single request."""
    if not product_keys:
        return True

    now = datetime.now().isoformat()
    records = [{'product_key': key, 'alerted_at': now} for key in product_keys]

    try:
        headers = _headers()
        headers['Prefer'] = 'resolution=ignore-duplicates'
        response = requests.post(
            _api_url('alerted_products'),
            headers=headers,
            json=records
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Error adding alerted products batch: {e}")
        return False


def clear_alerted_products() -> bool:
    """Clear all alerted products."""
    try:
        response = requests.delete(
            _api_url('alerted_products'),
            headers=_headers(),
            params={'id': 'gt.0'}
        )
        return response.status_code in [200, 204]
    except Exception as e:
        print(f"Error clearing alerted products: {e}")
        return False
