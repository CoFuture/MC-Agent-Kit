"""Built-in plugins for MC-Agent-Kit.

This package contains plugins that are included with MC-Agent-Kit by default.
"""

from mc_agent_kit.contrib.plugin.builtin.git_plugin import GitPlugin
from mc_agent_kit.contrib.plugin.builtin.notification_plugin import NotificationPlugin
from mc_agent_kit.contrib.plugin.builtin.file_monitor_plugin import FileMonitorPlugin
from mc_agent_kit.contrib.plugin.builtin.code_format_plugin import CodeFormatPlugin

__all__ = [
    "GitPlugin",
    "NotificationPlugin",
    "FileMonitorPlugin",
    "CodeFormatPlugin",
]


def get_builtin_plugins():
    """Get list of all built-in plugin instances.
    
    Returns:
        List of plugin instances.
    """
    return [
        GitPlugin(),
        NotificationPlugin(),
        FileMonitorPlugin(),
        CodeFormatPlugin(),
    ]