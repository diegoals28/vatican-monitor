"""
Aplicación web para el monitor de tickets de los Museos Vaticanos
"""
from flask import Flask, render_template, jsonify, request
from monitor import monitor
from vatican_client import VaticanClient
from config import TARGET_DATES, PREFERRED_TIMES, CHECK_INTERVAL_SECONDS

app = Flask(__name__)
client = VaticanClient()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Obtiene el estado actual del monitor."""
    return jsonify(monitor.get_status())


@app.route('/api/calendar')
def get_calendar():
    """Obtiene el calendario de fechas."""
    calendar = client.get_calendar()
    return jsonify(calendar)


@app.route('/api/timeslots/<date>')
def get_timeslots(date):
    """Obtiene los horarios para una fecha específica."""
    # Convertir formato de URL (YYYY-MM-DD) a formato API (DD/MM/YYYY)
    if '-' in date:
        parts = date.split('-')
        date = f"{parts[2]}/{parts[1]}/{parts[0]}"

    data = client.get_timeslots(date)
    return jsonify(data)


@app.route('/api/check-now', methods=['POST'])
def check_now():
    """Ejecuta una verificación manual."""
    monitor.check_and_alert()
    return jsonify({'success': True, 'status': monitor.get_status()})


@app.route('/api/clear-alerts', methods=['POST'])
def clear_alerts():
    """Limpia el historial de alertas."""
    monitor.clear_alerted_slots()
    return jsonify({'success': True})


@app.route('/api/start', methods=['POST'])
def start_monitor():
    """Inicia el monitor."""
    if not monitor.scheduler.running:
        monitor.start()
    return jsonify({'success': True, 'running': True})


@app.route('/api/stop', methods=['POST'])
def stop_monitor():
    """Detiene el monitor."""
    if monitor.scheduler.running:
        monitor.stop()
    return jsonify({'success': True, 'running': False})


if __name__ == '__main__':
    # Iniciar monitor automáticamente
    monitor.start()

    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
