# NYC Heat Wave Early Warning System - 5 Minute Presentation Script

## AI Systems Hackathon 2026
### Presenter: Zian Liu, Cornell University

---

## SLIDE 1: Title (30 seconds)

"Good morning everyone. I'm Zian Liu from Cornell University, and today I'm presenting the **NYC Heat Wave Early Warning System** — an AI-powered dashboard that helps emergency managers make life-saving decisions during extreme heat events."

---

## SLIDE 2: The Problem (1 minute)

"Every summer, heat waves kill more people in the US than any other weather event. In NYC, certain neighborhoods are much more vulnerable than others — especially areas with high elderly populations, low AC coverage, and little green space.

**The challenge**: Emergency managers need to know — in real-time — which neighborhoods are at highest risk, and what actions to take.

**Current problem**: They rely on static data and manual analysis. There's no unified system that combines live weather, demographic vulnerability, and AI-powered recommendations."

---

## SLIDE 3: Our Solution (1 minute)

"Our solution is a **real-time AI-powered dashboard** that:

1. **Calculates risk scores** for all 15 NYC neighborhoods using the NWS Heat Index formula + Heat Vulnerability Index
2. **Displays an interactive map** with color-coded risk levels
3. **Generates AI narratives** — not just numbers, but actionable recommendations
4. **Sends automated email alerts** when neighborhoods exceed risk thresholds
5. **Historical data query** — analyze any date in the past 2 years

The system is built with **Python Shiny** for the frontend and **Ollama Cloud** for AI analysis — no API costs, runs entirely in the cloud."

---

## SLIDE 4: Demo (2 minutes)

"Let me show you how it works.

**[DEMO STEPS]**

1. **Risk Overview Tab**: You see all 15 neighborhoods on an interactive NYC map. Each marker shows a risk score. Red = Critical, Orange = High.

2. **Calendar Feature**: I can select any date — let's pick last July 20th, a real heat wave day. The entire dashboard updates to show that historical data.

3. **AI Analysis Tab**: I select a neighborhood — say, Mott Haven in the Bronx. Click "Generate Report" — and within 30 seconds, AI generates a narrative report in English. It explains WHY this neighborhood is at risk and WHAT officials should do.

4. **Email Alerts Tab**: Officials can set a threshold — say, 65 out of 100. When neighborhoods exceed this, the system can automatically send email alerts to emergency managers."

---

## SLIDE 5: Technical Stack (1 minute)

"How we built it:

| Component | Technology |
|----------|------------|
| Frontend | Python Shiny |
| Risk Model | NWS Heat Index + HVI Framework |
| AI Engine | Ollama Cloud (gemma3:4b) |
| Weather Data | Open-Meteo API (free) |
| Email | SMTP (Gmail) |

**Key innovation**: We use the **Heat Vulnerability Index** from public health research — combining temperature exposure, demographic vulnerability, AC coverage, and green space deficits into a single score.

The AI layer transforms these scores into **narrative recommendations** — explaining the relationships between factors, not just listing numbers."

---

## SLIDE 6: Impact & Future (30 seconds)

"**Impact**: This system can help NYC Emergency Management:
- Identify at-risk neighborhoods in real-time
- Make data-driven decisions faster
- Proactively warn vulnerable communities

**Future plans**:
- Deploy to production with real-time SMS alerts
- Integrate with NYC 311 system
- Add predictive analytics using historical patterns

**We're live today** — the dashboard is running, and all code is open source on GitHub.

Thank you!"

---

## Chinese Version / 中文版演讲稿

---

**开场 (30秒)**

"大家好，我是康奈尔大学的刘子安。今天我介绍的是 **NYC 热浪预警系统** — 一个帮助应急管理人员在极端高温事件中做出救命决策的 AI 驱动仪表盘。"

---

**问题 (1分钟)**

"在美国，热浪每年造成的死亡人数超过任何其他天气事件。在纽约市，某些社区比其他社区更容易受到影响——尤其是老年人口多、空调覆盖率低、绿地少的地区。

**挑战**：应急管理人员需要实时知道哪些社区风险最高，以及应该采取什么行动。

**当前问题**：他们依赖静态数据和手动分析。没有一个统一的系统来结合实时天气、人口脆弱性和 AI 驱动的建议。"

---

**解决方案 (1分钟)**

"我们的解决方案是一个**实时 AI 驱动仪表盘**：

1. **计算风险分数** — 使用 NWS 热指数公式 + 热脆弱性指数为所有 15 个纽约市社区计算风险
2. **显示交互式地图** — 用颜色标记风险等级
3. **生成 AI 叙述** — 不仅是数字，而是可操作的建议
4. **自动发送邮件警报** — 当社区超过风险阈值时
5. **历史数据查询** — 分析过去 2 年中的任何日期

系统使用 **Python Shiny** 构建前端，**Ollama Cloud** 提供 AI 分析 — 无需 API 费用，完全在云端运行。"

---

**演示 (2分钟)**

"[演示步骤]

1. **风险概览标签页**：您可以在交互式纽约市地图上看到所有 15 个社区。每个标记显示风险分数。红色 = 危险，橙色 = 高。

2. **日历功能**：我可以选择任何日期 — 比如去年 7 月 20 日，一个真正的高温天。整个仪表盘会更新显示该历史数据。

3. **AI 分析标签页**：我选择一个社区 — 比如布朗克斯的 Mott Haven。点击“生成报告” — 在 30 秒内，AI 生成英文叙述报告。它解释了这个社区为什么存在风险，以及官员应该采取什么措施。

4. **邮件警报标签页**：官员可以设置阈值 — 比如 65/100。当社区超过此阈值时，系统可以自动向应急管理人员发送电子邮件警报。"

---

**技术栈 (1分钟)**

"我们如何构建：

| 组件 | 技术 |
|------|------|
| 前端 | Python Shiny |
| 风险模型 | NWS 热指数 + HVI 框架 |
| AI 引擎 | Ollama Cloud (gemma3:4b) |
| 天气数据 | Open-Meteo API（免费）|
| 邮件 | SMTP（Gmail）|

**关键创新**：我们使用公共健康研究中的**热脆弱性指数** — 将温度暴露、人口脆弱性、空调覆盖率和绿地不足结合成一个单一分数。

AI 层将这些分数转化为**叙述性建议** — 解释因素之间的关系，而不仅仅是列出数字。"

---

**影响与未来 (30秒)**

"**影响**：该系统可以帮助纽约市应急管理部门：
- 实时识别高风险社区
- 更快地做出数据驱动的决策
- 主动警告弱势社区

**未来计划**：
- 部署到生产环境，增加实时短信警报
- 与 NYC 311 系统集成
- 使用历史模式添加预测分析

**今天已经上线** — 仪表盘正在运行，所有代码在 GitHub 上开源。

谢谢大家！"

---

## Speaking Tips

- **Speak slowly** — 5 minutes is short, but feels long when nervous
- **Make eye contact** with judges during demo
- **Pause for effect** after showing the AI report
- **Point to the screen** when describing features
- **End strong** — "Thank you" with confidence
