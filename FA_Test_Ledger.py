#!/usr/bin/env python3

import sys
import shlex
import LedgerHub as hub
import Engine as engine


HELP_TEXT = """
╔══════════════════════════════════════════════════════╗
║              FA 记账系统  命令参考                    ║
╠══════════════════════════════════════════════════════╣
║ 查看                                                  ║
║   ls                     列出所有账本                 ║
║   show <账本>            显示账本全部内容              ║
║   show <账本> <月份>     显示指定月份区间              ║
║   summary                当前月收支汇总                ║
║   summary <月份>         指定月收支汇总                ║
║   summary all            所有月份收支汇总              ║
║   ts                     查看所有文件时间戳            ║
║                                                       ║
║ 搜索                                                  ║
║   find <账本> <关键字>   搜索包含关键字的行            ║
║                                                       ║
║ 增删改                                                ║
║   add <账本> <行号> <金额> <描述>   插入一条记录      ║
║   del <账本> <行号>                 删除一行           ║
║   mod val <账本> <行号> <新金额>    修改金额           ║
║   mod txt <账本> <行号> <新描述>    修改描述           ║
║   blank <账本> <行号>               插入空白行         ║
║                                                       ║
║ 校验 & 汇总                                           ║
║   check                  CheckSum 数学校验            ║
║   update                 将校验值写回 FA_SUM.md        ║
║                                                       ║
║ 备份                                                  ║
║   backup [目录]          备份所有账本                  ║
║   vbackup [目录]         校验备份文件一致性            ║
║                                                       ║
║ 其他                                                  ║
║   reload                 重新从磁盘同步所有账本        ║
║   help / ?               显示此帮助                   ║
║   q / quit / exit        退出                         ║
╚══════════════════════════════════════════════════════╝

账本别名在 FA_Auto_neo.ini 的 [Ledgers] 节中配置。
月份格式：YYYY.MM（例如 2024.03）
金额：正数为收入，负数为支出（例如 -200 或 200）
"""


def dispatch(parts: list[str]) -> bool:
    """
    解析并执行一条命令。
    返回 False 表示应退出程序。
    """
    if not parts:
        return True
    verb = parts[0].lower()

    # ── 退出 ────────────────────────────────
    if verb in ("q", "quit", "exit"):
        return False

    # ── 帮助 ────────────────────────────────
    if verb in ("help", "?", "h"):
        print(HELP_TEXT)

    if verb in ("test1"):
        engine.life_test()
    elif verb in ("test2"):
        engine.dgtler_test()
    elif verb in ("test3"):
        engine.dk_test()

    return True


def main():
    #if len(sys.argv) < 2:
    #    print("用法: python FA_Test.py <fa.md>")
    #    return

    #filepath = sys.argv[1]

    try:
        hub.init_ledger_hub()
    except Exception as e:
        print(f"解析失败: {e}")
        return

    while True:
        try:
            raw = input("\nCMD> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not raw:
            continue

        try:
            parts = shlex.split(raw)   # 支持带空格的描述用引号括起来
        except ValueError as e:
            print(f"[!] 解析命令出错: {e}")
            continue

        if not dispatch(parts):
            print("Bye!")
            break


if __name__ == "__main__":
    main()
