<#
.SYNOPSIS
    tune-ssd-ram.ps1 — настройка под SSD и 8 ГБ ОЗУ (шаг 10 алгоритма).

.DESCRIPTION
    Соответствует шагу 10 станционного алгоритма
    (ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md):
    снизить износ накопителя и уложиться в память.

    ГЛАВНОЕ ОГРАНИЧЕНИЕ ШАГА 10: файл подкачки НЕ ОТКЛЮЧАТЬ. При 8 ГБ
    распаянной памяти это прямой путь к падениям. Ставится фиксированный
    размер, чтобы система не пересоздавала файл.

    Каждое действие печатает обратную команду ДО изменения. Автоматического
    отката нет: при сбое выводится обратная команда, решает человек.

.PARAMETER PagefileMB
    Фиксированный размер файла подкачки в МБ (одновременно InitialSize и
    MaximumSize — иначе размер не фиксирован). По умолчанию 4096.

.PARAMETER MinFreePct
    Норма свободного места на системном разделе, %. Шаг 10: не менее 10–15.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tune-ssd-ram.ps1 -DryRun
    powershell -ExecutionPolicy Bypass -File tune-ssd-ram.ps1 -PagefileMB 4096 -MinFreePct 15

.OUTPUTS
    0 — успех (или -DryRun), 1 — ошибка, 2 — нет нужных средств,
    4 — выполнено не всё.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateRange(512, 65536)]
    [int]$PagefileMB = 4096,
    [ValidateRange(1, 90)]
    [int]$MinFreePct = 10,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

# Лог в файл (CONVENTIONS.md, раздел 5)
$LogFile = Join-Path ([IO.Path]::GetTempPath()) "$($MyInvocation.MyCommand.Name).log"
try {
    Start-Transcript -LiteralPath $LogFile -Append -UseMinimalHeader -ErrorAction Stop | Out-Null
    Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action {
        try { Stop-Transcript | Out-Null } catch { }
    } | Out-Null
} catch {
    Write-Warning "Лог в файл не ведётся: $($_.Exception.Message)"
}

$script:Failed = 0
$script:Applied = 0

# Печатает обратную команду до изменения и выполняет скриптовый блок.
# Обратная команда обязана быть на экране ДО правки: если действие упадёт,
# искать её будет негде.
function Invoke-Tuning {
    param([string]$What, [string]$Rollback, [scriptblock]$Action)
    Write-Host "  $What"
    Write-Host "    откат: $Rollback"
    if ($DryRun) {
        Write-Host '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        & $Action
        $script:Applied++
        Write-Host '    применено'
    } catch {
        Write-Host "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Host "    ОТКАТ ВРУЧНУЮ: $Rollback"
        $script:Failed++
    }
}

Write-Host '============================================================'
Write-Host "  tune-ssd-ram.ps1  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host '  SSD + 8 ГБ ОЗУ (шаг 10 алгоритма)'
Write-Host '============================================================'

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $DryRun -and -not $isAdmin) {
    Write-Host ''
    Write-Host 'ОШИБКА: нет прав администратора — powercfg, fsutil и pagefile недоступны.'
    Write-Host 'Запустите PowerShell от администратора или используйте -DryRun.'
    exit 2
}

# --- 1. Гибернация и Fast Startup ------------------------------------------
# powercfg /hibernate off отключает и Fast Startup (шаг 10). Для SSD быстрый
# запуск вреден: hiberfil.sys пишется при каждом выключении.
Write-Host ''
Write-Host '=== 1. Гибернация и Fast Startup ==='
$hib = & powercfg.exe /a 2>&1
$hibOn = -not (($hib -join ' ') -match 'Hibernate[\s\S]{0,400}(not available|недоступн)')
if ($hibOn) {
    Invoke-Tuning -What 'powercfg /hibernate off (отключает и Fast Startup)' `
        -Rollback 'powercfg /hibernate on' `
        -Action {
            $out = & powercfg.exe /hibernate off 2>&1
            # Для внешних программ успех определяется по $LASTEXITCODE, не по $?.
            if ($LASTEXITCODE -ne 0) { throw ($out -join ' ') }
        }
} else {
    Write-Host '  гибернация уже недоступна — ничего не меняем'
}

# --- 2. TRIM ---------------------------------------------------------------
Write-Host ''
Write-Host '=== 2. TRIM ==='
$fs = & fsutil.exe behavior query DisableDeleteNotify 2>&1
$ntfs = ($fs | Select-String -Pattern 'NTFS' | Select-Object -First 1)
if ($ntfs -and ($ntfs.Line -match '=\s*(\d+)\s*$')) {
    if ([int]$Matches[1] -eq 0) {
        Write-Host '  DisableDeleteNotify = 0 (TRIM включён) — ничего не меняем'
    } else {
        Invoke-Tuning -What "DisableDeleteNotify = $($Matches[1]) -> 0" `
            -Rollback "fsutil behavior set DisableDeleteNotify $($Matches[1])" `
            -Action {
                $out = & fsutil.exe behavior set DisableDeleteNotify 0 2>&1
                if ($LASTEXITCODE -ne 0) { throw ($out -join ' ') }
            }
    }
} else {
    Write-Host '  не удалось разобрать вывод fsutil — проверить вручную'
    $script:Failed++
}

