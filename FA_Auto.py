#!/usr/bin/env python3

from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine
from Shell import Shell
from __about__ import APP_VERSION, BUILD_DATE


banner = rf"""
--------------------------------------------------
     ____   __         __    _    _____  ___
    | |_   / /\       / /\  | | |  | |  / / \
    |_|   /_/--\     /_/--\ \_\_/  |_|  \_\_/

--------------------------------------------------
    Version: {Fore.CYAN}{APP_VERSION}{Style.RESET_ALL}
    Date: {Fore.CYAN}{BUILD_DATE}{Style.RESET_ALL}
--------------------------------------------------
"""

# ======================================== #
#    Main Entry
# ======================================== #

def main():
    print(banner)

    # 创建实例
    hub = LedgerHub()
    engine = Engine(hub)

    # 初始化
    try:
        hub.init()
        print(f"\n--------------------------------------------------\n")
        hub.validate()
        print(f"\n--------------------------------------------------")
    except Exception as e:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 账本加载失败: {e}")
        return
    
    # 启动Shell
    Shell(hub, engine).cmdloop()


if __name__ == "__main__":
    main()
