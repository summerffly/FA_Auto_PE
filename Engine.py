# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-31
# Description: FA系统核心引擎

from typing import List
from colorama import Fore, Style

from LedgerHub import LedgerHub


class Engine:

    def __init__(self, hub: LedgerHub):
        self._hub = hub

    # ======================================== #
    #    内部工具
    # ======================================== #

    def _get_month_list(self) -> List[str]:
        life_ledger = self._hub.get_ledger("life")
        return [seg.month_no for seg in life_ledger.segments]

    # ======================================== #
    #    同步方法
    # ======================================== #

    def sync_month(self):
        """同步月度账本数据到life账本"""
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
        """同步life账本数据到汇总账本"""
        month_list   = self._get_month_list()
        sum_ledger   = self._hub.get_sum_ledger()
        life_ledger  = self._hub.get_ledger("life")

        for month in month_list:
            month_income  = life_ledger.get_month_income(month)
            month_expense = life_ledger.get_month_expense(month)
            month_balance = life_ledger.get_month_balance(month)

            sum_ledger.mod_life_segment_value(
                month,
                month_income,
                month_expense,
                month_balance
            )

    def sync_title(self):
        """同步项目账本数据到汇总账本"""
        sum_ledger    = self._hub.get_sum_ledger()
        dk_ledger     = self._hub.get_ledger("dk")
        ns_ledger     = self._hub.get_ledger("ns")
        travel_ledger = self._hub.get_ledger("travel")
        box_ledger    = self._hub.get_ledger("box")

        total_dk     = dk_ledger.get_total_value()
        total_ns     = ns_ledger.get_total_value()
        total_travel = travel_ledger.get_total_value()
        total_box    = box_ledger.get_total_value()

        sum_ledger.mod_title_segment_value("DK",     total_dk)
        sum_ledger.mod_title_segment_value("NS",     total_ns)
        sum_ledger.mod_title_segment_value("travel", total_travel)
        sum_ledger.mod_title_segment_value("BOX",    total_box)

    def sync_all(self):
        """执行完整同步流程"""
        self.sync_month()
        self.sync_life()
        self.sync_title()

    def rebuild(self):
        """重建所有计算值"""
        sum_ledger = self._hub.get_sum_ledger()
        sum_ledger.rebuild_summary()

        for entry in self._hub._entries.values():
            ledger = entry.ledger
            if ledger:
                ledger.rebuild_ledger()

    def update(self):
        self.rebuild()
        self.sync_month()
        print(f"  [1/4] Month 已同步")
        self.rebuild()
        self.sync_life()
        print(f"  [2/4] Life 已同步")
        self.rebuild()
        self.sync_title()
        print(f"  [3/4] Title 已同步")
        self.rebuild()
        print(f"  [4/4] 重建完成")
