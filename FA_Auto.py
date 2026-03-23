#!/usr/bin/env python3
"""
FA_Test.py
FA 记账系统入口

职责：初始化账本，启动交互式 Shell。
命令实现全部在 cmd.py 的 FAShell 中。
"""

import LedgerHub as hub
from Shell import FAShell


def main():
    try:
        hub.init_ledger_hub()
    except Exception as e:
        print(f"[!] 账本加载失败: {e}")
        return

    FAShell().cmdloop()


if __name__ == "__main__":
    main()
