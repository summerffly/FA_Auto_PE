# File:        Shell.py
# Author:      summer@SummerStudio
# CreateDate:  2026-03-24
# LastEdit:    2026-03-25
# Description: 交互式命令行

import cmd
import shlex
from colorama import Fore, Style
import LedgerHub as hub
import Engine as engine


# ----- 工具函数 -------------------- #

def _parse(arg: str) -> list[str]:
    """把 arg 字符串安全拆分成 token 列表（支持引号包裹的描述）。"""
    try:
        return shlex.split(arg)
    except ValueError as e:
        raise ValueError(f"参数解析出错: {e}") from e


def _require(parts: list[str], n: int, usage: str):
    """检查参数数量，不足时抛 ValueError。"""
    if len(parts) < n:
        raise ValueError(f"参数不足，用法: {usage}")


def _print_section_summary(ledger, sec_name: str):
    sec = ledger.get_section(sec_name)
    if sec is None:
        print(f"  [!] 找不到区间: {sec_name}")
        return
    total = sec.calc_units_sum()
    sign  = "+" if total >= 0 else ""
    print(f"  {sec.name:<20} {sign}{total}")


def _print_ledger_summary(name: str):
    ledger = hub.get_ledger(name)
    print(f"\n── {name} ──")
    for sec in ledger.sections:
        total = sec.calc_units_sum()
        sign  = "+" if total >= 0 else ""
        print(f"  {sec.name:<20} {sign}{total}")


# ======================================== #
#    Shell
# ======================================== #

