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

        life_ledger.mod_segment_line_value(f"life.{month}", "DGtler", total_dgtler)
        life_ledger.mod_segment_line_value(f"life.{month}", "KEEP", total_keep)
        life_ledger.mod_segment_line_value(f"life.{month}", "TB", total_tb)

def sync_life():
    sum_ledger = hub.get_sum_ledger()
    life_ledger = hub.get_ledger("life")

    for month in month_list:
        month_income = life_ledger.get_month_income(f"{month}")
        month_expense = life_ledger.get_month_expense(f"{month}")
        month_balance = life_ledger.get_month_balance(f"{month}")

        sum_ledger.mod_life_segment_value(month, month_income, month_expense, month_balance)

def sync_title():
    sum_ledger = hub.get_sum_ledger()
    dk_ledger = hub.get_ledger("dk")
    ns_ledger = hub.get_ledger("ns")
    travel_ledger = hub.get_ledger("travel")
    box_ledger = hub.get_ledger("box")

    total_dk = dk_ledger.get_total_value()
    total_ns = ns_ledger.get_total_value()
    total_travel = travel_ledger.get_total_value()
    total_box = box_ledger.get_total_value()

    sum_ledger.mod_title_segment_value("DK", total_dk)
    sum_ledger.mod_title_segment_value("NS", total_ns)
    sum_ledger.mod_title_segment_value("travel", total_travel)
    sum_ledger.mod_title_segment_value("BOX", total_box)
