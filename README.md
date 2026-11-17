# Glados自动签到

## 本地浏览器签到（2026-11 补充）

当 GitHub Actions 返回 `code=5 Cloudflare verification failed` 时，已有 challenge nonce/proof 并不保证通过网站的人机验证。仓库新增 [Mac 本地真实浏览器签到实验方案](docs/local-browser-checkin.md)，使用自己的 Chrome 登录态，由网站自行完成验证；云端 Actions 无法因此自动获得验证能力。本地方案需先人工登录并实测，不保证完全无人值守。

## 食用方式：

### 注册一个GLaDOS的账号([注册地址](https://glados.space/landing/0A58E-NV28S-6U3QV-33VMG))

#### 我的邀请码：([0A58E-NV28S-6U3QV-33VMG](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

#### 我的优惠码（9折）：([DEVILSTORE](https://0a58e-nv28s-6u3qv-33vmg.glados.space)) 

### **Fork**本仓库

![图片加载失败](imgs/1.png)

### 添加**secret**

1. 跳转至自己的仓库的`Settings`->`Secrets and variables`->`Action`

2. 添加1个`repository secret`，命名为`GLADOS_COOKIES`，其值对应GLaDOS账号的cookie值中的有效部分（获取方式如下）

- 在GLaDOS的签到页面按`F12`

- 切换到`Network`页面下，刷新

![图片加载失败](imgs/2.png)

- 点击第一个选项卡后在`Request Headers`下找到`Cookie`，右键复制cookie的值即可

  > 参考格式：gld:sess=eyJ1c2xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxAwMH0=; gld:sess.sig=xJkOxxxxxxxxxxxxxxxtnM;

![图片加载失败](imgs/3.png)

- 多账号请在 `COOKIES` 中 添加多个 `cookies` 中间使用 `&`连接即可。（例如： `c1&c3&c3...`）

3. User-Agent（建议配置，GLaDOS 设备校验需要）\r\n\r\n- 添加 1 个 `repository secret`，命名为 `GLADOS_USER_AGENT`。\r\n- 在登录 GLaDOS 的浏览器 F12 → Console 执行 `navigator.userAgent`，将完整结果原样保存为 Secret。\r\n- 如果签到返回 `code 4 Automated check-in detected`，优先检查此项是否与登录浏览器一致。\r\n\r\n4. 手机推送（非必须）

- 添加1个`repository secret`，命名为`PUSHDEER_SENDKEY`，其值对应 PushDeer key: ([获取地址](https://www.pushdeer.com/product.html))。

### **star**自己的仓库

![图片加载失败](imgs/4.png)

## 文件结构

```shell
│  checkin.py	# 签到脚本
│
├─.github
│  └─workflows
│          gladosCheck.yml	# Actions 配置文件
```

## 更新日志

- **2026-01**: 重构代码，添加日志输出方便定位，支持新版网址。
- **2026-04**: 优化代码逻辑，优化日志输出。
- **2026-09**: 适配 GLaDOS 新版 Cookie 和设备校验；仅保留 GLaDOS 签到，取消自动兑换。


## 问题排查与定位\r\n- `glados.cloud` 使用 `gld:sess` / `gld:sess.sig` Cookie；签到请求还需要 `GLADOS_USER_AGENT` 与登录浏览器的平台保持一致。脚本不再执行自动兑换。
- GitHub Actions 默认启用安全诊断日志（`GLADOS_VERBOSE=true`）；若希望关闭，可添加 Secret `GLADOS_VERBOSE=false`。日志仅记录请求状态、challenge code 与是否存在 nonce/proof，不输出实际 Cookie、nonce 或 proof。
- `GLADOS_USER_AGENT` 请设置为实际登录 GLaDOS 的浏览器 `navigator.userAgent`，也支持 Repository variable。未配置时使用脚本默认值，但匹配 User-Agent 不能代替人机验证。
- 若日志为 `code=5 Cloudflare verification failed`，表示当次签到未完成。即使成功获取 challenge nonce/proof，也可能需要真实浏览器完成 Cloudflare/Turnstile 验证；建议浏览器人工补签，避免无意义地高频重试。
- 日志显示 `code=1` 只代表“当天已签到”，不能证明本次 Action 完成了新签到。
- 大家可以通过查询 actions 中的 running checkin 日志快速定位问题，有其他问题提交issue。

  <img width="1684" height="844" alt="image" src="https://github.com/user-attachments/assets/45348a5f-43e4-45f5-8fdf-ce84d343b30d" />

## 声明

本项目不保证稳定运行与更新, 因GitHub相关规定可能会删库, 请注意备份







