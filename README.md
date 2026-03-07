# NYC Heat Wave Early Warning System

<p align="center">
  <img src="https://img.shields.io/badge/AI-Systems-Hackathon%202026-blue" alt="AI Systems Hackathon 2026">
  <img src="https://img.shields.io/badge/Python-Shiny-orange" alt="Python Shiny">
  <img src="https://img.shields.io/badge/AI-Ollama%20Cloud-green" alt="Ollama Cloud">
</p>

An AI-powered heat wave risk monitoring dashboard for NYC Emergency Management. Built for **AI Systems Hackathon 2026**.

---

## Overview

NYC Heat Wave Early Warning System is a real-time dashboard that helps emergency managers identify at-risk neighborhoods during extreme heat events. It combines:

- **NWS Heat Index** + **Heat Vulnerability Index (HVI)** for risk scoring
- **Interactive NYC Map** with color-coded risk levels
- **AI-Powered Narrative Reports** explaining risk factors
- **Automated Email Alerts** when thresholds are exceeded
- **Historical Data Query** for any date in the past 2 years

---

## Live Demo

The system calculates risk scores (0-100) based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| Temperature / Heat Index | 30 pts | NWS official formula |
| Population Vulnerability | 30 pts | Elderly + Poverty rates |
| AC Coverage Gap | 20 pts | Low AC = higher risk |
| Green Space Deficit | 20 pts | Low green space = higher risk |

**Risk Levels:**
- 🔴 Critical (75-100): Immediate action required
- 🟠 High (50-74): Close monitoring needed
- 🟡 Medium (25-49): Stay vigilant
- 🟢 Low (0-24): Normal operations

---

## Features

### 1. Risk Overview
Interactive NYC map showing all 15 neighborhoods with real-time risk scores. Click any marker for detailed vulnerability data.

### 2. Calendar Query
Select any date within the past 2 years to view historical heat risk data. Perfect for analyzing past events and patterns.

### 3. Neighborhood Detail
Deep dive into individual community risk profiles with score breakdowns.

### 4. AI Analysis
Generate narrative risk reports with actionable recommendations. AI explains **why** a neighborhood is at risk and **what** officials should do.

### 5. Trends & History
14-day historical trends with AI-powered insights on risk acceleration and comparisons.

### 6. Citywide Summary
AI-generated executive briefing for decision-makers.

### 7. Email Alerts
Automated email notifications when neighborhoods exceed configurable risk thresholds.

---

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/ipandas111/NYC_HeatWave_Project.git
cd NYC_HeatWave_Project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
shiny run app:app --reload
```

Open http://localhost:8000 in your browser.

---

## Configuration

### AI Providers

The system supports three AI backends:

#### Option 1: Ollama Cloud (Recommended)
```json
{
  "ai_provider": "ollama_cloud",
  "ollama_model": "gemma3:4b",
  "ollama_base_url": "https://api.ollama.com",
  "ollama_api_key": "your-ollama-cloud-api-key"
}
```

#### Option 2: Ollama (Local)
```bash
# Install Ollama from https://ollama.ai
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

#### Option 3: OpenAI API
```json
{
  "ai_provider": "openai",
  "openai_api_key": "sk-your-key-here"
}
```

### Email Alerts (Optional)

For automated email alerts, configure SMTP:

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

## Tech Stack

| Component | Technology |
|----------|------------|
| Frontend | Python Shiny |
| Risk Model | NWS Heat Index + HVI Framework |
| AI Engine | Ollama Cloud (gemma3:4b) |
| Weather Data | Open-Meteo API (free) |
| Email Alerts | SMTP |
| Database | CSV / Supabase (optional) |

---

## Project Structure

```
NYC_HeatWave_Project/
├── app.py                  # Main Shiny dashboard
├── config.json             # Configuration
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── PRESENTATION.md         # 5-minute presentation script
├── DEPLOY.md               # Deployment guide
├── neighborhoods.csv       # 15 NYC neighborhoods data
├── daily_heat_data.csv     # 14-day historical data
└── core/
    ├── risk_formula.py     # NWS Heat Index + HVI
    ├── ai_client.py        # AI analysis (Ollama/OpenAI)
    ├── data_loader.py     # CSV data management
    ├── real_data_loader.py # Weather API
    └── email_alert.py     # Automated alerts
```

---

## Deployment

See [DEPLOY.md](DEPLOY.md) for detailed deployment instructions to Render.com or other platforms.

**Quick Deploy to Render.com:**
1. Push to GitHub
2. Create new "Web Service" on render.com
3. Set Build Command: `pip install -r requirements.txt`
4. Set Start Command: `shiny run app:app --host 0.0.0.0 --port $PORT`
5. Add environment variables

---

## Sample AI Report

```
### Situation Assessment

Mott Haven in the Bronx presents an elevated heat risk profile driven by compounding environmental and demographic factors. The current heat index of 98F, combined with 88% humidity, creates dangerous conditions for residents...

### Why This Matters

This neighborhood has one of the lowest AC coverage rates in the city at 45%, paired with an elderly population of 18%. When heat index spikes, these factors create a multiplier effect that significantly increases heat-related illness risk...

### Recommended Actions

Emergency managers should: 1) Open cooling centers immediately, 2) Deploy wellness check teams to elderly residents, 3) Coordinate with utility companies for AC assistance programs...
```

---

## Data Sources

- **Weather**: Open-Meteo API (real-time + historical)
- **Demographics**: NYC Open Data / US Census
- **Vulnerability**: Heat Vulnerability Index (HVI) framework

---

## License

MIT License

---

## Author

**Zian Liu** - Cornell University
- Email: zl2268@cornell.edu
- GitHub: [@ipandas111](https://github.com/ipandas111)

Built for **AI Systems Hackathon 2026**
