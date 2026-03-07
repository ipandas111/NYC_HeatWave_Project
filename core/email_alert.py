"""
Email Alert System for NYC Heat Wave Risk
==========================================
Sends automatic email alerts to officials when risk thresholds are exceeded.
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, date
from typing import List, Dict, Optional


class EmailAlertSystem:
    """Manages heat wave risk email alerts for government officials"""

    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.smtp_host = self.config.get("smtp_host", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.sender_email = self.config.get("sender_email", "")
        self.sender_password = self.config.get("sender_password", "")
        self.recipient_email = self.config.get("alert_recipient", "zl2268@cornell.edu")
        self.risk_threshold = self.config.get("alert_threshold", 65)
        self.enabled = self.config.get("alerts_enabled", True)

        # Track sent alerts to avoid duplicates (date -> set of neighborhoods)
        self._sent_today: Dict[str, set] = {}

    def _load_config(self, config_path: str = None) -> dict:
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        try:
            with open(config_path) as f:
                return json.load(f)
        except Exception:
            return {}

    def is_configured(self) -> bool:
        """Check if SMTP credentials are configured"""
        return bool(self.sender_email and self.sender_password)

    def _already_sent(self, neighborhood: str) -> bool:
        """Check if alert was already sent today for this neighborhood"""
        today = str(date.today())
        if today not in self._sent_today:
            self._sent_today = {today: set()}
        return neighborhood in self._sent_today[today]

    def _mark_sent(self, neighborhood: str):
        today = str(date.today())
        if today not in self._sent_today:
            self._sent_today = {today: set()}
        self._sent_today[today].add(neighborhood)

    def build_alert_html(self, alerts: List[Dict], weather_info: str = "") -> str:
        """Build HTML email body for risk alerts"""
        now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

        rows = ""
        for a in alerts:
            level = a.get("level_en", "HIGH")
            score = a.get("risk_score", 0)
            if score >= 75:
                color = "#C62828"
            elif score >= 50:
                color = "#E65100"
            else:
                color = "#F9A825"

            rows += f"""
            <tr>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;font-weight:600;">{a['name']}</td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;">{a.get('borough', '')}</td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;text-align:center;">
                    <span style="background:{color};color:white;padding:4px 12px;border-radius:4px;font-weight:700;font-size:14px;">{score}</span>
                </td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;text-align:center;font-weight:600;color:{color};">{level}</td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;">{a.get('heat_index', 'N/A')}F</td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;">{a.get('elderly_pct', '')}%</td>
                <td style="padding:12px 16px;border-bottom:1px solid #eee;">{a.get('ac_pct', '')}%</td>
            </tr>"""

        html = f"""
        <html>
        <body style="font-family:'Segoe UI',Arial,sans-serif;color:#1a1a1a;max-width:800px;margin:0 auto;padding:20px;">
            <div style="border-bottom:3px solid #CD4900;padding-bottom:16px;margin-bottom:24px;">
                <h1 style="color:#CD4900;margin:0;font-size:24px;">NYC Heat Wave Risk Alert</h1>
                <p style="color:#666;margin:4px 0 0;font-size:14px;">{now}</p>
            </div>

            <div style="background:#FFF3E0;border-left:4px solid #CD4900;padding:16px 20px;border-radius:0 6px 6px 0;margin-bottom:24px;">
                <strong style="color:#CD4900;">ALERT:</strong>
                <strong>{len(alerts)} neighborhood(s)</strong> have exceeded the risk threshold of {self.risk_threshold}/100.
                Immediate review and action may be required.
            </div>

            {f'<p style="color:#666;font-size:14px;margin-bottom:20px;">{weather_info}</p>' if weather_info else ''}

            <table style="width:100%;border-collapse:collapse;font-size:14px;border:1px solid #eee;border-radius:6px;">
                <thead>
                    <tr style="background:#f5f5f5;">
                        <th style="padding:12px 16px;text-align:left;font-weight:600;border-bottom:2px solid #ddd;">Neighborhood</th>
                        <th style="padding:12px 16px;text-align:left;font-weight:600;border-bottom:2px solid #ddd;">Borough</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;border-bottom:2px solid #ddd;">Risk Score</th>
                        <th style="padding:12px 16px;text-align:center;font-weight:600;border-bottom:2px solid #ddd;">Level</th>
                        <th style="padding:12px 16px;text-align:left;font-weight:600;border-bottom:2px solid #ddd;">Heat Index</th>
                        <th style="padding:12px 16px;text-align:left;font-weight:600;border-bottom:2px solid #ddd;">Elderly %</th>
                        <th style="padding:12px 16px;text-align:left;font-weight:600;border-bottom:2px solid #ddd;">AC %</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>

            <div style="margin-top:24px;padding:16px 20px;background:#f5f5f5;border-radius:6px;">
                <h3 style="margin:0 0 8px;font-size:15px;color:#1a1a1a;">Recommended Actions</h3>
                <ul style="margin:0;padding-left:20px;color:#444;font-size:14px;line-height:1.8;">
                    <li>Activate cooling centers in affected neighborhoods</li>
                    <li>Deploy wellness check teams to areas with high elderly population</li>
                    <li>Coordinate with utility companies for AC assistance programs</li>
                    <li>Issue public heat safety advisories for flagged boroughs</li>
                </ul>
            </div>

            <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
            <p style="color:#999;font-size:12px;margin:0;">
                NYC Heat Wave Early Warning System | AI Systems Hackathon 2026<br>
                This is an automated alert. Review full dashboard at http://localhost:8000
            </p>
        </body>
        </html>
        """
        return html

    def send_alert(self, alerts: List[Dict], weather_info: str = "") -> Dict:
        """
        Send email alert for high-risk neighborhoods.

        Args:
            alerts: List of neighborhood dicts that exceeded threshold
            weather_info: Weather description string

        Returns:
            Dict with success status and message
        """
        if not self.enabled:
            return {"success": False, "message": "Alerts are disabled"}

        if not self.is_configured():
            return {"success": False, "message": "SMTP not configured. Set sender_email and sender_password in config.json"}

        if not alerts:
            return {"success": False, "message": "No neighborhoods above threshold"}

        # Filter out already-sent alerts
        new_alerts = [a for a in alerts if not self._already_sent(a['name'])]
        if not new_alerts:
            return {"success": True, "message": "Alerts already sent today for these neighborhoods"}

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[HEAT ALERT] {len(new_alerts)} NYC Neighborhoods Above Risk {self.risk_threshold}"
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email

            html_body = self.build_alert_html(new_alerts, weather_info)
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            # Mark as sent
            for a in new_alerts:
                self._mark_sent(a['name'])

            return {
                "success": True,
                "message": f"Alert sent to {self.recipient_email} for {len(new_alerts)} neighborhood(s)"
            }
        except smtplib.SMTPAuthenticationError:
            return {"success": False, "message": "SMTP authentication failed. Check sender_email and sender_password (use App Password for Gmail)"}
        except Exception as e:
            return {"success": False, "message": f"Email send failed: {str(e)}"}

    def check_and_alert(self, risk_data: List[Dict], weather_info: str = "") -> Dict:
        """
        Check risk data against threshold and send alert if needed.

        Args:
            risk_data: List of all neighborhood risk dicts
            weather_info: Weather description string

        Returns:
            Dict with check results
        """
        level_en = {"极高": "CRITICAL", "高": "HIGH", "中": "MEDIUM", "低": "LOW"}

        exceeding = []
        for r in risk_data:
            if r.get("risk_score", 0) >= self.risk_threshold:
                exceeding.append({
                    "name": r["name"],
                    "borough": r.get("borough", ""),
                    "risk_score": r["risk_score"],
                    "level_en": level_en.get(r.get("risk_level", "低"), "LOW"),
                    "heat_index": r.get("heat_index", "N/A"),
                    "elderly_pct": r.get("elderly_pct", ""),
                    "ac_pct": r.get("ac_pct", ""),
                })

        if not exceeding:
            return {"triggered": False, "count": 0, "message": f"All neighborhoods below threshold ({self.risk_threshold})"}

        result = self.send_alert(exceeding, weather_info)
        return {
            "triggered": True,
            "count": len(exceeding),
            "neighborhoods": [e["name"] for e in exceeding],
            **result
        }


if __name__ == "__main__":
    system = EmailAlertSystem()
    print(f"Configured: {system.is_configured()}")
    print(f"Recipient: {system.recipient_email}")
    print(f"Threshold: {system.risk_threshold}")

    # Preview email HTML
    sample = [
        {"name": "Mott Haven", "borough": "Bronx", "risk_score": 78, "level_en": "CRITICAL",
         "heat_index": 105, "elderly_pct": 18, "ac_pct": 45},
        {"name": "East Harlem", "borough": "Manhattan", "risk_score": 72, "level_en": "HIGH",
         "heat_index": 101, "elderly_pct": 22, "ac_pct": 55},
    ]
    html = system.build_alert_html(sample, "NYC: 98F, Humidity 88%, Heat Index 105F")
    with open("/tmp/alert_preview.html", "w") as f:
        f.write(html)
    print("Preview saved to /tmp/alert_preview.html")
