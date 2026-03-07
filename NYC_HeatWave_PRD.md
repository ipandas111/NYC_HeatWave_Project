# NYC 热浪预警系统 - 产品需求文档 (PRD)

**项目名称**：NYC Heat Wave Early Warning System
**选题**：Prompt 3 - NYC Urban Risk（细化版）
**团队**：刘子安团队
**日期**：2026年3月6日

---

## 1. 产品概述

### 1.1 项目背景
NYC 应急管理部门需要在热浪来临前，提前识别高风险社区，合理分配降温资源。热浪是美国最致命的自然灾害之一，有成熟的方法论（CDC HeatRisk 框架）。

### 1.2 产品定位
一个 **AI 驱动的热浪风险预警系统**，帮助 NYC 应急管理部门：
- 实时监控各社区热浪风险
- 识别需要优先关注的社区
- 生成 AI 决策建议报告

### 1.3 Stakeholder（利益相关者）
| 角色 | 需求 |
|------|------|
| **NYC 应急管理部门** | 哪些社区最危险？资源该往哪派？ |
| **公共卫生官员** | 医院容量是否紧张？要不要发预警？ |
| **社区管理者** | 要不要开降温中心？ |

### 1.4 核心价值
- **量化风险**：用公式计算风险分数
- **AI 解读**：GPT 把数据变成人话 + 建议
- **决策支持**：告诉用户具体该怎么做

---

## 2. 功能需求

### 2.1 核心功能列表

| 功能 | 优先级 | 描述 |
|------|--------|------|
| F1: 风险仪表盘 | P0 | 显示各社区热浪风险等级 |
| F2: 风险分计算 | P0 | 用公式计算综合风险分 |
| F3: AI 风险分析 | P0 | AI 生成分析报告 + 建议 |
| F4: 趋势分析 | P1 | 显示过去7天风险变化 |
| F5: 预警提醒 | P1 | 高风险社区自动高亮 |
| F6: 全市摘要 | P1 | AI 生成每日风险报告 |

### 2.2 详细功能说明

#### F1: 风险仪表盘
- 表格显示所有社区
- 颜色编码：绿色(0-40)、黄色(41-70)、红色(71-100)
- 显示关键指标：温度、医院容量、老人比例、空调覆盖率

#### F2: 风险分计算（核心 "模型" - 基于 NWS Heat Index + HVI 框架）

本系统采用**国际公认**的热浪风险评估框架：
- **NWS Heat Index**：美国国家气象局官方体感温度公式
- **HVI (Heat Vulnerability Index)**：学术研究公认的热脆弱性指数框架

```python
def calculate_heat_risk(
    temperature: float,      # 温度 (°F)
    humidity: float,         # 湿度 (%)
    elderly_pct: float,    # 65岁以上老人 (%)
    ac_pct: float,         # 空调覆盖率 (%)
    poverty_pct: float,    # 贫困率 (%)
    green_space_pct: float  # 绿地覆盖率 (%)
) -> dict:
    """
    基于 NWS Heat Index + HVI 框架的综合热浪风险评估

    1. Heat Index 公式 (NWS官方)
    2. HVI 框架权重分配
    """

    # ======== 1. 计算 Heat Index (NWS官方公式) ========
    HI = (-42.379 +
           2.04901523 * temperature +
           10.14333127 * humidity -
           0.22475541 * temperature * humidity -
           0.00683783 * temperature**2 -
           0.05481717 * humidity**2 +
           0.00122874 * temperature**2 * humidity +
           0.00085282 * temperature * humidity**2 -
           0.00000199 * temperature**2 * humidity**2)

    # ======== 2. HVI 框架风险得分 ========

    # 温度/体感风险 (30分) - 基于NWS风险等级
    if HI >= 130:
        temp_score = 30
    elif HI >= 105:
        temp_score = 20 + (HI - 105) / 25 * 10
    elif HI >= 90:
        temp_score = 10 + (HI - 90) / 15 * 10
    else:
        temp_score = max(0, HI / 90 * 10)

    # 人口脆弱性 (30分) - 老人+贫困
    pop_score = (elderly_pct * 0.6 + poverty_pct * 0.4) * 0.3

    # 空调缺失 (20分)
    ac_score = (100 - ac_pct) * 0.20

    # 环境脆弱性 (20分) - 绿地
    green_score = (100 - green_space_pct) * 0.20

    total = temp_score + pop_score + ac_score + green_score

    # 风险等级
    if total >= 75:
        level, color = "极高", "🔴"
    elif total >= 50:
        level, color = "高", "🟠"
    elif total >= 25:
        level, color = "中", "🟡"
    else:
        level, color = "低", "🟢"

    return {
        "risk_score": round(total, 1),
        "risk_level": level,
        "color": color,
        "heat_index": round(HI, 1),
        "breakdown": {
            "temperature": round(temp_score, 1),
            "population": round(pop_score, 1),
            "ac_coverage": round(ac_score, 1),
            "environment": round(green_score, 1)
        }
    }
```