class Shell(cmd.Cmd):

    #intro = f"{Fore.CYAN}Start Shell{Style.RESET_ALL}"
    intro = rf" "
    prompt = "CMD > "

    # ----- 内部辅助 -------------------- #

    def _run(self, fn):
        try:
            fn()
        except ValueError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} {e}")
        except KeyError as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 找不到账本: {e}")
        except Exception as e:
            print(f"{Fore.RED}[!]{Style.RESET_ALL} 执行出错: {e}")

    def emptyline(self):
        pass

    def default(self, line):
        print(f"{Fore.RED}[!]{Style.RESET_ALL} 未知命令: {line.split()[0]}")

    # ----- 查看 -------------------- #

    def do_ls(self, _):
        """ls  列出所有已加载的账本"""
        def run():
            names = hub.list_ledgers()
            if not names:
                print("（无已加载账本）")
                return
            for name in names:
                ledger = hub.get_ledger(name)
                print(f"  {name:<12} {len(ledger.sections)} 个区间")
        self._run(run)

    def do_show(self, arg):
        """show <账本> [月份]  显示账本内容，月份可选（如 life.M03）"""
        def run():
            parts = _parse(arg)
            _require(parts, 1, "show <账本> [月份]")
            ledger = hub.get_ledger(parts[0])

            if len(parts) == 1:
                # 显示全部
                print(ledger.to_raw())
            else:
                # 显示指定 section
                sec = ledger.get_section(parts[1])
                if sec is None:
                    raise ValueError(f"找不到区间: {parts[1]}")
                print(sec.to_raw())
        self._run(run)

    def do_summary(self, arg):
        """summary [<账本> [月份|all]]  收支汇总；不带参数则汇总所有账本所有区间"""
        def run():
            parts = _parse(arg)

            if not parts:
                # 汇总所有
                for name in hub.list_ledgers():
                    _print_ledger_summary(name)
                return

            name = parts[0]
            ledger = hub.get_ledger(name)

            if len(parts) == 1 or parts[1].lower() == "all":
                _print_ledger_summary(name)
            else:
                _print_section_summary(ledger, parts[1])
        self._run(run)

    def do_ts(self, _):
        """ts"""
        def run():
            for name in hub.list_ledgers():
                ledger = hub.get_ledger(name)
                timestamp = ledger.tail.timestamp
                if timestamp:
                    print(f"  {name:<8} {timestamp}")
                else:
                    print(f"  {name:<8} NONE")
        self._run(run)

    # ----- 搜索 -------------------- #

    def do_find(self, arg):
        """find <账本> <关键字>  搜索包含关键字的行"""
        def run():
            parts = _parse(arg)
            _require(parts, 2, "find <账本> <关键字>")
            ledger  = hub.get_ledger(parts[0])
            keyword = parts[1]
            results = [ln for ln in ledger.all_lines() if keyword in ln.raw]
            if not results:
                print(f"  未找到包含 \"{keyword}\" 的行")
            for ln in results:
                print(f"  {ln.raw}")
        self._run(run)

    # ----- 修改 -------------------- #
    
    def do_mod(self, arg):
        """mod val|txt <账本> <区间> <行号> <新值>  修改金额(val)或描述(txt)"""
        def run():
            parts = _parse(arg)
            _require(parts, 6, "mod val|txt <账本> <区间> <行号> <新值>")
            mode, ledger_name, sec_name, idx_s, new_val = (
                parts[0], parts[1], parts[2], parts[3], parts[4]
            )
            ledger = hub.get_ledger(ledger_name)
            sec    = ledger.get_section(sec_name)
            if sec is None:
                raise ValueError(f"找不到区间: {sec_name}")
            idx = int(idx_s)
            if not (0 <= idx < len(sec.body_lines)):
                raise ValueError(f"行号越界 body_lines 共 {len(sec.body_lines)} 行")
            ln = sec.body_lines[idx]

            if mode == "val":
                ln.value = int(new_val)
                print(f"  已修改第 {idx} 行金额 → {new_val}")
            elif mode == "txt":
                ln.content = new_val
                print(f"  已修改第 {idx} 行描述 → {new_val}")
            else:
                raise ValueError(f"未知模式 \"{mode}\"，应为 val 或 txt")
        self._run(run)

    # ----- 校验 -------------------- #

    def do_check(self, arg):
        """check [ledger]"""
        def run():
            parts  = _parse(arg)
            names  = [parts[0]] if parts else hub.list_ledgers()
            ok_all = True
            for name in names:
                ledger = hub.get_ledger(name)
                for seg in ledger.segments:
                    ok = seg.validate_summary()
                    flag = f"{Fore.GREEN}OK{Style.RESET_ALL}" if ok else f"{Fore.RED}FAIL{Style.RESET_ALL}"
                    if not ok:
                        ok_all = False
                    print(f"  [{flag}] {name} / {seg.name}")
            if ok_all:
                print("  全部校验通过")
        self._run(run)

    # ----- 汇总重建 -------------------- #

    def do_rebuild(self, arg):
        """rebuild [ledger]"""
        def run():
            parts = _parse(arg)
            names = [parts[0]] if parts else hub.list_ledgers()
            for name in names:
                hub.get_ledger(name).rebuild_ledger()
                print(f"  {name} 重建完成")
        self._run(run)

    # ----- 保存 -------------------- #

    def do_save(self, arg):
        """save [ledger]"""
        def run():
            parts = _parse(arg)
            if parts:
                hub.save_ledger(parts[0])
                print(f"  {parts[0]} 已保存")
            else:
                hub.save_all()
                print("  所有账本已保存")
        self._run(run)

    # ----- 重载 -------------------- #

    def do_reload(self, arg):
        """reload [ledger]"""
        def run():
            parts = _parse(arg)
            if parts:
                hub.reload_ledger(parts[0])
                print(f"  {parts[0]} 已重载")
            else:
                hub.reload_all()
                print("  所有账本已重载")
        self._run(run)

    # ----- 测试入口 -------------------- #

    def do_dump(self, arg):
        """dump [ledger]"""
        def run():
            parts = _parse(arg)
            if parts and parts[0] == "sum":
                hub.get_sum_ledger().dump()
            elif parts:
                hub.get_ledger(parts[0]).dump()
        self._run(run)

    def do_repr(self, arg):
        """repr [ledger]"""
        def run():
            parts = _parse(arg)
            if parts:
                print(hub.get_ledger(parts[0]).__repr__())
        self._run(run)

    # ----- 退出 -------------------- #

    def do_q(self, _):
        return self._quit()

    def do_quit(self, _):
        return self._quit()

    def do_exit(self, _):
        return self._quit()

    def _quit(self):
        print("Bye!")
        return True
    
    # ----- END -------------------- #
