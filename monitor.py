"""
Monitor de disponibilidad de tickets de los Museos Vaticanos
Versión actualizada con los nuevos endpoints (Diciembre 2025)
"""
import sys
import io
import time
import random
from datetime import datetime
from typing import Set
from apscheduler.schedulers.background import BackgroundScheduler
from vatican_client import VaticanClient
from telegram_notifier import TelegramNotifier
from config import (
    CHECK_INTERVAL_SECONDS,
    TARGET_DATES,
    DEFAULT_VISIT_TAG,
    DEFAULT_WHO_ID,
    DEFAULT_VISITOR_NUM,
    PRODUCT_FILTER,
    MAX_DATES_PER_CHECK
)

# Fix encoding for Windows console (emojis)
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class VaticanMonitor:
    def __init__(self):
        self.client = VaticanClient()
        self.notifier = TelegramNotifier()
        self.scheduler = BackgroundScheduler()

        # Estado para evitar alertas duplicadas
        self.alerted_products: Set[str] = set()  # formato: "DD/MM/YYYY_productId"

        # Último resultado para la interfaz web
        self.last_check_time = None
        self.last_results = {}
        self.check_count = 0
        self.alerts_sent = 0

    def _product_key(self, date: str, product_id: int) -> str:
        """Genera clave única para un producto en una fecha."""
        return f"{date}_{product_id}"

    def check_and_alert(self):
        """Ejecuta verificación y envía alertas si hay disponibilidad."""
        self.check_count += 1
        self.last_check_time = datetime.now()

        print(f"\n[{self.last_check_time.strftime('%H:%M:%S')}] Verificando disponibilidad...")

        try:
            # Si hay fechas objetivo, usarlas; sino obtener fechas aleatorias
            if TARGET_DATES and TARGET_DATES[0]:
                dates_to_check = TARGET_DATES
            else:
                # Obtener todas las fechas abiertas y seleccionar unas pocas aleatorias
                all_dates = self.client.get_available_dates(DEFAULT_VISIT_TAG)
                # Priorizar fechas cercanas (primeras 30) y seleccionar aleatoriamente
                priority_dates = all_dates[:30] if len(all_dates) > 30 else all_dates
                dates_to_check = random.sample(
                    priority_dates,
                    min(MAX_DATES_PER_CHECK, len(priority_dates))
                )
                print(f"  Consultando {len(dates_to_check)} fechas aleatorias: {', '.join(dates_to_check)}")

            # Obtener disponibilidad para esas fechas
            availability = {}
            for date in dates_to_check:
                if not date:
                    continue

                products = self.client.get_available_products(
                    visit_date=date,
                    visitor_num=DEFAULT_VISITOR_NUM,
                    tag=DEFAULT_VISIT_TAG,
                    who_id=DEFAULT_WHO_ID,
                    product_filter=PRODUCT_FILTER
                )

                if products:
                    availability[date] = products

            self.last_results = availability

            if not availability:
                print("  No hay disponibilidad")
                return

            # Filtrar productos que no se han alertado aún
            new_availability = {}
            for date, products in availability.items():
                new_products = []
                for product in products:
                    key = self._product_key(date, product.get('id', 0))
                    if key not in self.alerted_products:
                        new_products.append(product)
                        self.alerted_products.add(key)

                if new_products:
                    new_availability[date] = new_products

            if new_availability:
                # Mostrar en consola
                print("  🎫 ¡NUEVA DISPONIBILIDAD!")
                for date, products in new_availability.items():
                    print(f"    📅 {date}:")
                    for product in products:
                        print(f"      ✅ {product.get('name', 'N/A')[:50]} - {product.get('availability', 'N/A')}")

                # Enviar alerta por Telegram
                if self.notifier.is_configured():
                    success = self.notifier.send_availability_alert(new_availability)
                    if success:
                        self.alerts_sent += 1
                        print("  📱 Alerta enviada por Telegram")
                    else:
                        print("  ⚠️ Error enviando alerta")
                else:
                    print("  ⚠️ Telegram no configurado")
            else:
                print("  (disponibilidad ya alertada anteriormente)")

        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            if self.notifier.is_configured():
                self.notifier.send_error_alert(str(e))

    def clear_alerted_slots(self):
        """Limpia los productos alertados (para re-alertar)."""
        self.alerted_products.clear()
        print("Historial de alertas limpiado")

    def start(self, interval_seconds: int = None):
        """Inicia el monitor con el intervalo especificado."""
        interval = interval_seconds or CHECK_INTERVAL_SECONDS

        print(f"🚀 Iniciando monitor de Museos Vaticanos")
        print(f"⏱️  Intervalo: cada {interval} segundos")
        print(f"🎫 Tipo de visita: {DEFAULT_VISIT_TAG}")
        print(f"👤 Tipo de visitante: {'Singoli' if DEFAULT_WHO_ID == '1' else DEFAULT_WHO_ID}")
        print(f"👥 Número de visitantes: {DEFAULT_VISITOR_NUM}")

        if PRODUCT_FILTER:
            print(f"🔍 Filtro de producto: {PRODUCT_FILTER}")

        if TARGET_DATES and TARGET_DATES[0]:
            print(f"📅 Fechas objetivo: {', '.join(TARGET_DATES)}")
        else:
            print("📅 Monitoreando todas las fechas disponibles")

        if self.notifier.is_configured():
            print("📱 Notificaciones Telegram: ✅ Activas")
            self.notifier.send_status_update(
                f"Monitor iniciado. Verificando cada {interval}s"
            )
        else:
            print("📱 Notificaciones Telegram: ❌ No configurado")

        print("-" * 50)

        # Ejecutar primera verificación inmediatamente
        self.check_and_alert()

        # Programar verificaciones periódicas
        self.scheduler.add_job(
            self.check_and_alert,
            'interval',
            seconds=interval,
            id='vatican_check'
        )
        self.scheduler.start()

    def stop(self):
        """Detiene el monitor."""
        self.scheduler.shutdown()
        print("Monitor detenido")

    def get_status(self) -> dict:
        """Obtiene el estado actual para la interfaz web."""
        return {
            'running': self.scheduler.running,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'check_count': self.check_count,
            'alerts_sent': self.alerts_sent,
            'last_results': self.last_results,
            'alerted_products_count': len(self.alerted_products),
            'target_dates': TARGET_DATES,
            'visit_tag': DEFAULT_VISIT_TAG,
            'visitor_num': DEFAULT_VISITOR_NUM,
            'product_filter': PRODUCT_FILTER,
            'interval_seconds': CHECK_INTERVAL_SECONDS
        }


# Instancia global para uso en la app Flask
monitor = VaticanMonitor()


if __name__ == '__main__':
    # Ejecutar monitor en modo standalone
    try:
        monitor.start()
        print("\nPresiona Ctrl+C para detener\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
        print("\n👋 Monitor detenido")