**参考来源**：
- NWS Heat Index: https://en.wikipedia.org/wiki/Heat_index
- Heat Vulnerability Index: 学术研究标准框架

**风险等级划分**：
| 风险分 | 等级 | 颜色 | 含义 |
|--------|------|------|------|
| 0-40 | 低 | 🟢 | 正常 |
| 41-70 | 中 | 🟡 | 关注 |
| 71-85 | 高 | 🟠 | 预警 |
| 86-100 | 极高 | 🔴 | 紧急 |

#### F3: AI 风险分析（核心 AI 功能）
```
输入：社区数据 + 风险分
输出：人类可读的分析报告
```

**AI Prompt**：
```
你是一个热浪风险管理专家。请分析以下 NYC 社区的热浪风险：

社区信息：
- 名称：{name}
- 今日温度：{temperature}°F
- 医院容量：{hospital_cap}%
- 65岁以上老人：{elderly_pct}%
- 有空调家庭：{ac_pct}%
- 计算风险分：{risk_score}/100

请按以下格式回答：
1. 风险等级（低/中/高/极高）及原因
2. 主要风险因素（2-3点）
3. 建议措施（2-3点）
```

**AI 返回示例**：
```
风险等级：极高 🔴

主要原因：
1. 温度极高（95°F），连续3天超过90°F
2. 医院容量已达92%，接近饱和
3. 仅45%家庭有空调，弱势群体暴露风险高
4. 18%为65岁以上老人，属于高风险群体

建议措施：
1. ⚠️ 立即对该社区发布高温预警
2. 🚑 准备热相关疾病应急床位
3. 👵 优先检查独居老人
4. 🏠 开放降温中心
```

#### F4: 趋势分析
- 折线图显示各社区过去7天风险分变化

#### F5: 预警提醒
- 默认阈值：75
- 超过阈值自动高亮

#### F6: 全市摘要
- AI 自动生成全市风险报告
- 包含：高风险社区列表、整体评估、建议

---

## 3. AI 接入方案

### 3.1 整体架构

```
用户浏览器 (Shiny App)
        ↓
   FastAPI (后端)
        ↓
┌───────┴───────┐
   Supabase     OpenAI API
  (数据库)       (GPT-4o-mini)
        ↓
  Python 风险公式计算
```

### 3.2 AI 调用流程

```python
# 1. 用户选择社区或点击"分析"
# 2. 后端获取该社区数据
neighborhood = get_neighborhood_data(zip_code)

# 3. 用公式计算风险分（你的"模型"）
risk_score = calculate_heat_risk(
    temp=neighborhood['temperature'],
    hospital_cap=neighborhood['hospital_capacity'],
    elderly_pct=neighborhood['elderly_pct'],
    ac_pct=neighborhood['ac_pct']
)

# 4. 构建 AI prompt
prompt = f"""
你是一个热浪风险管理专家。请分析以下 NYC 社区的热浪风险：

社区信息：
- 名称：{neighborhood['name']}
- 邮编：{neighborhood['zip_code']}
- 今日温度：{neighborhood['temperature']}°F
- 医院容量：{neighborhood['hospital_capacity']}%
- 65岁以上老人：{neighborhood['elderly_pct']}%
- 有空调家庭：{neighborhood['ac_pct']}%

计算风险分：{risk_score}/100

请按以下格式回答：
1. 风险等级（低/中/高/极高）
2. 主要风险因素（2-3点）
3. 建议措施（2-3点）
"""

# 5. 调用 OpenAI API
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "你是一个专业的城市热浪风险管理专家，擅长分析热浪风险并给出决策建议。"},
        {"role": "user", "content": prompt}
    ]
)

ai_report = response.choices[0].message.content

# 6. 返回给前端
return {
    "neighborhood": neighborhood,
    "risk_score": risk_score,
    "ai_report": ai_report
}
```

### 3.3 AI Prompt 库

#### 场景 1：单个社区分析
```python
SYSTEM_PROMPT = """你是一个城市热浪风险管理专家，擅长分析热浪风险并给出决策建议。
请根据数据进行分析，用清晰的结构化格式回答。"""

USER_PROMPT = """
社区：{name}
温度：{temperature}°F
医院容量：{hospital_capacity}%
65岁以上老人：{elderly_pct}%
有空调家庭：{ac_pct}%
风险分：{risk_score}/100
"""
```

