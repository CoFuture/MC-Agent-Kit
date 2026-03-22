"""Hello World Plugin Example.

This is a simple example plugin demonstrating the MC-Agent-Kit plugin system.
It provides a basic greeting capability.
"""

from mc_agent_kit.plugin import (
    PluginBase,
    PluginMetadata,
    PluginResult,
    PluginState,
)


class HelloPlugin(PluginBase):
    """A simple hello world plugin."""

    def on_load(self) -> None:
        """Called when plugin is loaded."""
        print(f"[HelloPlugin] Loading plugin: {self.metadata.name}")

    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        print(f"[HelloPlugin] Unloading plugin: {self.metadata.name}")

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        print(f"[HelloPlugin] Plugin enabled: {self.metadata.name}")

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        print(f"[HelloPlugin] Plugin disabled: {self.metadata.name}")

    def execute(self, name: str = "World", **kwargs) -> PluginResult:
        """Execute the plugin's main functionality.

        Args:
            name: Name to greet
            **kwargs: Additional keyword arguments

        Returns:
            PluginResult with greeting message
        """
        greeting = f"Hello, {name}! Welcome to MC-Agent-Kit!"
        return PluginResult(
            success=True,
            data={"greeting": greeting, "plugin": self.metadata.name},
        )


# Plugin metadata
__plugin__ = PluginMetadata(
    name="hello_plugin",
    version="1.0.0",
    description="A simple hello world plugin example",
    author="MC-Agent-Kit Team",
    provides=["greeting"],
    dependencies=[],
)
