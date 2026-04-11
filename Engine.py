# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-11
# Description: FA系统核心引擎

from typing import List
from colorama import Fore, Style

from rich.console import Console
from rich.table import Table
from rich.text import Text

from LedgerHub import LedgerHub, LedgerEntry


# ======================================== #
#    Engine
# ======================================== #

class Engine:

    def __init__(self, hub: LedgerHub):
        self._hub = hub
        self.console = Console()

    # ----- 内部工具 -------------------- #

    def _get_month_list(self) -> List[str]:
        life_ledger = self._hub.get_life_entry().ledger
        return [seg.month_no for seg in life_ledger.segments]

    # ----- 校验 -------------------- #

    def validate_ledger(self, entry: LedgerEntry, table: Table = None):
        ledger = entry.ledger
        filepath = entry.filepath
        ledger_type = type(ledger).__name__
        errors = ledger.validate()

        status = "✅" if not errors else "❌"
        table.add_row(filepath, ledger_type, status)

        for error in errors:
            print(f"{filepath} {Fore.RED}[!]{Style.RESET_ALL} {error}")
    
    def validate(self):
        table = Table(show_header=True, header_style="dark_cyan")
        table.add_column("Ledger", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Valid", justify="right")

        gen_entry = self._hub.get_gen_entry()
        self.validate_ledger(gen_entry, table)

        table.add_row(Text("─" * 10, style="dim"),
                      Text("─" * 14, style="dim"),
                      Text("─" * 5,  style="dim"))
        
        life_entry = self._hub.get_life_entry()
        self.validate_ledger(life_entry, table)

        table.add_row(Text("─" * 10, style="dim"),
                      Text("─" * 14, style="dim"),
                      Text("─" * 5,  style="dim"))
        
        for entry in self._hub.get_month_entries():
            self.validate_ledger(entry, table)
        
        table.add_row(Text("─" * 10, style="dim"),
                      Text("─" * 14, style="dim"),
                      Text("─" * 5,  style="dim"))
            
        for entry in self._hub.get_collect_entries():
            self.validate_ledger(entry, table)

        self.console.print(table)

    # ----- 校验 -------------------- #

    def check_gen_ledger(self, table: Table = None):
        gen_ledger = self._hub.get_gen_entry().ledger
        gen_name = self._hub.get_gen_entry().name

        ok = gen_ledger.checksum()
        status = "✅" if ok else "❌"
        table.add_row(gen_name, gen_ledger.general.name, status, " ")

        table.add_row(Text("─" * 10, style="dim"),
                      Text("─" * 16, style="dim"),
                      Text("─" * 5,  style="dim"),
                      Text("─" * 5,  style="dim"))

    def check_life_ledger(self, table: Table = None):
        gen_ledger = self._hub.get_gen_entry().ledger
        life_ledger = self._hub.get_life_entry().ledger
        life_name = self._hub.get_life_entry().name

        for seg in life_ledger.segments:
            ok = seg.checksum()
            status = "✅" if ok else "❌"
            table.add_row(life_name, seg.month_no, status, " ")

        ok = gen_ledger.checksync_life_segment(
            life_ledger.get_income_sum(),
            life_ledger.get_expense_sum(),
            life_ledger.get_balance_sum()
        )
        status = "✅" if ok else "❌"
        table.add_row(life_name, Text("Total", style="bright_yellow"), " ", status)

        table.add_row(Text("─" * 10, style="dim"),
                      Text("─" * 16, style="dim"),
                      Text("─" * 5,  style="dim"),
                      Text("─" * 5,  style="dim"))

    def check_month_ledger(self, table: Table = None):
        life_ledger = self._hub.get_life_entry().ledger

        for entry in self._hub.get_month_entries():
            for month in self._get_month_list():
                month_sum = entry.ledger.get_month_sum(f"{month}")
                ok1 = entry.ledger.get_month_segment(f"{month}").checksum()
                ok2 = life_ledger.checksync_month_line(f"{month}", entry.name, month_sum)
                status1 = "✅" if ok1 else "❌"
                status2 = "✅" if ok2 else "❌"
                table.add_row(entry.name, f"{month}", status1, status2)

            table.add_row(Text("─" * 10, style="dim"),
                          Text("─" * 16, style="dim"),
                          Text("─" * 5,  style="dim"),
                          Text("─" * 5,  style="dim"))

    def check_collect_ledger(self, table: Table = None):  
        gen_ledger = self._hub.get_gen_entry().ledger

        for entry in self._hub.get_collect_entries():
            for seg in entry.ledger.segments:
                ok = seg.checksum()
                status = "✅" if ok else "❌"
                table.add_row(entry.name, seg.name, status, " ")
        
            ok1 = entry.ledger.checksum()
            ok2 = gen_ledger.checksync_collect_segment(entry.name, entry.ledger.total)
            status1 = "✅" if ok1 else "❌"
            status2 = "✅" if ok2 else "❌"
            table.add_row(entry.name, Text(entry.ledger.total_seg.name, style="bright_yellow"), status1, status2)

            table.add_row(Text("─" * 10, style="dim"),
                          Text("─" * 16, style="dim"),
                          Text("─" * 5,  style="dim"),
                          Text("─" * 5,  style="dim"))

    def check_all(self):
        table = Table(show_header=True, header_style="dark_cyan")
        table.add_column("Ledger", style="cyan")
        table.add_column("Segment", style="green")
        table.add_column("Sum", justify="right")
        table.add_column("Sync", justify="right")

        self.check_gen_ledger(table)
        self.check_life_ledger(table)
        self.check_month_ledger(table)
        self.check_collect_ledger(table)
        self.console.print(table)

    # ----- 重计算 -------------------- #
    
    def rebuild_gen(self):
        gen_entry = self._hub.get_gen_entry()
        gen_ledger = gen_entry.ledger
        gen_ledger.rebuild()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {gen_entry.name:<9} 完成ReBuild")

    def rebuild_life(self):
        life_entry = self._hub.get_life_entry()
        life_entry.ledger.rebuild()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {life_entry.name:<9} 完成ReBuild")

    def rebuild_month(self):
        for entry in self._hub.get_month_entries():
            entry.ledger.rebuild()
            print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<9} 完成ReBuild")

    def rebuild_collect(self):
        for entry in self._hub.get_collect_entries():
            entry.ledger.rebuild()
            print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<9} 完成ReBuild")

    # ----- 同步 -------------------- #

    def sync_life(self):
        gen_ledger = self._hub.get_gen_entry().ledger
        life_ledger = self._hub.get_life_entry().ledger
        gen_ledger.sync_life_segment(life_ledger.get_income_sum(),
                                     life_ledger.get_expense_sum(),
                                     life_ledger.get_balance_sum())
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {"Life":<9} 完成Sync")

    def sync_month(self):
        life_ledger = self._hub.get_life_entry().ledger
        for entry in self._hub.get_month_entries():
            for month in self._get_month_list():
                month_sum = entry.ledger.get_month_sum(f"{month}")
                life_ledger.sync_month_line(f"{month}", entry.name, month_sum)
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {"Month":<9} 完成Sync")

    def sync_collect(self):
        gen_ledger = self._hub.get_gen_entry().ledger
        for entry in self._hub.get_collect_entries():
            gen_ledger.sync_collect_segment(entry.name, entry.ledger.total)
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {"Collect":<9} 完成Sync")

    # ----- 更新 -------------------- #

    def update(self):
        print(f"{Fore.CYAN}[1/4] Update Month ...{Style.RESET_ALL}")
        self.rebuild_month()
        self.sync_month()
        print(f"")

        print(f"{Fore.CYAN}[2/4] Update Life ...{Style.RESET_ALL}")
        self.rebuild_life()
        self.sync_life()
        print(f"")

        print(f"{Fore.CYAN}[3/4] Update Collect ...{Style.RESET_ALL}")
        self.rebuild_collect()
        self.sync_collect()
        print(f"")

        print(f"{Fore.CYAN}[4/4] Finish Update ⭐{Style.RESET_ALL}")
        self.rebuild_gen()
        print(f"")

    # ----- END -------------------- #
