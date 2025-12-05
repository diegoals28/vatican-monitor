import os
from dotenv import load_dotenv

load_dotenv(override=True)

# Telegram Config
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

# Vatican API Config
VATICAN_API_BASE = 'https://tickets.museivaticani.va/api'

# Tipos de visita disponibles (tags)
# - MV-Biglietti: Biglietti Musei Vaticani (entrada general)
# - VG-Musei: Visita Guidata Musei Vaticani
# - VG-GiardMusei: Visita Guidata Giardini e Musei
# - Pellegrini: Pellegrini di Speranza
DEFAULT_VISIT_TAG = os.getenv('VISIT_TAG', 'MV-Biglietti')

# Tipos de visitante (whoId)
# 1 = Singoli (individuales)
# 2 = Gruppi (grupos)
# 3 = Famiglie (familias)
# 4 = Pellegrini (peregrinos)
# 5 = Scuole (escuelas)
# 6 = Università (universidades)
DEFAULT_WHO_ID = os.getenv('WHO_ID', '1')  # Singoli por defecto

# Número de visitantes
DEFAULT_VISITOR_NUM = int(os.getenv('VISITOR_NUM', 1))

# Filtro de producto (opcional) - para buscar solo productos específicos
# Ejemplo: 'Biglietti d'ingresso' para solo entradas básicas
PRODUCT_FILTER = os.getenv('PRODUCT_FILTER', "Biglietti d'ingresso")

# Monitor Config
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 1800))  # Default: cada 30 min

# Fechas a monitorear (formato DD/MM/YYYY)
# Dejar vacío para monitorear todas las fechas disponibles
TARGET_DATES = os.getenv('TARGET_DATES', '').split(',') if os.getenv('TARGET_DATES') else []

# Máximo de fechas a consultar por verificación (para evitar detección)
MAX_DATES_PER_CHECK = int(os.getenv('MAX_DATES_PER_CHECK', 5))

# ===== Variables legacy (para compatibilidad) =====
# Estas ya no se usan pero se mantienen para no romper imports
VATICAN_CALENDAR_URL = f'{VATICAN_API_BASE}/search/calendar'
VATICAN_TIMEAVAIL_URL = f'{VATICAN_API_BASE}/search/resultPerTag'
DEFAULT_VISIT_TYPE_ID = ''  # Ya no se usa
DEFAULT_AREA_ID = 1
PREFERRED_TIMES = []  # Ya no aplica en la nueva API
