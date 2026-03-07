"""
AI Client for NYC Heat Wave Risk System
========================================
Supports both OpenAI API and Ollama local models
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
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        Initialize AI client

        Args:
            api_key: OpenAI API key (if using OpenAI)
            provider: "openai" or "ollama"
            ollama_model: Model name for Ollama
            ollama_base_url: Base URL for Ollama API
        """
        self.provider = provider
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
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
                        api_key = config.get("openai_api_key")
                except Exception:
                    pass

        self.provider = provider
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url

        # Initialize OpenAI client if using OpenAI
        if provider == "openai" and api_key and OPENAI_AVAILABLE:
            self.openai_client = OpenAI(api_key=api_key)

    def is_available(self) -> bool:
        """Check if AI client is available"""
        if self.provider == "openai":
            return self.openai_client is not None
        elif self.provider == "ollama":
            return self._check_ollama()
        return False

    def _check_ollama(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def _call_ollama(self, system_prompt: str, user_prompt: str, max_tokens: int = 500) -> str:
        """Call Ollama API"""
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
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json()["message"]["content"]
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
        elif self.provider == "ollama":
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

        system_prompt = """你是一个专业的城市热浪风险管理专家，为 NYC 应急管理部门提供决策支持。
请用中文回答。

请按以下格式回答（严格按这个格式）：

## 🚨 实时警报
[基于当前风险的紧急程度，用一句话说明现在的情况]

## 📋 立即行动（ Stakeholder 当下要做的事）
- [具体要做什么，谁来做]
- [具体要做什么，谁来做]

## 🏗️ 长期建议（城市规划/基础设施）
- [需要长期规划的事项]
- [需要长期规划的事项]
"""

        user_prompt = f"""
请分析以下 NYC 社区的热浪风险：

社区信息：
- 名称：{neighborhood_name}
- 邮编：{zip_code}

气象数据：
- 温度：{temperature}°F
- 湿度：{humidity}%
- 体感温度 (Heat Index)：{heat_index}°F

脆弱性指标：
- 65岁以上老人比例：{elderly_pct}%
- 空调覆盖率：{ac_pct}%
- 贫困率：{poverty_pct}%
- 绿地覆盖率：{green_space_pct}%

综合风险评估：
- 风险分：{risk_score}/100
- 风险等级：{risk_level}

请给出专业的风险分析和建议。
"""

        result = self._call_ai(system_prompt, user_prompt, 500)
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

        system_prompt = """你是一个 NYC 城市应急管理专家，为应急管理市长办公室提供每日热浪风险报告。
请用中文回答。

请按以下格式回答（严格按这个格式）：

## 🚨 全市实时警报
[一句话概括当前整体风险状态]

## 📋 立即行动
- [具体要做的行动]
- [具体要做的行动]

## 🏗️ 长期规划建议
- [需要长期规划的事项]
"""

        weather_info = f"\n当前天气：温度 {temperature}°F，湿度 {humidity}%" if temperature and humidity else ""

        user_prompt = f"""
今日 NYC 热浪风险概况：
{weather_info}

各风险等级社区数量：
- 极高风险：{risk_counts['极高']} 个
- 高风险：{risk_counts['高']} 个
- 中风险：{risk_counts['中']} 个
- 低风险：{risk_counts['低']} 个

高风险社区：{', '.join(high_risk[:5]) if high_risk else '无'}
"""

        result = self._call_ai(system_prompt, user_prompt, 300)
        if result:
            return result
        return "AI 摘要生成失败，请查看详细数据。"

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

        # Analyze rising risk
        rising_risk = []
        for n in neighborhoods_data:
            risk_score = n.get('risk_score', 0)
            level = n.get('risk_level', '低')
            if risk_score >= 50:
                rising_risk.append(f"{n['name']} (风险分: {risk_score})")

        system_prompt = """你是一个 NYC 城市应急管理专家，分析热浪风险趋势。
请用中文回答。

请按以下格式回答：

## 🚨 趋势警报
[哪些社区风险在上升]

## 📋 立即行动
- [针对上升趋势的紧急行动]

## 🏗️ 长期观察
- [需要持续关注的模式]
"""

        user_prompt = f"""
分析问题：哪些社区的热浪风险在上升？

当前高风险社区：
{', '.join(rising_risk) if rising_risk else '无'}
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

        system_prompt = """你是一个 NYC 城市应急管理专家，分析当前风险与历史模式对比。
请用中文回答。

请按以下格式回答：

## 📊 历史对比结论
[今天 vs 历史平均，简洁说明]

## 📋 含义与行动
[这意味着什么，需要立即做什么]
"""

        user_prompt = f"""
今日风险概况：
- 平均风险分：{current_avg:.1f}/100
- 高风险社区数：{current_high}/15

历史对比：{comparison_text}
"""

        result = self._call_ai(system_prompt, user_prompt, 200)
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

        system_prompt = """你是一个 NYC 城市应急管理专家，分析风险加速最快的社区。
请用中文回答。

请按以下格式回答：

## ⚡ 加速警报
[风险快速上升的社区]

## 📋 紧急优先行动
- [需要立即采取的行动]

## 🏗️ 基础设施改进
- [长期改进建议]
"""

        user_prompt = f"""
分析问题：哪些社区的风险正在加速上升？（对比昨天）

风险上升最快的社区：
{', '.join(accelerating) if accelerating else '无'}
"""

        if decreasing:
            user_prompt += f"\n风险下降的社区：{len(decreasing)} 个"

        user_prompt += "\n请给出分析和建议。"

        result = self._call_ai(system_prompt, user_prompt, 300)
        if result:
            return result
        return self._fallback_acceleration()

    def _fallback_analysis(self, name: str, score: float, level: str) -> str:
        """Fallback analysis when AI is not available"""
        return f"""
{fallback_analysis_template.format(name=name, score=score, level=level)}
"""

    def _fallback_trend_analysis(self) -> str:
        """Fallback for trend analysis"""
        return """⚠️ AI 分析暂时不可用。

趋势分析方法：
1. 查看风险分 > 50 的社区
2. 检查过去7天风险变化
3. 关注空调覆盖率低的社区"""

    def _fallback_historical_comparison(self) -> str:
        """Fallback for historical comparison"""
        return """⚠️ AI 分析暂时不可用。

历史对比方法：
1. 检查当前平均风险分
2. 与过去14天数据对比
3. 关注异常升高的社区"""

    def _fallback_acceleration(self) -> str:
        """Fallback for risk acceleration"""
        return """⚠️ AI 分析暂时不可用。

风险加速分析：
1. 找出风险分最高的社区
2. 检查哪些社区脆弱性指标最差
3. 优先关注：低空调 + 高贫困 + 高老人比例"""


# Fallback template
fallback_analysis_template = """
【{name} 风险分析】

风险等级：{level} ({score}/100)

⚠️ 注意：AI 分析暂时不可用，但基于风险分数：
- 如果分数 >= 75：该社区需要紧急关注
- 如果分数 >= 50：该社区需要保持关注
- 如果分数 < 50：常规监控即可

建议措施：
1. 密切关注高温天气变化
2. 检查降温设施
3. 关注弱势群体
"""


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
