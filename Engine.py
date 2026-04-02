# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-01
# Description: FA系统核心引擎

from typing import List
from wcwidth import wcswidth
from colorama import Fore, Style

from Ledger import (
    BaseLedger,
    LifeLedger,
    MonthLedger,
    CollectLedger,
    GeneralLedger
)
from LedgerHub import LedgerHub


# ======================================== #
#    Engine
# ======================================== #

class Engine:

    def __init__(self, hub: LedgerHub):
        self._hub = hub

    # ----- 内部工具 -------------------- #

    def _get_month_list(self) -> List[str]:
        life_ledger = self._hub.get_ledger("life")
        return [seg.month_no for seg in life_ledger.segments]

    def _pad_right(self, text: str, width: int) -> str:
        w = wcswidth(text)
        if w >= width:
            return text
        return text + " " * (width - w)

    # ----- 校验 -------------------- #

    def validate(self):
        gen_ledger  = self._hub.get_gen_ledger()
        filepath = self._hub.get_filepath("fa")
        ledger_type = type(gen_ledger).__name__
        errors = gen_ledger.validate()

        for error in errors:
            print(f"{filepath:<14} {ledger_type:<15} {Fore.RED}[!]{Style.RESET_ALL} {error}")
        if not errors:
            print(f"  {filepath:<14} {ledger_type:<15} {Fore.GREEN}[✓]{Style.RESET_ALL}")

        for alias in self._hub.list_ledger_alias():
            ledger = self._hub.get_ledger(alias)
            filepath = self._hub.get_filepath(alias)
            ledger_type = type(ledger).__name__
            errors = ledger.validate()

            for error in errors:
                print(f"{filepath:<14} {ledger_type:<15} {Fore.RED}[!]{Style.RESET_ALL} {error}")
            if not errors:
                print(f"  {filepath:<14} {ledger_type:<15} {Fore.GREEN}[✓]{Style.RESET_ALL}")

    def check_ledger(self, alias: str):
        ledger = self._hub.get_ledger(alias)
        name = self._hub.get_name(alias)
        print(f"── {name} ──")
        for seg in ledger.segments:
            ok = seg.checksum()
            flag = (f"{Fore.GREEN}OK{Style.RESET_ALL}"
                    if ok else
                    f"{Fore.RED}FAIL{Style.RESET_ALL}")
            print(f"  [{flag}] {seg.name}")
        print("")

    # ----- / -------------------- #

    def show_ledger_sum(self, alias: str):
        ledger = self._hub.get_ledger(alias)
        name = self._hub.get_name(alias)
        print(f"── {name} ──")
        for seg in ledger.segments:
            total    = seg.calculate_sum()
            sign     = "+" if total >= 0 else ""
            seg_name = self._pad_right(seg.name, 15)
            print(f"  {seg_name} {sign}{total}")
        print("")

    def show_segment_sum(self, alias: str, seg_name: str):
        ledger = self._hub.get_ledger(alias)
        seg = ledger.get_segment(seg_name)
        if seg is None:
            print(f"  [!] 找不到区间: {seg_name}")
            return
        sum = seg.calculate_sum()
        sign  = "+" if sum >= 0 else ""
        seg_name = self._pad_right(seg.name, 15)
        print(f"  {seg_name} {sign}{sum}")

    # ----- 重新计算 -------------------- #

    def recalculate_month(self):
        for entry in self._hub.list_ledger_entry():
            ledger = entry.ledger
            if ledger and isinstance(ledger, MonthLedger):
                ledger.recalculate()
                print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<11} 完成ReCalculate")
    
    def recalculate_life(self):
        for entry in self._hub.list_ledger_entry():
            ledger = entry.ledger
            if ledger and isinstance(ledger, LifeLedger):
                ledger.recalculate()
                print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<11} 完成ReCalculate")

    def recalculate_collect(self):
        for entry in self._hub.list_ledger_entry():
            ledger = entry.ledger
            if ledger and isinstance(ledger, CollectLedger):
                ledger.recalculate()
                print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {entry.name:<11} 完成ReCalculate")

    def recalculate_gen(self):
        gen_ledger = self._hub.get_gen_ledger()
        gen_ledger.recalculate()
        print(f"  {Fore.GREEN}[✓]{Style.RESET_ALL} {self._hub.get_name('fa'):<11} 完成ReCalculate")

    def recalculate_all(self):
        """重建所有计算值"""
        self.recalculate_month()
        self.recalculate_life()
        self.recalculate_collect()
        self.recalculate_gen()

    # ----- 同步 -------------------- #

    def sync_month(self):
        """同步月度账目数据到life账目"""
        month_list = self._get_month_list()
        life_ledger   = self._hub.get_ledger("life")
        dgtler_ledger = self._hub.get_ledger("dgtler")
        keep_ledger   = self._hub.get_ledger("keep")
        tb_ledger     = self._hub.get_ledger("tb")

        for month in month_list:
            total_dgtler = dgtler_ledger.get_month_total(f"DGtler.{month}")
            total_keep   = keep_ledger.get_month_total(f"KEEP.{month}")
            total_tb     = tb_ledger.get_month_total(f"TB.{month}")

            life_ledger.mod_segment_line_value(f"life.{month}", "DGtler", total_dgtler)
            life_ledger.mod_segment_line_value(f"life.{month}", "KEEP",   total_keep)
            life_ledger.mod_segment_line_value(f"life.{month}", "TB",     total_tb)

    def sync_life(self):
        """同步life账目数据到汇总账目"""
        month_list   = self._get_month_list()
        gen_ledger   = self._hub.get_gen_ledger()
        life_ledger  = self._hub.get_ledger("life")

        for month in month_list:
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
        """同步项目账目数据到汇总账目"""
        gen_ledger    = self._hub.get_gen_ledger()
        dk_ledger     = self._hub.get_ledger("dk")
        ns_ledger     = self._hub.get_ledger("ns")
        travel_ledger = self._hub.get_ledger("travel")
        box_ledger    = self._hub.get_ledger("box")

        total_dk     = dk_ledger.get_total_value()
        total_ns     = ns_ledger.get_total_value()
        total_travel = travel_ledger.get_total_value()
        total_box    = box_ledger.get_total_value()

        gen_ledger.mod_collect_segment_value("DK",     total_dk)
        gen_ledger.mod_collect_segment_value("NS",     total_ns)
        gen_ledger.mod_collect_segment_value("travel", total_travel)
        gen_ledger.mod_collect_segment_value("BOX",    total_box)

    def sync_all(self):
        """执行完整同步流程"""
        self.sync_month()
        self.sync_life()
        self.sync_collect()

    # ----- 更新 -------------------- #

    def update(self):
        self.recalculate_month()
        self.sync_month()
        print(f"  ----- {Fore.CYAN}[1/4]{Style.RESET_ALL} Month 同步完成 -----")
        self.recalculate_life()
        self.sync_life()
        print(f"  ----- {Fore.CYAN}[2/4]{Style.RESET_ALL} Life 同步完成 -----")
        self.recalculate_collect()
        self.sync_collect()
        print(f"  ----- {Fore.CYAN}[3/4]{Style.RESET_ALL} Collect 同步完成 -----")
        self.recalculate_gen()
        print(f"  ----- {Fore.CYAN}[4/4]{Style.RESET_ALL} FA 更新完成 -----")

    # ----- END -------------------- #
