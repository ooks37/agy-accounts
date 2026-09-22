# 🚀 agy-accounts (zh)

**High-Speed Visual Multi-Account Manager & Instant Switcher for Google Antigravity CLI**  
*Google Antigravity CLI 极速多账号可视化管理与秒级切换插件*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity CLI](https://img.shields.io/badge/Antigravity-CLI%202.0-blue.svg)](https://antigravity.google)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)]()
[![GitHub Stars](https://img.shields.io/github/stars/ooks37/agy-accounts?style=social)](https://github.com/ooks37/agy-accounts)

> [English Documentation](#-overview) | [🇨🇳 中文概述与使用指南](#-中文概述-chinese-overview)

---

> [!IMPORTANT]
> ### ⚠️ Critical: Using Commands Inside `agy` vs External Terminal
> - **Inside `agy` Chat Prompt (Antigravity CLI)**: You **MUST prefix all commands with `!`** (e.g., `!zh`, `!zh 1`, `!zh ui`, `!zh add`).  
>   *Why?* The `!` prefix is the Antigravity shell escape operator. It tells `agy` to run the command locally on your machine instead of passing it to the AI model as a conversation prompt. This guarantees **zero-latency (<10ms) execution without consuming any AI tokens**!
> - **In External Terminals (CMD / PowerShell)**: Run commands directly without `!` (e.g., `zh`, `zh 1`, `zh ui`).

---

## 💡 Overview

**agy-accounts** (`zh`) is a native, zero-latency multi-account manager and switcher designed specifically for **Google Antigravity CLI (`agy`)**.

Switching Google accounts in terminal-based AI workflows typically requires re-authenticating through the browser, losing active conversational state, or relying on LLM tool-calling overhead. **agy-accounts** solves this with:
1. **Zero-AI Dependency**: Direct local binary execution (<0.01s).
2. **Context Preservation**: Seamlessly hot-reloads the active session with `--conversation <ID>`, preserving full conversation history, agent memory, and workspace state.
3. **Dual Interaction Modes**: Direct one-line command switching (`!zh 1`, `!zh 2`) and native interactive arrow-key selector with popup support (`!zh ui`).
4. **Full Internationalization**: Comprehensive English and Chinese command support with East Asian Width (EAW) monospace pixel-perfect table alignment.

---

## 🌟 Key Features

- ⚡ **Zero-AI Execution (<10ms)**: Executes natively via local shell escape (`!`) without querying LLMs or waiting for token generation.
- 🔄 **Context-Preserving Auto-Reload**: Automatically hooks into `history.jsonl` to extract active `conversationId`, seamlessly continuing your exact session without losing chat history.
- 🎯 **Interactive Arrow-Key Selector**: Navigate accounts using `↑` / `↓` and press `Enter` to switch and reload in real-time. In `agy` sessions, run `!zh ui` to pop up a dedicated floating console window.
- 🌐 **Full Chinese & English Commands**: Supports both English (`!zh switch 1`, `!zh add`, `!zh whoami`) and Chinese (`!zh 切换 1`, `!zh 添加`, `!zh 状态`, `!zh 帮助`) syntax, including Chinese account aliases (e.g. `!zh 保存 主账号`).
- ➕ **One-Click Account Onboarding (`!zh add`)**: Automatically clears temporary credentials, triggers browser authentication, captures newly issued OAuth tokens, and saves them to the encrypted local pool within seconds.
- 🔐 **Native Credential Security**: Integrates directly with Windows Credential Manager (`gemini:antigravity`) and system keyrings. Tokens stay encrypted locally on your machine.

---

## 🖥️ Terminal Preview

```text
┌────────────────────────────────────────────────────────────────┐
│                     AGY Account Center (zh)                    │
├────────────────────────────────────────────────────────────────┤
│  Active: user_a@gmail.com [default]                            │
│                                                                │
│  Saved Accounts:                                               │
│    [1] default      user_a@gmail.com           ● [Active]      │
│    [2] work         user_b@gmail.com                           │
│    [+] Auto Add Account (run 'zh add' / '!zh add')             │
│                                                                │
│    Quick Commands (Auto-reloads session by default):           │
│    zh <index/alias>    Instant switch (e.g., zh 1 or zh work)  │
│    zh switch <index>   Switch account by number                │
│    zh ui (zh window)   Open interactive arrow-key picker       │
│    zh add [alias]      Add account via browser login           │
│    zh save <alias>     Save current active account as alias    │
│    zh reload           Hot-reload session with context intact  │
│    zh rm <alias>       Remove account from pool                │
│    zh whoami           Display active token & quota details    │
│                                                                │
│    * Tip: In agy prompt, prefix commands with ! (!zh 1)        │
└────────────────────────────────────────────────────────────────┘
```

---

## 📦 Quick Installation

### Option 1: PowerShell One-Liner (Recommended for Windows)

Open PowerShell and execute:

```powershell
irm https://raw.githubusercontent.com/ooks37/agy-accounts/main/install.ps1 | iex
```

### Option 2: Git Clone

```bash
git clone https://github.com/ooks37/agy-accounts.git "$HOME/.gemini/config/plugins/agy-accounts"
copy "$HOME/.gemini/config/plugins/agy-accounts/zh.cmd" "$LOCALAPPDATA/agy/bin/zh.cmd"
copy "$HOME/.gemini/config/plugins/agy-accounts/scripts/account_manager.py" "$LOCALAPPDATA/agy/bin/account_manager.py"
```

---

## 🚀 Usage Guide

| Inside `agy` Chat Prompt (Must prefix with `!`) | External Terminal (CMD / PowerShell) | Description |
| :--- | :--- | :--- |
| `!zh 1` or `!zh 2` | `zh 1` / `zh 2` | Instant switch account & auto-reload with context intact |
| `!zh switch 1` / `!zh 切换 1` | `zh switch 1` / `zh 切换 1` | Switch account by index or alias |
| `!zh ui` or `!zh 窗口` | `zh ui` / `zh 窗口` | Pop up native floating arrow-key (`↑`/`↓`/`Enter`) picker |
| `!zh add [alias]` / `!zh 添加` | `zh add [alias]` / `zh 添加` | One-click auto add new account via browser login |
| `!zh save <alias>` / `!zh 保存` | `zh save <alias>` / `zh 保存` | Save current active login as alias (supports Chinese) |
| `!zh whoami` / `!zh 状态` | `zh whoami` / `zh 状态` | Show active email, token expiration, and auth method |
| `!zh reload` / `!zh 重载` | `zh reload` / `zh 重载` | Manually reload session with 100% context preservation |
| `!zh rm <alias>` / `!zh 删除` | `zh rm <alias>` / `zh 删除` | Remove saved account from storage |
| `!zh` or `!zh 帮助` | `zh` / `zh help` | Display visual account dashboard |

---

## 🇨🇳 中文概述 (Chinese Overview)

> [!IMPORTANT]
> ### ⚠️ 重要提示：在 `agy` 会话对话框内使用必须加感叹号 `!`
> - **在 Antigravity CLI (`agy`) 聊天对话框中**：所有命令**必须以感叹号 `!` 开头**（例如输入 `!zh`、`!zh 1`、`!zh ui`、`!zh 添加`、`!zh 状态`）。  
>   *原理*：`!` 是 Antigravity 官方的系统命令转义符。带 `!` 的命令会直接由本地系统秒级执行，不会发送给大模型，因此**完全不消耗任何 AI Token，实现毫秒级即时响应**！如果直接在输入框输入 `zh 1`（不带 `!`），会被 `agy` 当成普通聊天提示词发给 AI。
> - **在普通外部终端中（PowerShell / CMD）**：直接输入 `zh`、`zh 1`、`zh ui` 即可，**无需**加 `!`。

### 💡 为什么需要 agy-accounts？
在日常使用 **Google Antigravity CLI (`agy`)** 进行高强度 AI 辅助编程时，用户经常需要使用多个 Google 账号（额度号/主力号/工作号）轮流作业。然而官方目前缺少多账号快速热切换机制，传统切换方式需要反复重新网页授权并导致当前的会话上下文（历史聊天、Memory）丢失。

**agy-accounts (`zh`)** 通过以下技术彻底解决痛点：
- ⚡ **零 AI 响应延迟 (<0.01s)**：配合 `!` 纯本地执行，无大模型 Token 损耗，秒级响应。
- 🔄 **100% 完整接续会话上下文**：切换后自动读取当前活动的 `conversationId` 并携带 `--conversation <ID>` 唤醒 `agy.exe`，历史对话与状态完全接续，工作不中断。
- 🎯 **双重交互体验**：既支持极简单行命令（`!zh 1` / `!zh 2`），又支持终端方向键（`↑`/`↓`）原生交互面板与独立弹窗（`!zh ui`）。
- 🌐 **全链路中文与中英文双语**：中文指令（`!zh 切换 1`、`!zh 添加`、`!zh 状态`、`!zh 帮助`）、中文别名（`主账号`、`公司`）全面支持，边框基于 East Asian Width 算法像素级对齐，拒绝乱码。
- ➕ **一键自动添加新账号 (`!zh add`)**：自动重置临时凭据并弹出登录，捕获授权后自动写库，10 秒内即可录入新号。
- 🔐 **系统原生钥匙串级安全**：直接与 Windows 凭据管理器 (`gemini:antigravity`) 对接，安全加密存放于本地。

### ⌨️ 常用中文指令速查表

| 在 `agy` 对话框内 (必须加 `!`) | 外部普通终端 (CMD / PowerShell) | 功能描述 |
| :--- | :--- | :--- |
| `!zh 1` 或 `!zh 切换 1` | `zh 1` / `zh switch 1` | 秒级切换到 1 号账号，自动重载并接续上下文 |
| `!zh 窗口` 或 `!zh ui` | `zh ui` / `zh 窗口` | 弹出原生方向键（`↑`/`↓`/`Enter`）交互选择小窗口 |
| `!zh 添加 [别名]` | `zh add [alias]` / `zh 添加` | 一键自动添加账号（唤起浏览器登录并存库） |
| `!zh 保存 <别名>` | `zh save <alias>` / `zh 保存` | 保存当前活跃账号为指定别名（支持中文） |
| `!zh 状态` | `zh whoami` / `zh 状态` | 查看当前活跃邮箱、Token 过期时间与鉴权方式 |
| `!zh 重载` | `zh reload` / `zh 重载` | 一键重新载入当前会话，上下文完整保留 |
| `!zh 删除 <别名>` | `zh rm <alias>` / `zh 删除` | 删除已保存的指定账号凭据 |
| `!zh` 或 `!zh 帮助` | `zh` / `zh help` | 查看可视化状态看板与已保存账号列表 |

---

## 🛠️ Architecture & Under the Hood

1. **Credential Hot-Swapping**:
   - Stores account credentials in `~/.gemini/accounts/<alias>.json`.
   - Uses the Win32 API `CredWriteW` for atomic credential updates to `gemini:antigravity`, enabling instant hot-reloading by statusline monitors (such as `agy-hud`).
2. **Context-Preserving Process Reload**:
   - Inspects `~/.gemini/antigravity-cli/history.jsonl` in reverse order to extract the current `conversationId`.
   - Spawns a replacement `agy.exe` instance with `--conversation <ID> --dangerously-skip-permissions -WorkingDirectory <CWD>`, ensuring 100% conversation history and memory continuity.
3. **Display Alignment Engine**:
   - Implements Unicode East Asian Width (EAW) calculations to accurately pad full-width CJK characters, ambiguous glyphs, and emojis for consistent border rendering across Windows Terminal, ConEmu, and standard consoles.

---

## 🤝 Attribution & Acknowledgements (项目致谢)

This project builds upon ideas and designs from the community. Special thanks and attribution to:

- **[pjpv/zcode-switch](https://github.com/pjpv/zcode-switch)**: The core UI layout philosophy, account library storage pattern, and instant switching ergonomics were inspired by `pjpv`'s `zcode-switch` / `Z·SWITCH` architecture. *(核心交互灵感与账号库管理架构借鉴致谢)*
- **[lllopic/agy-hud](https://github.com/lllopic/agy-hud)**: The statusline ecosystem and integration hooks that allow real-time awareness of account changes in Antigravity CLI. *(状态栏生态整合与热感知致谢)*
- **[Google Antigravity](https://antigravity.google)**: The powerful agentic AI development platform.

---

## 📄 License

Distributed under the [MIT License](LICENSE).  
Copyright (c) 2026 ooks37.
