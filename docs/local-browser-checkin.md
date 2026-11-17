# Mac 本地真实浏览器签到（可选）

适用：GitHub Actions 能访问账号，却在 POST 签到时收到 \`code=5 Cloudflare verification failed\`。云端 HTTP 请求无法可靠完成网站浏览器验证。该脚本在**自己的 Mac 上打开可见 Chrome**，进入官方签到页面，并点击一次签到按钮，由网站自身处理 Turnstile；如果出现人工验证，请自行完成。脚本不提供验证码绕过，不保证网站长期接受自动签到。

## 准备

需要安装 Google Chrome、Python 3.10+。在终端执行：

\`\`\`bash
git clone https://github.com/chenghengheng/Gladoscheckin.git
cd Gladoscheckin
python3 -m pip install -r requirements-local.txt
python3 browser_checkin.py login
\`\`\`

首次会打开一个独立 Chrome 配置文件，请在窗口中登录 \`https://glados.cloud\`，根据网站要求完成验证。确认已登录后回到终端按 Enter。登录状态保留在 Mac 本机 \`~/.gladoscheckin/chrome-profile\`，无需复制 Cookie 到 GitHub，也不应共享该目录。

## 测试签到

\`\`\`bash
python3 browser_checkin.py checkin
\`\`\`

- 仅点击一次官方 Check in 按钮，监听该页面发出的 POST \`/api/user/checkin\` 响应。
- 收到 \`code=0\` 或 \`code=1\` 时，在本机写入当天成功标记，避免再次提交。
- 收到 \`code=5\` 或响应超时，明确失败并停止，不会循环重试、伪造 Turnstile token 或把失败当成功。
- 若网站要求人机验证，需在打开的 Chrome 窗口中自行完成；如果页面布局变化，脚本也可能找不到按钮。
- Mac 必须保持唤醒且能够显示 Chrome；睡眠/关机时无法签到。首次验证成功后再考虑通过 macOS launchd 定时运行，暂未自动安装计划任务。

## 与 GitHub Actions 的关系

现有 GitHub Actions 工作流保持不变。**本地浏览器首次签到成功之前，不应停用原工作流或声称已恢复云端自动签到。** 两条路径可能在同一天执行，请以 \`code=0\` 或 \`code=1\` 及官网记录为准，尽量避免同时触发。如果决定长期使用本地浏览器，建议将原工作流改成只读监控或关闭其签到 schedule，防止反复触发被 Cloudflare 拒绝的请求。

如果 Chrome 提示浏览器 Profile 正在使用，请关闭这个独立的自动签到 Chrome 窗口后再试。不可将此 Profile 目录提交到 Git。
