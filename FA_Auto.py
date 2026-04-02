#!/usr/bin/env python3

import os
import sys
from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine
from Shell import Shell
from __about__ import APP_VERSION, BUILD_DATE


def _get_base_dir() -> str:
    if getattr(sys, "frozen", False):
        # PyInstaller打包后 sys.frozen = True
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

banner = rf"""
---------------------------------------------------------
---------------------------------------------------------
--                                                     --
--       ____   __         __    _    _____  ___       --
--      | |_   / /\       / /\  | | |  | |  / / \      --
--      |_|   /_/--\     /_/--\ \_\_/  |_|  \_\_/      --
--                                                     --
--                                                     --
--   -----------------------------------------------   --
--                                                     --
--      Version: {Fore.CYAN}{APP_VERSION:<36}{Style.RESET_ALL}  --
--      Date:    {Fore.CYAN}{BUILD_DATE:<36}{Style.RESET_ALL}  --
--      Dir:     {_get_base_dir():<36}  --
--                                                     --
---------------------------------------------------------
---------------------------------------------------------
"""


# ======================================== #
#    Main Entry
# ======================================== #

def main():
    print(banner)

    # 切换工作目录
    base_dir = _get_base_dir()
    os.chdir(base_dir)

    # 创建实例
    hub = LedgerHub()
    engine = Engine(hub)

    # 初始化
    try:
        hub.init()
        engine.validate()
        print(f"\n--------------------------------------------------")
    except Exception as e:
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 账目加载失败: {e}")
        return
    
    # 启动Shell
    Shell(hub, engine).cmdloop()


if __name__ == "__main__":
    main()
