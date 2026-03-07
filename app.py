"""
NYC Heat Wave Risk Dashboard
===========================
Shiny Dashboard for NYC Heat Wave Risk Monitoring

Run with: shiny run app:app --reload
"""

from shiny import App, ui, render, reactive
import pandas as pd
import json
from pathlib import Path

from core.risk_formula import calculate_heat_risk, get_risk_level
from core.ai_client import AIClient
from core.data_loader import DataLoader
from core.real_data_loader import fetch_live_weather


# Initialize data loader and AI client
DATA_DIR = Path(__file__).parent
data_loader = DataLoader(DATA_DIR)

# Load API key from config.json
config_path = DATA_DIR / "config.json"
api_key = None
if config_path.exists():
    try:
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("openai_api_key")
            if api_key and api_key != "YOUR_API_KEY_HERE":
                print(f"✓ Loaded API key from config.json")
    except Exception as e:
        print(f"Error loading config: {e}")

ai_client = AIClient(api_key=api_key)


# CSS styling
app_css = """
.app-container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #ff6b6b, #ffa500);
    color: white;
    border-radius: 10px;
    margin-bottom: 20px;
}

.header h1 {
    margin: 0;
    font-size: 2.5em;
}

.header p {
    margin: 10px 0 0 0;
    opacity: 0.9;
}

.nav-tabs {
    margin-bottom: 20px;
}

.card {
    background: white;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.risk-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
    color: white;
}

.risk-low { background: #28a745; }
.risk-medium { background: #ffc107; color: black; }
.risk-high { background: #fd7e14; }
.risk-critical { background: #dc3545; }

.data-table {
    width: 100%;
    border-collapse: collapse;
}

.data-table th {
    background: #f8f9fa;
    padding: 12px;
    text-align: left;
    border-bottom: 2px solid #dee2e6;
}

.data-table td {
    padding: 10px;
    border-bottom: 1px solid #dee2e6;
}

.neighborhood-select {
    width: 100%;
    padding: 10px;
    font-size: 16px;
    border-radius: 5px;
}

.analysis-box {
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    border-left: 4px solid #ffa500;
    margin-top: 20px;
}

.loading {
    text-align: center;
    padding: 20px;
    color: #6c757d;
}
"""


# UI Layout
app_ui = ui.page_fluid(
    # Custom CSS
    ui.tags.style(app_css),

    # Header with Live Weather
    ui.div(
        ui.h1("NYC 热浪预警系统"),
        ui.p("NYC Heat Wave Early Warning System"),
        ui.div(
            ui.output_ui("live_weather"),
            style="text-align: center; margin-top: 10px;"
        ),
        class_="header"
    ),

    # Navigation Tabs
    ui.navset_tab(
        # Tab 1: Risk Dashboard
        ui.nav_panel(
            "📊 风险地图",
            ui.div(
                ui.h3("各社区热浪风险概览"),
                ui.output_data_frame("risk_table"),
                class_="card"
            )
        ),

        # Tab 2: Neighborhood Details
        ui.nav_panel(
            "🏘️ 社区详情",
            ui.div(
                ui.h3("查看社区详情"),
                ui.div(
                    ui.input_select(
                        "neighborhood",
                        "选择社区:",
                        choices={},
                        selected=None
                    ),
                    class_="neighborhood-select"
                ),
                ui.output_ui("neighborhood_detail"),
                class_="card"
            )
        ),

        # Tab 3: AI Analysis
        ui.nav_panel(
            "🤖 AI 分析",
            ui.div(
                ui.h3("AI 智能风险分析"),
                ui.div(
                    ui.input_select(
                        "ai_neighborhood",
                        "选择社区进行 AI 分析:",
                        choices={},
                        selected=None
                    ),
                    ui.input_action_button("run_ai", "生成 AI 分析报告", class_="btn-primary")
                ),
                ui.output_ui("ai_analysis_result"),
                class_="card"
            )
        ),

        # Tab 4: Trends
        ui.nav_panel(
            "📈 趋势分析",
            ui.div(
                ui.h3("风险趋势"),
                ui.div(
                    ui.input_select(
                        "trend_neighborhood",
                        "选择社区:",
                        choices={},
                        selected=None
                    ),
                    class_="neighborhood-select"
                ),
                ui.output_data_frame("trend_table"),
                class_="card"
            )
        ),

        # Tab 5: City Summary
        ui.nav_panel(
            "📋 全市摘要",
            ui.div(
                ui.h3("AI 生成的全市风险摘要"),
                ui.input_action_button("generate_summary", "生成全市摘要", class_="btn-primary"),
                ui.output_ui("city_summary"),
                class_="card"
            )
        ),

        # Tab 6: Risk Trends (NEW - Hackathon requirement)
        ui.nav_panel(
            "📈 风险趋势",
            ui.div(
                ui.h3("哪些社区的熱浪风险在上升？"),
                ui.p("分析各社区风险变化趋势"),
                ui.input_action_button("analyze_trends", "分析风险趋势", class_="btn-primary"),
                ui.output_ui("trend_analysis_result"),
                class_="card"
            )
        ),

        # Tab 7: Historical Comparison (NEW - Hackathon requirement)
        ui.nav_panel(
            "📊 历史对比",
            ui.div(
                ui.h3("今天与历史同期对比"),
                ui.p("当前风险水平与历史模式对比"),
                ui.input_action_button("compare_history", "历史对比分析", class_="btn-primary"),
                ui.output_ui("historical_comparison_result"),
                class_="card"
            )
        ),

        # Tab 8: Risk Acceleration (NEW - Hackathon requirement)
        ui.nav_panel(
            "⚡ 风险加速",
            ui.div(
                ui.h3("哪里风险上升最快？"),
                ui.p("识别风险加速最快的社区"),
                ui.input_action_button("analyze_acceleration", "分析风险加速", class_="btn-primary"),
                ui.output_ui("acceleration_result"),
                class_="card"
            )
        ),

        # Tab 9: About
        ui.nav_panel(
            "ℹ️ 关于",
            ui.div(
                ui.h3("关于本系统"),
                ui.p("""
                本系统基于 NWS Heat Index 公式和 Heat Vulnerability Index (HVI) 框架，
                为 NYC 应急管理部门提供热浪风险预警。
                """),
                ui.h4("风险等级说明"),
                ui.tags.ul(
                    ui.tags.li("🔴 极高 (75-100): 紧急状态，需立即采取行动"),
                    ui.tags.li("🟠 高 (50-74): 预警状态，需要关注"),
                    ui.tags.li("🟡 中 (25-49): 关注状态，保持警惕"),
                    ui.tags.li("🟢 低 (0-24): 正常状态"),
                ),
                ui.h4("数据来源"),
                ui.p("基于合成数据，仅供演示使用。"),
                class_="card"
            )
        ),
        id="main_tabs"
    )
)


