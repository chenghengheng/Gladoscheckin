#!/usr/bin/env python3
"""GLaDOS local browser-assisted check-in.

Uses a real, visible Chrome window and its persistent login session. The GLaDOS
page remains responsible for Cloudflare verification. Does not solve, forge, or
suppress verification; never sends session credentials to GitHub.
"""
import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit

SITE = "https://glados.cloud"
CHECKIN_PAGE = SITE + "/console/checkin"
STATE_HOME = Path.home() / ".gladoscheckin"
CHROME_PROFILE = STATE_HOME / "chrome-profile"
SUCCESS_STATE = STATE_HOME / "completed.json"
BEIJING = timezone(timedelta(hours=8))
BUTTON_PATTERN = re.compile(r"check[\s-]*in|签\s*到", re.IGNORECASE)


def today() -> str:
    """Service calendar date in UTC+8; independent of the Mac's time zone."""
    return datetime.now(BEIJING).date().isoformat()


def is_checkin_response(url: str, method: str) -> bool:
    """Ignore /api/user/checkin/challenge and unrelated responses."""
    parsed = urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == "glados.cloud"
        and parsed.path == "/api/user/checkin"
        and method.upper() == "POST"
    )


def classify_result(data: object) -> str:
    """Return success, repeat, cloudflare, or failure; never trust message alone."""
    if not isinstance(data, dict):
        return "failure"
    try:
        code = int(data.get("code", -2))
    except (TypeError, ValueError):
        return "failure"
    if code == 0:
        if "please checkin via" not in str(data.get("message", "")).lower():
            return "success"
    if code == 1:
        return "repeat"
    if code == 5 or "cloudflare verification failed" in str(data.get("message", "")).lower():
        return "cloudflare"
    return "failure"


def has_completed(date: str, path: Path = SUCCESS_STATE) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return isinstance(data, dict) and data.get("date") == date
    except (FileNotFoundError, ValueError, OSError):
        return False


def remember_completed(date: str, result: str, path: Path = SUCCESS_STATE) -> None:
    """Write only local completion metadata; credentials stay in browser profile."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    fd, temp_path = tempfile.mkstemp(prefix=".completed-", dir=str(path.parent))
    try:
        os.chmod(temp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump({"date": date, "result": result}, stream)
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def find_checkin_button(page):
    for button in page.locator("button").all():
        if not button.is_visible() or not button.is_enabled():
            continue
        name = (button.inner_text(timeout=1500) or "") + " " + (button.get_attribute("aria-label") or "")
        if BUTTON_PATTERN.search(name):
            return button
    return None


def run(mode: str, timeout: int, profile: Path = CHROME_PROFILE) -> int:
    if mode == "checkin" and has_completed(today()):
        print("今天已在本机记录为完成，跳过重复提交。")
        return 0
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("缺少 Playwright：先执行 python3 -m pip install playwright")
        return 2

    profile.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(profile.parent, 0o700)
    try:
        with sync_playwright() as playwright:
            # The actual Chrome browser handles its own supported verification UI.
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile),
                channel="chrome",
                headless=False,
                viewport={"width": 1280, "height": 850},
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                if mode == "login":
                    page.goto(CHECKIN_PAGE, wait_until="domcontentloaded", timeout=45000)
                    print("请在打开的 Chrome 中登录 GLaDOS，按官方要求完成验证。")
                    input("确认登录完成后，在终端按 Enter 保存浏览器登录态：")
                    return 0

                received = []
                pressed = [False]

                def on_response(response):
                    if not pressed[0] or not is_checkin_response(response.url, response.request.method):
                        return
                    try:
                        received.append(response.json())
                    except ValueError:
                        received.append(None)

                page.on("response", on_response)
                page.goto(CHECKIN_PAGE, wait_until="domcontentloaded", timeout=45000)
                print("已打开官方签到页；若需要登录或人机验证，请在浏览器中完成。")
                # Only click once. Never retry an ambiguous response or verification failure.
                for _ in range(120):
                    button = find_checkin_button(page)
                    if button:
                        pressed[0] = True
                        button.click(timeout=5000)
                        print("已点击一次官方签到按钮；等待页面返回签到结果。")
                        break
                    page.wait_for_timeout(500)
                else:
                    print("未找到可点击的签到按钮。请确认登录状态和页面结构。")
                    return 1

                for _ in range(timeout * 2):
                    if received:
                        result = classify_result(received[0])
                        if result in ("success", "repeat"):
                            remember_completed(today(), result)
                            print("签到成功。" if result == "success" else "服务端确认今天已签到。")
                            return 0
                        if result == "cloudflare":
                            print("服务端拒绝：Cloudflare 验证失败。未自动重试；请在浏览器中人工核对。")
                        else:
                            print("服务端返回失败或未知响应。未自动重试，请在官网核对。")
                        return 1
                    page.wait_for_timeout(500)
                print("没有观察到明确的签到响应，不再重复提交。请在官网登录页核对。")
                return 1
            finally:
                context.close()
    except (Exception, KeyboardInterrupt) as exc:
        # Playwright/Chrome errors contain environment details; no Cookie is printed.
        print(f"无法完成浏览器操作（{type(exc).__name__}）。确认安装 Chrome，且独立浏览器未被其他任务占用。")
        return 2


def main() -> int:
    parser = argparse.ArgumentParser(description="在本机真实 Chrome 中执行官方 GLaDOS 页面签到")
    parser.add_argument("mode", choices=["login", "checkin"], help="首次 login，之后 checkin")
    parser.add_argument("--timeout", type=int, default=120, help="等待服务器结果的秒数")
    args = parser.parse_args()
    if args.timeout < 1 or args.timeout > 300:
        parser.error("--timeout 必须在 1 到 300 秒之间")
    return run(args.mode, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
