#!/usr/bin/env python3
"""Optional macOS launchd scheduling for local browser check-in.

Runs a visible Chrome check-in in the user's graphical login session. Does
not store cookies or secrets in the LaunchAgent. A sleeping Mac cannot check in.
"""
import argparse
import os
import plistlib
import subprocess
import sys
from pathlib import Path

LABEL = "local.gladoscheckin.browser"
PLIST = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
LOG_DIR = Path.home() / ".gladoscheckin"
CHECKIN_SCRIPT = Path(__file__).resolve().with_name("browser_checkin.py")


def build_plist(python_path: Path, script_path: Path, log_path: Path) -> dict:
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python_path), str(script_path), "checkin"],
        "WorkingDirectory": str(script_path.parent),
        "StartCalendarInterval": {"Hour": 9, "Minute": 30},
        "RunAtLoad": False,
        "StandardOutPath": str(log_path),
        "StandardErrorPath": str(log_path),
        "ProcessType": "Interactive",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="在 macOS 图形登录会话安装/卸载每天 09:30 的签到任务")
    parser.add_argument("action", choices=["install", "uninstall"])
    args = parser.parse_args()
    if sys.platform != "darwin":
        parser.error("仅支持 macOS；Linux/Windows 不支持此 LaunchAgent 安装器。")
    target = f"gui/{os.getuid()}"
    if args.action == "uninstall":
        subprocess.run(["launchctl", "bootout", target, str(PLIST)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        PLIST.unlink(missing_ok=True)
        print("已卸载 macOS 定时任务。浏览器登录资料仍保留在本机。")
        return 0

    LOG_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(LOG_DIR, 0o700)
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    if not CHECKIN_SCRIPT.is_file():
        print("未找到 browser_checkin.py。")
        return 2
    with PLIST.open("wb") as stream:
        plistlib.dump(build_plist(Path(sys.executable), CHECKIN_SCRIPT, LOG_DIR / "launchd.log"), stream)
    os.chmod(PLIST, 0o600)
    subprocess.run(["launchctl", "bootout", target, str(PLIST)],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    try:
        subprocess.run(["launchctl", "bootstrap", target, str(PLIST)], check=True)
    except subprocess.CalledProcessError:
        print(f"LaunchAgent 注册失败：请检查 {PLIST}，并确认已登录 macOS 图形桌面。")
        return 2
    print("已安装每天 09:30（Mac 系统时区）的本地浏览器签到任务。")
    print(f"日志：{LOG_DIR / 'launchd.log'}")
    print("需保持 Mac 醒着并可启动 Chrome；遇人机验证仍可能需要本人操作。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
