"""
Plugin CLI for MC-Agent-Kit.

Provides commands for managing plugins:
- mc-plugin list - List all plugins
- mc-plugin install <name> - Install a plugin
- mc-plugin uninstall <name> - Uninstall a plugin
- mc-plugin config <name> - Configure a plugin
- mc-plugin hooks - List all hooks
"""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path

from mc_agent_kit.contrib.plugin.manager import PluginManager, PluginManagerConfig
from mc_agent_kit.contrib.plugin.marketplace import PluginMarketplace, MarketplaceConfig
from mc_agent_kit.contrib.plugin.hooks import get_hook_registry, HookType
from mc_agent_kit.contrib.plugin.config import PluginConfigManager


console = Console()


@click.group()
def main():
    """Plugin management for MC-Agent-Kit."""
    pass


@main.command()
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def list(verbose: bool):
    """List all available and installed plugins."""
    console.print("[bold]Installed Plugins[/bold]\n")
    
    # Create plugin manager
    config = PluginManagerConfig(
        plugin_dirs=[Path.home() / ".mc-agent-kit" / "plugins"],
        auto_load=False,
        scan_on_startup=False,
    )
    manager = PluginManager(config)
    
    # Get marketplace
    marketplace = PluginMarketplace(MarketplaceConfig())
    
    # Get all plugins from marketplace
    all_plugins = marketplace.list_all()
    
    if not all_plugins:
        console.print("[yellow]No plugins found.[/yellow]")
        return
    
    # Create table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Description", style="white")
    table.add_column("Status", style="yellow")
    table.add_column("Category", style="blue")
    
    for plugin in all_plugins:
        status = "Installed" if plugin.status.value == "installed" else "Available"
        table.add_row(
            plugin.name,
            plugin.version,
            plugin.description[:50] + "..." if len(plugin.description) > 50 else plugin.description,
            status,
            plugin.category.value if plugin.category else "Other",
        )
    
    console.print(table)
    
    if verbose:
        console.print(f"\n[bold]Total:[/bold] {len(all_plugins)} plugins")


@main.command()
@click.argument('name')
@click.option('--from-url', '-u', help='Install from URL')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def install(name: str, from_url: str | None, yes: bool):
    """Install a plugin."""
    console.print(f"[bold]Installing plugin:[/bold] {name}\n")
    
    marketplace = PluginMarketplace(MarketplaceConfig())
    
    # Search for plugin
    results = marketplace.search(name)
    
    if not results:
        console.print(f"[red]Plugin '{name}' not found.[/red]")
        return
    
    plugin_info = results[0]
    
    if not yes:
        console.print(f"Plugin: {plugin_info.name}")
        console.print(f"Version: {plugin_info.version}")
        console.print(f"Description: {plugin_info.description}")
        console.print(f"Author: {plugin_info.author or 'Unknown'}")
        
        if not click.confirm('\nDo you want to install this plugin?'):
            console.print("[yellow]Installation cancelled.[/yellow]")
            return
    
    # Install plugin
    success = marketplace.install(plugin_info.id)
    
    if success:
        console.print(f"[green]✓ Plugin '{name}' installed successfully.[/green]")
    else:
        console.print(f"[red]✗ Failed to install plugin '{name}'.[/red]")


@main.command()
@click.argument('name')
@click.option('--yes', '-y', is_flag=True, help='Skip confirmation')
def uninstall(name: str, yes: bool):
    """Uninstall a plugin."""
    console.print(f"[bold]Uninstalling plugin:[/bold] {name}\n")
    
    if not yes:
        if not click.confirm(f'Are you sure you want to uninstall "{name}"?'):
            console.print("[yellow]Uninstallation cancelled.[/yellow]")
            return
    
    marketplace = PluginMarketplace(MarketplaceConfig())
    
    # Uninstall plugin
    success = marketplace.uninstall(name)
    
    if success:
        console.print(f"[green]✓ Plugin '{name}' uninstalled successfully.[/green]")
    else:
        console.print(f"[red]✗ Failed to uninstall plugin '{name}'.[/red]")


