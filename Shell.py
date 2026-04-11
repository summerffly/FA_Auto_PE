# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-07
# Description: 交互式命令行

import cmd
import shlex
from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine
from Viewer import Viewer


# ======================================== #
#    Shell
# ======================================== #

class Shell(cmd.Cmd):

    intro  = ""
    prompt = "[CMD] > "

    def __init__(self, hub: LedgerHub, engine: Engine, viewer: Viewer):
        super().__init__()
        self._hub = hub
        self._engine = engine
        self._viewer = viewer

    # ----- 内部辅助 -------------------- #

    def _parse(self, arg: str) -> list[str]:
        try:
            return shlex.split(arg)
        except ValueError as e:
            raise ValueError(f"参数解析出错: {e}") from e

    def _require(self, parts: list[str], m: int, n: int, usage: str):
        if len(parts) < m:
            raise ValueError(f"参数不足 用法: {usage}")
        elif len(parts) > n:
            raise ValueError(f"参数过多 用法: {usage}")
        else:
            return

    def _run(self, fn):
        try:
            print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
            fn()
            print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")
        except ValueError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} {e}")
        except KeyError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 找不到账目: {e}")
        except Exception as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 执行出错: {e}")

    def emptyline(self):
        pass

    def default(self, line):
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 未知命令: {line.split()[0]}")

    # ----- 查看 -------------------- #

    def do_view(self, arg):
        """view <ts|fa|sum>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "view <ts|fa|sum>")

            if parts[0] == "ts":
                self._viewer.view_ts()
            elif parts[0] == "fa":
                self._viewer.view_gen_ledger()
            elif parts[0] == "sum":
                self._viewer.view_all_sum()
            else:
                raise ValueError(f"未知参数: {parts[0]}")
        self._run(run)

    def do_print(self, arg):
        """print <账目别名>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "print <账目别名>")

            ledger = self._hub.get_entry(parts[0]).ledger
            print(ledger.to_raw())
        self._run(run)

    # ----- 操作 -------------------- #

    def do_validate(self, _):
        """validate"""
        def run():
            self._engine.validate()
        self._run(run)

    def do_check(self, _):
        """check"""
        def run():
            self._engine.check_all()
        self._run(run)

    def do_checksync(self, arg):
        """checksync"""
        def run():
            self._engine.checksync_all()
        self._run(run)

    def do_rebuild(self, arg):
        """rebuild <gen|life|month|collect>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "rebuild <gen|life|month|collect>")

            if parts[0] == "gen":
                self._engine.rebuild_gen()
            elif parts[0] == "life":
                self._engine.rebuild_life()
            elif parts[0] == "month":
                self._engine.rebuild_month()
            elif parts[0] == "collect":
                self._engine.rebuild_collect()
            else:
                raise ValueError(f"未知账目: {parts[0]}")
        self._run(run)

    def do_sync(self, arg):
        """sync <life|month|collect>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "sync <life|month|collect>")

            if parts[0] == "life":
                self._engine.sync_life()
                print(f"  Life 已同步")
            elif parts[0] == "month":
                self._engine.sync_month()
                print(f"  Month 已同步")
            elif parts[0] == "collect":
                self._engine.sync_collect()
                print(f"  Collect 已同步")
            else:
                raise ValueError(f"未知账目: {parts[0]}")
        self._run(run)

    def do_update(self, _):
        """update"""
        def run():
            self._engine.update()
        self._run(run)

    # ----- 重载 -------------------- #

    def do_reload(self, _):
        """reload"""
        def run():
            self._hub.reload_all()
        self._run(run)
        self._engine.validate()
        print(f"{Fore.CYAN}{'-'*50}{Style.RESET_ALL}")

    # ----- 保存 -------------------- #

    def do_save(self, _):
        """save"""
        def run():
            self._hub.save_all()
        self._run(run)

    def do_bakup(self, _):
        """bakup"""
        def run():
            self._hub.backup_all()
        self._run(run)

    # ----- Debug -------------------- #

    def do_dump(self, arg):
        """dump <账目别名>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "dump <账目别名>")

            if parts[0] in self._hub.get_alias_list():
                self._hub.get_entry(parts[0]).ledger.dump()
            else:
                raise ValueError(f"无效账目别名: {parts[0]}")
        self._run(run)

    def do_repr(self, arg):
        """repr <账目别名>"""
        def run():
            parts = self._parse(arg)
            self._require(parts, 1, 1, "repr <账目别名>")

            if parts[0] in self._hub.get_alias_list():
                print(self._hub.get_entry(parts[0]).ledger.__repr__())
            else:
                raise ValueError(f"无效账目别名: {parts[0]}")
        self._run(run)

    def do_test(self, _):
        """test"""
        def run():
            month_list = self._engine._get_month_list()
            print(f"Month List: {month_list}")
        self._run(run)

    # ----- 退出 -------------------- #

    def do_quit(self, _):
        """quit"""
        return self._quit()

    def do_q(self, _):
        """q"""
        return self._quit()

    def _quit(self):
        print("Bye!")
        return True
    
    # ----- END -------------------- #
