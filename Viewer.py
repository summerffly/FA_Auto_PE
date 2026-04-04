# File:        Viewer.py
# Author:      summer@SummerStudio
# CreateDate:  2026-04-04
# LastEdit:    2026-04-04
# Description: FA系统查看器

from typing import List
from colorama import Fore, Style

from rich.console import Console
from rich.table import Table
from rich.text import Text

from LedgerHub import LedgerHub, LedgerEntry


# ======================================== #
#    Viewer
# ======================================== #

class Viewer:

    def __init__(self, hub: LedgerHub):
        self._hub = hub
        self.console = Console()

    # ----- 内部工具 -------------------- #

    def _get_month_list(self) -> List[str]:
        life_ledger = self._hub.get_life_entry().ledger
        return [seg.month_no for seg in life_ledger.segments]

    # ----- 查看 -------------------- #


    def view_gen_ledger(self):
        table = Table(show_header=True, header_style="magenta")
        table.add_column("Line", style="green")
        table.add_column("Value", justify="right")

        gen_entry = self._hub.get_gen_entry()
        gen_ledger = gen_entry.ledger

        value = gen_ledger.general.initial_wealth
        sign = "+" if value >= 0 else ""
        table.add_row("初始财富", f"{sign}{value}")

        value = gen_ledger.general.current_wealth
        sign = "+" if value >= 0 else ""
        table.add_row("当前财富", f"{sign}{value}")

        table.add_row(
            Text("─" * 14, style="dim"),
            Text("─" * 8, style="dim")
        )

        value = gen_ledger.general.disposable_wealth
        sign = "+" if value >= 0 else ""
        table.add_row("可支配财富", f"{sign}{value}")

        table.add_row(
            Text("─" * 14, style="dim"),
            Text("─" * 8, style="dim")
        )

        line = gen_ledger.general.principal_line
        sign = "+" if line.value >= 0 else ""
        table.add_row(line.content, f"{sign}{line.value}")

        self.console.print(table)

    def view_all_sum(self):
        table = Table(show_header=True, header_style="magenta")
        table.add_column("Ledger", style="cyan")
        table.add_column("Segment", style="green")
        table.add_column("Sum", justify="right")

        for entry in self._hub.get_entries():
            ledger = entry.ledger
            name = entry.name
            for seg in ledger.segments:
                sum = seg.sum
                sign = "+" if sum >= 0 else ""
                table.add_row(name, seg.name, f"{sign}{sum}")
            table.add_row(
                    Text("─" * 10, style="dim"),
                    Text("─" * 14, style="dim"),
                    Text("─" * 8, style="dim"))
        self.console.print(table)

    # ----- END -------------------- #
