#!/usr/bin/env python3

from Shell import Shell
from colorama import Fore, Style

import LedgerHub as hub


VERSION = "Alpha"
DATE = "2026-03-30"
banner = rf"""
--------------------------------------------------
     ____   __         __    _    _____  ___
    | |_   / /\       / /\  | | |  | |  / / \
    |_|   /_/--\     /_/--\ \_\_/  |_|  \_\_/

--------------------------------------------------
    Version: {Fore.CYAN}{VERSION}{Style.RESET_ALL}
    Date: {Fore.CYAN}{DATE}{Style.RESET_ALL}
--------------------------------------------------
"""

# ======================================== #
#    Main Entry
# ======================================== #

def main():
    print(banner)

    try:
        hub.init_ledger_hub()
        hub.validate_ledger_hub()
    except Exception as e:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 账本加载失败: {e}")
        return

    Shell().cmdloop()


if __name__ == "__main__":
    main()
