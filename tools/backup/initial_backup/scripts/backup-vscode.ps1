<#
.SYNOPSIS
    backup-vscode.ps1 — резервная копия настроек и расширений VS Code.

.DESCRIPTION
    Копирует %APPDATA%\Code\User (settings.json, keybindings.json, snippets)
    и %USERPROFILE%\.vscode\extensions, формирует список расширений и манифест
    SHA256.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File backup-vscode.ps1 -Destination T:\backup\profiles
    powershell -ExecutionPolicy Bypass -File backup-vscode.ps1 -Destination T:\backup\profiles -WhatIf

.OUTPUTS
    0 — успех, 1 — ошибка, 3 — ни один каталог не найден.
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [string]$UserDir      = "$env:APPDATA\Code\User",
    [string]$ExtensionsDir = "$env:USERPROFILE\.vscode\extensions",
    [string]$Name = 'vscode'
)

$ErrorActionPreference = 'Stop'

$hasUser = Test-Path -LiteralPath $UserDir -PathType Container
$hasExt  = Test-Path -LiteralPath $ExtensionsDir -PathType Container
if (-not $hasUser -and -not $hasExt) {
    Write-Error "Не найдены ни $UserDir, ни $ExtensionsDir — VS Code не установлен?"
    exit 3
}

$stamp  = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$target = Join-Path $Destination "$Name`_$stamp"

if ($PSCmdlet.ShouldProcess($target, 'Скопировать настройки VS Code')) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    if ($hasUser) {
        Copy-Item -Path $UserDir -Destination (Join-Path $target 'User') -Recurse -Force
        Write-Host "Скопированы настройки: $UserDir"
    }
    if ($hasExt) {
        Copy-Item -Path $ExtensionsDir -Destination (Join-Path $target 'extensions') -Recurse -Force
        Write-Host "Скопированы расширения: $ExtensionsDir"
    }
}

if ($PSCmdlet.ShouldProcess($target, 'Сформировать список расширений')) {
    $list = Join-Path $target 'extensions-list.txt'
    $code = Get-Command code -ErrorAction SilentlyContinue
    if ($code) {
        & code --list-extensions --show-versions | Set-Content -LiteralPath $list -Encoding UTF8
        Write-Host "Список расширений получен от code --list-extensions"
    } elseif ($hasExt) {
        Get-ChildItem -LiteralPath $ExtensionsDir -Directory |
            Select-Object -ExpandProperty Name |
            Set-Content -LiteralPath $list -Encoding UTF8
        Write-Host 'CLI code недоступен: список собран по именам каталогов'
    }
}

$files = @(Get-ChildItem -LiteralPath $target -Recurse -File -ErrorAction SilentlyContinue)
if ($PSCmdlet.ShouldProcess($target, 'Построить манифест SHA256')) {
    $manifest = Join-Path $target '_manifest.sha256.csv'
    'path,sha256,size_bytes,captured_at' | Set-Content -LiteralPath $manifest -Encoding UTF8
    foreach ($f in $files) {
        $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $rel = $f.FullName.Substring($target.Length).TrimStart('\')
        "$rel,$h,$($f.Length),$stamp" | Add-Content -LiteralPath $manifest -Encoding UTF8
    }
}

Write-Host ("Файлов в копии: {0}, объём: {1:N1} МБ" -f $files.Count, (($files | Measure-Object Length -Sum).Sum / 1MB))
Write-Host "Копия: $target"
exit 0
