"""Notification plugin for MC-Agent-Kit.

Provides notification capabilities via multiple channels (console, file, webhook).
"""

from __future__ import annotations

import json
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from enum import Enum
from pathlib import Path
from typing import Any

from mc_agent_kit.contrib.plugin.base import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginPriority,
    PluginState,
)
from mc_agent_kit.contrib.plugin.hooks import HookType, HookPriority, register_hook
from mc_agent_kit.contrib.plugin.config import PluginConfigSchema


class NotificationLevel(Enum):
    """Notification severity level."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(Enum):
    """Notification channel type."""
    CONSOLE = "console"
    FILE = "file"
    EMAIL = "email"
    WEBHOOK = "webhook"
    FEISHU = "feishu"
    DINGTALK = "dingtalk"


@dataclass
class Notification:
    """Notification data."""
    title: str
    message: str
    level: NotificationLevel = NotificationLevel.INFO
    channel: NotificationChannel = NotificationChannel.CONSOLE
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationConfig:
    """Configuration for a notification channel."""
    enabled: bool = True
    min_level: NotificationLevel = NotificationLevel.INFO
    
    # Email settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: list[str] = field(default_factory=list)
    
    # Webhook settings
    webhook_url: str = ""
    webhook_headers: dict[str, str] = field(default_factory=dict)
    
    # Feishu settings
    feishu_webhook: str = ""
    
    # DingTalk settings
    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""
    
    # File settings
    log_file: str = "notifications.log"


class NotificationPlugin(PluginBase):
    """Plugin for sending notifications."""

    def __init__(self) -> None:
        """Initialize the notification plugin."""
        metadata = PluginMetadata(
            name="notification",
            version="1.0.0",
            description="Notification plugin for alerts and messages",
            author="MC-Agent-Kit",
            capabilities=["notification", "alert", "email", "webhook"],
            priority=PluginPriority.HIGH,
        )
        super().__init__(metadata)
        self._configs: dict[NotificationChannel, NotificationConfig] = {}
        self._history: list[Notification] = []
        self._max_history = 100

    def initialize(self) -> bool:
        """Initialize the plugin.
        
        Returns:
            True if successful.
        """
        # Set state to LOADED
        self._state = PluginState.LOADED
        
        # Set default configs
        self._configs[NotificationChannel.CONSOLE] = NotificationConfig()
        self._configs[NotificationChannel.FILE] = NotificationConfig()
        
        # Register hooks for error notifications
        register_hook(
            HookType.ON_ERROR,
            self._on_error,
            HookPriority.MONITOR,
            self.metadata.name,
            "Send notification on errors",
        )
        
        register_hook(
            HookType.ON_EXECUTION_ERROR,
            self._on_execution_error,
            HookPriority.MONITOR,
            self.metadata.name,
            "Send notification on execution errors",
        )
        
        return True

    def shutdown(self) -> None:
        """Shutdown the plugin."""
        pass

    def execute(self, **kwargs: Any) -> PluginResult:
        """Send a notification.
        
        Args:
            **kwargs: Notification parameters.
                - title: Notification title
                - message: Notification message
                - level: Severity level (debug/info/warning/error/critical)
                - channel: Channel type (console/file/email/webhook/feishu/dingtalk)
                - metadata: Additional metadata
        
        Returns:
            Execution result.
        """
        title = kwargs.get("title", "Notification")
        message = kwargs.get("message", "")
        level_str = kwargs.get("level", "info").upper()
        channel_str = kwargs.get("channel", "console").lower()
        
        try:
            level = NotificationLevel[level_str]
        except KeyError:
            level = NotificationLevel.INFO
        
        try:
            channel = NotificationChannel[channel_str]
        except KeyError:
            channel = NotificationChannel.CONSOLE
        
        notification = Notification(
            title=title,
            message=message,
            level=level,
            channel=channel,
            metadata=kwargs.get("metadata", {}),
        )
        
        # Add to history
        self._history.append(notification)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]
        
        # Send via channel
        try:
            result = self._send(notification)
            return PluginResult(success=True, data=result, message="Notification sent")
        except Exception as e:
            return PluginResult(success=False, error=str(e))

    def _send(self, notification: Notification) -> dict[str, Any]:
        """Send notification via configured channel.
        
        Args:
            notification: Notification to send.
            
        Returns:
            Send result.
        """
        channel = notification.channel
        config = self._configs.get(channel, NotificationConfig())
        
        # Check if channel is enabled and level is sufficient
        if not config.enabled:
            return {"status": "skipped", "reason": "Channel disabled"}
        
        level_order = [NotificationLevel.DEBUG, NotificationLevel.INFO, 
                       NotificationLevel.WARNING, NotificationLevel.ERROR, 
                       NotificationLevel.CRITICAL]
        if level_order.index(notification.level) < level_order.index(config.min_level):
            return {"status": "skipped", "reason": "Level below minimum"}

        handlers = {
            NotificationChannel.CONSOLE: self._send_console,
            NotificationChannel.FILE: self._send_file,
            NotificationChannel.EMAIL: self._send_email,
            NotificationChannel.WEBHOOK: self._send_webhook,
            NotificationChannel.FEISHU: self._send_feishu,
            NotificationChannel.DINGTALK: self._send_dingtalk,
        }
        
        handler = handlers.get(channel, self._send_console)
        return handler(notification, config)

    def _send_console(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send to console.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        level_colors = {
            NotificationLevel.DEBUG: "\033[36m",     # Cyan
            NotificationLevel.INFO: "\033[32m",      # Green
            NotificationLevel.WARNING: "\033[33m",   # Yellow
            NotificationLevel.ERROR: "\033[31m",     # Red
            NotificationLevel.CRITICAL: "\033[35m",  # Magenta
        }
        reset = "\033[0m"
        color = level_colors.get(notification.level, "")
        
        print(f"{color}[{notification.level.value.upper()}]{reset} {notification.title}: {notification.message}")
        return {"status": "sent", "channel": "console"}

    def _send_file(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send to file.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        log_file = Path(config.log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        log_entry = f"[{notification.timestamp}] [{notification.level.value.upper()}] {notification.title}: {notification.message}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        return {"status": "sent", "channel": "file", "file": str(log_file)}

    def _send_email(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send via email.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        if not all([config.smtp_host, config.email_from, config.email_to]):
            return {"status": "error", "reason": "Email not configured"}
        
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[{notification.level.value.upper()}] {notification.title}"
        msg["From"] = config.email_from
        msg["To"] = ", ".join(config.email_to)
        
        text = f"{notification.message}\n\nTimestamp: {notification.timestamp}"
        if notification.metadata:
            text += f"\n\nMetadata: {json.dumps(notification.metadata, indent=2)}"
        
        msg.attach(MIMEText(text, "plain"))
        
        try:
            with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
                server.starttls()
                if config.smtp_user and config.smtp_password:
                    server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.email_from, config.email_to, msg.as_string())
            
            return {"status": "sent", "channel": "email"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def _send_webhook(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send via webhook.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        if not config.webhook_url:
            return {"status": "error", "reason": "Webhook not configured"}
        
        try:
            import urllib.request
            
            payload = {
                "title": notification.title,
                "message": notification.message,
                "level": notification.level.value,
                "timestamp": notification.timestamp,
                "metadata": notification.metadata,
            }
            
            data = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json", **config.webhook_headers}
            
            req = urllib.request.Request(
                config.webhook_url,
                data=data,
                headers=headers,
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return {"status": "sent", "channel": "webhook", "response_code": response.status}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def _send_feishu(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send via Feishu webhook.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        if not config.feishu_webhook:
            return {"status": "error", "reason": "Feishu webhook not configured"}
        
        try:
            import urllib.request
            
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"[{notification.level.value.upper()}] {notification.title}\n{notification.message}"
                }
            }
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                config.feishu_webhook,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return {"status": "sent", "channel": "feishu"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def _send_dingtalk(self, notification: Notification, config: NotificationConfig) -> dict[str, Any]:
        """Send via DingTalk webhook.
        
        Args:
            notification: Notification to send.
            config: Channel config.
            
        Returns:
            Send result.
        """
        if not config.dingtalk_webhook:
            return {"status": "error", "reason": "DingTalk webhook not configured"}
        
        try:
            import urllib.request
            import time
            import hmac
            import hashlib
            import base64
            import urllib.parse
            
            url = config.dingtalk_webhook
            
            # Add signature if secret is configured
            if config.dingtalk_secret:
                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{config.dingtalk_secret}"
                hmac_code = hmac.new(
                    config.dingtalk_secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                url = f"{url}&timestamp={timestamp}&sign={sign}"
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"[{notification.level.value.upper()}] {notification.title}\n{notification.message}"
                }
            }
            
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return {"status": "sent", "channel": "dingtalk"}
        except Exception as e:
            return {"status": "error", "reason": str(e)}

    def configure_channel(self, channel: str, config: dict[str, Any]) -> None:
        """Configure a notification channel.
        
        Args:
            channel: Channel name.
            config: Configuration dictionary.
        """
        try:
            channel_enum = NotificationChannel[channel.upper()]
        except KeyError:
            raise ValueError(f"Unknown channel: {channel}")
        
        current = self._configs.get(channel_enum, NotificationConfig())
        
        # Update config
        for key, value in config.items():
            if hasattr(current, key):
                setattr(current, key, value)
        
        self._configs[channel_enum] = current

    def get_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get notification history.
        
        Args:
            limit: Maximum number of entries.
            
        Returns:
            List of notification dictionaries.
        """
        return [
            {
                "title": n.title,
                "message": n.message,
                "level": n.level.value,
                "channel": n.channel.value,
                "timestamp": n.timestamp,
            }
            for n in self._history[-limit:]
        ]

    def _on_error(self, error: str, context: dict[str, Any] | None = None, **kwargs: Any) -> None:
        """Hook callback for errors.
        
        Args:
            error: Error message.
            context: Error context.
            **kwargs: Additional arguments.
        """
        self.execute(
            title="Error Occurred",
            message=error,
            level="error",
            channel="console",
            metadata=context or {},
        )

    def _on_execution_error(self, error: str, **kwargs: Any) -> None:
        """Hook callback for execution errors.
        
        Args:
            error: Error message.
            **kwargs: Additional arguments.
        """
        self.execute(
            title="Execution Error",
            message=error,
            level="error",
            channel="console",
        )

    @classmethod
    def get_config_schemas(cls) -> list[PluginConfigSchema]:
        """Get configuration schemas.
        
        Returns:
            List of config schemas.
        """
        return [
            PluginConfigSchema(
                key="console_enabled",
                type="bool",
                default=True,
                description="Enable console notifications",
            ),
            PluginConfigSchema(
                key="file_enabled",
                type="bool",
                default=False,
                description="Enable file notifications",
            ),
            PluginConfigSchema(
                key="log_file",
                type="string",
                default="notifications.log",
                description="Path to notification log file",
            ),
            PluginConfigSchema(
                key="min_level",
                type="string",
                default="info",
                description="Minimum notification level",
                choices=["debug", "info", "warning", "error", "critical"],
            ),
            PluginConfigSchema(
                key="webhook_url",
                type="string",
                default="",
                description="Webhook URL for notifications",
            ),
            PluginConfigSchema(
                key="feishu_webhook",
                type="string",
                default="",
                description="Feishu webhook URL",
            ),
        ]