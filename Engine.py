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

def test_life():
    ledger = hub.get_ledger("life")

    print(ledger)
    print()
    
    ledger.dump()
    print()

    #print("=== Rebuild Markdown ===")
    #ledger.rebuild_all_summaries()
    #print(ledger.to_raw())

    #hub.save_ledger("life", "Test.md")

def test_dgtler():
    ledger = hub.get_ledger("dg")

    print(ledger)
    print()
    
    ledger.dump()
    print()

    #print("=== Rebuild Markdown ===")
    #ledger.rebuild_all_summaries()
    #print(ledger.to_raw())

    #hub.save_ledger("dg", "Test.md")

def test_dk():
    ledger = hub.get_ledger("dk")

    print(ledger)
    print()

    ledger.dump()
    print()

    #print("=== Rebuild Markdown ===")
    #ledger.rebuild_all_summaries()
    #print(ledger.to_raw())

    #hub.save_ledger("dk", "Test.md")
