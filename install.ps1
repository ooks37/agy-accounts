# agy-accounts 一键安装与更新脚本 (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  正在安装 / 更新 agy-accounts (Antigravity 账号切换中心)  " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$pluginDir = "$env:USERPROFILE\.gemini\config\plugins\agy-accounts"
$binDir = "$env:LOCALAPPDATA\agy\bin"

# 确保目录存在
if (-not (Test-Path $pluginDir)) { New-Item -ItemType Directory -Path $pluginDir -Force | Out-Null }
if (-not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir -Force | Out-Null }

$repoRaw = "https://raw.githubusercontent.com/ooks37/agy-accounts/main"

$files = @(
    @{ Remote = "$repoRaw/plugin.json"; Local = "$pluginDir\plugin.json" },
    @{ Remote = "$repoRaw/commands/agy-accounts.md"; Local = "$pluginDir\commands\agy-accounts.md" },
    @{ Remote = "$repoRaw/commands/zh.md"; Local = "$pluginDir\commands\zh.md" },
    @{ Remote = "$repoRaw/skills/agy-accounts/SKILL.md"; Local = "$pluginDir\skills\agy-accounts\SKILL.md" },
    @{ Remote = "$repoRaw/skills/zh/SKILL.md"; Local = "$pluginDir\skills\zh\SKILL.md" },
    @{ Remote = "$repoRaw/scripts/account_manager.py"; Local = "$pluginDir\scripts\account_manager.py" },
    @{ Remote = "$repoRaw/scripts/account_manager.py"; Local = "$binDir\account_manager.py" },
    @{ Remote = "$repoRaw/zh.cmd"; Local = "$binDir\zh.cmd" },
    @{ Remote = "$repoRaw/zh.ps1"; Local = "$binDir\zh.ps1" }
)

foreach ($f in $files) {
    $parent = Split-Path -Path $f.Local -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Write-Host "  -> 下载: $($f.Local)" -ForegroundColor Gray
    try {
        Invoke-WebRequest -Uri $f.Remote -OutFile $f.Local -UseBasicParsing
    } catch {
        Write-Warning "下载失败: $($f.Remote)"
    }
}

Write-Host ""
Write-Host "✔ agy-accounts 安装成功！" -ForegroundColor Green
Write-Host "✔ 终端快捷指令: zh 或 zh 帮助" -ForegroundColor Green
Write-Host "✔ 快捷切换指令: zh 1 或 zh 2 (自动重载并保留上下文)" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Cyan