# --- 3. Файл подкачки ------------------------------------------------------
# НЕ ОТКЛЮЧАТЬ (шаг 10). Ставится фиксированный размер: иначе система
# пересоздаёт файл, и на SSD это лишняя запись.
Write-Host ''
Write-Host '=== 3. Файл подкачки ==='
Write-Host '  Файл подкачки НЕ отключается: при 8 ГБ распаянной памяти'
Write-Host '  это прямой путь к падениям (шаг 10 алгоритма).'
$cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
$pf = @(Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue)
$needFix = $false
if ($cs -and $cs.AutomaticManagedPagefile) {
    Write-Host '  размер управляется автоматически -> фиксированный'
    $needFix = $true
} elseif ($pf.Count -eq 0) {
    Write-Host '  файл подкачки не задан -> создаём фиксированный'
    $needFix = $true
} else {
    foreach ($f in $pf) {
        if ($f.InitialSize -ne $f.MaximumSize) {
            Write-Host "  $($f.Name): $($f.InitialSize)-$($f.MaximumSize) -> фиксированный"
            $needFix = $true
        }
    }
}
if ($needFix) {
    Invoke-Tuning -What "pagefile: фиксированный $PagefileMB МБ" `
        -Rollback 'Set-CimInstance -Query "SELECT * FROM Win32_ComputerSystem" -Property @{AutomaticManagedPagefile=$true}' `
        -Action {
            if ($cs.AutomaticManagedPagefile) {
                Set-CimInstance -InputObject $cs `
                    -Property @{ AutomaticManagedPagefile = $false } -ErrorAction Stop
            }
            $existing = @(Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue)
            if ($existing.Count -gt 0) {
                foreach ($e in $existing) {
                    Set-CimInstance -InputObject $e -Property @{
                        InitialSize = $PagefileMB
                        MaximumSize = $PagefileMB
                    } -ErrorAction Stop
                }
            } else {
                $sysDrive = $env:SystemDrive
                if (-not $sysDrive) { $sysDrive = 'C:' }
                New-CimInstance -ClassName Win32_PageFileSetting -Property @{
                    Name          = "$sysDrive\pagefile.sys"
                    InitialSize   = $PagefileMB
                    MaximumSize   = $PagefileMB
                } -ErrorAction Stop | Out-Null
            }
        }
} else {
    Write-Host "  pagefile уже фиксирован: $(($pf | ForEach-Object { $_.InitialSize }) -join ', ') МБ"
}

# --- 4. Свободное место ----------------------------------------------------
Write-Host ''
Write-Host '=== 4. Свободное место ==='
$sysDrive = $env:SystemDrive
if (-not $sysDrive) { $sysDrive = 'C:' }
$vol = Get-PSDrive -Name ($sysDrive -replace ':', '') -ErrorAction SilentlyContinue
if ($vol -and ($vol.Used + $vol.Free) -gt 0) {
    $pct = [int](100 * $vol.Free / ($vol.Used + $vol.Free))
    Write-Host "  $sysDrive свободно $pct% (норма не менее $MinFreePct%)"
    if ($pct -lt $MinFreePct) {
        Write-Host '    МАЛО МЕСТА: очистите кэш и временные файлы'
        $script:Failed++
    }
} else {
    Write-Host '  не удалось определить свободное место'
}

# --- 5. Кэш и временные файлы ----------------------------------------------
Write-Host ''
Write-Host '=== 5. Кэш и временные файлы ==='
# Шаг 10: «кэш браузера и временные файлы ограничить по размеру». Ограничение
# размера — настройка приложения; удаление без спроса может уничтожить данные
# текущего сеанса заказчика, поэтому скрипт ничего не удаляет.
Write-Host '  Кэш браузера и временные файлы скрипт НЕ удаляет: в них могут'
Write-Host '  быть данные текущего сеанса. Ограничение размера — настройка'
Write-Host '  приложения, выполняется по процедуре-инструкции.'
foreach ($d in @($env:TEMP, "$sysDrive\Windows\Temp")) {
    if ($d -and (Test-Path -LiteralPath $d -PathType Container)) {
        $sz = (Get-ChildItem -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum).Sum
        if ($null -eq $sz) { $sz = 0 }
        Write-Host ("  {0}: {1} МБ" -f $d, [int]($sz / 1MB))
    }
}

# --- Итог ------------------------------------------------------------------
Write-Host ''
Write-Host '============================================================'
Write-Host "Действий выполнено: $script:Applied   Провалено: $script:Failed"

if ($DryRun) {
    Write-Host ''
    Write-Host 'Ничего не изменено (-DryRun).'
    exit 0
}

if ($script:Failed -gt 0) {
    Write-Host ''
    Write-Host 'ВЫПОЛНЕНО НЕ ВСЁ. Автоматический откат НЕ выполняется:'
    Write-Host 'обратные команды — в выводе выше, по одной на действие.'
    exit 4
}

Write-Host ''
Write-Host 'Готово. Проверка: validate-system (пункты 7, 8, 9).'
exit 0
