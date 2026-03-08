"""
NYC Heat Wave Risk Dashboard
===========================
Run with: shiny run app:app --reload
"""

from shiny import App, ui, render, reactive
import pandas as pd
import json
import folium
from pathlib import Path

from core.risk_formula import calculate_heat_risk, get_risk_level
from core.ai_client import AIClient
from core.data_loader import DataLoader
from core.real_data_loader import fetch_live_weather, fetch_historical_weather
from core.email_alert import EmailAlertSystem
from datetime import date, timedelta

# ========== Init ==========
DATA_DIR = Path(__file__).parent
data_loader = DataLoader(DATA_DIR)

config_path = DATA_DIR / "config.json"
api_key = None
email_system = None

if config_path.exists():
    try:
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("openai_api_key")
            if api_key and api_key != "YOUR_API_KEY_HERE":
                print("Loaded API key from config.json")
        email_system = EmailAlertSystem(config_path=str(config_path))
    except Exception as e:
        print(f"Config loading warning: {e}")
        pass

# If no config, create default AI client
if 'ai_client' not in locals():
    ai_client = AIClient()

if email_system is None:
    # Create default email system with defaults
    try:
        email_system = EmailAlertSystem()
    except Exception:
        pass  # Email alerts won't work but app will run


# ========== CSS ==========
app_css = """
@import url('https://fonts.googleapis.com/css2?family=Rethink+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --orange: #CD4900;
    --orange-light: #E8650A;
    --black: #000000;
    --dark: #1a1a1a;
    --grey-dark: #A3A3A3;
    --grey: #E5E5E5;
    --grey-light: #F5F5F5;
    --white: #FFFFFF;
    --risk-critical: #C62828;
    --risk-high: #E65100;
    --risk-medium: #F9A825;
    --risk-low: #2E7D32;
    --font: 'Rethink Sans', -apple-system, 'Segoe UI', sans-serif;
}

body {
    background: var(--white);
    font-family: var(--font);
    color: var(--dark);
    line-height: 1.6;
    overflow-x: hidden;
}

/* ===== HEADER ===== */
.site-header {
    border-bottom: 1px solid var(--grey);
    padding: 28px 0;
    margin-bottom: 0;
}
.site-header h1 {
    font-size: 2em;
    font-weight: 800;
    letter-spacing: -1px;
    color: var(--black);
    margin: 0 0 4px;
}
.site-header .tagline {
    font-size: 0.95em;
    color: var(--grey-dark);
    margin: 0 0 14px;
    font-weight: 400;
}
.site-header .weather-pill {
    display: inline-block;
    background: var(--grey-light);
    padding: 6px 18px;
    border-radius: 24px;
    font-size: 0.85em;
    color: var(--dark);
    font-weight: 500;
}

/* ===== HEADER CONTROLS ===== */
.header-controls {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 12px;
}
.date-picker-row {
    display: flex;
    align-items: center;
    gap: 8px;
}
.date-picker-row .form-group { margin-bottom: 0 !important; }
.date-picker-row label { display: none !important; }
.date-picker-row input[type="text"] {
    font-family: var(--font) !important;
    font-size: 0.88em !important;
    border: 1px solid var(--grey) !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
}
.btn-today {
    background: var(--white) !important;
    border: 1px solid var(--grey) !important;
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.85em !important;
    border-radius: 6px !important;
    padding: 6px 16px !important;
    color: var(--dark) !important;
    cursor: pointer;
    transition: all 0.15s;
}
.btn-today:hover {
    border-color: var(--orange) !important;
    color: var(--orange) !important;
}
.historical-badge {
    display: inline-block;
    background: var(--orange);
    color: white;
    padding: 2px 10px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 600;
    margin-left: 8px;
}

/* ===== ALERT STATUS ===== */
.alert-success {
    background: #E8F5E9; border-left: 3px solid var(--risk-low);
    border-radius: 0 6px 6px 0; padding: 16px 20px; margin-top: 16px;
    font-size: 0.92em; color: #2E7D32;
}
.alert-fail {
    background: #FFF3E0; border-left: 3px solid var(--orange);
    border-radius: 0 6px 6px 0; padding: 16px 20px; margin-top: 16px;
    font-size: 0.92em; color: #E65100;
}
.alert-info {
    background: var(--grey-light); border-left: 3px solid var(--grey-dark);
    border-radius: 0 6px 6px 0; padding: 16px 20px; margin-top: 16px;
    font-size: 0.92em; color: var(--dark);
}
.threshold-display {
    font-size: 2.5em; font-weight: 800; color: var(--orange);
    letter-spacing: -1px; line-height: 1;
}
.config-row {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 0; border-bottom: 1px solid var(--grey);
}
.config-row .config-label {
    font-weight: 600; font-size: 0.9em; min-width: 140px;
}
.config-row .config-value {
    color: var(--grey-dark); font-size: 0.9em;
}

/* ===== VERTICAL SIDEBAR via navset_pill_list ===== */
.well {
    background: var(--white) !important;
    border: none !important;
    border-right: 1px solid var(--grey) !important;
    border-radius: 0 !important;
    padding: 20px 0 !important;
    box-shadow: none !important;
    -webkit-box-shadow: none !important;
    min-height: calc(100vh - 140px);
}
.nav-pills.nav-stacked {
    display: flex !important;
    flex-direction: column !important;
    gap: 2px !important;
}
.nav-pills.nav-stacked .nav-link {
    font-family: var(--font) !important;
    font-weight: 600 !important;
    font-size: 0.92em !important;
    color: var(--grey-dark) !important;
    padding: 14px 24px !important;
    border-radius: 0 !important;
    border-left: 3px solid transparent !important;
    transition: all 0.2s ease !important;
    background: transparent !important;
}
.nav-pills.nav-stacked .nav-link:hover {
    color: var(--dark) !important;
    background: var(--grey-light) !important;
    border-left-color: var(--grey) !important;
}
.nav-pills.nav-stacked .nav-link.active,
.nav-pills.nav-stacked .show > .nav-link {
    color: var(--black) !important;
    background: var(--grey-light) !important;
    border-left-color: var(--orange) !important;
    font-weight: 700 !important;
}
.col-sm-10 > .tab-content {
    padding: 28px 40px !important;
}

/* ===== CARDS ===== */
.panel {
    background: var(--white);
    border: 1px solid var(--grey);
    border-radius: 8px;
    padding: 32px;
    margin-bottom: 28px;
    transition: box-shadow 0.2s;
}
.panel:hover { box-shadow: 0 2px 16px rgba(0,0,0,0.05); }

.panel-title {
    font-size: 1.3em; font-weight: 700; color: var(--black);
    margin: 0 0 6px; letter-spacing: -0.3px;
}
.panel-subtitle {
    font-size: 0.92em; color: var(--grey-dark); margin: 0 0 24px;
}

/* ===== STAT ROW ===== */
.stat-row {
    display: grid; grid-template-columns: repeat(6, 1fr);
    gap: 16px; margin-bottom: 28px;
}
.stat-box {
    border: 1px solid var(--grey); border-radius: 8px;
    padding: 20px 16px; text-align: center;
    transition: transform 0.15s, box-shadow 0.15s;
}
.stat-box:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
}
.stat-box .num { font-size: 2em; font-weight: 800; letter-spacing: -1px; line-height: 1; }
.stat-box .lbl {
    font-size: 0.78em; color: var(--grey-dark); margin-top: 6px;
    font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;
}

/* ===== RISK BADGES ===== */
.risk-badge {
    display: inline-block; padding: 4px 14px; border-radius: 4px;
    font-weight: 700; font-size: 0.85em; letter-spacing: 0.03em;
}
.risk-critical { background: var(--risk-critical); color: white; }
.risk-high { background: var(--risk-high); color: white; }
.risk-medium { background: var(--risk-medium); color: var(--dark); }
.risk-low { background: var(--risk-low); color: white; }

/* ===== ANALYSIS BOX ===== */
.analysis-box {
    background: var(--grey-light); border-left: 3px solid var(--orange);
    border-radius: 0 6px 6px 0; padding: 28px 32px;
    margin-top: 20px; line-height: 1.85; font-size: 0.95em; color: var(--dark);
}
.analysis-box h2, .analysis-box h3, .analysis-box h4 {
    font-family: var(--font); color: var(--black);
    margin-top: 20px; margin-bottom: 8px;
}
.analysis-box p { margin-bottom: 12px; }
.analysis-box strong { color: var(--black); }

/* ===== BREAKDOWN GRID ===== */
.breakdown-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; }
.breakdown-item {
    border: 1px solid var(--grey); border-radius: 6px; padding: 16px;
    transition: border-color 0.15s;
}
.breakdown-item:hover { border-color: var(--orange); }
.breakdown-item .label {
    font-size: 0.82em; color: var(--grey-dark); text-transform: uppercase;
    letter-spacing: 0.04em; font-weight: 500;
}
.breakdown-item .value { font-size: 1.4em; font-weight: 700; color: var(--black); margin-top: 4px; }

/* ===== SECTION LABEL ===== */
.section-label {
    font-size: 0.82em; font-weight: 600; color: var(--orange);
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 28px 0 12px; padding-bottom: 8px;
    border-bottom: 1px solid var(--grey);
}

/* ===== BUTTONS ===== */
.btn-primary {
    background: var(--orange) !important; border-color: var(--orange) !important;
    font-family: var(--font); font-weight: 600; border-radius: 6px; padding: 10px 24px;
    transition: transform 0.1s;
}
.btn-primary:hover { background: var(--orange-light) !important; transform: translateY(-1px); }
.btn-primary:active { transform: translateY(0); }

.action-card {
    border: 1px solid var(--grey); border-radius: 8px; padding: 20px 24px;
    cursor: pointer; transition: all 0.2s ease; background: var(--white);
    text-align: center;
}
.action-card:hover {
    border-color: var(--orange); transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(205, 73, 0, 0.08);
}
.action-card:active { transform: translateY(0); }
.action-card .ac-title { font-weight: 700; font-size: 0.95em; color: var(--black); }
.action-card .ac-desc { font-size: 0.8em; color: var(--grey-dark); margin-top: 4px; }

/* ===== TABLE ===== */
.shiny-data-frame table { font-family: var(--font); font-size: 0.9em; }

/* ===== RESPONSIVE ===== */
@media (max-width: 900px) {
    .stat-row { grid-template-columns: repeat(3, 1fr); }
    .breakdown-grid { grid-template-columns: 1fr; }
}
"""


