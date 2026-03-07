# Deployment Guide

## Option 1: Render.com (Recommended for Shiny)

### Steps:

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "NYC Heat Wave Early Warning System v1.0"
   git push origin main
   ```

2. **Create Render Account**
   - Go to [render.com](https://render.com) and sign up
   - Connect your GitHub repository

3. **Create New Web Service**
   - Click "New" → "Web Service"
   - Select your repository
   - Configure:
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `shiny run app:app --host 0.0.0.0 --port $PORT`
   - Select "Free" tier

4. **Environment Variables**
   Add these in Render dashboard:
   - `OLLAMA_API_KEY`: your Ollama Cloud API key
   - Or keep local Ollama and use `ai_provider: "ollama"`

### Alternative: Use local Ollama

If you want to use local Ollama instead of Ollama Cloud on Render:
- Set `ai_provider: "ollama"` in config.json
- Note: Render free tier doesn't support running Ollama locally

---

## Option 2: Fly.io

1. Install flyctl: `brew install flyctl`
2. Login: `flyctl auth login`
3. Launch: `flyctl launch`
4. Set environment variables in Fly dashboard
5. Deploy: `flyctl deploy`

---

## Option 3: Run Locally (Development)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run
shiny run app:app --reload
```

Open http://localhost:8000

---

## Configuration

Edit `config.json` for deployment:

```json
{
    "ai_provider": "ollama_cloud",
    "ollama_model": "gemma3:4b",
    "ollama_base_url": "https://api.ollama.com",
    "ollama_api_key": "YOUR_KEY_HERE",
    "alert_recipient": "your-email@example.com"
}
```
