import sys
from urllib.parse import urlparse
from itertools import groupby

import questionary
import argparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.status import Status
from rich import box
from rich.align import Align
from rich.text import Text

from src.database import GameCache
from src.scraper import PSScraper

console = Console()

class PKGScraperCLI:
    def __init__(self):
        self.db = GameCache()
        self.scraper = PSScraper()
        self.db.load()

    def get_host_name(self, url):
        try:
            domain = urlparse(url).netloc
            parts = domain.replace("www.", "").split(".")
            return parts[0].capitalize() if parts else "Link"
        except Exception:
            return "Link"

    def display_game_details(self, game):
        console.print(Panel(
            Align.center(f"[bold cyan]{game['title']}[/bold cyan]"), 
            box=box.ROUNDED, 
            border_style="cyan",
            expand=False,
            padding=(1, 4)
        ))
        
        cached_data = self.db.get(game["url"])

        if cached_data:
            if getattr(self.db, "redis_client", None):
                console.print(" [bold green]✓[/bold green] [italic]Loaded from Redis Cloud[/italic]")
            else:
                console.print(" [bold green]✓[/bold green] [italic]Loaded from local cache[/italic]")
            
            links = cached_data["links"]
            metadata = cached_data.get("metadata", {"size": cached_data.get("size", "N/A")})
        else:
            with console.status("[bold yellow]Scraping live data...[/bold yellow]", spinner="dots"):
                links, metadata = self.scraper.get_game_links(game["url"], game["size"])
                if links:
                    game["size"] = metadata.get("size", "N/A")
                    self.db.save(game, links, metadata)

        grid = Table.grid(expand=True, padding=(0, 2))
        grid.add_column(style="bold white")
        grid.add_column(style="yellow")
        grid.add_column(style="bold white")
        grid.add_column(style="yellow")

        region = metadata.get("region", "N/A")
        cusa = metadata.get("cusa", "N/A")
        reg_str = f"{region} ({cusa})" if region != "N/A" and cusa != "N/A" else (cusa if cusa != "N/A" else region)

        grid.add_row("Size:", metadata.get("size", "N/A"), "Version:", metadata.get("version", "N/A"))
        grid.add_row("Region:", reg_str, "Firmware:", metadata.get("firmware", "N/A"))
        grid.add_row("Voice:", metadata.get("voice", "N/A"), "Subtitles:", metadata.get("subtitles", "N/A"))
        
        console.print(Panel(grid, title="Game Info", title_align="left", border_style="dim", padding=(0, 1)))

        pwd = metadata.get("password")
        if pwd and pwd.lower() != "n/a":
             console.print(Panel(f"[bold white]Password: {pwd}[/bold white]", style="bold red", expand=False))
        
        console.print("")

        if links:
            is_grouped = isinstance(links[0], dict)

            if is_grouped:
                links.sort(key=lambda x: x.get("group", "Misc"))
                
                for group_name, group_items in groupby(links, key=lambda x: x.get("group", "Misc")):
                    table = Table(
                        title=f"{group_name}", 
                        title_style="bold magenta", 
                        show_header=True, 
                        header_style="bold white",
                        box=box.SIMPLE,
                        border_style="bright_black",
                        expand=True,
                        collapse_padding=True
                    )
                    table.add_column("Type", style="cyan", width=20)
                    table.add_column("Host", style="yellow", width=15)
                    table.add_column("URL", style="blue")

                    for item in group_items:
                        url = item.get("url", "")
                        label = item.get("label", "Link")
                        host = self.get_host_name(url)
                        table.add_row(label, host, url)
                    
                    console.print(table)
                    console.print("")
            else:
                table = Table(
                    title="Download Mirrors", 
                    title_style="bold magenta", 
                    show_header=True, 
                    header_style="bold white",
                    box=box.SIMPLE,
                    border_style="bright_black",
                    pad_edge=False,
                    collapse_padding=True
                )
                table.add_column("Host", style="cyan", width=15)
                table.add_column("URL", style="blue")

                sorted_links = sorted(links, key=lambda x: self.get_host_name(x))
                for link in sorted_links:
                    table.add_row(self.get_host_name(link), link)
                
                console.print(table)
        else:
            console.print("[bold red]× No download links found for this entry.[/bold red]")
        
        console.print("\n" + "[dim]━[/dim]" * 50 + "\n")

    def run(self):
        title_text = Text("PS PKG Scraper Pro", style="bold white")
        subtitle = Text("Interactive Search & Scrape Tool", style="dim")
        
        console.print(Panel.fit(
            Align.center(Text.assemble(title_text, "\n", subtitle)), 
            border_style="blue",
            box=box.DOUBLE,
            padding=(1, 4)
        ))
        
        while True:
            try:
                query = questionary.text(
                    "Search Game (or press Esc to quit):",
                    instruction="Enter name..."
                ).ask()

                if query is None or query.lower() in ["exit", "quit", "q"]:
                    console.print("[yellow]Exiting...[/yellow]")
                    break

                if not query.strip():
                    continue

                with console.status(f"[bold blue]Searching for '{query}'...[/bold blue]", spinner="earth"):
                    games = self.scraper.search_games(query)

                if not games:
                    console.print("[bold red]! No games found. Try a different keyword.[/bold red]")
                    continue

                self.handle_selection(games)

            except KeyboardInterrupt:
                console.print("\n[bold red]! Operation cancelled.[/bold red]")
                sys.exit(0)
            except Exception as e:
                console.print(f"[bold red]ERROR:[/bold red] {e}")

    def handle_selection(self, games):
        while True:
            choices = [f"{i+1}. {g['title']}" for i, g in enumerate(games)]
            choices.append(questionary.Separator())
            choices.append("Back to search")

            selected_text = questionary.select(
                "Select a game:",
                choices=choices,
                style=questionary.Style([
                    ('qmark', 'fg:cyan bold'),
                    ('question', 'bold'),
                    ('answer', 'fg:green bold'),
                    ('pointer', 'fg:cyan bold'),
                ])
            ).ask()

            if selected_text == "Back to search" or selected_text is None:
                break

            try:
                idx = int(selected_text.split(".")[0]) - 1
                self.display_game_details(games[idx])
                
                if not questionary.confirm("Return to results?").ask():
                    break
            except (ValueError, IndexError):
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PS PKG Scraper CLI")
    parser.add_argument("-s", "--search", type=str, help="Immediately search for a game")
    args = parser.parse_args()

    app = PKGScraperCLI()

    if args.search:
        console.print(f"[bold blue]Searching for '{args.search}'...[/bold blue]")
        games = app.scraper.search_games(args.search)
        if games:
            app.handle_selection(games)
        else:
            console.print("[bold red]No games found.[/bold red]")
    else:
        app.run()