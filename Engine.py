"""
Engine.py
整个账本文件抽象
"""

import LedgerHub as hub


def life_test():
    ledger = hub.get_ledger("life")
    ledger.dump()
    print()

    print("=== Section Names ===")
    for name in ledger.section_names():
        print(name)

    print()
    ledger.rebuild_all_summaries()
    print("=== Rebuild Markdown ===")
    print(ledger.to_raw())

    hub.save_ledger("life", "Test.md")

def dgtler_test():
    ledger = hub.get_ledger("dg")
    ledger.dump()
    print()

    print("=== Section Names ===")
    for name in ledger.section_names():
        print(name)

    print()
    ledger.rebuild_all_summaries()
    print("=== Rebuild Markdown ===")
    print(ledger.to_raw())

    hub.save_ledger("dg", "Test.md")

def dk_test():
    ledger = hub.get_ledger("dk")
    ledger.dump()
    print()

    print("=== Section Names ===")
    for name in ledger.section_names():
        print(name)

    print()
    ledger.rebuild_all_summaries()
    print("=== Rebuild Markdown ===")
    print(ledger.to_raw())

    hub.save_ledger("dk", "Test.md")
