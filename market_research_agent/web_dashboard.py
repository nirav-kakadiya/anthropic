"""
Web Dashboard - Simple Flask-based UI for Market Research Agent.

Features:
- Web interface for running scans
- View scan history
- Competitor comparison
- Export reports
- Configuration management

Usage:
    from market_research_agent.web_dashboard import create_app, run_dashboard

    # Run the dashboard
    run_dashboard(port=5000)

    # Or create app for WSGI
    app = create_app()
"""

import json
from datetime import datetime
from typing import Optional

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Market Research Agent Dashboard</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: white;
            padding: 30px;
            border-radius: 16px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .header h1 { color: #1a1a1a; font-size: 2em; }
        .header p { color: #666; margin-top: 5px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card {
            background: white;
            padding: 25px;
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .card h2 { color: #4f46e5; margin-bottom: 20px; font-size: 1.3em; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; color: #333; font-weight: 500; }
        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.2s;
        }
        .form-group input:focus, .form-group textarea:focus {
            border-color: #4f46e5;
            outline: none;
        }
        .btn {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            width: 100%;
        }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4); }
        .btn-secondary { background: #6b7280; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .stat {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
        }
        .stat-value { font-size: 2em; font-weight: bold; color: #4f46e5; }
        .stat-label { color: #64748b; font-size: 0.9em; margin-top: 5px; }
        .results {
            background: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .results pre { white-space: pre-wrap; font-size: 0.9em; }
        .tag {
            display: inline-block;
            padding: 4px 10px;
            background: #e0e7ff;
            color: #4338ca;
            border-radius: 20px;
            font-size: 0.85em;
            margin: 3px;
        }
        .tag.gap { background: #fee2e2; color: #dc2626; }
        .tag.covered { background: #d1fae5; color: #059669; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #e5e7eb; }
        th { background: #f8fafc; color: #64748b; font-weight: 500; }
        .history-item {
            background: #f8fafc;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        .history-item h4 { color: #1a1a1a; margin-bottom: 5px; }
        .history-item p { color: #64748b; font-size: 0.9em; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 8px;
            color: white;
            cursor: pointer;
            font-weight: 500;
        }
        .tab.active { background: white; color: #4f46e5; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .loading { text-align: center; padding: 40px; color: #666; }
        .loading::after { content: '...'; animation: dots 1.5s infinite; }
        @keyframes dots { 0%, 20% { content: '.'; } 40% { content: '..'; } 60%, 100% { content: '...'; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Market Research Agent</h1>
            <p>AI-powered market research and competitive analysis</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="showTab('scan')">New Scan</button>
            <button class="tab" onclick="showTab('competitors')">Competitors</button>
            <button class="tab" onclick="showTab('history')">History</button>
            <button class="tab" onclick="showTab('settings')">Settings</button>
        </div>

        <!-- New Scan Tab -->
        <div id="scan" class="tab-content active">
            <div class="grid">
                <div class="card">
                    <h2>🎯 Quick Scan</h2>
                    <form id="scanForm">
                        <div class="form-group">
                            <label>Mode</label>
                            <select id="scanMode" onchange="toggleScanMode()">
                                <option value="auto">Auto (from URL)</option>
                                <option value="manual">Manual (enter features)</option>
                            </select>
                        </div>
                        <div class="form-group" id="urlGroup">
                            <label>Your Website URL</label>
                            <input type="url" id="siteUrl" placeholder="https://your-site.com">
                        </div>
                        <div class="form-group" id="featuresGroup" style="display:none;">
                            <label>Your Features (comma-separated)</label>
                            <textarea id="features" rows="3" placeholder="flux ai, kling ai, ai upscaler, background remover"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Niche (optional)</label>
                            <input type="text" id="niche" placeholder="AI image/video platform">
                        </div>
                        <button type="submit" class="btn">🚀 Start Scan</button>
                    </form>
                </div>

                <div class="card">
                    <h2>📊 Scan Results</h2>
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value" id="keywordCount">0</div>
                            <div class="stat-label">Keywords</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="gapCount">0</div>
                            <div class="stat-label">Gaps</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="coveredCount">0</div>
                            <div class="stat-label">Covered</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value" id="clusterCount">0</div>
                            <div class="stat-label">Clusters</div>
                        </div>
                    </div>
                    <div class="results" id="scanResults">
                        <p style="color: #666; text-align: center;">Run a scan to see results</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Competitors Tab -->
        <div id="competitors" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h2>➕ Add Competitor</h2>
                    <form id="competitorForm">
                        <div class="form-group">
                            <label>Competitor URL</label>
                            <input type="url" id="compUrl" placeholder="https://competitor.com">
                        </div>
                        <div class="form-group">
                            <label>Competitor Name</label>
                            <input type="text" id="compName" placeholder="Competitor Name">
                        </div>
                        <div class="form-group">
                            <label>Their Features (comma-separated)</label>
                            <textarea id="compFeatures" rows="3" placeholder="feature1, feature2, feature3"></textarea>
                        </div>
                        <button type="submit" class="btn">Add Competitor</button>
                    </form>
                </div>

                <div class="card">
                    <h2>🏆 Competitor Analysis</h2>
                    <div id="competitorList">
                        <p style="color: #666;">No competitors added yet</p>
                    </div>
                    <button class="btn btn-secondary" style="margin-top: 15px;" onclick="runComparison()">
                        🔄 Run Comparison
                    </button>
                </div>
            </div>
        </div>

        <!-- History Tab -->
        <div id="history" class="tab-content">
            <div class="card">
                <h2>📜 Scan History</h2>
                <div id="historyList">
                    <p style="color: #666;">No scan history yet</p>
                </div>
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="settings" class="tab-content">
            <div class="grid">
                <div class="card">
                    <h2>🔔 Alert Settings</h2>
                    <form id="alertForm">
                        <div class="form-group">
                            <label>Discord Webhook URL</label>
                            <input type="url" id="discordWebhook" placeholder="https://discord.com/api/webhooks/...">
                        </div>
                        <div class="form-group">
                            <label>Slack Webhook URL</label>
                            <input type="url" id="slackWebhook" placeholder="https://hooks.slack.com/services/...">
                        </div>
                        <button type="submit" class="btn">Save Alert Settings</button>
                    </form>
                </div>

                <div class="card">
                    <h2>⏰ Scheduled Scans</h2>
                    <form id="scheduleForm">
                        <div class="form-group">
                            <label>Scan Interval</label>
                            <select id="scanInterval">
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="hourly">Hourly</option>
                            </select>
                        </div>
                        <button type="submit" class="btn">Enable Scheduled Scans</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Tab switching
        function showTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
        }

        // Toggle scan mode
        function toggleScanMode() {
            const mode = document.getElementById('scanMode').value;
            document.getElementById('urlGroup').style.display = mode === 'auto' ? 'block' : 'none';
            document.getElementById('featuresGroup').style.display = mode === 'manual' ? 'block' : 'none';
        }

        // Scan form submission
        document.getElementById('scanForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const resultsDiv = document.getElementById('scanResults');
            resultsDiv.innerHTML = '<div class="loading">Scanning</div>';

            const mode = document.getElementById('scanMode').value;
            const url = document.getElementById('siteUrl').value;
            const features = document.getElementById('features').value.split(',').map(f => f.trim()).filter(f => f);
            const niche = document.getElementById('niche').value;

            try {
                const response = await fetch('/api/scan', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mode, url, features, niche })
                });
                const data = await response.json();

                // Update stats
                document.getElementById('keywordCount').textContent = data.keywords?.length || 0;
                document.getElementById('gapCount').textContent = data.gaps?.length || 0;
                document.getElementById('coveredCount').textContent = data.covered || 0;
                document.getElementById('clusterCount').textContent = data.clusters?.length || 0;

                // Show results
                let html = '<h4>Top Keywords</h4><div>';
                (data.keywords || []).slice(0, 20).forEach(kw => {
                    const name = typeof kw === 'string' ? kw : kw.keyword;
                    html += `<span class="tag">${name}</span>`;
                });
                html += '</div>';

                html += '<h4 style="margin-top:15px;">Top Gaps</h4><div>';
                (data.gaps || []).slice(0, 15).forEach(gap => {
                    const name = typeof gap === 'string' ? gap : gap.keyword;
                    html += `<span class="tag gap">${name}</span>`;
                });
                html += '</div>';

                resultsDiv.innerHTML = html;
            } catch (err) {
                resultsDiv.innerHTML = `<p style="color: red;">Error: ${err.message}</p>`;
            }
        });

        // Competitor form submission
        document.getElementById('competitorForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const name = document.getElementById('compName').value;
            const url = document.getElementById('compUrl').value;
            const features = document.getElementById('compFeatures').value;

            const list = document.getElementById('competitorList');
            list.innerHTML += `
                <div class="history-item">
                    <h4>${name}</h4>
                    <p>${url}</p>
                    <p>${features.split(',').length} features</p>
                </div>
            `;

            // Clear form
            document.getElementById('competitorForm').reset();
        });

        // Alert form
        document.getElementById('alertForm').addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Alert settings saved!');
        });

        // Schedule form
        document.getElementById('scheduleForm').addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Scheduled scans enabled!');
        });

        function runComparison() {
            alert('Running competitive analysis...');
        }
    </script>
