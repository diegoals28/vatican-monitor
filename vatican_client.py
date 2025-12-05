"""
Cliente para la API de tickets de los Museos Vaticanos
Versión actualizada con los nuevos endpoints (Diciembre 2025)
"""
import os
import requests
import random
import time
from typing import Optional, List, Dict
from config import (
    VATICAN_API_BASE,
    DEFAULT_VISIT_TAG,
    DEFAULT_VISITOR_NUM,
    DEFAULT_WHO_ID
)

# Webshare API Configuration
WEBSHARE_API_KEY = os.getenv('WEBSHARE_API_KEY', '')

# User agents reales de navegadores comunes
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

BASE_URL = 'https://tickets.museivaticani.va'


class WebshareProxyManager:
    """Gestiona proxies de Webshare via API."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.proxies = []
        self.current_index = 0

    def fetch_proxies(self) -> bool:
        """Obtiene lista de proxies desde Webshare API."""
        if not self.api_key:
            return False

        try:
            response = requests.get(
                "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100",
                headers={"Authorization": f"Token {self.api_key}"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            self.proxies = []
            for proxy in data.get('results', []):
                proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['port']}"
                self.proxies.append({
                    'http': proxy_url,
                    'https': proxy_url,
                    'address': proxy['proxy_address'],
                    'country': proxy.get('country_code', 'XX')
                })

            print(f"Webshare: {len(self.proxies)} proxies cargados")
            return len(self.proxies) > 0

        except Exception as e:
            print(f"Error obteniendo proxies de Webshare: {e}")
            return False

    def get_random_proxy(self) -> Optional[dict]:
        """Retorna un proxy aleatorio."""
        if not self.proxies:
            self.fetch_proxies()

        if self.proxies:
            proxy = random.choice(self.proxies)
            return {'http': proxy['http'], 'https': proxy['https']}
        return None

    def get_next_proxy(self) -> Optional[dict]:
        """Retorna el siguiente proxy en rotación."""
        if not self.proxies:
            self.fetch_proxies()

        if self.proxies:
            proxy = self.proxies[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.proxies)
            print(f"Usando proxy: {proxy['address']} ({proxy['country']})")
            return {'http': proxy['http'], 'https': proxy['https']}
        return None


# Instancia global del gestor de proxies
proxy_manager = WebshareProxyManager(WEBSHARE_API_KEY) if WEBSHARE_API_KEY else None


class VaticanClient:
    def __init__(self):
        self.session = requests.Session()
        self.proxy_manager = proxy_manager
        self._rotate_proxy()
        self._update_headers()
        self._init_session()

    def _rotate_proxy(self):
        """Rota al siguiente proxy disponible."""
        if self.proxy_manager:
            proxy = self.proxy_manager.get_next_proxy()
            if proxy:
                self.session.proxies.update(proxy)

    def _update_headers(self):
        """Actualiza headers con User-Agent aleatorio."""
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': f'{BASE_URL}/',
            'Origin': BASE_URL,
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })

    def _init_session(self):
        """Inicializa sesión visitando la página para obtener cookies."""
        try:
            # Visitar página principal para obtener JSESSIONID
            self.session.headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            response = self.session.get(f'{BASE_URL}/home', timeout=30)

            # Restaurar Accept para API
            self.session.headers['Accept'] = 'application/json, text/plain, */*'

            cookies = list(self.session.cookies.keys())
            print(f"Sesión inicializada. Cookies: {cookies}")

            if 'JSESSIONID' not in cookies:
                print("ADVERTENCIA: No se obtuvo JSESSIONID")

        except Exception as e:
            print(f"Error inicializando sesión: {e}")

    def refresh_session(self):
        """Refresca la sesión si las cookies expiraron."""
        print("Refrescando sesion...")
        self.session.cookies.clear()
        self._rotate_proxy()  # Rotar proxy al refrescar
        self._init_session()

    def _random_delay(self, min_sec=1, max_sec=3):
        """Añade un delay aleatorio entre peticiones."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)

    def get_calendar(self, tag: str = DEFAULT_VISIT_TAG, who_id: str = DEFAULT_WHO_ID,
                     visitor_num: int = DEFAULT_VISITOR_NUM, lang: str = 'it') -> dict:
        """
        Obtiene el calendario con las fechas disponibles.

        Args:
            tag: Tag del tipo de visita (ej: 'MV-Biglietti')
            who_id: ID del tipo de visitante (1=Singoli, 2=Gruppi, etc.)
            visitor_num: Número de visitantes
            lang: Idioma

        Returns:
            dict con 'calendar': lista de {date, state}
            state: 1 = abierto, 0 = cerrado
        """
        self._update_headers()

        params = {
            'lang': lang,
            'tag': tag,
            'whoId': who_id,
            'visitorNum': visitor_num
        }

        try:
            response = self.session.get(
                f'{VATICAN_API_BASE}/search/calendar',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error obteniendo calendario: {e}")
            return {'calendar': []}

    def get_available_dates(self, tag: str = DEFAULT_VISIT_TAG) -> List[str]:
        """
        Obtiene solo las fechas que están abiertas (state=1) y son futuras.
        """
        from datetime import datetime

        today = datetime.now().date()
        calendar = self.get_calendar(tag)

        available = []
        for day in calendar.get('calendar', []):
            if day.get('state') != 1:
                continue

            # Parsear fecha DD/MM/YYYY
            try:
                date_parts = day['date'].split('/')
                date_obj = datetime(
                    int(date_parts[2]),
                    int(date_parts[1]),
                    int(date_parts[0])
                ).date()

                # Solo fechas futuras o de hoy
                if date_obj >= today:
                    available.append(day['date'])
            except (ValueError, IndexError):
                continue

        return available

    def search_availability(
        self,
        visit_date: str,
        visitor_num: int = DEFAULT_VISITOR_NUM,
        tag: str = DEFAULT_VISIT_TAG,
        who_id: str = DEFAULT_WHO_ID,
        lang: str = 'it'
    ) -> dict:
        """
        Busca disponibilidad de productos para una fecha específica.

        Args:
            visit_date: Fecha en formato DD/MM/YYYY
            visitor_num: Número de visitantes
            tag: Tag del tipo de visita
            who_id: ID del tipo de visitante
            lang: Idioma

        Returns:
            dict con 'visits': lista de productos disponibles
            Cada producto tiene: id, name, availability, who, etc.
            availability: AVAILABLE, LOW_AVAILABILITY, SOLD_OUT, NOT_ALLOWED
        """
        self._random_delay(1, 3)
        self._update_headers()

        params = {
            'lang': lang,
            'visitorNum': visitor_num,
            'visitDate': visit_date,
            'page': 0,
            'tag': tag,
            'who': ''  # Vacío para ver todos los productos
        }

        try:
            response = self.session.get(
                f'{VATICAN_API_BASE}/search/resultPerTag',
                params=params,
                timeout=30
            )

            # Si hay error 500, intentar refrescar sesión
            if response.status_code == 500:
                print(f"Error 500 para {visit_date}, refrescando sesión...")
                self.refresh_session()
                self._random_delay(2, 4)
                response = self.session.get(
                    f'{VATICAN_API_BASE}/search/resultPerTag',
                    params=params,
                    timeout=30
                )

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error buscando disponibilidad para {visit_date}: {e}")
            return {'visits': [], 'totalResults': 0}

    def get_available_products(
        self,
        visit_date: str,
        visitor_num: int = DEFAULT_VISITOR_NUM,
        tag: str = DEFAULT_VISIT_TAG,
        who_id: str = DEFAULT_WHO_ID,
        product_filter: str = None
    ) -> List[Dict]:
        """
        Obtiene solo los productos disponibles (AVAILABLE o LOW_AVAILABILITY).

        Args:
            visit_date: Fecha en formato DD/MM/YYYY
            visitor_num: Número de visitantes
            tag: Tag del tipo de visita
            who_id: ID del tipo de visitante
            product_filter: Filtro opcional para el nombre del producto

        Returns:
            Lista de productos disponibles
        """
        data = self.search_availability(visit_date, visitor_num, tag, who_id)

        # Productos a excluir
        excluded_products = ['palazzo papale', 'castel gandolfo']

        available = []
        for visit in data.get('visits', []):
            availability = visit.get('availability', '')
            if availability in ['AVAILABLE', 'LOW_AVAILABILITY']:
                name = visit.get('name', '').lower()

                # Excluir productos no deseados
                if any(excluded in name for excluded in excluded_products):
                    continue

                # Aplicar filtro de producto si existe
                if product_filter:
                    if product_filter.lower() not in name:
                        continue
                available.append(visit)

        return available

    def check_availability(
        self,
        target_dates: List[str] = None,
        visitor_num: int = DEFAULT_VISITOR_NUM,
        tag: str = DEFAULT_VISIT_TAG,
        who_id: str = DEFAULT_WHO_ID,
        product_filter: str = None
    ) -> dict:
        """
        Verifica disponibilidad en las fechas objetivo.

        Args:
            target_dates: Lista de fechas a verificar (DD/MM/YYYY). Si es None, verifica todas.
            visitor_num: Número de visitantes
            tag: Tag del tipo de visita
            who_id: ID del tipo de visitante
            product_filter: Filtro para nombre de producto (ej: 'Biglietti d'ingresso')

        Returns:
            dict con las fechas que tienen disponibilidad y sus productos
        """
        results = {}

        # Si no hay fechas objetivo, obtener todas las fechas abiertas
        dates_to_check = target_dates if target_dates else self.get_available_dates(tag)

        for date in dates_to_check:
            if not date:  # Skip empty strings
                continue

            available_products = self.get_available_products(
                date, visitor_num, tag, who_id, product_filter
            )

            if available_products:
                results[date] = available_products

        return results

    def get_filter_info(self, tag: str = DEFAULT_VISIT_TAG, lang: str = 'it') -> dict:
        """
        Obtiene información del filtro (tipos de visitante, áreas, etc.)
        """
        self._update_headers()

        params = {
            'lang': lang,
            'tag': tag
        }

        try:
            response = self.session.get(
                f'{VATICAN_API_BASE}/search/filter',
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error obteniendo filtros: {e}")
            return {}


# Test
if __name__ == '__main__':
    import sys
    import io
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    client = VaticanClient()

    print("\n=== Información del filtro ===")
    filter_info = client.get_filter_info()
    if filter_info:
        print(f"Tipos de visitante: {[w['descr'] for w in filter_info.get('who', [])]}")
        print(f"Rango de fechas: {filter_info.get('dateRange', {})}")

    print("\n=== Fechas abiertas (futuras) ===")
    open_dates = client.get_available_dates()
    print(f"Fechas abiertas: {open_dates[:10]}")

    if open_dates:
        test_date = open_dates[0]  # Primera fecha abierta (futura)
        print(f"\n=== Disponibilidad para {test_date} ===")
        data = client.search_availability(test_date, visitor_num=1)

        for visit in data.get('visits', [])[:5]:
            status = "✅" if visit['availability'] == 'AVAILABLE' else \
                     "⚠️" if visit['availability'] == 'LOW_AVAILABILITY' else "❌"
            print(f"  {status} {visit['name'][:60]}... - {visit['availability']}")

        print(f"\n=== Productos 'Biglietti' disponibles para {test_date} ===")
        available = client.get_available_products(test_date, visitor_num=1, product_filter='Biglietti')
        for p in available:
            print(f"  ✅ {p['name']} - {p['availability']}")
