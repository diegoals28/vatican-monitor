"""
Vercel Serverless Function - Main API
"""
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the main HTML page"""
        html = self._get_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())

    def _get_html(self):
        return '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vatican Ticket Monitor</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2em;
        }
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
        }
        .card h2 {
            margin-bottom: 15px;
            color: #ffd700;
            font-size: 1.2em;
        }
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
        .status-item .label {
            font-size: 0.85em;
            color: #aaa;
            margin-top: 5px;
        }
        .date-input {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        .date-input input {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: transform 0.2s;
        }
        .btn:hover { transform: scale(1.05); }
        .btn-primary { background: #ffd700; color: #000; }
        .btn-secondary { background: #4a5568; color: #fff; }
        .btn-success { background: #4ade80; color: #000; }
        .date-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }
        .date-tag {
            background: #3b82f6;
            padding: 8px 15px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .date-tag .remove {
            cursor: pointer;
            opacity: 0.7;
        }
        .date-tag .remove:hover { opacity: 1; }
        .results {
            margin-top: 15px;
        }
        .result-item {
            background: rgba(74, 222, 128, 0.2);
            border-left: 4px solid #4ade80;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 0 8px 8px 0;
        }
        .no-results {
            color: #aaa;
            text-align: center;
            padding: 20px;
        }
        .actions {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .loading {
            opacity: 0.5;
            pointer-events: none;
        }
        #lastUpdate {
            text-align: center;
            color: #888;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Vatican Ticket Monitor</h1>

        <div class="card">
            <h2>Estado del Monitor</h2>
            <div class="status-grid">
                <div class="status-item">
                    <div class="value" id="checkCount">0</div>
                    <div class="label">Verificaciones</div>
                </div>
                <div class="status-item">
                    <div class="value" id="alertCount">0</div>
                    <div class="label">Alertas Enviadas</div>
                </div>
                <div class="status-item">
                    <div class="value" id="dateCount">0</div>
                    <div class="label">Fechas Monitoreando</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>Fechas a Monitorear</h2>
            <div class="date-input">
                <input type="date" id="newDate">
                <button class="btn btn-primary" onclick="addDate()">Agregar</button>
            </div>
            <div class="date-tags" id="dateTags"></div>
        </div>

        <div class="card">
            <h2>Acciones</h2>
            <div class="actions">
                <button class="btn btn-success" onclick="checkNow()">Verificar Ahora</button>
                <button class="btn btn-secondary" onclick="clearAlerts()">Limpiar Alertas</button>
            </div>
        </div>

        <div class="card">
            <h2>Ultima Disponibilidad</h2>
            <div class="results" id="results">
                <div class="no-results">Sin resultados aun</div>
            </div>
        </div>

        <div id="lastUpdate"></div>
    </div>

    <script>
        const API_BASE = '/api';
        const CACHE_KEY = 'vatican_status_cache';
        let pollingInterval = 30000; // 30 seconds default
        let pollTimer = null;
        let isLoading = false;

        // Load cached data immediately on page load
        function loadCachedData() {
            try {
                const cached = localStorage.getItem(CACHE_KEY);
                if (cached) {
                    const data = JSON.parse(cached);
                    updateUI(data);
                    document.getElementById('lastUpdate').textContent =
                        'Cargando datos actualizados...';
                }
            } catch (e) {
                console.error('Error loading cache:', e);
            }
        }

        function updateUI(data) {
            document.getElementById('checkCount').textContent = data.check_count || 0;
            document.getElementById('alertCount').textContent = data.alerts_sent || 0;
            document.getElementById('dateCount').textContent = (data.target_dates || []).length;
            renderDates(data.target_dates || []);
            renderResults(data.last_results || {});
        }

        async function loadStatus() {
            if (isLoading) return;
            isLoading = true;

            try {
                const res = await fetch(`${API_BASE}/status`);
                const data = await res.json();

                // Cache the data
                localStorage.setItem(CACHE_KEY, JSON.stringify(data));

                updateUI(data);
                document.getElementById('lastUpdate').textContent =
                    'Actualizado: ' + new Date().toLocaleTimeString();
            } catch (e) {
                console.error('Error loading status:', e);
                document.getElementById('lastUpdate').textContent =
                    'Error al actualizar - reintentando...';
            } finally {
                isLoading = false;
            }
        }

        function renderDates(dates) {
            const container = document.getElementById('dateTags');
            container.innerHTML = dates.map(date => `
                <div class="date-tag">
                    <span>${date}</span>
                    <span class="remove" onclick="removeDate('${date}')">&times;</span>
                </div>
            `).join('');
        }

        function renderResults(results) {
            const container = document.getElementById('results');
            const entries = Object.entries(results);

            if (entries.length === 0) {
                container.innerHTML = '<div class="no-results">Sin disponibilidad encontrada</div>';
                return;
            }

            container.innerHTML = entries.map(([date, products]) => `
                <div class="result-item">
                    <strong>${date}</strong><br>
                    ${products.map(p => {
                        const status = p.availability === 'AVAILABLE' ? 'DISP' :
                                       p.availability === 'LOW_AVAILABILITY' ? 'POCAS' : 'AGOT';
                        const color = p.availability === 'AVAILABLE' ? '#4ade80' :
                                      p.availability === 'LOW_AVAILABILITY' ? '#fbbf24' : '#ef4444';
                        return `<span style="color:${color}">[${status}]</span> ${p.name || 'Producto'}`;
                    }).join('<br>')}
                </div>
            `).join('');
        }

        // Adaptive polling: faster after user action
        function setFastPolling() {
            clearInterval(pollTimer);
            pollingInterval = 10000; // 10 seconds after action
            pollTimer = setInterval(loadStatus, pollingInterval);

            // Reset to normal after 2 minutes
            setTimeout(() => {
                clearInterval(pollTimer);
                pollingInterval = 30000;
                pollTimer = setInterval(loadStatus, pollingInterval);
            }, 120000);
        }

        async function addDate() {
            const input = document.getElementById('newDate');
            const dateValue = input.value;
            if (!dateValue) return;

            const [year, month, day] = dateValue.split('-');
            const formatted = `${day}/${month}/${year}`;

            try {
                await fetch(`${API_BASE}/dates`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date: formatted })
                });
                input.value = '';
                loadStatus();
                setFastPolling();
            } catch (e) {
                alert('Error agregando fecha');
            }
        }

        async function removeDate(date) {
            try {
                await fetch(`${API_BASE}/dates`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date })
                });
                loadStatus();
                setFastPolling();
            } catch (e) {
                alert('Error eliminando fecha');
            }
        }

        async function checkNow() {
            const btn = event.target;
            if (btn.disabled) return;

            btn.disabled = true;
            btn.classList.add('loading');
            btn.textContent = 'Verificando...';

            try {
                const res = await fetch(`${API_BASE}/check`, { method: 'POST' });
                const data = await res.json();
                loadStatus();
                setFastPolling();

                if (data.availability && Object.keys(data.availability).length > 0) {
                    alert('Disponibilidad encontrada!');
                } else {
                    alert('Sin disponibilidad');
                }
            } catch (e) {
                alert('Error verificando');
            } finally {
                btn.disabled = false;
                btn.classList.remove('loading');
                btn.textContent = 'Verificar Ahora';
            }
        }

        async function clearAlerts() {
            const btn = event.target;
            if (btn.disabled) return;

            btn.disabled = true;
            try {
                await fetch(`${API_BASE}/clear-alerts`, { method: 'POST' });
                loadStatus();
            } catch (e) {
                alert('Error limpiando alertas');
            } finally {
                btn.disabled = false;
            }
        }

        // Initialize: load cache first, then fetch fresh data
        loadCachedData();
        loadStatus();
        pollTimer = setInterval(loadStatus, pollingInterval);
    </script>
</body>
</html>'''
