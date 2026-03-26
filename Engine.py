# File:        Engine.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-26
# Description: FA系统核心引擎

import LedgerHub as hub


def test_sum():
    ledger = hub.get_sum_ledger()
    ledger.dump()
    print()
