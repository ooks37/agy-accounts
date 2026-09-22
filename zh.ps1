$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
& python "$PSScriptRoot\.agents\skills\zh\scripts\account_manager.py" $args
