"""
Alerts - Send notifications via Discord, Slack, and Email.

Features:
- Discord webhook integration
- Slack webhook integration
- Email alerts (SMTP)
- Alert templates for different event types
- Rate limiting to prevent spam
- Alert history tracking
"""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Literal
from enum import Enum


class AlertType(Enum):
    """Types of alerts."""
    NEW_TREND = "new_trend"
    HOT_KEYWORD = "hot_keyword"
    GAP_FOUND = "gap_found"
    COMPETITOR_UPDATE = "competitor_update"
    SCAN_COMPLETE = "scan_complete"
    ERROR = "error"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Single alert to send."""
    alert_type: AlertType
    title: str
    message: str
    priority: AlertPriority = AlertPriority.MEDIUM
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class AlertResult:
    """Result of sending an alert."""
    success: bool
    channel: str  # "discord", "slack", "email"
    error: Optional[str] = None
    response: Optional[str] = None


class DiscordWebhook:
    """Send alerts to Discord via webhook."""

    # Color codes for different priorities
    COLORS = {
        AlertPriority.LOW: 0x3498db,      # Blue
        AlertPriority.MEDIUM: 0xf39c12,   # Orange
        AlertPriority.HIGH: 0xe74c3c,     # Red
        AlertPriority.CRITICAL: 0x9b59b6, # Purple
    }

    # Emojis for different alert types
    EMOJIS = {
        AlertType.NEW_TREND: "📈",
        AlertType.HOT_KEYWORD: "🔥",
        AlertType.GAP_FOUND: "🎯",
        AlertType.COMPETITOR_UPDATE: "🏆",
        AlertType.SCAN_COMPLETE: "✅",
        AlertType.ERROR: "❌",
    }

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.last_sent: dict[str, datetime] = {}
        self.rate_limit_seconds = 5

    def _check_rate_limit(self, key: str) -> bool:
        """Check if we can send (rate limiting)."""
        last = self.last_sent.get(key)
        if last and datetime.now() - last < timedelta(seconds=self.rate_limit_seconds):
            return False
        return True

    def send(self, alert: Alert) -> AlertResult:
        """Send alert to Discord."""
        rate_key = f"{alert.alert_type.value}:{alert.title[:50]}"
        if not self._check_rate_limit(rate_key):
            return AlertResult(
                success=False,
                channel="discord",
                error="Rate limited"
            )

        emoji = self.EMOJIS.get(alert.alert_type, "📢")
        color = self.COLORS.get(alert.priority, 0x95a5a6)

        # Build Discord embed
        embed = {
            "title": f"{emoji} {alert.title}",
            "description": alert.message,
            "color": color,
            "timestamp": alert.timestamp,
            "footer": {
                "text": f"Priority: {alert.priority.value.upper()} | Type: {alert.alert_type.value}"
            }
        }

        # Add fields from data
        if alert.data:
            embed["fields"] = []
            for key, value in list(alert.data.items())[:10]:
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:5])
                embed["fields"].append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value)[:1000],
                    "inline": True
                })

        payload = {
            "embeds": [embed]
        }

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                self.last_sent[rate_key] = datetime.now()
                return AlertResult(
                    success=True,
                    channel="discord",
                    response=f"Status: {response.status}"
                )

        except urllib.error.HTTPError as e:
            return AlertResult(
                success=False,
                channel="discord",
                error=f"HTTP {e.code}: {e.reason}"
            )
        except Exception as e:
            return AlertResult(
                success=False,
                channel="discord",
                error=str(e)
            )


class SlackWebhook:
    """Send alerts to Slack via webhook."""

    EMOJIS = {
        AlertType.NEW_TREND: ":chart_with_upwards_trend:",
        AlertType.HOT_KEYWORD: ":fire:",
        AlertType.GAP_FOUND: ":dart:",
        AlertType.COMPETITOR_UPDATE: ":trophy:",
        AlertType.SCAN_COMPLETE: ":white_check_mark:",
        AlertType.ERROR: ":x:",
    }

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.last_sent: dict[str, datetime] = {}
        self.rate_limit_seconds = 5

    def _check_rate_limit(self, key: str) -> bool:
        """Check if we can send (rate limiting)."""
        last = self.last_sent.get(key)
        if last and datetime.now() - last < timedelta(seconds=self.rate_limit_seconds):
            return False
        return True

    def send(self, alert: Alert) -> AlertResult:
        """Send alert to Slack."""
        rate_key = f"{alert.alert_type.value}:{alert.title[:50]}"
        if not self._check_rate_limit(rate_key):
            return AlertResult(
                success=False,
                channel="slack",
                error="Rate limited"
            )

        emoji = self.EMOJIS.get(alert.alert_type, ":bell:")

        # Build Slack blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {alert.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": alert.message
                }
            }
        ]

        # Add data fields
        if alert.data:
            fields = []
            for key, value in list(alert.data.items())[:6]:
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:5])
                fields.append({
                    "type": "mrkdwn",
                    "text": f"*{key.replace('_', ' ').title()}*\n{str(value)[:200]}"
                })

            if fields:
                blocks.append({
                    "type": "section",
                    "fields": fields[:10]
                })

        # Add footer
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Priority: *{alert.priority.value.upper()}* | Type: {alert.alert_type.value} | {alert.timestamp}"
                }
            ]
        })

        payload = {"blocks": blocks}

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                self.last_sent[rate_key] = datetime.now()
                return AlertResult(
                    success=True,
                    channel="slack",
                    response=f"Status: {response.status}"
                )

        except urllib.error.HTTPError as e:
            return AlertResult(
                success=False,
                channel="slack",
                error=f"HTTP {e.code}: {e.reason}"
            )
        except Exception as e:
            return AlertResult(
                success=False,
                channel="slack",
                error=str(e)
            )


class AlertManager:
    """
    Manage multiple alert channels.

    Usage:
        manager = AlertManager()
        manager.add_discord("https://discord.com/api/webhooks/...")
        manager.add_slack("https://hooks.slack.com/services/...")

        # Send alert
        manager.send_alert(
            alert_type=AlertType.HOT_KEYWORD,
            title="New Trending Keyword!",
            message="'Flux 2.0' is trending on Reddit",
            priority=AlertPriority.HIGH,
            data={"keyword": "Flux 2.0", "trend_score": 95}
        )

        # Or use convenience methods
        manager.notify_trend("Flux 2.0", score=95, source="Reddit")
        manager.notify_gap("video inpainting", competitors=["Runway", "Pika"])
    """

    def __init__(self):
        self.discord: Optional[DiscordWebhook] = None
        self.slack: Optional[SlackWebhook] = None
        self.history: list[tuple[Alert, list[AlertResult]]] = []

    def add_discord(self, webhook_url: str):
        """Add Discord webhook."""
        self.discord = DiscordWebhook(webhook_url)

    def add_slack(self, webhook_url: str):
        """Add Slack webhook."""
        self.slack = SlackWebhook(webhook_url)

    def send_alert(
        self,
        alert_type: AlertType,
        title: str,
        message: str,
        priority: AlertPriority = AlertPriority.MEDIUM,
        data: Optional[dict] = None,
    ) -> list[AlertResult]:
        """Send alert to all configured channels."""
        alert = Alert(
            alert_type=alert_type,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
        )

        results = []

        if self.discord:
            results.append(self.discord.send(alert))

        if self.slack:
            results.append(self.slack.send(alert))

        self.history.append((alert, results))

        return results

    # Convenience methods for common alerts

    def notify_trend(
        self,
        keyword: str,
        score: float,
        source: str,
        direction: str = "rising"
    ) -> list[AlertResult]:
        """Notify about a trending keyword."""
        return self.send_alert(
            alert_type=AlertType.HOT_KEYWORD,
            title=f"Trending: {keyword}",
            message=f"'{keyword}' is {direction} on {source}",
            priority=AlertPriority.HIGH if score >= 80 else AlertPriority.MEDIUM,
            data={
                "keyword": keyword,
                "trend_score": f"{score:.0f}%",
                "source": source,
                "direction": direction,
            }
        )

    def notify_gap(
        self,
        feature: str,
        competitors: list[str],
        priority: str = "high"
    ) -> list[AlertResult]:
        """Notify about a gap opportunity."""
        priority_map = {
            "high": AlertPriority.HIGH,
            "medium": AlertPriority.MEDIUM,
            "low": AlertPriority.LOW,
        }
        return self.send_alert(
            alert_type=AlertType.GAP_FOUND,
            title=f"Gap Found: {feature}",
            message=f"Competitors have '{feature}' but you don't!",
            priority=priority_map.get(priority, AlertPriority.MEDIUM),
            data={
                "feature": feature,
                "competitors_with": competitors,
                "recommendation": "Consider adding this feature",
            }
        )

    def notify_scan_complete(
        self,
        keywords_found: int,
        gaps_found: int,
        top_opportunities: list[str]
    ) -> list[AlertResult]:
        """Notify that a scan completed."""
        return self.send_alert(
            alert_type=AlertType.SCAN_COMPLETE,
            title="Market Scan Complete",
            message=f"Found {keywords_found} keywords and {gaps_found} gaps",
            priority=AlertPriority.LOW,
            data={
                "keywords_found": keywords_found,
                "gaps_found": gaps_found,
                "top_opportunities": top_opportunities[:5],
            }
        )

    def notify_competitor_update(
        self,
        competitor: str,
        new_features: list[str]
    ) -> list[AlertResult]:
        """Notify about competitor changes."""
        return self.send_alert(
            alert_type=AlertType.COMPETITOR_UPDATE,
            title=f"Competitor Update: {competitor}",
            message=f"{competitor} added {len(new_features)} new features",
            priority=AlertPriority.MEDIUM,
            data={
                "competitor": competitor,
                "new_features": new_features[:10],
            }
        )

    def notify_error(self, error_message: str, context: str = "") -> list[AlertResult]:
        """Notify about an error."""
        return self.send_alert(
            alert_type=AlertType.ERROR,
            title="Error Occurred",
            message=error_message,
            priority=AlertPriority.HIGH,
            data={"context": context} if context else {}
        )

    def get_history(self) -> list[tuple[Alert, list[AlertResult]]]:
        """Get alert history."""
        return self.history


def create_alert_manager(
    discord_webhook: Optional[str] = None,
    slack_webhook: Optional[str] = None,
) -> AlertManager:
    """Factory function to create AlertManager."""
    manager = AlertManager()
    if discord_webhook:
        manager.add_discord(discord_webhook)
    if slack_webhook:
        manager.add_slack(slack_webhook)
    return manager