@main.command()
@click.argument('name')
@click.option('--set', '-s', 'settings', multiple=True, help='Set a configuration value (key=value)')
@click.option('--show', is_flag=True, help='Show current configuration')
def config(name: str, settings: list[str], show: bool):
    """Configure a plugin."""
    config_manager = PluginConfigManager()
    
    if show:
        # Show current configuration
        try:
            plugin_config = config_manager.get_config(name)
            console.print(f"[bold]Configuration for {name}:[/bold]\n")
            
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Key", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("enabled", str(plugin_config.enabled))
            for key, value in plugin_config.settings.items():
                table.add_row(key, str(value))
            
            console.print(table)
        except Exception as e:
            console.print(f"[red]Error loading configuration: {e}[/red]")
        return
    
    if not settings:
        console.print("[yellow]No settings specified. Use --set key=value or --show to view.[/yellow]")
        return
    
    # Parse settings
    updates = {}
    for setting in settings:
        if '=' not in setting:
            console.print(f"[red]Invalid setting format: {setting} (use key=value)[/red]")
            return
        key, value = setting.split('=', 1)
        updates[key.strip()] = value.strip()
    
    # Update configuration
    plugin_config = config_manager.get_config(name)
    for key, value in updates.items():
        # Try to convert to appropriate type
        if value.lower() == 'true':
            value = True
        elif value.lower() == 'false':
            value = False
        elif value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                pass  # Keep as string
        
        plugin_config.set(key, value)
    
    config_manager.set_config(name, plugin_config)
    
    console.print(f"[green]✓ Configuration updated for '{name}'.[/green]")
    console.print("Updated settings:")
    for key, value in updates.items():
        console.print(f"  {key} = {value}")


@main.command()
@click.option('--type', '-t', 'hook_type', help='Filter by hook type')
@click.option('--verbose', '-v', is_flag=True, help='Show verbose output')
def hooks(hook_type: str | None, verbose: bool):
    """List all registered hooks."""
    console.print("[bold]Registered Hooks[/bold]\n")
    
    registry = get_hook_registry()
    all_hooks = registry.list_all()
    
    if not all_hooks:
        console.print("[yellow]No hooks registered.[/yellow]")
        return
    
    # Filter by type if specified
    if hook_type:
        if hook_type in all_hooks:
            all_hooks = {hook_type: all_hooks[hook_type]}
        else:
            console.print(f"[red]Hook type '{hook_type}' not found.[/red]")
            return
    
    for type_name, hooks in all_hooks.items():
        console.print(f"[bold cyan]{type_name}[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Plugin", style="green")
        table.add_column("Priority", style="yellow")
        
        if verbose:
            table.add_column("Description", style="white")
        
        for hook in hooks:
            table.add_row(
                hook.plugin_name or "Unknown",
                hook.priority.name,
                hook.description if verbose else "",
            )
        
        console.print(table)
        console.print()


@main.command()
@click.argument('name')
def info(name: str):
    """Show detailed information about a plugin."""
    console.print(f"[bold]Plugin Information:[/bold] {name}\n")
    
    marketplace = PluginMarketplace(MarketplaceConfig())
    
    # Search for plugin
    results = marketplace.search(name)
    
    if not results:
        console.print(f"[red]Plugin '{name}' not found.[/red]")
        return
    
    plugin_info = results[0]
    
    # Display information
    console.print(Panel(
        f"[bold]Name:[/bold] {plugin_info.name}\n"
        f"[bold]Version:[/bold] {plugin_info.version}\n"
        f"[bold]Description:[/bold] {plugin_info.description}\n"
        f"[bold]Author:[/bold] {plugin_info.author or 'Unknown'}\n"
        f"[bold]Category:[/bold] {plugin_info.category.value if plugin_info.category else 'Other'}\n"
        f"[bold]Status:[/bold] {plugin_info.status.value}\n"
        f"[bold]Downloads:[/bold] {plugin_info.downloads if hasattr(plugin_info, 'downloads') else 'N/A'}\n"
        f"[bold]Rating:[/bold] {plugin_info.rating if hasattr(plugin_info, 'rating') else 'N/A'}",
        title=f"Plugin: {name}",
        border_style="green",
    ))


def main_entry():
    """Main entry point."""
    main()


if __name__ == '__main__':
    main_entry()
