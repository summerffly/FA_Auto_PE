# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-30
# Description: FA系统核心引擎

from typing import List
from colorama import Fore, Style

import LedgerHub as hub
"""
from Ledger import (
    BaseLedger,
    LifeLedger,
    MonthLedger,
    TitleLedger,
    SumLedger
)
"""


# ======================================== #
#    全局变量
# ======================================== #

month_list: List[str] = []

# ======================================== #
#    引擎方法
# ======================================== #

def extract_month_list() -> List[str]:
    life_ledger = hub.get_ledger("life")

    for segment in life_ledger.segments:
        month_list.append(segment.month_no)
    return month_list


def sync_month():
    life_ledger = hub.get_ledger("life")
    dgtler_ledger = hub.get_ledger("dgtler")
    keep_ledger = hub.get_ledger("keep")
    tb_ledger = hub.get_ledger("tb")

    for month in month_list:
        total_dgtler = dgtler_ledger.get_month_total(f"DGtler.{month}")
        total_keep = keep_ledger.get_month_total(f"KEEP.{month}")
        total_tb = tb_ledger.get_month_total(f"TB.{month}")

        life_ledger.mod_segment_line(f"life.{month}", "DGtler", total_dgtler)
        life_ledger.mod_segment_line(f"life.{month}", "KEEP", total_keep)
        life_ledger.mod_segment_line(f"life.{month}", "TB", total_tb)
