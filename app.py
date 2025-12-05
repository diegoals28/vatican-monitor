"""
Aplicación web para el monitor de tickets de los Museos Vaticanos
"""
import os
import json
from flask import Flask, render_template_string, jsonify, request
from monitor import monitor
from vatican_client import VaticanClient
from config import CHECK_INTERVAL_SECONDS

app = Flask(__name__)
client = VaticanClient()

# Archivo para persistir las fechas configuradas
DATES_FILE = 'target_dates.json'


def load_target_dates():
    """Carga las fechas desde el archivo JSON."""
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE, 'r') as f:
            data = json.load(f)
            return data.get('dates', [])
    return []


def save_target_dates(dates):
    """Guarda las fechas en el archivo JSON."""
    with open(DATES_FILE, 'w') as f:
        json.dump({'dates': dates}, f)


def update_monitor_dates(dates):
    """Actualiza las fechas en el módulo config."""
    import config
    config.TARGET_DATES = dates


# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vatican Monitor</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 900px; margin: 0 auto; }
        h1 { text-align: center; margin-bottom: 30px; font-size: 2em; }
        h1 span { color: #ffd700; }

        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .card h2 {
            font-size: 1.2em;
            margin-bottom: 15px;
            color: #ffd700;
        }

        /* Status */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .status-item {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .status-item .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #4ade80;
        }
        .status-item .label { font-size: 0.85em; opacity: 0.7; margin-top: 5px; }

        /* Dates */
        .date-input-row {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        input[type="date"] {
            flex: 1;
            padding: 12px 15px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            background: rgba(255,255,255,0.9);
            color: #333;
        }
        .btn {
            padding: 12px 25px;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            font-weight: 600;
        }
        .btn-primary { background: #ffd700; color: #1a1a2e; }
        .btn-primary:hover { background: #ffed4a; transform: translateY(-2px); }
        .btn-danger { background: #ef4444; color: #fff; }
        .btn-danger:hover { background: #dc2626; }
        .btn-success { background: #22c55e; color: #fff; }
        .btn-success:hover { background: #16a34a; }
        .btn-secondary { background: rgba(255,255,255,0.2); color: #fff; }
        .btn-secondary:hover { background: rgba(255,255,255,0.3); }

        .dates-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .date-tag {
            background: rgba(255,215,0,0.2);
            border: 1px solid #ffd700;
            padding: 8px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .date-tag .remove {
            background: none;
            border: none;
            color: #ef4444;
            cursor: pointer;
            font-size: 1.2em;
            line-height: 1;
        }
        .date-tag .remove:hover { color: #dc2626; }

        .no-dates {
            color: rgba(255,255,255,0.5);
            font-style: italic;
            padding: 20px;
            text-align: center;
        }

        /* Actions */
        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        /* Results */
        .result-item {
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        .result-date {
            font-weight: bold;
            color: #ffd700;
            margin-bottom: 8px;
        }
        .result-product {
            padding: 5px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .result-product:last-child { border-bottom: none; }
        .available { color: #4ade80; }
        .low { color: #fbbf24; }
        .sold-out { color: #ef4444; }

        /* Loading */
        .loading {
            text-align: center;
            padding: 20px;
            opacity: 0.7;
        }
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255,255,255,0.3);
            border-top-color: #ffd700;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        /* Toast */
        .toast {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #22c55e;
            color: #fff;
            padding: 15px 25px;
            border-radius: 10px;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s;
            z-index: 1000;
        }
        .toast.show { opacity: 1; transform: translateY(0); }
        .toast.error { background: #ef4444; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ <span>Vatican</span> Monitor</h1>

        <!-- Status Card -->
        <div class="card">
            <h2>📊 Estado del Monitor</h2>
            <div class="status-grid">
                <div class="status-item">
                    <div class="value" id="status-running">-</div>
                    <div class="label">Estado</div>
                </div>
                <div class="status-item">
                    <div class="value" id="status-checks">0</div>
                    <div class="label">Verificaciones</div>
                </div>
                <div class="status-item">
                    <div class="value" id="status-alerts">0</div>
                    <div class="label">Alertas Enviadas</div>
                </div>
                <div class="status-item">
                    <div class="value" id="status-interval">-</div>
                    <div class="label">Intervalo</div>
                </div>
            </div>
        </div>

        <!-- Dates Card -->
        <div class="card">
            <h2>📅 Fechas a Monitorear</h2>
            <div class="date-input-row">
                <input type="date" id="new-date" min="">
                <button class="btn btn-primary" onclick="addDate()">+ Agregar</button>
            </div>
            <div class="dates-list" id="dates-list">
                <div class="loading"><span class="spinner"></span> Cargando...</div>
            </div>
        </div>

        <!-- Actions Card -->
        <div class="card">
            <h2>⚡ Acciones</h2>
            <div class="actions">
                <button class="btn btn-success" onclick="checkNow()">🔍 Verificar Ahora</button>
                <button class="btn btn-secondary" onclick="clearAlerts()">🗑️ Limpiar Historial</button>
                <button class="btn btn-secondary" onclick="exportExcel()">📊 Exportar Excel</button>
            </div>
        </div>

        <!-- Results Card -->
        <div class="card">
            <h2>📋 Última Verificación</h2>
            <div id="last-check-time" style="opacity: 0.7; margin-bottom: 15px;">-</div>
            <div id="results">
                <div class="no-dates">Sin resultados aún</div>
            </div>
        </div>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        // Set min date to today
        document.getElementById('new-date').min = new Date().toISOString().split('T')[0];

        // Load data on page load
        loadDates();
        loadStatus();
        setInterval(loadStatus, 30000); // Refresh every 30s

        function showToast(message, isError = false) {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast' + (isError ? ' error' : '');
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }

        async function loadDates() {
            try {
                const res = await fetch('/api/dates');
                const data = await res.json();
                renderDates(data.dates || []);
            } catch (e) {
                console.error('Error loading dates:', e);
            }
        }

        function renderDates(dates) {
            const container = document.getElementById('dates-list');
            if (!dates.length) {
                container.innerHTML = '<div class="no-dates">No hay fechas configuradas. Agrega fechas para monitorear.</div>';
                return;
            }
            container.innerHTML = dates.map(d => `
                <div class="date-tag">
                    <span>${formatDate(d)}</span>
                    <button class="remove" onclick="removeDate('${d}')">&times;</button>
                </div>
            `).join('');
        }

        function formatDate(dateStr) {
            // Convert DD/MM/YYYY to readable format
            const parts = dateStr.split('/');
            const months = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
            return `${parts[0]} ${months[parseInt(parts[1])-1]} ${parts[2]}`;
        }

        async function addDate() {
            const input = document.getElementById('new-date');
            if (!input.value) {
                showToast('Selecciona una fecha', true);
                return;
            }

            // Convert YYYY-MM-DD to DD/MM/YYYY
            const parts = input.value.split('-');
            const dateStr = `${parts[2]}/${parts[1]}/${parts[0]}`;

            try {
                const res = await fetch('/api/dates', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({date: dateStr})
                });
                const data = await res.json();
                if (data.success) {
                    renderDates(data.dates);
                    input.value = '';
                    showToast('Fecha agregada');
                } else {
                    showToast(data.error || 'Error', true);
                }
            } catch (e) {
                showToast('Error al agregar fecha', true);
            }
        }

        async function removeDate(dateStr) {
            try {
                const res = await fetch('/api/dates', {
                    method: 'DELETE',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({date: dateStr})
                });
                const data = await res.json();
                if (data.success) {
                    renderDates(data.dates);
                    showToast('Fecha eliminada');
                }
            } catch (e) {
                showToast('Error al eliminar', true);
            }
        }

        async function loadStatus() {
            try {
                const res = await fetch('/api/status');
                const data = await res.json();

                document.getElementById('status-running').textContent = data.running ? '✅ Activo' : '⏸️ Pausado';
                document.getElementById('status-running').style.color = data.running ? '#4ade80' : '#fbbf24';
                document.getElementById('status-checks').textContent = data.check_count || 0;
                document.getElementById('status-alerts').textContent = data.alerts_sent || 0;
                document.getElementById('status-interval').textContent = formatInterval(data.interval_seconds);

                if (data.last_check) {
                    const date = new Date(data.last_check);
                    document.getElementById('last-check-time').textContent =
                        'Última verificación: ' + date.toLocaleString('es-ES');
                }

                renderResults(data.last_results);
            } catch (e) {
                console.error('Error loading status:', e);
            }
        }

        function formatInterval(seconds) {
            if (seconds >= 3600) return Math.round(seconds/3600) + 'h';
            if (seconds >= 60) return Math.round(seconds/60) + 'm';
            return seconds + 's';
        }

        function renderResults(results) {
            const container = document.getElementById('results');
            if (!results || !Object.keys(results).length) {
                container.innerHTML = '<div class="no-dates">Sin disponibilidad encontrada</div>';
                return;
            }

            container.innerHTML = Object.entries(results).map(([date, products]) => `
                <div class="result-item">
                    <div class="result-date">📅 ${formatDate(date)}</div>
                    ${products.map(p => `
                        <div class="result-product">
                            <span class="${p.availability === 'AVAILABLE' ? 'available' : p.availability === 'LOW_AVAILABILITY' ? 'low' : 'sold-out'}">
                                ${p.availability === 'AVAILABLE' ? '✅' : p.availability === 'LOW_AVAILABILITY' ? '⚠️' : '❌'}
                            </span>
                            ${p.name}
                        </div>
                    `).join('')}
                </div>
            `).join('');
        }

        async function checkNow() {
            showToast('Verificando...');
            try {
                const res = await fetch('/api/check-now', {method: 'POST'});
                const data = await res.json();
                loadStatus();
                showToast('Verificación completada');
            } catch (e) {
                showToast('Error al verificar', true);
            }
        }

        async function clearAlerts() {
            try {
                await fetch('/api/clear-alerts', {method: 'POST'});
                showToast('Historial limpiado');
            } catch (e) {
                showToast('Error', true);
            }
        }

        async function exportExcel() {
            showToast('Generando Excel... Esto puede tardar unos minutos');
            try {
                const res = await fetch('/api/export-excel', {method: 'POST'});
                const data = await res.json();
                if (data.success) {
                    showToast('Excel generado: ' + data.filename);
                } else {
                    showToast(data.error || 'Error', true);
                }
            } catch (e) {
                showToast('Error al exportar', true);
            }
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/status')
def get_status():
    """Obtiene el estado actual del monitor."""
    return jsonify(monitor.get_status())


@app.route('/api/dates', methods=['GET'])
def get_dates():
    """Obtiene las fechas configuradas."""
    dates = load_target_dates()
    return jsonify({'dates': dates})


@app.route('/api/dates', methods=['POST'])
def add_date():
    """Agrega una fecha a monitorear."""
    data = request.get_json()
    date = data.get('date', '').strip()

    if not date:
        return jsonify({'success': False, 'error': 'Fecha requerida'})

    dates = load_target_dates()
    if date in dates:
        return jsonify({'success': False, 'error': 'Fecha ya existe'})

    dates.append(date)
    dates.sort(key=lambda x: (int(x.split('/')[2]), int(x.split('/')[1]), int(x.split('/')[0])))

    save_target_dates(dates)
    update_monitor_dates(dates)

    return jsonify({'success': True, 'dates': dates})


@app.route('/api/dates', methods=['DELETE'])
def remove_date():
    """Elimina una fecha del monitoreo."""
    data = request.get_json()
    date = data.get('date', '').strip()

    dates = load_target_dates()
    if date in dates:
        dates.remove(date)
        save_target_dates(dates)
        update_monitor_dates(dates)

    return jsonify({'success': True, 'dates': dates})


@app.route('/api/calendar')
def get_calendar():
    """Obtiene el calendario de fechas disponibles."""
    calendar = client.get_calendar()
    return jsonify(calendar)


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


@app.route('/api/export-excel', methods=['POST'])
def export_excel():
    """Exporta disponibilidad a Excel."""
    try:
        from export_availability import export_to_excel
        filename = export_to_excel()
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


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
    # Cargar fechas desde archivo
    dates = load_target_dates()
    if dates:
        update_monitor_dates(dates)
        print(f"Fechas cargadas: {dates}")

    # Iniciar monitor automáticamente
    monitor.start()

    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)