#### 场景 2：全市摘要
```python
USER_PROMPT = """
今日 NYC 热浪风险概况：
- 总社区数：{total}
- 极高风险社区：{critical_count}
- 高风险社区：{high_count}
- 中风险社区：{medium_count}
- 低风险社区：{low_count}

前3个最危险社区：
{top_3_dangerous}

请生成一份简短的每日风险摘要：
1. 整体风险评估
2. 需要重点关注的社区
3. 建议采取的预防措施
"""
```

### 3.4 API 配置

```python
# config.py
import os
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key")
MODEL = "gpt-4o-mini"  # 便宜、快速

client = OpenAI(api_key=OPENAI_API_KEY)
```

---

## 4. 数据设计

### 4.1 数据库表结构

#### 表 1: neighborhoods（社区表）
```sql
CREATE TABLE neighborhoods (
    zip_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    population INTEGER NOT NULL,
    borough VARCHAR(50),
    elderly_pct DECIMAL(5,2),  -- 65岁以上人口比例
    ac_pct DECIMAL(5,2),        -- 有空调家庭比例
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8)
);
```

#### 表 2: daily_heat_data（每日热浪数据）
```sql
CREATE TABLE daily_heat_data (
    id SERIAL PRIMARY KEY,
    zip_code VARCHAR(10) REFERENCES neighborhoods(zip_code),
    date DATE NOT NULL,
    temperature DECIMAL(5,2),           -- 温度（华氏度）
    heat_index DECIMAL(5,2),            -- 体感温度
    hospital_capacity_pct DECIMAL(5,2), -- 医院容量百分比
    risk_score DECIMAL(5,2),            -- 计算出的风险分
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(zip_code, date)
);
```

### 4.2 风险计算公式

```
风险分 = 温度得分 + 医院得分 + 老人得分 + 空调惩罚

其中：
- 温度得分 = max(0, (温度 - 70) / 30 × 30)  -- 70°F开始计分，最高30分
- 医院得分 = 医院容量% × 0.3                  -- 最高30分
- 老人得分 = 65岁以上人口% × 1.5              -- 20%=30分
- 空调惩罚 = (100 - 空调覆盖率) × 0.1         -- 最高10分

总分上限：100分
```

### 4.3 测试数据

**neighborhoods.csv（15个 NYC 社区）**
```csv
zip_code,name,population,borough,elderly_pct,ac_pct,latitude,longitude
10001,Chelsea,52000,Manhattan,14,82,40.7484,-74.0018
10002,Lower East Side,78000,Manhattan,16,75,40.7150,-73.9843
10004,Battery Park,18000,Manhattan,12,88,40.7033,-74.0170
10005,Financial District,35000,Manhattan,10,90,40.7061,-74.0087
11201,Downtown Brooklyn,55000,Brooklyn,13,78,40.6930,-73.9899
11211,Williamsburg,85000,Brooklyn,8,72,40.7081,-73.9571
11206,Bushwick,42000,Brooklyn,11,65,40.7050,-73.9213
10301,Stapleton,45000,Staten Island,18,70,40.6362,-74.0789
10314,New Springville,78000,Staten Island,20,68,40.5886,-74.1471
11375,Forest Hills,55000,Queens,22,75,40.7213,-73.8444
11354,Flushing,65000,Queens,19,78,40.7677,-73.8330
10451,Mott Haven,38000,Bronx,18,45,40.8180,-73.9276
10461,Parkchester,32000,Bronx,15,68,40.8333,-73.8607
10453,University Heights,28000,Bronx,12,55,40.8583,-73.9108
10467,Riverdale,42000,Bronx,25,72,40.8876,-73.9143
```

**daily_heat_data.csv（15社区 × 14天 = 210条）**

示例数据（2026-03-06）：
```csv
zip_code,date,temperature,heat_index,hospital_capacity_pct,risk_score
10001,2026-03-06,88,92,65,36.4
10002,2026-03-06,90,95,75,42.0
10451,2026-03-06,98,105,92,72.6
11206,2026-03-06,95,100,88,63.5
```

---

## 5. 界面设计

### 5.1 页面结构

```
┌─────────────────────────────────────────────┐
│         NYC 热浪预警系统                      │
├─────────────────────────────────────────────┤
│ [风险地图] [趋势分析] [AI 分析] [预警设置]   │
├─────────────────────────────────────────────┤
│                                             │
│  内容区                                      │
│                                             │
└─────────────────────────────────────────────┘
```

### 5.2 页面 1：风险地图（首页）
- 表格显示所有社区
- 列：社区名、邮编、温度、医院容量%、风险分、等级
- 颜色编码：绿/黄/橙/红
- 点击任意行进入详情

### 5.3 页面 2：趋势分析
- 选择社区（下拉多选）
- 折线图显示过去7天风险趋势

