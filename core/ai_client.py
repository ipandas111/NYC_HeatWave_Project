"""
AI Client for NYC Heat Wave Risk System
========================================
Supports OpenAI API, Ollama local models, and Ollama Cloud
"""

import os
import json
import requests
from typing import Optional

# Try to import openai, handle if not installed
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class AIClient:
    """Client for generating AI-powered risk analysis"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        provider: str = "ollama",
        ollama_model: str = "qwen2.5:3b",
        ollama_base_url: str = "http://localhost:11434",
        ollama_api_key: Optional[str] = None
    ):
        """
        Initialize AI client

        Args:
            api_key: OpenAI API key (if using OpenAI)
            provider: "openai", "ollama", or "ollama_cloud"
            ollama_model: Model name for Ollama
            ollama_base_url: Base URL for Ollama API (local or cloud)
            ollama_api_key: API key for Ollama Cloud
        """
        self.provider = provider
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        self.ollama_api_key = ollama_api_key
        self.openai_client = None

        # Try to load from config file if not provided
        if api_key is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path) as f:
                        config = json.load(f)
                        provider = config.get("ai_provider", provider)
                        ollama_model = config.get("ollama_model", ollama_model)
                        ollama_base_url = config.get("ollama_base_url", ollama_base_url)
                        ollama_api_key = config.get("ollama_api_key")
                        api_key = config.get("openai_api_key")
                except Exception:
                    pass

        self.provider = provider
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        self.ollama_api_key = ollama_api_key

        # Initialize OpenAI client if using OpenAI
        if provider == "openai" and api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=api_key)

        # Override with environment variables if set
        if os.environ.get("OLLAMA_API_KEY"):
            self.ollama_api_key = os.environ.get("OLLAMA_API_KEY")
        if os.environ.get("OLLAMA_MODEL"):
            self.ollama_model = os.environ.get("OLLAMA_MODEL")
        if os.environ.get("OLLAMA_BASE_URL"):
            self.ollama_base_url = os.environ.get("OLLAMA_BASE_URL")
        if os.environ.get("AI_PROVIDER"):
            self.provider = os.environ.get("AI_PROVIDER")

    def is_available(self) -> bool:
        """Check if AI client is available"""
        if self.provider == "openai":
            return self.openai_client is not None
        elif self.provider in ("ollama", "ollama_cloud"):
            return self._check_ollama()
        return False

    def _check_ollama(self) -> bool:
        """Check if Ollama is running or cloud is accessible"""
        try:
            # Cloud has longer timeout since it's remote
            timeout = 10 if self.provider == "ollama_cloud" else 2
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def _call_ollama(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API (local or cloud)"""
        try:
            url = f"{self.ollama_base_url}/api/chat"
            payload = {
                "model": self.ollama_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"num_predict": max_tokens}
            }

            # Add headers for cloud authentication
            headers = {}
            if self.ollama_api_key:
                headers["Authorization"] = f"Bearer {self.ollama_api_key}"

            # Cloud has longer timeout
            timeout = 180 if self.provider == "ollama_cloud" else 120

            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                print(f"Ollama API error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Ollama error: {e}")
        return None

    def _call_ai(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call AI using configured provider"""
        if self.provider == "openai" and self.openai_client:
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI error: {e}")
        elif self.provider in ("ollama", "ollama_cloud"):
            return self._call_ollama(system_prompt, user_prompt, max_tokens)
        return None

    def generate_analysis(
        self,
        neighborhood_name: str,
        zip_code: str,
        temperature: float,
        humidity: float,
        heat_index: float,
        risk_score: float,
        risk_level: str,
        elderly_pct: float,
        ac_pct: float,
        poverty_pct: float,
        green_space_pct: float,
    ) -> str:
        """
        Generate AI-powered risk analysis for a neighborhood

        Args:
            neighborhood_name: Name of the neighborhood
            zip_code: ZIP code
            temperature: Current temperature in °F
            humidity: Humidity in %
            heat_index: Calculated heat index in °F
            risk_score: Risk score (0-100)
            risk_level: Risk level (低/中/高/极高)
            elderly_pct: Elderly population percentage
            ac_pct: AC coverage percentage
            poverty_pct: Poverty rate
            green_space_pct: Green space coverage

        Returns:
            AI-generated analysis report
        """

        if not self.is_available():
            return self._fallback_analysis(
                neighborhood_name, risk_score, risk_level
            )

        system_prompt = """You are a senior urban heat risk analyst writing for NYC emergency management officials. Write ONLY in English. Never use Chinese.

WRITING STYLE:
- Write in flowing narrative paragraphs, NOT bullet-point lists
- Explain WHY the data matters, don't just restate numbers
- Connect data points to each other: show how factors compound (e.g., "The low AC coverage becomes especially dangerous because the neighborhood also has high elderly population, meaning...")
- Use clear section headings but write prose underneath them
- Be specific and actionable — tell officials exactly what to do, not vague generalities
- Keep it concise: 3-4 short paragraphs total

STRUCTURE:
### Situation Assessment
One paragraph: What is the current risk level and why? Explain the key drivers and how they interact.

### Why This Matters
One paragraph: What makes this neighborhood uniquely vulnerable? Connect the demographic, infrastructure, and environmental factors into a coherent story.

### Recommended Actions
One paragraph: What should emergency managers do in the next 24-48 hours? Be specific about resource deployment.
"""

        user_prompt = f"""
Analyze {neighborhood_name} (ZIP {zip_code}):

Weather: {temperature}F, {humidity}% humidity, heat index {heat_index}F
Vulnerability: {elderly_pct}% elderly, {ac_pct}% AC coverage, {poverty_pct}% poverty, {green_space_pct}% green space
Risk score: {risk_score}/100

Write a concise narrative analysis explaining the relationships between these factors and what they mean for emergency response.
"""

        result = self._call_ai(system_prompt, user_prompt, 400)
        if result:
            return result
        return self._fallback_analysis(neighborhood_name, risk_score, risk_level)

    def generate_citywide_summary(self, neighborhoods_data: list, temperature: float = None, humidity: float = None) -> str:
        """
        Generate citywide heat risk summary

        Args:
            neighborhoods_data: List of neighborhood risk data
            temperature: Current temperature in °F
            humidity: Current humidity in %

        Returns:
            AI-generated citywide summary
        """

        if not self.is_available():
            return "AI 不可用，请查看详细数据。"

        # Count risk levels
        risk_counts = {"极高": 0, "高": 0, "中": 0, "低": 0}
        for n in neighborhoods_data:
            level = n.get("risk_level", "低")
            if level in risk_counts:
                risk_counts[level] += 1

        # Get high risk neighborhoods
        high_risk = [n['name'] for n in neighborhoods_data if n.get('risk_level') == "极高" or n.get('risk_level') == "高"]

        system_prompt = """You are the Chief Risk Analyst for NYC Department of Emergency Management. Write ONLY in English. Never use Chinese.

WRITING STYLE:
- Write an executive briefing in narrative prose, not bullet lists
- Open with the big picture: how many neighborhoods are at risk and what's driving it
- Explain which boroughs are most affected and WHY (connect weather to infrastructure gaps)
- Name the top priority neighborhoods and explain what makes each one dangerous
- Close with 2-3 concrete, specific actions for the next 24 hours
- Keep it to 3-4 paragraphs. Be direct and decisive.
"""

        weather_info = f"\nCurrent Weather: {temperature}F, {humidity}% Humidity" if temperature and humidity else ""

        user_prompt = f"""
NYC citywide heat risk briefing:{weather_info}

Risk distribution: {risk_counts['极高']} critical, {risk_counts['高']} high, {risk_counts['中']} medium, {risk_counts['低']} low risk neighborhoods.
Highest-risk areas: {', '.join(high_risk[:5]) if high_risk else 'None identified'}

Write a concise executive briefing explaining the citywide situation and recommended response.
"""

        result = self._call_ai(system_prompt, user_prompt, 350)
        if result:
            return result
        return "AI summary unavailable. Please review detailed data."

    def generate_risk_trend_analysis(self, neighborhoods_data: list, trend_data: list) -> str:
        """
        Generate AI analysis for risk trends - "Which neighborhoods show rising heat?"

        Args:
            neighborhoods_data: Current neighborhood risk data
            trend_data: Historical trend data

        Returns:
            AI-generated trend analysis
        """

        if not self.is_available():
            return self._fallback_trend_analysis()

        rising_risk = []
        for n in neighborhoods_data:
            if n.get('risk_score', 0) >= 50:
                rising_risk.append(f"{n['name']} (score: {n['risk_score']})")

        system_prompt = """You are a heat risk trend analyst for NYC. Write ONLY in English. Never use Chinese.

Write 2-3 narrative paragraphs explaining:
- Which neighborhoods are trending toward higher risk and WHY
- How demographic and infrastructure factors are compounding over time
- What early warning signs officials should watch for
- Specific preparedness actions to take now before conditions worsen

Do NOT use bullet lists. Write flowing prose that explains the relationships between data points."""

        user_prompt = f"""
Current high-risk neighborhoods: {', '.join(rising_risk) if rising_risk else 'None above 50'}

Explain the risk trajectory and what it means for emergency preparedness.
"""

        result = self._call_ai(system_prompt, user_prompt, 300)
        if result:
            return result
        return self._fallback_trend_analysis()

    def generate_historical_comparison(self, current_data: list, historical_info: dict) -> str:
        """
        Generate AI analysis for historical comparison - "How does today compare to similar historical patterns?"

        Args:
            current_data: Current risk data
            historical_info: Dict with historical_avg and acceleration data

        Returns:
            AI-generated historical comparison
        """

        if not self.is_available():
            return self._fallback_historical_comparison()

        # Calculate current average
        current_avg = sum(n.get('risk_score', 0) for n in current_data) / len(current_data) if current_data else 0
        current_high = len([n for n in current_data if n.get('risk_score', 0) >= 50])

        # Get historical average
        historical_avg = historical_info.get('historical_avg', 0) if isinstance(historical_info, dict) else 0

        # Determine comparison
        if current_avg > historical_avg + 5:
            comparison_text = f"高于历史平均 (当前 {current_avg:.1f} vs 历史 {historical_avg:.1f})"
        elif current_avg < historical_avg - 5:
            comparison_text = f"低于历史平均 (当前 {current_avg:.1f} vs 历史 {historical_avg:.1f})"
        else:
            comparison_text = f"接近历史平均 (当前 {current_avg:.1f} vs 历史 {historical_avg:.1f})"

        system_prompt = """You are a comparative risk analyst for NYC emergency management. Write ONLY in English. Never use Chinese.

Write 2-3 narrative paragraphs that:
- Compare current conditions to the historical baseline and explain what the deviation means
- Explain whether the city is in a normal, elevated, or emergency posture and why
- Describe what this comparison tells us about resource needs and public communication

Write flowing prose, not bullet lists. Connect the numbers to their real-world implications."""

        user_prompt = f"""
Current average risk: {current_avg:.1f}/100. High-risk neighborhoods: {current_high}/15.
Comparison: {comparison_text}

Explain what this means for NYC emergency management operations.
"""

        result = self._call_ai(system_prompt, user_prompt, 250)
        if result:
            return result
        return self._fallback_historical_comparison()

    def generate_risk_acceleration(self, neighborhoods_data: list, acceleration_data: list) -> str:
        """
        Generate AI analysis for risk acceleration - "Where is the risk accelerating the fastest?"

        Args:
            neighborhoods_data: Current risk data
            acceleration_data: List of neighborhoods with risk change from yesterday

        Returns:
            AI-generated risk acceleration analysis
        """

        if not self.is_available():
            return self._fallback_acceleration()

        # Use actual acceleration data
        if acceleration_data and len(acceleration_data) > 0:
            # Get top 5 neighborhoods with highest risk increase
            top_increasing = acceleration_data[:5]
            accelerating = []
            for n in top_increasing:
                name = n.get('name', 'Unknown')
                change = n.get('change', 0)
                score = n.get('risk_score_today', 0)
                accelerating.append(f"{name} (风险分: {score:.1f}, 变化: +{change:.1f})")

            # Get neighborhoods with decreasing risk
            decreasing = [n for n in acceleration_data if n.get('change', 0) < 0]
        else:
            # Fallback to high risk neighborhoods
            accelerating = []
            for n in neighborhoods_data:
                score = n.get('risk_score', 0)
                if score >= 50:
                    accelerating.append(f"{n['name']} (风险分: {score})")
            decreasing = []

        system_prompt = """You are a risk acceleration analyst for NYC emergency management. Write ONLY in English. Never use Chinese.

Write 2-3 narrative paragraphs that:
- Identify which neighborhoods are seeing the fastest risk increase and explain the underlying causes
- Connect the acceleration to specific vulnerability factors (low AC + high poverty creates a feedback loop, etc.)
- Recommend specific, time-sensitive interventions for the fastest-accelerating areas
- Explain what happens if no action is taken in the next 48-72 hours

Write flowing prose, not bullet lists. Explain cause-and-effect relationships."""

        user_prompt = f"""
Fastest-accelerating neighborhoods (vs yesterday):
{', '.join(accelerating) if accelerating else 'No significant acceleration detected'}
"""

        if decreasing:
            user_prompt += f"\nNeighborhoods with declining risk: {len(decreasing)}"

        user_prompt += "\nExplain the acceleration patterns and recommend immediate interventions."

        result = self._call_ai(system_prompt, user_prompt, 300)
        if result:
            return result
        return self._fallback_acceleration()

    def _fallback_analysis(self, name: str, score: float, level: str) -> str:
        """Fallback analysis when AI is not available"""
        if score >= 75:
            action = "urgent attention is needed — deploy cooling resources and check on vulnerable residents immediately"
        elif score >= 50:
            action = "elevated risk — monitor conditions closely and prepare cooling centers"
        else:
            action = "moderate conditions — maintain routine monitoring and ensure cooling infrastructure is operational"
        return f"### {name} — Risk Score: {score}/100 ({level})\n\nAI analysis is currently unavailable. Based on the risk score of {score}, {action}."

    def _fallback_trend_analysis(self) -> str:
        return "AI analysis is currently unavailable. Review neighborhoods with risk scores above 50 and check 7-day trend data for rising patterns. Focus on areas with low AC coverage."

    def _fallback_historical_comparison(self) -> str:
        return "AI analysis is currently unavailable. Compare the current average risk score against the 14-day historical baseline. Look for neighborhoods with unusual spikes."

    def _fallback_acceleration(self) -> str:
        return "AI analysis is currently unavailable. Identify neighborhoods with the highest risk scores and the worst vulnerability indicators (low AC + high poverty + high elderly population)."




# Example usage
if __name__ == "__main__":
    # Test without API key
    client = AIClient()

    if client.is_available():
        print("AI Client: Available")
    else:
        print("AI Client: Not available (no API key)")

    # Test with sample data
    analysis = client.generate_analysis(
        neighborhood_name="Mott Haven",
        zip_code="10451",
        temperature=98,
        humidity=88,
        heat_index=105,
        risk_score=78,
        risk_level="高",
        elderly_pct=18,
        ac_pct=45,
        poverty_pct=32,
        green_space_pct=5
    )

    print("\nSample Analysis:")
    print(analysis)
