---
name: agy-accounts
description: Manage, list, and switch multiple Antigravity accounts within the terminal or chat session.
---

# Antigravity Multi-Account Manager

This skill allows listing, saving, and switching between multiple Antigravity (AGY) accounts directly inside the terminal.

## Commands

Run the following commands using the terminal execution tool:

- **查看当前活动账号**: `agy-switch whoami`
- **查看所有已保存账号**: `agy-switch list`
- **保存当前账号**: `agy-switch save <别名>`
- **快速切换账号**: `agy-switch use <别名>`
- **删除保存的账号**: `agy-switch remove <别名>`

When the user requests an account switch or inspection, run the corresponding `agy-switch` command and report the output clearly.