### 5.4 页面 3：AI 分析（核心）
- 选择社区或生成全市摘要
- 显示：
  - 社区基本信息
  - 风险分 + 等级
  - **AI 分析报告**（风险等级、原因、建议）

### 5.5 页面 4：预警设置
- 滑块设置阈值（默认75）
- 高亮超过阈值的社区

---

## 6. 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Shiny (Python) | Dashboard 界面 |
| 后端 | FastAPI | REST API |
| 数据库 | Supabase | PostgreSQL |
| AI | OpenAI API | GPT-4o-mini |
| 部署 | Posit Connect | （主办方提供） |

---

## 7. 交付清单

| 交付物 | 说明 |
|--------|------|
| ✅ Shiny Dashboard | 可运行的 Web 应用 |
| ✅ FastAPI 后端 | 提供 API 接口 |
| ✅ Supabase 数据库 | 存储数据 |
| ✅ 2个 CSV 测试数据 | neighborhoods, daily_heat_data |
| ✅ 风险计算公式 | Python 函数（你的"模型"） |
| ✅ AI 集成 | OpenAI API 调用 |
| ✅ README 文档 | 使用说明 |
| ✅ Codebook | 数据字段说明 |
| ✅ GitHub 仓库 | 公开代码 |

---

## 8. 时间计划

| 时间 | 任务 |
|------|------|
| 3:30-4:00 | 参加介绍会议，确认选题 |
| 4:00-5:00 | 确认分工，准备数据 |
| 5:00-6:30 | 搭建基础架构，注册 Supabase |
| 6:30-8:00 | 导入测试数据 |
| 8:00-10:00 | 开发核心功能：公式 + API + AI |
| 10:00-12:00 | 开发 Dashboard |
| 12:00-7:00 | 休息 |
| 7:00-9:00 | 调试，优化 |
| 9:00-1:00 | 完善文档 |
| 1:00-2:00 | 推送到 GitHub |
| 2:00-2:30 | 准备演示 |

---

## 9. 评分要点

| 评分项 | 分值 | 关键点 |
|--------|------|--------|
| 工具实现 | 25 | 能运行，部署成功 |
| AI 集成 | 25 | AI 分析有实际意义，给出有用建议 |
| 匹配提示 | 5 | 紧扣城市风险主题 |
| 测试数据 | 20 | 2-3个数据集，能演示 |
| 文档 | 10 | README + Codebook |
| GitHub | 5 | 公开仓库，可复现 |

---

## 10. 核心概念说明

| 概念 | 说明 |
|------|------|
| **风险公式** | 你定义的加权计算公式，这就是你的"模型"，不需要机器学习 |
| **Prompt 工程** | 写指令让 AI 做什么，不需要训练/微调 |
| **AI 分析** | AI 读取公式计算的风险分，生成人类可读的分析报告 |

---

## 11. 注意事项

1. **风险公式 = 你的"模型"**：不需要训练，直接用加权公式计算
2. **AI = 解释器**：把数字变成人话，给出建议
3. **数据要合理**：高温 + 低空调覆盖率 = 高风险
4. **演示要流畅**：提前演练，确保能跑通

---

## 12. 数据来源说明

### 12.1 当前数据（合成数据）
当前系统使用**合成数据**进行演示，数据存储在：
- `neighborhoods.csv` - 15个NYC社区的基础信息
- `daily_heat_data.csv` - 14天的热浪模拟数据

### 12.2 真实数据来源

如需接入真实数据，可使用以下数据源：

| 数据类型 | 数据源 | API/URL |
|----------|--------|---------|
| 实时天气 | **Open-Meteo** (免费) | https://api.open-meteo.com/v1/forecast |
| 气象历史数据 | **NOAA** | https://www.ncdc.noaa.gov/cdo-web/datasets |
| 人口统计 | **US Census Bureau** | https://api.census.gov/ |
| 绿地覆盖 | **NYC Open Data** - Street Tree Census | https://data.cityofnewyork.us/resource/5rq2-4hqu.json |
| 社区统计 | **NYC Open Data** | https://data.cityofnewyork.us/resource/hhdx-uv46.json |
| 空气质量 | **NYC Open Data** | https://data.cityofnewyork.us/resource/ia6d-86ji.json |

### 12.3 真实数据集成

系统已集成 `core/real_data_loader.py`，支持：
- Open-Meteo 免费天气 API（无需注册）
- NYC Open Data Socrata API
- US Census Bureau API

示例代码：
```python
from core.real_data_loader import fetch_live_weather
weather = fetch_live_weather()
print(f"当前温度: {weather['temperature']}°C")
```

---

**文档版本**：v2.1（添加真实数据源）
**最后更新**：2026-03-06
