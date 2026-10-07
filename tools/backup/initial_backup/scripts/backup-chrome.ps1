<#
.SYNOPSIS
    backup-chrome.ps1 — резервная копия профиля Google Chrome.

.DESCRIPTION
    Копирует каталог User Data со всеми профилями и строит манифест SHA256.
    Отказывается работать при запущенном Chrome: базы SQLite в этом случае
    заблокированы и копия получается несогласованной.

    ВАЖНО: файл Default\Login Data зашифрован DPAPI в контексте учётной записи.
    На другой машине пароли из копии не расшифруются — для переноса паролей
    используйте штатный экспорт chrome://settings/passwords -> «Экспорт паролей».

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File backup-chrome.ps1 -Destination T:\backup\profiles
    powershell -ExecutionPolicy Bypass -File backup-chrome.ps1 -Destination T:\backup\profiles -WhatIf

.OUTPUTS
    0 — успех, 1 — ошибка, 3 — профиль не найден, 4 — Chrome запущен.
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [string]$ProfilePath = "$env:LOCALAPPDATA\Google\Chrome\User Data",
    [string]$Name = 'chrome',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ProfilePath -PathType Container)) {
    Write-Error "Профиль Chrome не найден: $ProfilePath"
    exit 3
}

$running = Get-Process -Name 'chrome' -ErrorAction SilentlyContinue
if ($running -and -not $Force) {
    Write-Error ('Chrome запущен (процессов: ' + @($running).Count + '). Закройте браузер или используйте -Force. ' +
                 'Копия при работающем браузере несогласованна.')
    exit 4
}
if ($running -and $Force) {
    Write-Warning 'Chrome запущен: копия может быть несогласованной (запрошен -Force).'
}

$stamp  = Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'
$target = Join-Path $Destination "$Name`_$stamp"

if ($PSCmdlet.ShouldProcess($target, 'Скопировать профиль Chrome')) {
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -Path (Join-Path $ProfilePath '*') -Destination $target -Recurse -Force
}

$files = @(Get-ChildItem -LiteralPath $target -Recurse -File -ErrorAction SilentlyContinue)
Write-Host ("Скопировано файлов: {0}, объём: {1:N1} МБ" -f $files.Count, (($files | Measure-Object Length -Sum).Sum / 1MB))

if ($PSCmdlet.ShouldProcess($target, 'Построить манифест SHA256')) {
    $manifest = Join-Path $target '_manifest.sha256.csv'
    'path,sha256,size_bytes,captured_at' | Set-Content -LiteralPath $manifest -Encoding UTF8
    foreach ($f in $files) {
        $h = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $rel = $f.FullName.Substring($target.Length).TrimStart('\')
        "$rel,$h,$($f.Length),$stamp" | Add-Content -LiteralPath $manifest -Encoding UTF8
    }
}

$note = Join-Path $target '_RESTORE_NOTES.md'
@"
# Восстановление профиля Chrome

Скопировано: $stamp
Источник: ``$ProfilePath``

## Порядок восстановления

1. Полностью закрыть Chrome (проверить: ``Get-Process chrome``).
2. Установить Chrome той же или более новой версии.
3. Заменить ``%LOCALAPPDATA%\Google\Chrome\User Data`` содержимым этой копии.
4. Запустить Chrome.

## Ограничение по паролям

Файл ``Default\Login Data`` зашифрован DPAPI в контексте исходной учётной записи.
На другой машине или в новом профиле пароли из него **не расшифруются**.
Перенос паролей выполняется штатным экспортом:
``chrome://settings/passwords`` -> «Экспорт паролей» -> CSV.

## Что входит в копию

``Default\Bookmarks``, ``History``, ``Cookies``, ``Web Data``, ``Preferences``,
``Extensions\``, ``Local Extension Settings\``, ``Local Storage\``,
``Sync Extension Settings\``, ``Local State``.
"@ | Set-Content -LiteralPath $note -Encoding UTF8

Write-Host "Копия: $target"
exit 0
