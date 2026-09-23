$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

$scriptPath = if (Test-Path "$PSScriptRoot\scripts\account_manager.py") {
    "$PSScriptRoot\scripts\account_manager.py"
} elseif (Test-Path "$PSScriptRoot\account_manager.py") {
    "$PSScriptRoot\account_manager.py"
} elseif (Test-Path "$env:USERPROFILE\.gemini\config\plugins\agy-accounts\scripts\account_manager.py") {
    "$env:USERPROFILE\.gemini\config\plugins\agy-accounts\scripts\account_manager.py"
} else {
    "account_manager.py"
}

python -u "$scriptPath" @args