# ========== UI Layout ==========
app_ui = ui.page_fluid(
    ui.tags.style(app_css),

    ui.div(
        # Header
        ui.div(
            ui.h1("NYC Heat Wave Early Warning System"),
            ui.p("Real-time heat risk monitoring and AI-powered analysis for NYC neighborhoods", class_="tagline"),
            ui.div(
                ui.div(ui.output_ui("live_weather"), class_="weather-pill"),
                ui.div(
                    ui.input_date("query_date", None, value=str(date.today()),
                                  min=str(date.today() - timedelta(days=730)),
                                  max=str(date.today()),
                                  width="160px"),
                    ui.input_action_button("reset_today", "Today", class_="btn-today"),
                    class_="date-picker-row"
                ),
                class_="header-controls"
            ),
            class_="site-header"
        ),

        # Vertical sidebar navigation using Shiny's built-in navset_pill_list
        ui.navset_pill_list(

            # === Tab: Overview ===
            ui.nav_panel("Risk Overview",
                ui.output_ui("summary_stats"),
                ui.div(
                    ui.div("NYC Heat Risk Map", class_="panel-title"),
                    ui.p("Click any marker for detailed vulnerability data", class_="panel-subtitle"),
                    ui.output_ui("risk_map"),
                    class_="panel"
                ),
                ui.div(
                    ui.div("All Neighborhoods", class_="panel-title"),
                    ui.p("Live risk scores ranked by severity", class_="panel-subtitle"),
                    ui.output_data_frame("risk_table"),
                    class_="panel"
                ),
            ),

            # === Tab: Detail ===
            ui.nav_panel("Neighborhood Detail",
                ui.div(
                    ui.div("Neighborhood Deep Dive", class_="panel-title"),
                    ui.p("Select a neighborhood to explore its risk profile and vulnerability factors", class_="panel-subtitle"),
                    ui.input_select("neighborhood", "Neighborhood", choices={}, selected=None, width="100%"),
                    ui.output_ui("neighborhood_detail"),
                    class_="panel"
                ),
            ),

            # === Tab: AI ===
            ui.nav_panel("AI Analysis",
                ui.div(
                    ui.div("AI-Powered Risk Analysis", class_="panel-title"),
                    ui.p("Generate a narrative risk report with actionable recommendations", class_="panel-subtitle"),
                    ui.layout_columns(
                        ui.input_select("ai_neighborhood", "Neighborhood", choices={}, selected=None, width="100%"),
                        ui.input_action_button("run_ai", "Generate Report", class_="btn-primary btn-lg", width="100%"),
                        col_widths=(8, 4)
                    ),
                    ui.output_ui("ai_analysis_result"),
                    class_="panel"
                ),
            ),

            ui.nav_spacer(),

            # === Tab: Trends ===
            ui.nav_panel("Trends & History",
                ui.div(
                    ui.div("Historical Risk Trends", class_="panel-title"),
                    ui.p("14-day risk history for selected neighborhood", class_="panel-subtitle"),
                    ui.input_select("trend_neighborhood", "Neighborhood", choices={}, selected=None, width="100%"),
                    ui.output_data_frame("trend_table"),
                    class_="panel"
                ),
                ui.div(
                    ui.div("AI Trend Intelligence", class_="panel-title"),
                    ui.p("Choose an analysis type to generate AI-powered insights", class_="panel-subtitle"),
                    ui.layout_columns(
                        ui.div(
                            ui.div("Rising Risk", class_="ac-title"),
                            ui.div("Which areas are getting worse?", class_="ac-desc"),
                            ui.input_action_button("analyze_trends", "Analyze", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        ui.div(
                            ui.div("Historical Comparison", class_="ac-title"),
                            ui.div("Current vs past patterns", class_="ac-desc"),
                            ui.input_action_button("compare_history", "Compare", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        ui.div(
                            ui.div("Risk Acceleration", class_="ac-title"),
                            ui.div("Where is risk growing fastest?", class_="ac-desc"),
                            ui.input_action_button("analyze_acceleration", "Detect", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        col_widths=(4, 4, 4)
                    ),
                    ui.output_ui("trend_analysis_result"),
                    ui.output_ui("historical_comparison_result"),
                    ui.output_ui("acceleration_result"),
                    class_="panel"
                ),
            ),

            # === Tab: Citywide ===
            ui.nav_panel("Citywide Summary",
                ui.div(
                    ui.div("Citywide Risk Briefing", class_="panel-title"),
                    ui.p("AI-generated executive summary for NYC emergency management stakeholders", class_="panel-subtitle"),
                    ui.input_action_button("generate_summary", "Generate Briefing", class_="btn-primary btn-lg"),
                    ui.output_ui("city_summary"),
                    class_="panel"
                ),
            ),

            # === Tab: Email Alerts ===
            ui.nav_panel("Email Alerts",
                ui.div(
                    ui.div("Automated Email Alerts", class_="panel-title"),
                    ui.p("Configure automatic email notifications when neighborhoods exceed the risk threshold", class_="panel-subtitle"),

                    # Current config
                    ui.div("Configuration", class_="section-label"),
                    ui.div(
                        ui.div(ui.span("Recipient", class_="config-label"), ui.span("zl2268@cornell.edu", class_="config-value"), class_="config-row"),
                        ui.div(ui.span("SMTP Status", class_="config-label"), ui.output_ui("smtp_status"), class_="config-row"),
                        ui.div(ui.span("AI Status", class_="config-label"), ui.output_ui("ai_debug_status"), class_="config-row"),
                    ),

                    # Threshold setting
                    ui.div("Alert Threshold", class_="section-label"),
                    ui.layout_columns(
                        ui.div(
                            ui.output_ui("current_threshold_display"),
                            style="text-align:center;padding:16px 0;"
                        ),
                        ui.div(
                            ui.input_slider("alert_threshold", "Risk Score Threshold",
                                           min=30, max=90, value=email_system.risk_threshold if email_system else 65, step=5,
                                           post="/100"),
                            ui.p("Neighborhoods scoring above this threshold will trigger an email alert.",
                                 style="font-size:0.85em;color:var(--grey-dark);margin-top:4px;"),
                        ),
                        col_widths=(3, 9)
                    ),

                    # Actions
                    ui.div("Actions", class_="section-label"),
                    ui.layout_columns(
                        ui.div(
                            ui.div("Test Alert", class_="ac-title"),
                            ui.div("Send a test email now", class_="ac-desc"),
                            ui.input_action_button("send_test_alert", "Send Test", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        ui.div(
                            ui.div("Check & Alert", class_="ac-title"),
                            ui.div("Check current data and alert if needed", class_="ac-desc"),
                            ui.input_action_button("check_and_alert", "Run Check", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        ui.div(
                            ui.div("Preview Email", class_="ac-title"),
                            ui.div("Preview alert email in browser", class_="ac-desc"),
                            ui.input_action_button("preview_alert", "Preview", class_="btn-primary", style="margin-top:12px;", width="100%"),
                            class_="action-card"
                        ),
                        col_widths=(4, 4, 4)
                    ),

                    # Results
                    ui.output_ui("alert_send_result"),
                    ui.output_ui("alert_preview_result"),

                    # Current at-risk neighborhoods
                    ui.div("Neighborhoods Above Threshold", class_="section-label"),
                    ui.output_ui("at_risk_neighborhoods"),

                    class_="panel"
                ),
            ),

            ui.nav_spacer(),

            # === Tab: About ===
            ui.nav_panel("About",
                ui.div(
                    ui.div("About This System", class_="panel-title"),
                    ui.p(
                        "This system uses the NWS Heat Index formula and the Heat Vulnerability Index (HVI) framework "
                        "to provide heat wave risk early warning for NYC Emergency Management.",
                        class_="panel-subtitle", style="max-width: 640px;"
                    ),

                    ui.div("Risk Levels", class_="section-label"),
                    ui.tags.table(
                        ui.tags.thead(ui.tags.tr(
                            ui.tags.th("Score", style="width:100px;"), ui.tags.th("Level"), ui.tags.th("Response")
                        )),
                        ui.tags.tbody(
                            ui.tags.tr(ui.tags.td("75 - 100"), ui.tags.td(ui.span("CRITICAL", class_="risk-badge risk-critical")), ui.tags.td("Immediate action required")),
                            ui.tags.tr(ui.tags.td("50 - 74"), ui.tags.td(ui.span("HIGH", class_="risk-badge risk-high")), ui.tags.td("Close monitoring needed")),
                            ui.tags.tr(ui.tags.td("25 - 49"), ui.tags.td(ui.span("MEDIUM", class_="risk-badge risk-medium")), ui.tags.td("Stay vigilant")),
                            ui.tags.tr(ui.tags.td("0 - 24"), ui.tags.td(ui.span("LOW", class_="risk-badge risk-low")), ui.tags.td("Normal operations")),
                        ),
                        class_="table", style="max-width: 540px;"
                    ),

                    ui.div("Risk Formula", class_="section-label"),
                    ui.div(
                        ui.div(ui.div("TEMPERATURE", class_="label"), ui.div("0 - 30 pts", class_="value"), class_="breakdown-item"),
                        ui.div(ui.div("POPULATION VULNERABILITY", class_="label"), ui.div("0 - 30 pts", class_="value"), class_="breakdown-item"),
                        ui.div(ui.div("AC COVERAGE GAP", class_="label"), ui.div("0 - 20 pts", class_="value"), class_="breakdown-item"),
                        ui.div(ui.div("GREEN SPACE DEFICIT", class_="label"), ui.div("0 - 20 pts", class_="value"), class_="breakdown-item"),
                        class_="breakdown-grid"
                    ),

                    ui.div("Data Sources", class_="section-label"),
                    ui.p("Real-time weather from Open-Meteo API. Neighborhood vulnerability based on NYC Open Data patterns. AI analysis via Ollama local LLM or OpenAI GPT-4o-mini.", style="color: var(--grey-dark); max-width: 640px;"),

                    ui.p("Built for AI Systems Hackathon 2026", style="margin-top: 40px; color: var(--grey-dark); font-size: 0.85em;"),
                    class_="panel"
                ),
            ),

            widths=(2, 10),
        ),

        style="max-width: 1400px; margin: 0 auto; padding: 0 24px;"
    )
)


# ========== Server ==========
def server(input, output, session):

    def c_to_f(c):
        return c * 9/5 + 32

    @reactive.effect
    @reactive.event(input.reset_today)
    def _reset_to_today():
        ui.update_date("query_date", value=str(date.today()))

    @reactive.calc
    def selected_date():
        d = input.query_date()
        if d is None:
            return date.today()
        if isinstance(d, str):
            return date.fromisoformat(d)
        return d

    @reactive.calc
    def is_historical():
        return selected_date() < date.today()

    @reactive.calc
    def live_weather_data():
        sel = selected_date()
        if sel < date.today():
            weather = fetch_historical_weather(str(sel))
        else:
            weather = fetch_live_weather()

        if weather and "error" not in weather:
            temp_c = weather.get("temperature", 20)
            humidity = weather.get("humidity", 50)
            apparent = weather.get("apparent_temperature", temp_c)
            temp_f = c_to_f(temp_c)
            return {"temp_c": temp_c, "temp_f": temp_f, "humidity": humidity, "apparent_c": apparent, "date": str(sel)}
        return {"temp_c": 20, "temp_f": 68, "humidity": 50, "apparent_c": 20, "date": str(sel)}

    @output
    @render.ui
    def live_weather():
        w = live_weather_data()
        historical = is_historical()
        sel = selected_date()
        if historical:
            return ui.span(
                f"NYC {sel.strftime('%b %d, %Y')}: {w['temp_c']:.1f}C / {w['temp_f']:.0f}F  |  "
                f"Feels like {w['apparent_c']:.1f}C  |  "
                f"Humidity {w['humidity']}%",
                ui.span("HISTORICAL", class_="historical-badge")
            )
        return ui.span(
            f"NYC Now: {w['temp_c']:.1f}C / {w['temp_f']:.0f}F  |  "
            f"Feels like {w['apparent_c']:.1f}C  |  "
            f"Humidity {w['humidity']}%"
        )

    @reactive.calc
    def all_risk_data():
        weather = live_weather_data()
        neighborhoods = data_loader.get_all_neighborhoods()
        results = []
        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=weather["temp_f"], humidity=weather["humidity"],
                elderly_pct=row['elderly_pct'], ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'], green_space_pct=row['green_space_pct']
            )
            results.append({
                'zip_code': row['zip_code'], 'name': row['name'],
                'borough': row['borough'], 'population': row['population'],
                'latitude': row['latitude'], 'longitude': row['longitude'],
                'elderly_pct': row['elderly_pct'], 'ac_pct': row['ac_pct'],
                'poverty_pct': row['poverty_pct'], 'green_space_pct': row['green_space_pct'],
                'temperature': weather["temp_f"], 'humidity': weather["humidity"],
                'heat_index': risk['heat_index'], 'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level'], 'color': risk['color'],
                'breakdown': risk['breakdown'],
            })
        return results

    @reactive.calc
    def neighborhood_choices():
        data = all_risk_data()
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        choices = {}
        for r in sorted(data, key=lambda x: x['risk_score'], reverse=True):
            choices[str(r['zip_code'])] = f"{r['name']} ({r['zip_code']}) -- {r['risk_score']} {level_en.get(r['risk_level'], 'LOW')}"
        return choices

    @reactive.effect
    def _update_selects():
        choices = neighborhood_choices()
        ui.update_select("neighborhood", choices=choices)
        ui.update_select("ai_neighborhood", choices=choices)
        ui.update_select("trend_neighborhood", choices=choices)

    # ---------- Summary Stats ----------
    @output
    @render.ui
    def summary_stats():
        data = all_risk_data()
        total = len(data)
        critical = sum(1 for r in data if r['risk_score'] >= 75)
        high = sum(1 for r in data if 50 <= r['risk_score'] < 75)
        medium = sum(1 for r in data if 25 <= r['risk_score'] < 50)
        low = sum(1 for r in data if r['risk_score'] < 25)
        avg = sum(r['risk_score'] for r in data) / total if total else 0
        w = live_weather_data()
        def stat(num, label, color="var(--black)"):
            return ui.div(ui.div(num, class_="num", style=f"color: {color};"), ui.div(label, class_="lbl"), class_="stat-box")
        return ui.div(
            stat(f"{w['temp_f']:.0f}F", "Temperature", "var(--orange)"),
            stat(f"{avg:.1f}", "Avg Risk", "var(--orange)"),
            stat(str(critical), "Critical", "var(--risk-critical)"),
            stat(str(high), "High", "var(--risk-high)"),
            stat(str(medium), "Medium", "var(--risk-medium)"),
            stat(str(low), "Low", "var(--risk-low)"),
            class_="stat-row"
        )

    # ---------- Risk Map ----------
    @output
    @render.ui
    def risk_map():
        data = all_risk_data()
        m = folium.Map(location=[40.7128, -73.98], zoom_start=11, tiles="CartoDB positron", width="100%", height=520)
        color_map = {"极高": "#C62828", "高": "#E65100", "中": "#F9A825", "低": "#2E7D32"}
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        for r in data:
            lat, lng = r['latitude'], r['longitude']
            score, level = r['risk_score'], r['risk_level']
            fc = color_map.get(level, "#2E7D32")
            popup_html = f"""<div style="font-family:'Rethink Sans',sans-serif;min-width:200px;">
                <div style="font-size:15px;font-weight:700;color:{fc};margin-bottom:2px;">{r['name']}</div>
                <div style="font-size:12px;color:#A3A3A3;margin-bottom:10px;">{r['borough']} | {r['zip_code']}</div>
                <div style="background:{fc};color:white;padding:4px 12px;border-radius:4px;display:inline-block;font-weight:700;font-size:13px;margin-bottom:10px;">{score}/100 -- {level_en.get(level,'LOW')}</div>
                <table style="width:100%;font-size:12px;border-collapse:collapse;">
                    <tr><td style="padding:3px 0;">Heat Index</td><td style="text-align:right;font-weight:600;">{r['heat_index']}F</td></tr>
                    <tr><td style="padding:3px 0;">Elderly (65+)</td><td style="text-align:right;font-weight:600;">{r['elderly_pct']}%</td></tr>
                    <tr><td style="padding:3px 0;">AC Coverage</td><td style="text-align:right;font-weight:600;">{r['ac_pct']}%</td></tr>
                    <tr><td style="padding:3px 0;">Poverty Rate</td><td style="text-align:right;font-weight:600;">{r['poverty_pct']}%</td></tr>
                    <tr><td style="padding:3px 0;">Green Space</td><td style="text-align:right;font-weight:600;">{r['green_space_pct']}%</td></tr>
                </table></div>"""
            folium.CircleMarker(location=[lat, lng], radius=max(12, score/3), color=fc, fill=True, fill_color=fc, fill_opacity=0.65, weight=2,
                popup=folium.Popup(popup_html, max_width=260),
                tooltip=f"{r['name']}: {score}/100 ({level_en.get(level,'LOW')})").add_to(m)
            folium.Marker(location=[lat, lng], icon=folium.DivIcon(
                html=f'<div style="font-family:Rethink Sans,sans-serif;font-size:11px;font-weight:700;color:white;background:{fc};border-radius:3px;padding:2px 6px;text-align:center;border:1.5px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.2);white-space:nowrap;">{score}</div>',
                icon_size=(36, 20), icon_anchor=(18, 10))).add_to(m)
        legend_html = """<div style="position:fixed;bottom:30px;left:290px;z-index:1000;background:white;padding:14px 18px;border-radius:6px;border:1px solid #E5E5E5;font-family:'Rethink Sans',sans-serif;">
            <div style="font-weight:700;margin-bottom:8px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;color:#A3A3A3;">Risk Level</div>
            <div style="display:flex;flex-direction:column;gap:5px;font-size:12px;">
                <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#C62828;margin-right:8px;vertical-align:middle;"></span>Critical (75-100)</div>
                <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#E65100;margin-right:8px;vertical-align:middle;"></span>High (50-74)</div>
                <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#F9A825;margin-right:8px;vertical-align:middle;"></span>Medium (25-49)</div>
                <div><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#2E7D32;margin-right:8px;vertical-align:middle;"></span>Low (0-24)</div>
            </div></div>"""
        m.get_root().html.add_child(folium.Element(legend_html))
        return ui.HTML(m._repr_html_())

    # ---------- Risk Table ----------
    @output
    @render.data_frame
    def risk_table():
        data = all_risk_data()
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        rows = [{'ZIP': r['zip_code'], 'Neighborhood': r['name'], 'Borough': r['borough'],
                 'Temp (F)': f"{r['temperature']:.0f}", 'Heat Index': r['heat_index'],
                 'Risk Score': r['risk_score'], 'Level': level_en.get(r['risk_level'], 'LOW')} for r in data]
        return render.DataTable(pd.DataFrame(rows).sort_values('Risk Score', ascending=False), height="480px")

    # ---------- Neighborhood Detail ----------
    @output
    @render.ui
    def neighborhood_detail():
        zip_code = input.neighborhood()
        if not zip_code:
            return ui.p("Select a neighborhood above.", style="color:var(--grey-dark);padding:40px 0;text-align:center;")
        data = all_risk_data()
        r = next((x for x in data if str(x['zip_code']) == str(zip_code)), None)
        if not r:
            return ui.p("Neighborhood not found.")
        risk_class = {"极高": "risk-critical", "高": "risk-high", "中": "risk-medium", "低": "risk-low"}.get(r['risk_level'], "risk-low")
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}.get(r['risk_level'], "LOW")
        w = live_weather_data()
        return ui.div(
            ui.h3(r['name'], style="font-weight:800;margin:0;"),
            ui.p(f"{r['borough']}  |  ZIP {zip_code}  |  Pop. {r['population']:,}", style="color:var(--grey-dark);margin:4px 0 20px;"),
            ui.div(ui.span(f"{r['risk_score']}/100 -- {level_en}", class_=f"risk-badge {risk_class}", style="font-size:1.1em;padding:6px 18px;"), style="margin-bottom:24px;"),
            ui.div("Score Breakdown", class_="section-label"),
            ui.div(
                ui.div(ui.div("TEMPERATURE", class_="label"), ui.div(f"{r['breakdown']['temperature']}/30", class_="value"), class_="breakdown-item"),
                ui.div(ui.div("POPULATION", class_="label"), ui.div(f"{r['breakdown']['population']}/30", class_="value"), class_="breakdown-item"),
                ui.div(ui.div("AC COVERAGE", class_="label"), ui.div(f"{r['breakdown']['ac_coverage']}/20", class_="value"), class_="breakdown-item"),
                ui.div(ui.div("GREEN SPACE", class_="label"), ui.div(f"{r['breakdown']['environment']}/20", class_="value"), class_="breakdown-item"),
                class_="breakdown-grid"),
            ui.div("Live Weather", class_="section-label"),
            ui.p(f"Temperature {r['temperature']:.1f}F ({w['temp_c']:.1f}C)  |  Humidity {r['humidity']}%  |  Heat Index {r['heat_index']}F"),
            ui.div("Vulnerability Indicators", class_="section-label"),
            ui.p(f"Elderly (65+): {r['elderly_pct']}%  |  AC Coverage: {r['ac_pct']}%  |  Poverty Rate: {r['poverty_pct']}%  |  Green Space: {r['green_space_pct']}%"),
        )

    # ---------- AI Analysis ----------
    @output
    @render.ui
    @reactive.event(input.run_ai)
    def ai_analysis_result():
        zip_code = input.ai_neighborhood()
        if not zip_code:
            return ui.p("Select a neighborhood first.", style="color:var(--grey-dark);")
        data = all_risk_data()
        r = next((x for x in data if str(x['zip_code']) == str(zip_code)), None)
        if not r:
            return ui.p("Neighborhood not found.")
        analysis = ai_client.generate_analysis(
            neighborhood_name=r['name'], zip_code=str(r['zip_code']),
            temperature=r['temperature'], humidity=r['humidity'],
            heat_index=r['heat_index'], risk_score=r['risk_score'],
            risk_level=r['risk_level'], elderly_pct=r['elderly_pct'],
            ac_pct=r['ac_pct'], poverty_pct=r['poverty_pct'],
            green_space_pct=r['green_space_pct'])
        return ui.div(ui.markdown(analysis), class_="analysis-box")

    # ---------- Trend Table ----------
    @output
    @render.data_frame
    def trend_table():
        zip_code = input.trend_neighborhood()
        if not zip_code:
            return pd.DataFrame()
        trend = data_loader.get_heat_trend(zip_code, 14)
        if trend.empty:
            return pd.DataFrame()
        df = trend[['date', 'temperature', 'humidity', 'heat_index', 'risk_score']].copy()
        df.columns = ['Date', 'Temp (F)', 'Humidity (%)', 'Heat Index', 'Risk Score']
        return df

    # ---------- AI Trend Analyses ----------
    @output
    @render.ui
    @reactive.event(input.analyze_trends)
    def trend_analysis_result():
        data = all_risk_data()
        results = [{'name': r['name'], 'zip_code': r['zip_code'], 'risk_score': r['risk_score'], 'risk_level': r['risk_level']} for r in data]
        return ui.div(ui.markdown(ai_client.generate_risk_trend_analysis(results, [])), class_="analysis-box")

    @output
    @render.ui
    @reactive.event(input.compare_history)
    def historical_comparison_result():
        data = all_risk_data()
        results = [{'name': r['name'], 'risk_score': r['risk_score'], 'risk_level': r['risk_level']} for r in data]
        return ui.div(ui.markdown(ai_client.generate_historical_comparison(results, {"historical_avg": data_loader.get_historical_average(14), "acceleration": data_loader.get_risk_acceleration()})), class_="analysis-box")

    @output
    @render.ui
    @reactive.event(input.analyze_acceleration)
    def acceleration_result():
        data = all_risk_data()
        results = [{'name': r['name'], 'zip_code': r['zip_code'], 'risk_score': r['risk_score'], 'risk_level': r['risk_level']} for r in data]
        return ui.div(ui.markdown(ai_client.generate_risk_acceleration(results, data_loader.get_risk_acceleration())), class_="analysis-box")

    # ---------- City Summary ----------
    @output
    @render.ui
    @reactive.event(input.generate_summary)
    def city_summary():
        data = all_risk_data()
        w = live_weather_data()
        results = [{'name': r['name'], 'zip_code': r['zip_code'], 'risk_score': r['risk_score'], 'risk_level': r['risk_level']} for r in data]
        summary = ai_client.generate_citywide_summary(results, w['temp_f'], w['humidity'])
        return ui.div(
            ui.p(f"Based on live weather: {w['temp_c']:.1f}C, Humidity {w['humidity']}%", style="font-size:0.85em;color:var(--grey-dark);margin-bottom:8px;"),
            ui.div(ui.markdown(summary), class_="analysis-box")
        )

    # ---------- Email Alert System ----------
    @output
    @render.ui
    def smtp_status():
        if email_system and email_system.is_configured():
            return ui.span("Connected", style="color:var(--risk-low);font-weight:600;")
        return ui.span("Not configured — set sender_email and sender_password in config.json", style="color:var(--risk-high);font-weight:500;font-size:0.88em;")

    @output
    @render.ui
    def ai_debug_status():
        import os
        provider = os.environ.get("AI_PROVIDER") or os.environ.get("ai_provider") or "not set"
        model = os.environ.get("OLLAMA_MODEL") or os.environ.get("ollama_model") or "not set"
        url = os.environ.get("OLLAMA_BASE_URL") or os.environ.get("ollama_base_url") or "not set"
        api_key = os.environ.get("OLLAMA_API_KEY") or os.environ.get("ollama_api_key") or "not set"
        return ui.div(
            ui.p(f"DEBUG - Provider: {provider}", style="font-size:12px;margin:4px 0;"),
            ui.p(f"DEBUG - Model: {model}", style="font-size:12px;margin:4px 0;"),
            ui.p(f"DEBUG - URL: {url}", style="font-size:12px;margin:4px 0;"),
            ui.p(f"DEBUG - API Key: {'set' if api_key != 'not set' else 'not set'}", style="font-size:12px;margin:4px 0;"),
            style="background:#f5f5f5;padding:12px;border-radius:4px;margin-top:8px;font-family:monospace;"
        )

    @output
    @render.ui
    def current_threshold_display():
        threshold = input.alert_threshold()
        if threshold >= 75:
            color = "var(--risk-critical)"
        elif threshold >= 50:
            color = "var(--risk-high)"
        else:
            color = "var(--risk-medium)"
        return ui.div(
            ui.div(str(threshold), class_="threshold-display", style=f"color:{color};"),
            ui.div("THRESHOLD", class_="lbl", style="margin-top:4px;")
        )

    @output
    @render.ui
    def at_risk_neighborhoods():
        data = all_risk_data()
        threshold = input.alert_threshold()
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        exceeding = [r for r in data if r['risk_score'] >= threshold]
        exceeding.sort(key=lambda x: x['risk_score'], reverse=True)

        if not exceeding:
            return ui.div(
                ui.p(f"No neighborhoods currently above the threshold of {threshold}/100.", style="color:var(--risk-low);font-weight:600;"),
                class_="alert-success"
            )

        items = []
        for r in exceeding:
            risk_class = {"极高": "risk-critical", "高": "risk-high", "中": "risk-medium", "低": "risk-low"}.get(r['risk_level'], "risk-low")
            items.append(
                ui.div(
                    ui.div(
                        ui.span(f"{r['risk_score']}", class_=f"risk-badge {risk_class}", style="margin-right:12px;"),
                        ui.strong(r['name']),
                        ui.span(f"  {r['borough']}  |  Heat Index {r['heat_index']}F  |  Elderly {r['elderly_pct']}%  |  AC {r['ac_pct']}%",
                                style="color:var(--grey-dark);font-size:0.88em;margin-left:8px;"),
                    ),
                    style="padding:10px 0;border-bottom:1px solid var(--grey);"
                )
            )
        return ui.div(
            ui.p(f"{len(exceeding)} neighborhood(s) above threshold of {threshold}/100:",
                 style="font-weight:600;color:var(--risk-high);margin-bottom:8px;"),
            *items
        )

    @output
    @render.ui
    @reactive.event(input.send_test_alert)
    def alert_send_result():
        if not email_system:
            return ui.div("Email alerts not configured. Add SMTP settings in config.json.", class_="alert-info")

        data = all_risk_data()
        threshold = input.alert_threshold()
        email_system.risk_threshold = threshold
        w = live_weather_data()
        weather_info = f"NYC Weather: {w['temp_f']:.0f}F, Humidity {w['humidity']}%"

        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}
        exceeding = []
        for r in data:
            if r['risk_score'] >= threshold:
                exceeding.append({
                    "name": r["name"], "borough": r["borough"],
                    "risk_score": r["risk_score"],
                    "level_en": level_en.get(r.get("risk_level", "低"), "LOW"),
                    "heat_index": r.get("heat_index", "N/A"),
                    "elderly_pct": r.get("elderly_pct", ""), "ac_pct": r.get("ac_pct", ""),
                })

        if not exceeding:
            return ui.div(f"No neighborhoods above threshold ({threshold}). No alert sent.", class_="alert-info")

        result = email_system.send_alert(exceeding, weather_info)
        if result["success"]:
            return ui.div(f"Alert sent successfully to {email_system.recipient_email} -- {len(exceeding)} neighborhood(s) flagged.", class_="alert-success")
        return ui.div(f"Send failed: {result['message']}", class_="alert-fail")

    @reactive.effect
    @reactive.event(input.check_and_alert)
    def _check_alert():
        if not email_system:
            return
        data = all_risk_data()
        threshold = input.alert_threshold()
        email_system.risk_threshold = threshold
        w = live_weather_data()
        weather_info = f"NYC Weather: {w['temp_f']:.0f}F, Humidity {w['humidity']}%"
        email_system.check_and_alert(data, weather_info)

    @output
    @render.ui
    @reactive.event(input.preview_alert)
    def alert_preview_result():
        if not email_system:
            return ui.div("Email alerts not configured. Add SMTP settings in config.json.", class_="alert-info")

        data = all_risk_data()
        threshold = input.alert_threshold()
        w = live_weather_data()
        weather_info = f"NYC Weather: {w['temp_f']:.0f}F, Humidity {w['humidity']}%"
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}

        exceeding = []
        for r in data:
            if r['risk_score'] >= threshold:
                exceeding.append({
                    "name": r["name"], "borough": r["borough"],
                    "risk_score": r["risk_score"],
                    "level_en": level_en.get(r.get("risk_level", "低"), "LOW"),
                    "heat_index": r.get("heat_index", "N/A"),
                    "elderly_pct": r.get("elderly_pct", ""), "ac_pct": r.get("ac_pct", ""),
                })

        if not exceeding:
            return ui.div(f"No neighborhoods above threshold ({threshold}). Nothing to preview.", class_="alert-info")

        html = email_system.build_alert_html(exceeding, weather_info)
        return ui.div(
            ui.p(f"Email preview — {len(exceeding)} neighborhood(s) above {threshold}:", style="font-weight:600;margin-bottom:12px;"),
            ui.HTML(f'<div style="border:1px solid var(--grey);border-radius:6px;padding:4px;margin-top:8px;">{html}</div>')
        )


app = App(app_ui, server, debug=False)
