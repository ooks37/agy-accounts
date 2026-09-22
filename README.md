# 🚀 agy-accounts (zh)

**High-Speed Visual Multi-Account Manager & Instant Switcher for Google Antigravity CLI**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Antigravity CLI](https://img.shields.io/badge/Antigravity-CLI%202.0-blue.svg)](https://antigravity.google)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-brightgreen.svg)]()
[![GitHub Stars](https://img.shields.io/github/stars/ooks37/agy-accounts?style=social)](https://github.com/ooks37/agy-accounts)

---

## 💡 Overview

**agy-accounts** (`zh`) is a native, zero-latency multi-account manager and switcher designed specifically for **Google Antigravity CLI (`agy`)**.

Switching Google accounts in terminal-based AI workflows typically requires re-authenticating through the browser, losing active conversational state, or relying on LLM tool-calling overhead. **agy-accounts** solves this with:
1. **Zero-AI Dependency**: Direct local binary execution (<0.01s).
2. **Context Preservation**: Seamlessly hot-reloads the active session with `--conversation <ID>`, preserving full conversation history, agent memory, and workspace state.
3. **Dual Interaction Modes**: Direct one-line command switching (`zh 1`, `zh 2`) and native interactive arrow-key selector with popup support (`zh ui`).
4. **Full Internationalization**: Comprehensive English and Chinese command support with East Asian Width (EAW) monospace pixel-perfect table alignment.

---

## 🌟 Key Features

- ⚡ **Zero-AI Execution (<10ms)**: Executes natively without querying LLMs or waiting for token generation.
- 🔄 **Context-Preserving Auto-Reload**: Automatically hooks into `history.jsonl` to extract active `conversationId`, seamlessly continuing your exact session without losing chat history.
- 🎯 **Interactive Arrow-Key Selector**: Navigate accounts using `↑` / `↓` and press `Enter` to switch and reload in real-time. In `agy` sessions, run `zh ui` to pop up a dedicated floating console window.
- 🌐 **Full Chinese & English Commands**: Supports both English (`zh switch 1`, `zh add`, `zh whoami`) and Chinese (`zh 切换 1`, `zh 添加`, `zh 状态`, `zh 帮助`) syntax, including Chinese account aliases (e.g. `zh 保存 主账号`).
- ➕ **One-Click Account Onboarding (`zh add`)**: Automatically clears temporary credentials, triggers browser authentication, captures newly issued OAuth tokens, and saves them to the encrypted local pool within seconds.
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
│    [+] Auto Add Account (run 'zh add')                         │
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

Commands can be invoked directly from your terminal (CMD/PowerShell) or inside the `agy` prompt line (via `!<command>`):

### 1. Instant Account Switching
```bash
zh 1                 # Switch to Account 1 and auto-reload session
zh 2                 # Switch to Account 2
zh work              # Switch by alias
zh switch 1          # Verbose switch syntax
zh 切换 1            # Chinese command syntax
```

### 2. Interactive Navigation (Arrow Keys)
```bash
zh                   # Open interactive picker in external terminal
zh ui                # Open interactive floating picker window from inside agy
zh 窗口              # Chinese command syntax
```

### 3. Add New Accounts
```bash
zh add               # Launch browser to log into a new Google account
zh add work          # Add new account with alias "work"
zh 添加 工作号       # Add with Chinese alias
```

### 4. Account Details & Status
```bash
zh whoami            # Check active email, auth method, and token expiration
zh 状态              # Chinese command syntax
```

### 5. Session Reload & Management
```bash
zh reload            # Hot reload session while preserving context
zh save main         # Save current active credentials with alias "main"
zh rm test           # Remove account "test" from local storage
```

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

## 🤝 Attribution & Acknowledgements

This project builds upon ideas and designs from the community. Special thanks and attribution to:

- **[pjpv/zcode-switch](https://github.com/pjpv/zcode-switch)**: The core UI layout philosophy, account library storage pattern, and instant switching ergonomics were inspired by `pjpv`'s `zcode-switch` / `Z·SWITCH` architecture.
- **[lllopic/agy-hud](https://github.com/lllopic/agy-hud)**: The statusline ecosystem and integration hooks that allow real-time awareness of account changes in Antigravity CLI.
- **[Google Antigravity](https://antigravity.google)**: The powerful agentic AI development platform.

---

## 📄 License

Distributed under the [MIT License](LICENSE).  
Copyright (c) 2026 ooks37.
