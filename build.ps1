# builds dist\upf-calendar-exporter.exe, a single file with Python and every dependency bundled
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

uv sync --locked
uv run pyinstaller main.py `
    --onefile `
    --console `
    --clean `
    --noconfirm `
    --name upf-calendar-exporter `
    --icon src\baseline_today_white_48dp.ico
