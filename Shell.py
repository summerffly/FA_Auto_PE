# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-04-02
# Description: 交互式命令行

import cmd
import shlex
from colorama import Fore, Style

from LedgerHub import LedgerHub
from Engine import Engine


# ======================================== #
#    工具函数
# ======================================== #

def _parse(arg: str) -> list[str]:
    """把arg字符串安全拆分成token列表"""
    try:
        return shlex.split(arg)
    except ValueError as e:
        raise ValueError(f"参数解析出错: {e}") from e


def _require(parts: list[str], n: int, usage: str):
    """检查参数数量"""
    if len(parts) < n:
        raise ValueError(f"参数不足 用法: {usage}")


# ======================================== #
#    Shell
# ======================================== #

class Shell(cmd.Cmd):

    intro  = ""
    prompt = "[CMD] > "

    def __init__(self, hub: LedgerHub, engine: Engine):
        super().__init__()
        self._hub    = hub
        self._engine = engine

    # ----- 内部辅助 -------------------- #

    def _run(self, fn):
        try:
            print(f"--------------------------------------------------")
            fn()
            print(f"--------------------------------------------------")
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

    def do_ts(self, _):
        """ts"""
        def run():
            gen_ledger = self._hub.get_gen_ledger()
            filepath   = self._hub.get_filepath("fa")
            timestamp  = gen_ledger.tail.timestamp
            print(f"  {filepath:<14} {timestamp if timestamp else 'NONE'}")

            for alias in self._hub.list_ledger_alias():
                ledger    = self._hub.get_ledger(alias)
                filepath  = self._hub.get_filepath(alias)
                timestamp = ledger.tail.timestamp
                print(f"  {filepath:<14} {timestamp if timestamp else 'NONE'}")
        self._run(run)

    def do_ls(self, _):
        """ls"""
        def run():
            alias_list = self._hub.list_ledger_alias()
            for alias in alias_list:
                ledger = self._hub.get_ledger(alias)
                name   = self._hub.get_name(alias)
                print(f"── {name} ──")
                for seg in ledger.segments:
                    print(f"  {seg.name}")
                print("")
        self._run(run)

    def do_print(self, arg):
        """print <账目别名> [分段名]"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "print <账目别名> [分段名]")
            ledger = self._hub.get_ledger(parts[0])

            if len(parts) == 1:
                print(ledger.to_raw())
            else:
                seg = ledger.get_segment(parts[1])
                if seg is None:
                    raise ValueError(f"找不到区间: {parts[1]}")
                print(seg.to_raw())
        self._run(run)

    def do_sum(self, arg):
        """sum [<账目别名> [分段名]]"""
        def run():
            parts = _parse(arg)

            if not parts:
                for alias in self._hub.list_ledger_alias():
                    self._engine.show_ledger_sum(alias)
                return

            alias = parts[0]
            ledger = self._hub.get_ledger(alias)

            if len(parts) == 1:
                self._engine.show_ledger_sum(alias)
            else:
                self._engine.show_segment_sum(alias, parts[1])
        self._run(run)

    # ----- 校验 -------------------- #

    def do_check(self, arg):
        """check [账目]"""
        def run():
            parts = _parse(arg)
            if parts:
                alias = parts[0]
                if alias not in self._hub.list_ledger_alias() and alias != "fa":
                    raise ValueError(f"无效的账目别名: {alias}")
                alias_list = [alias]
            else:
                alias_list = self._hub.list_ledger_alias()

            for alias in alias_list:
                self._engine.check_ledger(alias)
        self._run(run)


    # ----- 操作 -------------------- #

    def do_recalc(self, arg):
        """recalc <month|life|collect|gen>"""
        def run():
            parts = _parse(arg)

            if not parts:
                self._engine.recalculate_all()
            elif parts[0] == "month":
                self._engine.recalculate_month()
            elif parts[0] == "life":
                self._engine.recalculate_life()
            elif parts[0] == "collect":
                self._engine.recalculate_collect()
            elif parts[0] == "gen":
                self._engine.recalculate_gen()
            else:
                raise ValueError(f"未知账目: {parts[0]}")
        self._run(run)

    def do_sync(self, arg):
        """sync <month|life|collect>"""
        def run():
            parts = _parse(arg)
            #_require(parts, 1, "sync <month|life|collect>")

            if not parts:
                self._engine.sync_all()
                print(f"  所有账目已同步")
            elif parts[0] == "month":
                self._engine.sync_month()
                print(f"  Month 已同步")
            elif parts[0] == "life":
                self._engine.sync_life()
                print(f"  Life 已同步")
            elif parts[0] == "collect":
                self._engine.sync_collect()
                print(f"  Collect 已同步")
            else:
                raise ValueError(f"未知同步目标: {parts[0]}")
        self._run(run)

    def do_update(self, _):
        """update"""
        def run():
            self._engine.update()
        self._run(run)

    def do_save(self, arg):
        """save"""
        def run():
            self._hub.save_all()
        self._run(run)

    def do_reload(self, arg):
        """reload"""
        def run():
            self._hub.reload_all()
            print("  所有账目已重载")
        self._run(run)

    # ----- Debug -------------------- #

    def do_dump(self, arg):
        """dump [账目]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "fa":
                self._hub.get_gen_ledger().dump()
            elif parts:
                self._hub.get_ledger(parts[0]).dump()
            else:
                for name in self._hub.list_ledger_alias():
                    print(f"\nLedger: {name}")
                    self._hub.get_ledger(name).dump()
        self._run(run)

    def do_repr(self, arg):
        """repr [账目]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "fa":
                print(self._hub.get_gen_ledger().__repr__())
            elif parts:
                print(self._hub.get_ledger(parts[0]).__repr__())
            else:
                name = self._hub.get_name("fa")
                print(f"\n── {name} ──")
                print(self._hub.get_gen_ledger().__repr__())
                for alias in self._hub.list_ledger_alias():
                    name = self._hub.get_name(alias)
                    print(f"\n── {name} ──")
                    print(self._hub.get_ledger(alias).__repr__())
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
