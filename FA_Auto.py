#!/usr/bin/env python3

import LedgerHub as hub
from Shell import Shell
from colorama import Fore, Style


def main():
    try:
        hub.init_ledger_hub()
    except Exception as e:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 账本加载失败: {e}")
        return

    Shell().cmdloop()


if __name__ == "__main__":
    main()
