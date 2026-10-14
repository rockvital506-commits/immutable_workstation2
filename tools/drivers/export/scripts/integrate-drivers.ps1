<#
.SYNOPSIS
    integrate-drivers.ps1 — добавление драйверов в образ Windows или в систему.

.DESCRIPTION
    Парная версия integrate-drivers.sh. Охват намеренно узкий: ТОЛЬКО драйверы.
    Обновления Windows (Add-WindowsPackage) этим скриптом не ставятся — у них
    другие последствия ошибки: драйвер снимается через pnputil /delete-driver,
    обновление с SSU не удаляется вовсе. См. research/13-offline-updates.md.

    Режим -Image монтирует WIM, добавляет драйверы рекурсивно и отключает образ
    с фиксацией. Режим -Path работает с уже подключённым каталогом Windows.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File integrate-drivers.ps1 -Source E:\tools\drivers -Image D:\sources\install.wim

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File integrate-drivers.ps1 -Source E:\tools\drivers -Path E:\mount -WhatIf

.OUTPUTS
    0 — успех, 1 — ошибка, 2 — нет прав или DISM, 3 — источник/образ недоступны.
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Source,
    [string]$Image,
    [string]$Path,
    [int]$Index = 1,
    [switch]$KeepMount
)

$ErrorActionPreference = 'Stop'

# Лог в файл (CONVENTIONS.md, раздел 5). Register-EngineEvent на PowerShell.Exiting
# закрывает транскрипт и при штатном завершении, и при exit внутри скрипта.
$LogFile = Join-Path ([IO.Path]::GetTempPath()) "$($MyInvocation.MyCommand.Name).log"
try {
    Start-Transcript -LiteralPath $LogFile -Append -UseMinimalHeader -ErrorAction Stop | Out-Null
    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action {
        try { Stop-Transcript | Out-Null } catch { }
    } | Out-Null
} catch {
    Write-Warning "Лог в файл не ведётся: $($_.Exception.Message)"
}

if (-not (Test-Path -LiteralPath $Source -PathType Container)) {
    Write-Error "Каталог с драйверами не найден: $Source"
    exit 3
}
if ($Image -and $Path) {
    Write-Error '-Image и -Path одновременно не задаются: это разные цели'
    exit 1
}
if (-not $Image -and -not $Path) {
    Write-Error 'Нужен -Image или -Path'
    exit 1
}

$infFiles = @(Get-ChildItem -LiteralPath $Source -Filter '*.inf' -Recurse -File)
Write-Host "Источник драйверов: $Source"
Write-Host "Найдено INF: $($infFiles.Count)"
if ($infFiles.Count -eq 0) {
    Write-Error 'В каталоге нет ни одного .inf — добавлять нечего'
    exit 3
}

if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()
        ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error 'Требуются права администратора'
    exit 2
}

try {
    if ($Image) {
        if (-not (Test-Path -LiteralPath $Image -PathType Leaf)) {
            Write-Error "Образ не найден: $Image"
            exit 3
        }
        $mountDir = Join-Path ([IO.Path]::GetTempPath()) 'integrate-drivers-mount'
        Write-Host "Образ: $Image (индекс $Index)"
        Write-Host "Точка монтирования: $mountDir"

        if ($PSCmdlet.ShouldProcess($Image, 'Смонтировать образ')) {
            New-Item -ItemType Directory -Path $mountDir -Force | Out-Null
            Mount-WindowsImage -ImagePath $Image -Index $Index -Path $mountDir | Out-Null
        }
        if ($PSCmdlet.ShouldProcess($mountDir, 'Добавить драйверы рекурсивно')) {
            Add-WindowsDriver -Path $mountDir -Driver $Source -Recurse |
                Select-Object Driver, OriginalFileName, ClassName |
                Format-Table -AutoSize | Out-Host
        }
        if ($KeepMount) {
            Write-Host "-KeepMount: образ оставлен смонтированным в $mountDir"
            Write-Host "Завершить вручную: Dismount-WindowsImage -Path '$mountDir' -Save"
        } elseif ($PSCmdlet.ShouldProcess($mountDir, 'Отключить образ с фиксацией')) {
            Dismount-WindowsImage -Path $mountDir -Save | Out-Null
            Remove-Item -LiteralPath $mountDir -Force -ErrorAction SilentlyContinue
        }
    } else {
        if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
            Write-Error "Каталог не найден: $Path"
            exit 3
        }
        Write-Host "Цель: $Path"
        if ($PSCmdlet.ShouldProcess($Path, 'Добавить драйверы рекурсивно')) {
            Add-WindowsDriver -Path $Path -Driver $Source -Recurse |
                Select-Object Driver, OriginalFileName, ClassName |
                Format-Table -AutoSize | Out-Host
        }
    }
} catch {
    Write-Error $_.Exception.Message
    exit 1
}

Write-Host "Готово. INF в источнике: $($infFiles.Count)"
Write-Host 'Проверить: Get-WindowsDriver -Path <каталог> -All'
exit 0
