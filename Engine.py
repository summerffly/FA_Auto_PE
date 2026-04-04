# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-03
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

    def validate_gen_ledger(self, table: Table = None):
        gen_ledger = self._hub.get_gen_entry().ledger
        filepath = self._hub.get_gen_entry().filepath
        ledger_type = type(gen_ledger).__name__
        errors = gen_ledger.validate()

        status = "✅" if not errors else "❌"
        table.add_row(filepath, ledger_type, status)

        for error in errors:
            print(f"{filepath} {ledger_type} {Fore.RED}[!]{Style.RESET_ALL} {error}")

    def validate_ledger(self, entry: LedgerEntry, table: Table = None):
        ledger = entry.ledger
        filepath = entry.filepath
        ledger_type = type(ledger).__name__
        errors = ledger.validate()

        status = "✅" if not errors else "❌"
        table.add_row(filepath, ledger_type, status)

        for error in errors:
            print(f"{filepath} {ledger_type} {Fore.RED}[!]{Style.RESET_ALL} {error}")
    
    def validate(self):
        table = Table(show_header=True, header_style="magenta")
        table.add_column("Ledger", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Valid", justify="right")

        self.validate_gen_ledger(table)
        for entry in self._hub.get_entries():
            self.validate_ledger(entry, table)

        self.console.print(table)

    # ----- / -------------------- #

    def show_all_sum(self):
        table = Table(show_header=True, header_style="magenta")
        table.add_column("Ledger", style="cyan")
        table.add_column("Segment", style="green")
        table.add_column("Sum", justify="right")

        for entry in self._hub.get_entries():
            ledger = entry.ledger
            name = entry.name
            for seg in ledger.segments:
                sum = seg.get_sum()
                sign = "+" if sum >= 0 else ""
                table.add_row(name, seg.name, f"{sign}{sum}")
            table.add_row(
                    Text("─" * 10, style="dim"),
                    Text("─" * 14, style="dim"),
                    Text("─" * 8, style="dim"))
        self.console.print(table)

    # ----- / -------------------- #

    def check_gen_ledger(self, table: Table = None):
        gen_ledger = self._hub.get_gen_entry().ledger
        gen_name = self._hub.get_gen_entry().name

        ok = gen_ledger.checksum()
        status = "✅" if ok else "❌"
        table.add_row(gen_name, gen_ledger.general.name, status)

        table.add_row(
                    Text("─" * 10, style="dim"),
                    Text("─" * 16, style="dim"),
                    Text("─" * 6, style="dim"))

    def check_ledger(self, entry: LedgerEntry, table: Table = None):
        ledger = entry.ledger
        name = entry.name
        
        for seg in ledger.segments:
            ok = seg.checksum()
            status = "✅" if ok else "❌"
            table.add_row(name, seg.name, status)
        
        if ledger.total:
            ok = ledger.checksum()
            status = "✅" if ok else "❌"
            table.add_row(name, "Total", status)

        table.add_row(
                    Text("─" * 10, style="dim"),
                    Text("─" * 16, style="dim"),
                    Text("─" * 6, style="dim"))

    def check_all(self):
        table = Table(show_header=True, header_style="magenta")
        table.add_column("Ledger", style="cyan")
        table.add_column("Segment", style="green")
        table.add_column("Check", justify="right")

        self.check_gen_ledger(table)
        for entry in self._hub.get_entries():
            self.check_ledger(entry, table)
        
        self.console.print(table)

    # ----- 重新计算 -------------------- #

    def rebuild_month(self):
        for entry in self._hub.get_month_entries():
            entry.ledger.rebuild()
            print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<10} 完成ReBuild")
    
    def rebuild_life(self):
        life_entry = self._hub.get_life_entry()
        life_entry.ledger.rebuild()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {life_entry.name:<10} 完成ReBuild")

    def rebuild_collect(self):
        for entry in self._hub.get_collect_entries():
            entry.ledger.rebuild()
            print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<10} 完成ReBuild")

    def rebuild_gen(self):
        gen_entry = self._hub.get_gen_entry()
        gen_ledger = gen_entry.ledger
        gen_ledger.rebuild()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {gen_entry.name:<10} 完成ReBuild")

    def rebuild_all(self):
        self.rebuild_month()
        self.rebuild_life()
        self.rebuild_collect()
        self.rebuild_gen()

    # ----- 同步 -------------------- #

    def sync_month(self):
        life_ledger = self._hub.get_life_entry().ledger

        for entry in self._hub.get_month_entries():
            for month in self._get_month_list():
                month_sum = entry.ledger.get_month_sum(f"{entry.name}{month[1:]}")
                life_ledger.mod_segment_line_value(f"life.{month}", entry.name, month_sum)

    def sync_life(self):
        gen_ledger  = self._hub.get_gen_entry().ledger
        life_ledger = self._hub.get_life_entry().ledger

        for month in self._get_month_list():
            month_income  = life_ledger.get_month_income(month)
            month_expense = life_ledger.get_month_expense(month)
            month_balance = life_ledger.get_month_balance(month)

            gen_ledger.mod_life_segment_value(
                month,
                month_income,
                month_expense,
                month_balance
            )

    def sync_collect(self):
        gen_ledger = self._hub.get_gen_entry().ledger

        for entry in self._hub.get_collect_entries():
            ledger = entry.ledger
            total_value = ledger.get_total_value()
            gen_ledger.mod_collect_segment_value(entry.name, total_value)

    def sync_all(self):
        self.sync_month()
        self.sync_life()
        self.sync_collect()

    # ----- 更新 -------------------- #

    def update(self):
        print(f"{Fore.CYAN}[1/4]{Style.RESET_ALL} Update Month ...")
        self.rebuild_month()
        self.sync_month()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} Month 完成同步 \n")

        print(f"{Fore.CYAN}[2/4]{Style.RESET_ALL} Update Life ...")
        self.rebuild_life()
        self.sync_life()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} Life 完成同步 \n")

        print(f"{Fore.CYAN}[3/4]{Style.RESET_ALL} Update Collect ...")
        self.rebuild_collect()
        self.sync_collect()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} Collect 完成同步 \n")

        print(f"{Fore.CYAN}[4/4]{Style.RESET_ALL} Finish Update ⭐")
        self.rebuild_gen()

    # ----- END -------------------- #
