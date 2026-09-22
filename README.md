# 🚀 agy-accounts (zh)

**Google Antigravity CLI 极速多账号可视化管理与秒级切换插件**  
*Native Visual Multi-Account Manager & Instant Switcher for Antigravity CLI*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity CLI](https://img.shields.io/badge/Antigravity-CLI%202.0-blue.svg)](https://antigravity.google)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)]()

---

## 🌟 核心特性 (Key Features)

- ⚡ **零 AI 依赖，本地极速执行 (<0.01s)**：输入指令瞬间完成切换，无需等待大模型 Token 生成与响应。
- 🔄 **自动重载并接续上下文 (Context Preservation)**：账号切换后自动重载 `agy` 会话，**保留全部对话历史、记忆与上下文**（基于 `--conversation <ID>` 原生接续），直接无缝接力当前任务。
- 🎯 **方向键原生交互面板 (Arrow-Key Selector)**：支持方向键 `↑` / `↓` 自由浏览选择，回车即切；在 `agy` 会话中输入 `zh ui` 可秒级唤出轻量独立交互窗口。
- 🌐 **全链路中文与中英双语支持**：中文指令（`zh 切换 1`、`zh 添加`、`zh 帮助`、`zh 状态`）、中文账号别名（如 `主账号`、`公司`）均完美支持，边框采用 East Asian Width 算法像素级对齐，杜绝乱码与错位。
- ➕ **一键自动添加新账号 (`zh add`)**：全自动清空临时钥匙串、唤起浏览器登录授权并回捕凭据存库，10 秒内即可将新 Google 账号纳入账号池。
- 🔐 **系统原生凭据级安全**：直接与 Windows 凭据管理器 (`gemini:antigravity`) / Keyring 对接，本地加密存储，绝不经过任何第三方服务器。

---

## 🖥️ 终端效果展示 (Preview)

```text
┌────────────────────────────────────────────────────────────────┐
│                     AGY 账号切换中心 (zh)                      │
├────────────────────────────────────────────────────────────────┤
│  当前活跃: user_a@gmail.com [default]                          │
│                                                                │
│  已保存账号列表:                                               │
│    [1] default      user_a@gmail.com           ● [当前使用]    │
│    [2] work         user_b@gmail.com                           │
│    [+] 自动添加新账号 (输入 zh add 或 zh 添加)                 │
│                                                                │
│    快捷指令 (全面支持中英文，默认自动重载):                    │
│    zh <序号/别名>      秒级切换 (例: zh 1 或 zh work)          │
│    zh 切换 <序号>      中文切换 (例: zh 切换 1)                │
│    zh 窗口 (zh ui)     唤起方向键独立交互窗口                  │
│    zh 添加 [别名]      一键自动添加账号 (唤起浏览器登录)       │
│    zh 保存 <别名>      保存当前账号为指定别名 (支持中文名)     │
│    zh 重载 (reload)    一键自动重新载入当前会话                │
│    zh 删除 <别名>      删除指定已保存账号                      │
│    zh 状态 (whoami)    查看当前账号详细认证信息                │
└────────────────────────────────────────────────────────────────┘
```

---

## 📦 一键安装 (Installation)

### 方式一：PowerShell 一键极速安装（推荐）

在 PowerShell 中直接运行以下命令即可全自动安装并配置环境变量：

```powershell
irm https://raw.githubusercontent.com/ooks37/agy-accounts/main/install.ps1 | iex
```

### 方式二：Git 本地克隆安装

```bash
git clone https://github.com/ooks37/agy-accounts.git "$HOME/.gemini/config/plugins/agy-accounts"
# 将命令快捷方式复制到系统路径
copy "$HOME/.gemini/config/plugins/agy-accounts/zh.cmd" "$LOCALAPPDATA/agy/bin/zh.cmd"
copy "$HOME/.gemini/config/plugins/agy-accounts/scripts/account_manager.py" "$LOCALAPPDATA/agy/bin/account_manager.py"
```

---

## 🚀 使用指南 (Usage)

在任何终端（CMD / PowerShell）或 `agy` 聊天框内均可直接执行：

### 1. 秒级切换账号
```bash
# 在外部终端：
zh 1                 # 切换到 1 号账号，自动重载会话
zh 2                 # 切换到 2 号账号
zh work              # 按别名切换
zh 切换 1            # 中文指令切换

# 在 agy 对话框中（使用 ! 执行系统命令）：
!zh 1
!zh 2
```

### 2. 原生方向键交互选择
```bash
zh                   # 在独立终端中打开交互式方向键选择器
zh ui                # 在 agy 会话内弹出独立方向键选择小窗口
zh 窗口              # 中文指令
```

### 3. 一键添加新账号
```bash
zh add               # 唤起浏览器登录新账号，自动生成别名
zh add 工作号        # 登录并指定别名为「工作号」
zh 添加              # 中文指令
```

### 4. 查看当前账号认证状态
```bash
zh whoami            # 查看当前活跃邮箱、Token 过期时间与鉴权方式
zh 状态              # 中文指令
```

### 5. 保存与删除账号
```bash
zh save 主账号       # 将当前已登录账号保存为别名「主账号」
zh rm 工作号         # 删除已保存的「工作号」
zh 删除 测试号       # 中文指令
```

---

## 🛠️ 架构与原理 (Architecture)

1. **凭据存储与热切换**：
   - 账号凭据安全隔离存储于 `~/.gemini/accounts/<别名>.json` 中。
   - 切换时通过 Win32 API `CredWriteW` 原生原子化写入 Windows 凭据管理器 `gemini:antigravity`，系统状态栏 (`agy-hud`) 瞬间热感知。
2. **会话接续与重载机制**：
   - 会话重载时，通过逆序解析 `~/.gemini/antigravity-cli/history.jsonl`，精确提取当前活动会话的 `conversationId`。
   - 携带 `--conversation <ID>` 参数重启 `agy.exe`，实现**零丢失保留全部会话上下文与历史流**。
3. **字符对齐引擎**：
   - 基于 Unicode East Asian Width 标准动态计算中英文字符、符号及 Emoji 宽度，确保跨平台控制台严格等宽对齐。

---

## 📄 开源许可 (License)

本项目基于 [MIT 协议](LICENSE) 开源。
欢迎 Star ⭐️ 与提交 PR！
