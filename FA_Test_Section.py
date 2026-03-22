#!/usr/bin/env python3

import sys
from Ledger import Ledger


def main():
    if len(sys.argv) < 2:
        print("用法: python main_ledger.py <fa.md>")
        return

    filepath = sys.argv[1]

    try:
        ledger = Ledger.parse_file(filepath)
    except Exception as e:
        print(f"解析失败: {e}")
        return

    ledger.dump()
    print()

    print("=== Section Names ===")
    for name in ledger.section_names():
        print(name)

    print()
    ledger.rebuild_section_summary("life.M02")
    ledger.rebuild_section_summary("life.M03")
    print("=== Rebuild Markdown ===")
    print(ledger.to_raw())

    ledger.save("life.M.md")


if __name__ == "__main__":
    main()
