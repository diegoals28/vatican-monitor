"""
Supabase Database Client for Vatican Monitor
"""
import os
from supabase import create_client, Client
from datetime import datetime

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')


def get_client() -> Client:
    """Get Supabase client instance."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


# ============ DATES ============

def get_dates() -> list:
    """Get all target dates."""
    client = get_client()
    result = client.table('target_dates').select('date').execute()
    return [row['date'] for row in result.data]


def add_date(date: str) -> bool:
    """Add a date to monitor."""
    client = get_client()
    try:
        client.table('target_dates').insert({'date': date}).execute()
        return True
    except Exception as e:
        print(f"Error adding date: {e}")
        return False


def remove_date(date: str) -> bool:
    """Remove a date from monitoring."""
    client = get_client()
    try:
        client.table('target_dates').delete().eq('date', date).execute()
        return True
    except Exception as e:
        print(f"Error removing date: {e}")
        return False


# ============ STATUS ============

def get_status() -> dict:
    """Get monitor status."""
    client = get_client()
    result = client.table('monitor_status').select('*').eq('id', 1).execute()
    if result.data:
        return result.data[0]
    return {
        'check_count': 0,
        'alerts_sent': 0,
        'last_check': None,
        'last_results': {}
    }


def update_status(check_count: int = None, alerts_sent: int = None,
                  last_check: str = None, last_results: dict = None) -> bool:
    """Update monitor status."""
    client = get_client()

    updates = {}
    if check_count is not None:
        updates['check_count'] = check_count
    if alerts_sent is not None:
        updates['alerts_sent'] = alerts_sent
    if last_check is not None:
        updates['last_check'] = last_check
    if last_results is not None:
        updates['last_results'] = last_results

    if updates:
        updates['updated_at'] = datetime.now().isoformat()
        try:
            client.table('monitor_status').upsert({
                'id': 1,
                **updates
            }).execute()
            return True
        except Exception as e:
            print(f"Error updating status: {e}")
            return False
    return True


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


# ============ ALERTED PRODUCTS ============

def get_alerted_products() -> set:
    """Get set of already alerted products."""
    client = get_client()
    result = client.table('alerted_products').select('product_key').execute()
    return {row['product_key'] for row in result.data}


def add_alerted_product(product_key: str) -> bool:
    """Add a product to alerted set."""
    client = get_client()
    try:
        client.table('alerted_products').insert({
            'product_key': product_key,
            'alerted_at': datetime.now().isoformat()
        }).execute()
        return True
    except:
        return False  # Probably already exists


def clear_alerted_products() -> bool:
    """Clear all alerted products."""
    client = get_client()
    try:
        client.table('alerted_products').delete().neq('id', 0).execute()
        return True
    except Exception as e:
        print(f"Error clearing alerted products: {e}")
        return False