def server(input, output, session):
    """Server logic for Shiny app"""

    # Convert C to F
    def c_to_f(c):
        return c * 9/5 + 32

    # Live Weather - fetch once and cache
    @reactive.calc
    def live_weather_data():
        weather = fetch_live_weather()
        if weather and "error" not in weather:
            temp_c = weather.get("temperature", 20)
            humidity = weather.get("humidity", 50)
            # Convert to Fahrenheit for risk calculation
            temp_f = c_to_f(temp_c)
            return {"temp_c": temp_c, "temp_f": temp_f, "humidity": humidity}
        # Default values if API fails
        return {"temp_c": 20, "temp_f": 68, "humidity": 50}

    # Live Weather Display
    @output
    @render.ui
    def live_weather():
        weather = fetch_live_weather()
        if weather and "error" not in weather:
            temp = weather.get("temperature", "N/A")
            feels_like = weather.get("apparent_temperature", "N/A")
            humidity = weather.get("humidity", "N/A")
            return ui.div(
                f"🌡️ NYC 当前: {temp}°C | 体感 {feels_like}°C | 湿度 {humidity}%",
                style="font-size: 14px; opacity: 0.9;"
            )
        else:
            return ui.div("🌡️ 天气数据加载中...", style="font-size: 14px;")

    # Get neighborhood choices
    @reactive.calc
    def neighborhood_choices():
        df = data_loader.get_all_latest_data()
        choices = {}
        for _, row in df.iterrows():
            risk_emoji = "🔴" if row['risk_score'] >= 75 else \
                        "🟠" if row['risk_score'] >= 50 else \
                        "🟡" if row['risk_score'] >= 25 else "🟢"
            choices[row['zip_code']] = f"{risk_emoji} {row['name']} ({row['zip_code']})"
        return choices

    # Update select inputs on load
    @reactive.effect
    def _():
        choices = neighborhood_choices()
        ui.update_select("neighborhood", choices=choices)
        ui.update_select("ai_neighborhood", choices=choices)
        ui.update_select("trend_neighborhood", choices=choices)

    # Tab 1: Risk Table
    @output
    @render.data_frame
    def risk_table():
        # Get live weather data
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        # Get all neighborhoods
        neighborhoods = data_loader.get_all_neighborhoods()

        # Calculate risk for each neighborhood based on live weather
        results = []
        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=temp_f,
                humidity=humidity,
                elderly_pct=row['elderly_pct'],
                ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'],
                green_space_pct=row['green_space_pct']
            )
            results.append({
                'zip_code': row['zip_code'],
                'name': row['name'],
                'borough': row['borough'],
                'temperature': temp_f,
                'humidity': humidity,
                'heat_index': risk['heat_index'],
                'risk_score': risk['risk_score'],
                '风险等级': "🔴 极高" if risk['risk_score'] >= 75 else \
                           "🟠 高" if risk['risk_score'] >= 50 else \
                           "🟡 中" if risk['risk_score'] >= 25 else "🟢 低"
            })

        df_display = pd.DataFrame(results)
        df_display.columns = ['邮编', '社区名称', '行政区', '温度(°F)',
                             '湿度(%)', '体感温度', '风险分', '风险等级']

        return df_display

    # Tab 2: Neighborhood Detail
    @output
    @render.ui
    def neighborhood_detail():
        zip_code = input.neighborhood()
        if not zip_code:
            return ui.p("请选择一个社区", class_="loading")

        # Get neighborhood data
        nh = data_loader.get_neighborhood(zip_code)
        if nh is None:
            return ui.p("未找到社区数据", class_="loading")

        # Get live weather data
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        # Calculate risk using live weather
        risk = calculate_heat_risk(
            temperature=temp_f,
            humidity=humidity,
            elderly_pct=nh['elderly_pct'],
            ac_pct=nh['ac_pct'],
            poverty_pct=nh['poverty_pct'],
            green_space_pct=nh['green_space_pct']
        )

        # Get risk badge class
        risk_class = f"risk-{risk['risk_level']}"

        return ui.div(
            ui.h4(f"📍 {nh['name']} ({zip_code})"),
            ui.tags.p(f"行政区: {nh['borough']}"),
            ui.tags.p(f"人口: {nh['population']:,}"),

            ui.h5("📊 风险评估"),
            ui.div(
                f"风险分: {risk['risk_score']}/100",
                class_=f"risk-badge {risk_class}",
                style="font-size: 24px; padding: 10px 20px;"
            ),
            ui.tags.p(f"风险等级: {risk['color']} {risk['risk_level']}"),
            ui.tags.p(f"体感温度: {risk['heat_index']}°F"),

            ui.h5("🌡️ 气象数据 (实时)"),
            ui.tags.li(f"温度: {temp_f:.1f}°F ({weather['temp_c']:.1f}°C)"),
            ui.tags.li(f"湿度: {humidity}%"),
            ui.tags.li(f"体感温度: {risk['heat_index']}°F"),

            ui.h5("👥 脆弱性指标"),
            ui.tags.li(f"65岁以上老人: {nh['elderly_pct']}%"),
            ui.tags.li(f"空调覆盖率: {nh['ac_pct']}%"),
            ui.tags.li(f"贫困率: {nh['poverty_pct']}%"),
            ui.tags.li(f"绿地覆盖率: {nh['green_space_pct']}%"),

            ui.h5("📉 得分明细"),
            ui.tags.li(f"温度/体感: {risk['breakdown']['temperature']}分"),
            ui.tags.li(f"人口脆弱性: {risk['breakdown']['population']}分"),
            ui.tags.li(f"空调覆盖: {risk['breakdown']['ac_coverage']}分"),
            ui.tags.li(f"环境: {risk['breakdown']['environment']}分"),
        )

    # Tab 3: AI Analysis
    @output
    @render.ui
    @reactive.event(input.run_ai)
    def ai_analysis_result():
        zip_code = input.ai_neighborhood()
        if not zip_code:
            return ui.p("请选择一个社区", class_="loading")

        # Get neighborhood data
        nh = data_loader.get_neighborhood(zip_code)
        if nh is None:
            return ui.p("未找到社区数据", class_="loading")

        # Get live weather data
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        # Calculate risk using live weather
        risk = calculate_heat_risk(
            temperature=temp_f,
            humidity=humidity,
            elderly_pct=nh['elderly_pct'],
            ac_pct=nh['ac_pct'],
            poverty_pct=nh['poverty_pct'],
            green_space_pct=nh['green_space_pct']
        )

        # Generate AI analysis
        analysis = ai_client.generate_analysis(
            neighborhood_name=nh['name'],
            zip_code=zip_code,
            temperature=temp_f,
            humidity=humidity,
            heat_index=risk['heat_index'],
            risk_score=risk['risk_score'],
            risk_level=risk['risk_level'],
            elderly_pct=nh['elderly_pct'],
            ac_pct=nh['ac_pct'],
            poverty_pct=nh['poverty_pct'],
            green_space_pct=nh['green_space_pct']
        )

        return ui.div(
            ui.h4(f"🤖 {nh['name']} AI 风险分析"),
            ui.div(
                ui.markdown(analysis),
                class_="analysis-box"
            )
        )

    # Tab 4: Trends
    @output
    @render.data_frame
    def trend_table():
        zip_code = input.trend_neighborhood()
        if not zip_code:
            return pd.DataFrame()

        trend = data_loader.get_heat_trend(zip_code, 7)

        df_display = trend[['date', 'temperature', 'humidity', 'heat_index', 'risk_score']].copy()
        df_display.columns = ['日期', '温度(°F)', '湿度(%)', '体感温度', '风险分']

        return df_display

    # Tab 5: City Summary
    @output
    @render.ui
    @reactive.event(input.generate_summary)
    def city_summary():
        # Get live weather data
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        # Get all neighborhoods
        neighborhoods = data_loader.get_all_neighborhoods()

        # Calculate risk for each neighborhood using live weather
        results = []
        risk_counts = {"极高": 0, "高": 0, "中": 0, "低": 0}

        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=temp_f,
                humidity=humidity,
                elderly_pct=row['elderly_pct'],
                ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'],
                green_space_pct=row['green_space_pct']
            )
            level = risk['risk_level']
            risk_counts[level] = risk_counts.get(level, 0) + 1
            results.append({
                'name': row['name'],
                'zip_code': row['zip_code'],
                'risk_score': risk['risk_score'],
                'risk_level': level
            })

        # Generate summary using live weather data
        summary = ai_client.generate_citywide_summary(results, temp_f, humidity)

        return ui.div(
            ui.h4("📋 全市风险摘要"),
            ui.p(f"基于实时天气: {weather['temp_c']:.1f}°C, 湿度 {humidity}%", style="font-size: 12px; color: #666;"),
            ui.div(
                ui.markdown(summary),
                class_="analysis-box"
            )
        )

    # Tab 6: Risk Trend Analysis - "Which neighborhoods show rising heat?"
    @output
    @render.ui
    @reactive.event(input.analyze_trends)
    def trend_analysis_result():
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        neighborhoods = data_loader.get_all_neighborhoods()
        results = []

        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=temp_f,
                humidity=humidity,
                elderly_pct=row['elderly_pct'],
                ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'],
                green_space_pct=row['green_space_pct']
            )
            results.append({
                'name': row['name'],
                'zip_code': row['zip_code'],
                'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level']
            })

        trend_analysis = ai_client.generate_risk_trend_analysis(results, [])

        return ui.div(
            ui.h4("📈 风险趋势分析"),
            ui.p(f"基于实时天气: {weather['temp_c']:.1f}°C", style="font-size: 12px; color: #666;"),
            ui.div(
                ui.markdown(trend_analysis),
                class_="analysis-box"
            )
        )

    # Tab 7: Historical Comparison - "How does today compare to similar historical patterns?"
    @output
    @render.ui
    @reactive.event(input.compare_history)
    def historical_comparison_result():
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        neighborhoods = data_loader.get_all_neighborhoods()
        results = []

        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=temp_f,
                humidity=humidity,
                elderly_pct=row['elderly_pct'],
                ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'],
                green_space_pct=row['green_space_pct']
            )
            results.append({
                'name': row['name'],
                'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level']
            })

        # Calculate historical average from all neighborhoods
        historical_avg = data_loader.get_historical_average(14)

        # Get acceleration data
        acceleration_data = data_loader.get_risk_acceleration()

        comparison = ai_client.generate_historical_comparison(
            results,
            {"historical_avg": historical_avg, "acceleration": acceleration_data}
        )

        return ui.div(
            ui.h4("📊 历史对比分析"),
            ui.p(f"当前天气: {weather['temp_c']:.1f}°C vs 历史数据", style="font-size: 12px; color: #666;"),
            ui.div(
                ui.markdown(comparison),
                class_="analysis-box"
            )
        )

    # Tab 8: Risk Acceleration - "Where is the risk accelerating the fastest?"
    @output
    @render.ui
    @reactive.event(input.analyze_acceleration)
    def acceleration_result():
        weather = live_weather_data()
        temp_f = weather["temp_f"]
        humidity = weather["humidity"]

        neighborhoods = data_loader.get_all_neighborhoods()
        results = []

        for _, row in neighborhoods.iterrows():
            risk = calculate_heat_risk(
                temperature=temp_f,
                humidity=humidity,
                elderly_pct=row['elderly_pct'],
                ac_pct=row['ac_pct'],
                poverty_pct=row['poverty_pct'],
                green_space_pct=row['green_space_pct']
            )
            results.append({
                'name': row['name'],
                'zip_code': row['zip_code'],
                'risk_score': risk['risk_score'],
                'risk_level': risk['risk_level']
            })

        # Get acceleration data
        acceleration_data = data_loader.get_risk_acceleration()

        acceleration = ai_client.generate_risk_acceleration(results, acceleration_data)

        return ui.div(
            ui.h4("⚡ 风险加速分析"),
            ui.p(f"基于实时天气: {weather['temp_c']:.1f}°C", style="font-size: 12px; color: #666;"),
            ui.div(
                ui.markdown(acceleration),
                class_="analysis-box"
            )
        )


# Create app
app = App(app_ui, server, debug=False)