</body>
</html>
"""


class DashboardApp:
    """
    Simple dashboard application.

    Can run standalone or be integrated with Flask/FastAPI.
    """

    def __init__(self, storage=None, scheduler=None, alert_manager=None):
        self.storage = storage
        self.scheduler = scheduler
        self.alert_manager = alert_manager
        self._competitors = []

    def get_html(self) -> str:
        """Get the dashboard HTML."""
        return DASHBOARD_HTML

    def handle_scan(self, data: dict) -> dict:
        """Handle a scan request."""
        from .scout_agent import AutoScoutAgent

        mode = data.get("mode", "manual")
        url = data.get("url", "")
        features = data.get("features", [])
        niche = data.get("niche", "")

        if mode == "auto" and url:
            agent = AutoScoutAgent.from_url(url)
            if features:
                agent.add_manual_features(features)
            if niche:
                agent.set_manual_niche(niche)
        else:
            agent = AutoScoutAgent.manual(
                features=features,
                niche=niche or "Unknown"
            )

        # Run research
        result = agent.run_research()

        # Format response
        response = {
            "scan_id": result.scan_id,
            "keywords": result.all_keywords,
            "gaps": [
                {"keyword": g.keyword, "trend_score": g.trend_score}
                for g in (result.gap_report.gaps if result.gap_report else [])
            ],
            "covered": result.total_covered,
            "clusters": [
                {"name": c.name, "keywords": c.keywords}
                for c in result.clusters
            ],
        }

        # Save to storage if available
        if self.storage:
            self.storage.save_scan(
                scan_id=result.scan_id,
                url=url,
                niche=niche,
                keywords=result.all_keywords,
                gaps=response["gaps"],
            )

        return response

    def add_competitor(self, data: dict):
        """Add a competitor."""
        self._competitors.append({
            "name": data.get("name", "Unknown"),
            "url": data.get("url", ""),
            "features": data.get("features", []),
        })

    def get_competitors(self) -> list:
        """Get all competitors."""
        return self._competitors


def create_flask_app(
    storage=None,
    scheduler=None,
    alert_manager=None,
):
    """
    Create a Flask application.

    Requires Flask to be installed: pip install flask
    """
    try:
        from flask import Flask, request, jsonify, Response
    except ImportError:
        raise ImportError("Flask is required. Install with: pip install flask")

    app = Flask(__name__)
    dashboard = DashboardApp(storage, scheduler, alert_manager)

    @app.route('/')
    def index():
        return Response(dashboard.get_html(), mimetype='text/html')

    @app.route('/api/scan', methods=['POST'])
    def scan():
        data = request.get_json()
        result = dashboard.handle_scan(data)
        return jsonify(result)

    @app.route('/api/competitors', methods=['GET', 'POST'])
    def competitors():
        if request.method == 'POST':
            data = request.get_json()
            dashboard.add_competitor(data)
            return jsonify({"status": "ok"})
        return jsonify(dashboard.get_competitors())

    @app.route('/api/history', methods=['GET'])
    def history():
        if dashboard.storage:
            scans = dashboard.storage.get_scan_history(limit=20)
            return jsonify([{
                "scan_id": s.scan_id,
                "scan_time": s.scan_time,
                "url": s.url,
                "keywords": s.total_keywords,
                "gaps": s.total_gaps,
            } for s in scans])
        return jsonify([])

    return app


def run_dashboard(
    port: int = 5000,
    host: str = "127.0.0.1",
    debug: bool = False,
    storage=None,
    scheduler=None,
    alert_manager=None,
):
    """
    Run the dashboard server.

    Args:
        port: Port to run on
        host: Host to bind to
        debug: Enable debug mode
        storage: Optional ScanStorage instance
        scheduler: Optional ScanScheduler instance
        alert_manager: Optional AlertManager instance
    """
    app = create_flask_app(storage, scheduler, alert_manager)
    print(f"\n🚀 Market Research Dashboard running at http://{host}:{port}\n")
    app.run(host=host, port=port, debug=debug)


def create_app(**kwargs):
    """Factory function to create the Flask app."""
    return create_flask_app(**kwargs)
