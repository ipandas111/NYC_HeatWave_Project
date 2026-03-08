# NYC 热浪预警系统

<p align="center">
  <img src="https://img.shields.io/badge/AI-Systems-Hackathon%202026-blue" alt="AI Systems Hackathon 2026">
  <img src="https://img.shields.io/badge/Python-Shiny-orange" alt="Python Shiny">
  <img src="https://img.shields.io/badge/AI-Ollama%20Cloud-green" alt="Ollama Cloud">
</p>

一款由人工智能驱动的热浪风险监控仪表板，专为纽约市应急管理部门设计。入选 **AI Systems Hackathon 2026** 决赛。

---

## 项目简介

NYC 热浪预警系统是一个实时仪表板，帮助应急管理人员在极端高温事件中识别高风险社区。系统整合了：

- **NWS 体感温度指数** + **热脆弱性指数 (HVI)** 风险评分
- **交互式纽约市地图**，按风险等级着色
- **AI 驱动的风险分析报告**，解释风险因素并提供建议
- **邮件自动告警**，当风险超阈值时通知官员
- **历史数据查询**，可查看过去 2 年任意日期的风险数据

---

## 在线演示

访问实时演示: https://nyc-heatwave-project.onrender.com

---

## 风险评分体系

系统根据以下因素计算 0-100 的风险分数：

| 因素 | 权重 | 说明 |
|------|------|------|
| 温度 / 体感温度 | 30 分 | NWS 官方公式计算 |
| 人口脆弱性 | 30 分 | 老年人口 + 贫困率 |
| 空调覆盖率差距 | 20 分 | 空调覆盖率越低，风险越高 |
| 绿地缺失 | 20 分 | 绿地覆盖率越低，风险越高 |

**风险等级：**
- 🔴 极高 (75-100)：需立即采取行动
- 🟠 高 (50-74)：需密切监控
- 🟡 中 (25-49)：保持警惕
- 🟢 低 (0-24)：正常运营

---

## 核心功能

### 1. 风险地图
交互式 NYC 地图展示全市 15 个社区的实时风险分数。点击任意标记可查看详细脆弱性数据。

### 2. 日历查询
选择过去 2 年内的任意日期，查看历史热浪风险数据。非常适合分析过去事件和模式。

### 3. 社区详情
深入了解各社区的风险档案，查看分数明细。

### 4. AI 分析
生成叙事性风险报告，包含可操作建议。AI 解释**为什么**某个社区存在风险，以及官员**应该做什么**。

### 5. 趋势与历史
14 天历史趋势，搭配 AI 驱动的风险加速洞察和对比分析。

### 6. 市摘要
AI 生成面向决策者的执行简报。

### 7. 邮件告警
当社区风险超过可配置阈值时，自动发送邮件通知。

---

## 快速开始

### 本地开发

```bash
# 克隆仓库
git clone https://github.com/ipandas111/NYC_HeatWave_Project.git
cd NYC_HeatWave_Project

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# 安装依赖
pip install -r requirements.txt

# 运行仪表板
shiny run app:app --reload
```

在浏览器中打开 http://localhost:8000

---

## 配置说明

### AI 提供商

系统支持三种 AI 后端：

#### 方式 1：Ollama Cloud（推荐）
```json
{
  "ai_provider": "ollama_cloud",
  "ollama_model": "gemma3:4b",
  "ollama_base_url": "https://api.ollama.com",
  "ollama_api_key": "your-ollama-cloud-api-key"
}
```

#### 方式 2：本地 Ollama
```bash
# 安装 Ollama
ollama pull gemma3:4b
ollama serve
```

```json
{
  "ai_provider": "ollama",
  "ollama_model": "gemma3:4b",
  "ollama_base_url": "http://localhost:11434"
}
```

#### 方式 3：OpenAI API
```json
{
  "ai_provider": "openai",
  "openai_api_key": "sk-your-key-here"
}
```

### 邮件告警（可选）

配置 SMTP 以接收自动邮件告警：

```json
{
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "alert_recipient": "official@nyc.gov",
  "alert_threshold": 65
}
```

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 前端 | Python Shiny |
| 风险模型 | NWS 体感温度 + HVI 框架 |
| AI 引擎 | Ollama Cloud (gemma3:4b) |
| 天气数据 | Open-Meteo API（免费） |
| 邮件告警 | SMTP |
| 数据库 | CSV / Supabase（可选） |

---

## 项目结构

```
NYC_HeatWave_Project/
├── app.py                  # 主 Shiny 仪表板
├── config.json             # 配置文件
├── requirements.txt        # Python 依赖
├── README.md               # 本文件
├── neighborhoods.csv       # 15 个 NYC 社区数据
├── daily_heat_data.csv     # 14 天历史数据
└── core/
    ├── risk_formula.py     # NWS 体感温度 + HVI
    ├── ai_client.py        # AI 分析（Ollama/OpenAI）
    ├── data_loader.py      # CSV 数据管理
    ├── real_data_loader.py # 天气 API
    └── email_alert.py      # 自动告警
```

---

## 部署

详细部署说明请参阅 [DEPLOY.md](DEPLOY.md)

**快速部署到 Render.com：**
1. 推送到 GitHub
2. 在 render.com 创建新的 Web Service
3. 设置 Build Command: `pip install -r requirements.txt`
4. 设置 Start Command: `shiny run app:app --host 0.0.0.0 --port $PORT`
5. 添加环境变量

---

## AI 报告示例

```
### 情况评估

布朗克斯的 Mott Haven 呈现较高的热风险，其特点是环境因素和人口因素叠加。当前体感温度为 98°F，湿度达 88%，为居民创造了危险条件...

### 为什么这很重要

该社区全市空调覆盖率最低，仅 45%，同时 65 岁以上老年人口占 18%。当体感温度飙升时，这些因素会产生倍增效应，显著增加热相关疾病风险...

### 建议行动

应急管理人员应该：
1. 立即开放避暑中心
2. 派遣健康检查团队探访老年居民
3. 与公用事业公司协调空调援助项目...
```

---

## 数据来源

- **天气**: Open-Meteo API（实时 + 历史）
- **人口统计**: NYC Open Data / 美国人口普查
- **脆弱性**: 热脆弱性指数 (HVI) 框架

---

## 许可证

MIT License

---

## 作者

**刘子安 (Zian Liu)** - 康奈尔大学
- 邮箱: zl2268@cornell.edu
- GitHub: [@ipandas111](https://github.com/ipandas111)

为 **AI Systems Hackathon 2026** 构建
