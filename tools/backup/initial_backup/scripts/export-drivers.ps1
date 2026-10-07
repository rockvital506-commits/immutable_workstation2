<#
.SYNOPSIS
    export-drivers.ps1 — экспорт всех сторонних INF-драйверов системы.

.DESCRIPTION
    Выгружает драйверы из Driver Store в указанный каталог и строит манифест
    SHA256. Работает из-под работающей ОС (/Online) и из WinPE (/Image), потому
    что в WinPE ключ /Online завершается ошибкой 50.

    DISM выгружает только INF-пакеты: EXE/MSI-установщики вендоров в экспорт
    не попадают.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File export-drivers.ps1 -Destination T:\backup\drivers
    powershell -ExecutionPolicy Bypass -File export-drivers.ps1 -Destination T:\backup\drivers -WinImage C:\
    powershell -ExecutionPolicy Bypass -File export-drivers.ps1 -Destination T:\backup\drivers -WhatIf

.OUTPUTS
    0 — успех, 1 — ошибка, 2 — нет прав или нет DISM, 3 — целевой каталог недоступен.
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [string]$WinImage = '',
    [switch]$NoManifest
)

$ErrorActionPreference = 'Stop'

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
         ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error 'Требуются права администратора.'
    exit 2
}

$dism = Get-Command DISM.exe -ErrorAction SilentlyContinue
if (-not $dism) { Write-Error 'DISM.exe не найден в PATH.'; exit 2 }

if ($PSCmdlet.ShouldProcess($Destination, 'Создать каталог назначения')) {
    try { New-Item -ItemType Directory -Path $Destination -Force | Out-Null }
    catch { Write-Error "Не удалось создать каталог $Destination : $($_.Exception.Message)"; exit 3 }
}

if ($WinImage) {
    if (-not (Test-Path -LiteralPath $WinImage)) {
        Write-Error "Каталог Windows «$WinImage» не найден."
        exit 3
    }
    Write-Host "Режим: OFFLINE (WinPE), образ $WinImage"
    $args = @('/Image:' + $WinImage.TrimEnd('\'), '/Export-Driver', '/Destination:' + $Destination)
} else {
    Write-Host 'Режим: ONLINE (работающая ОС)'
    $args = @('/Online', '/Export-Driver', '/Destination:' + $Destination)
}

Write-Host ('Запуск: DISM ' + ($args -join ' '))
if ($PSCmdlet.ShouldProcess('DISM /Export-Driver', 'Выполнить экспорт драйверов')) {
    & DISM.exe @args | Tee-Object -Variable dismOut | Out-Null
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Write-Error "DISM завершился с кодом $code"
        $dismOut | Select-Object -Last 15 | ForEach-Object { Write-Host "  $_" }
        exit 1
    }
}

$count = @(Get-ChildItem -LiteralPath $Destination -Recurse -File -ErrorAction SilentlyContinue).Count
Write-Host "Выгружено файлов: $count"

if (-not $NoManifest -and $PSCmdlet.ShouldProcess($Destination, 'Построить манифест SHA256')) {
    $manifest = Join-Path $Destination 'manifest.sha256.csv'
    $stamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "path,sha256,size_bytes,modified,captured_at" | Set-Content -LiteralPath $manifest -Encoding UTF8
    Get-ChildItem -LiteralPath $Destination -Recurse -File |
        Where-Object { $_.Name -ne 'manifest.sha256.csv' } |
        ForEach-Object {
            $h = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            $rel = $_.FullName.Substring($Destination.Length).TrimStart('\')
            "$rel,$h,$($_.Length),$($_.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss')),$stamp" |
                Add-Content -LiteralPath $manifest -Encoding UTF8
        }
    Write-Host "Манифест: $manifest"
}

Write-Host 'Готово.'
exit 0
