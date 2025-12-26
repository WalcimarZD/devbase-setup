"""
Notifications Service - Cross-Platform Alerts
==============================================
Desktop and console notifications for async task completion.

Uses plyer for cross-platform desktop notifications.
Falls back to console if plyer not installed.

Author: DevBase Team
Version: 5.1.0
"""
from __future__ import annotations

from typing import Protocol


class Notifier(Protocol):
    """Protocol for notification implementations."""
    
    def notify(self, title: str, message: str) -> None:
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification body
        """
        ...


class PlyerNotifier:
    """
    Desktop notification via plyer library.
    
    Falls back silently if plyer is not installed.
    """
    
    def __init__(self) -> None:
        """Initialize notifier, checking for plyer availability."""
        try:
            from plyer import notification
            self._notification = notification
            self._available = True
        except ImportError:
            self._notification = None
            self._available = False
    
    @property
    def available(self) -> bool:
        """Check if desktop notifications are available."""
        return self._available
    
    def notify(self, title: str, message: str) -> None:
        """
        Send desktop notification.
        
        Silently no-ops if plyer not installed.
        
        Args:
            title: Notification title
            message: Notification body
        """
        if not self._available or self._notification is None:
            return
        
        try:
            self._notification.notify(
                title=title,
                message=message,
                app_name="DevBase",
                timeout=5,
            )
        except Exception:
            # Desktop notifications should never crash the app
            pass


class ConsoleNotifier:
    """
    Console-based notification fallback.
    
    Uses Rich for styled output.
    """
    
    def __init__(self) -> None:
        """Initialize console notifier."""
        try:
            from rich.console import Console
            self._console = Console()
        except ImportError:
            self._console = None
    
    def notify(self, title: str, message: str) -> None:
        """
        Print notification to console.
        
        Args:
            title: Notification title
            message: Notification body
        """
        if self._console:
            self._console.print(f"[blue]📢 {title}:[/blue] {message}")
        else:
            print(f"📢 {title}: {message}")


class SilentNotifier:
    """No-op notifier for when notifications are disabled."""
    
    def notify(self, title: str, message: str) -> None:
        """Do nothing."""
        pass


def get_notifier(notification_type: str | None = None) -> Notifier:
    """
    Factory function to get appropriate notifier.
    
    Args:
        notification_type: One of "desktop", "console", "none"
                          (reads from config if None)
        
    Returns:
        Notifier implementation
    """
    if notification_type is None:
        # Try to read from config
        try:
            from devbase.utils.config import get_config
            config = get_config()
            notification_type = config.get("ai.notification", "console")
        except Exception:
            notification_type = "console"
    
    if notification_type == "desktop":
        notifier = PlyerNotifier()
        if notifier.available:
            return notifier
        # Fall back to console if plyer not available
        return ConsoleNotifier()
    
    if notification_type == "none":
        return SilentNotifier()
    
    # Default: console
    return ConsoleNotifier()


# Convenience functions
def notify_task_complete(task_type: str, result_summary: str) -> None:
    """
    Notify user that an AI task completed.
    
    Args:
        task_type: Type of task (classify, synthesize, etc.)
        result_summary: Brief summary of result
    """
    notifier = get_notifier()
    notifier.notify(
        title=f"DevBase: {task_type.title()} Complete",
        message=result_summary[:100],
    )


def notify_quota_warning(remaining: int) -> None:
    """
    Warn user about remaining AI quota.
    
    Args:
        remaining: Number of artifacts remaining today
    """
    if remaining <= 2:
        notifier = get_notifier()
        notifier.notify(
            title="DevBase: Quota Warning",
            message=f"Only {remaining} AI artifacts remaining today",
        )
