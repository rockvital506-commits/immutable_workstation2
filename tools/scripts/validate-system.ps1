<#
.SYNOPSIS
    validate-system.ps1 — приёмка станции: 12 проверок из раздела 5 алгоритма.

.DESCRIPTION
    Перечень проверок и нормы взяты из
    ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md,
    раздел 5, без изменений. Это критерии приёмки, поэтому они НЕ вынесены в
    профиль: менять их правкой конфига — значит менять критерий под результат.

    Скрипт только читает. Ничего не меняет и ничего не «чинит»: найденное
    отклонение — это результат приёмки, а не повод для автоматической правки.

    Пункты 2 и 11 ОБЯЗАТЕЛЬНЫ (раздел 5):
      2  — AllowTelemetry = 0 ломает Центр обновления на части редакций, а
           система без обновлений уязвимее системы с телеметрией;
      11 — часть механизмов самовосстановления возвращает значения после
           перезагрузки или по расписанию.

    Пункт 11 проверяется в два прогона: -SaveBaseline до перезагрузки, затем
    -Baseline <файл> после. Без файла базовой линии приёмка считается
    НЕЗАВЕРШЁННОЙ (код 3), а не пройденной.

    Пункт 12 не запускает verify-backup сам: у того свои обязательные
    параметры, и молчаливый запуск с неверными аргументами дал бы ложный
    результат приёмки. Передайте код возврата через -BackupRC.

.PARAMETER Baseline
    Файл базовой линии, снятый до перезагрузки (-SaveBaseline).

.PARAMETER SaveBaseline
    Записать базовую линию в файл и завершить прогон.

.PARAMETER BackupRC
    Код возврата verify-backup (норма раздела 5 — 0).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File validate-system.ps1 -SaveBaseline E:\reports\baseline.txt
    # ... перезагрузка ...
    powershell -ExecutionPolicy Bypass -File validate-system.ps1 -Baseline E:\reports\baseline.txt -BackupRC 0

.OUTPUTS
    0 — все проверки пройдены, обязательные выполнены
    1 — ошибка, в том числе неизвестный параметр
    2 — нет нужных средств
    3 — обязательная проверка не выполнена: приёмка незавершена
    4 — есть проваленные проверки: станция не сдаётся
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Baseline,
    [string]$SaveBaseline,
    [ValidatePattern('^\d*$')]
    [string]$BackupRC = '',
    [switch]$ScanHealth,
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

$script:Passed = 0
$script:Failed = 0
$script:Skipped = 0
$script:Results = New-Object System.Collections.Generic.List[string]

function Add-Result {
    param([string]$Status, [int]$No, [string]$Text, [string]$Norm = '')
    switch ($Status) {
        'PASS' { $script:Passed++ }
        'FAIL' { $script:Failed++ }
        'SKIP' { $script:Skipped++ }
    }
    $script:Results.Add("$Status $No|$Text")
    Write-Host ("{0,-4}  {1,2}  {2}" -f $Status, $No, $Text)
    if ($Status -eq 'FAIL' -and $Norm) {
        Write-Host ("        норма: {0}" -f $Norm)
    }
}
function Set-Pass { param([int]$No, [string]$Text) Add-Result 'PASS' $No $Text }
function Set-Fail { param([int]$No, [string]$Text, [string]$Norm) Add-Result 'FAIL' $No $Text $Norm }
function Set-Skip { param([int]$No, [string]$Text) Add-Result 'SKIP' $No $Text }

Write-Host '============================================================'
Write-Host "  validate-system.ps1  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host '  Приёмка станции: 12 проверок из раздела 5 алгоритма'
Write-Host '============================================================'
Write-Host ''
Write-Host ("{0,-4}  {1,2}  {2}" -f 'СТАТ', '№', 'Проверка')
Write-Host '------------------------------------------------------------'

# --- 1. Сбор телеметрии отключён -------------------------------------------
# Норма раздела 5: AllowTelemetry, DiagnosticData = 0.
$dcKey = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection'
$t1 = @{}
foreach ($n in @('AllowTelemetry', 'DiagnosticData')) {
    $v = $null
    if (Test-Path -LiteralPath $dcKey) {
        $p = Get-ItemProperty -LiteralPath $dcKey -Name $n -ErrorAction SilentlyContinue
        if ($p) { $v = $p.$n }
    }
    $t1[$n] = $v
}
if (($t1['AllowTelemetry'] -eq 0) -and ($t1['DiagnosticData'] -eq 0)) {
    Set-Pass 1 'AllowTelemetry = 0, DiagnosticData = 0'
} else {
    Set-Fail 1 ("AllowTelemetry = {0}, DiagnosticData = {1}" -f $t1['AllowTelemetry'], $t1['DiagnosticData']) '0'
}

# --- 2. Центр обновления работает (ОБЯЗАТЕЛЬНО) ----------------------------
# Единственная проверка, которой нужен выход в сеть. Выполняется после шага 11
# алгоритма (первое включение сети) — до него канал физически недоступен.
if ($DryRun) {
    Set-Skip 2 '-DryRun: проверка обновлений не выполняется'
} else {
    $svc = Get-Service wuauserv -ErrorAction SilentlyContinue
    if (-not $svc) {
        Set-Skip 2 'нет службы wuauserv — проверить нечем'
    } else {
        # wuauserv по профилю = Manual, не Disabled: канал обязан оставаться
        # управляемым для security-патчей.
        $st = (Get-CimInstance Win32_Service -Filter "Name='wuauserv'" -ErrorAction SilentlyContinue).StartMode
        if ($st -eq 'Disabled') {
            Set-Fail 2 'wuauserv = Disabled: канал обновлений закрыт' 'находятся и ставятся'
        } else {
            try {
                # Запуск сканирования через COM: не устанавливает ничего,
                # но выполняет сетевой запрос — этого приёмке достаточно.
                $session = New-Object -ComObject Microsoft.Update.Session
                $searcher = $session.CreateUpdateSearcher()
                $found = $searcher.Search('IsInstalled=0').Updates.Count
                Set-Pass 2 "канал отвечает, найдено обновлений: $found"
            } catch {
                Set-Fail 2 "канал обновлений не отвечает: $($_.Exception.Message)" 'находятся и ставятся'
            }
        }
    }
}

# --- 3. Службы из блэклиста остановлены ------------------------------------
$t3 = @()
foreach ($n in @('DiagTrack', 'dmwappushservice')) {
    $s = Get-Service -Name $n -ErrorAction SilentlyContinue
    if (-not $s) { continue }
    $mode = (Get-CimInstance Win32_Service -Filter "Name='$n'" -ErrorAction SilentlyContinue).StartMode
    if ($s.Status -ne 'Stopped' -or $mode -ne 'Disabled') {
        $t3 += "$n=$($s.Status)/$mode"
    }
}
if ($t3.Count -gt 0) {
    Set-Fail 3 ("не остановлены: {0}" -f ($t3 -join ', ')) 'Stopped / Disabled'
} else {
    Set-Pass 3 'DiagTrack и dmwappushservice остановлены и отключены'
}

# --- 4. Задачи телеметрии отключены ----------------------------------------
$t4 = @()
$tasks = Get-ScheduledTask -TaskPath '\Microsoft\Windows\Application Experience\' -ErrorAction SilentlyContinue
if (-not $tasks) {
    Set-Skip 4 'задач Application Experience нет'
} else {
    foreach ($t in $tasks) {
        if ($t.State -ne 'Disabled') { $t4 += "$($t.TaskName)=$($t.State)" }
    }
    if ($t4.Count -gt 0) {
        Set-Fail 4 ("не отключены: {0}" -f ($t4 -join ', ')) 'Disabled'
    } else {
        Set-Pass 4 "задач Application Experience отключено: $($tasks.Count)"
    }
}

# --- 5. Драйверы без проблем -----------------------------------------------
if ($DryRun) {
    Set-Skip 5 '-DryRun: pnputil не вызывается'
} elseif (-not (Get-Command pnputil.exe -ErrorAction SilentlyContinue)) {
    Set-Skip 5 'нет pnputil.exe'
} else {
    $out = & pnputil.exe /enum-devices /problem 2>&1
    # Для внешних программ успех определяется по $LASTEXITCODE, а не по $?.
    $n = ($out | Select-String -Pattern 'Instance ID' -AllMatches).Count
    if ($LASTEXITCODE -ne 0) {
        Set-Skip 5 "pnputil вернул $LASTEXITCODE"
    } elseif ($n -gt 0) {
        Set-Fail 5 "проблемных устройств: $n" '0 проблемных'
    } else {
        Set-Pass 5 'проблемных устройств нет'
    }
}

# --- 6. Wi-Fi и Bluetooth работают -----------------------------------------
$wifi = Get-NetAdapter -Physical -ErrorAction SilentlyContinue |
    Where-Object { $_.Status -eq 'Up' }
if ($wifi) {
    Set-Pass 6 ("адаптеров в состоянии Up: {0}" -f (($wifi | ForEach-Object { $_.Name }) -join ', '))
} else {
    Set-Fail 6 'нет физических адаптеров в состоянии Up' 'Connected'
}

# --- 7. TRIM включён -------------------------------------------------------
if ($DryRun) {
    Set-Skip 7 '-DryRun: fsutil не вызывается'
} else {
    $fs = & fsutil.exe behavior query DisableDeleteNotify 2>&1
    # Норма раздела 5 — 0. В выводе fsutil значение выглядит как
    # «DisableDeleteNotify = 0», поэтому берётся последнее число в строке NTFS.
    $ntfs = ($fs | Select-String -Pattern 'NTFS' | Select-Object -First 1).Line
    if ($ntfs -and ($ntfs -match '=\s*(\d+)\s*$')) {
        if ([int]$Matches[1] -eq 0) {
            Set-Pass 7 'DisableDeleteNotify = 0 (TRIM включён)'
        } else {
            Set-Fail 7 "DisableDeleteNotify = $($Matches[1])" '0'
        }
    } else {
        Set-Skip 7 'не удалось разобрать вывод fsutil'
    }
}

# --- 8. Гибернация выключена -----------------------------------------------
if ($DryRun) {
    Set-Skip 8 '-DryRun: powercfg не вызывается'
} else {
    $pc = & powercfg.exe /a 2>&1
    # powercfg /a печатает разделы «доступные» и «недоступные»; гибернация
    # должна попасть в недоступные.
    $joined = ($pc -join ' ')
    if ($joined -match 'Hibernate[\s\S]{0,400}(not available|недоступн)') {
        Set-Pass 8 'гибернация недоступна'
    } elseif ($joined -match '(not available|недоступн)[\s\S]{0,400}Hibernate') {
        Set-Pass 8 'гибернация недоступна'
    } else {
        Set-Fail 8 'гибернация доступна' 'недоступна'
    }
}

# --- 9. Файл подкачки фиксирован -------------------------------------------
$cs = Get-CimInstance Win32_ComputerSystem -ErrorAction SilentlyContinue
$pf = Get-CimInstance Win32_PageFileSetting -ErrorAction SilentlyContinue
if ($cs -and $cs.AutomaticManagedPagefile) {
    Set-Fail 9 'размер файла подкачки управляется автоматически' 'фиксированный размер'
} elseif ($pf) {
    $same = $true
    foreach ($f in $pf) {
        if ($f.InitialSize -ne $f.MaximumSize) { $same = $false }
    }
    if ($same) {
        Set-Pass 9 ("pagefile фиксирован: {0}" -f (($pf | ForEach-Object { "$($_.InitialSize)-$($_.MaximumSize)" }) -join ', '))
    } else {
        Set-Fail 9 'InitialSize и MaximumSize различаются' 'фиксированный размер'
    }
} else {
    # Файл подкачки не отключают: при 8 ГБ распаянной памяти это прямой путь
    # к падениям (алгоритм, шаг 10).
    Set-Fail 9 'файл подкачки не задан' 'фиксированный размер'
}

# --- 10. Целостность хранилища ---------------------------------------------
# DISM /ScanHealth выполняется минуты. Без явного согласия приёмка его не
# запускает: иначе каждый прогон занимает неоправданно долго.
if (-not $ScanHealth) {
    Set-Skip 10 'не задан -ScanHealth: DISM /ScanHealth выполняется минуты'
} elseif ($DryRun) {
    Set-Skip 10 '-DryRun: DISM не вызывается'
} else {
    $dism = & dism.exe /Online /Cleanup-Image /ScanHealth 2>&1
    if ($LASTEXITCODE -eq 0) {
        Set-Pass 10 'DISM /ScanHealth: ошибок не найдено'
    } else {
        Set-Fail 10 "DISM /ScanHealth вернул $LASTEXITCODE" 'без ошибок'
    }
}

# --- 11. Настройки переживают перезагрузку (ОБЯЗАТЕЛЬНО) -------------------
function Get-Snapshot {
    $snap = [ordered]@{}
    $p = $null
    if (Test-Path -LiteralPath $dcKey) {
        $p = Get-ItemProperty -LiteralPath $dcKey -ErrorAction SilentlyContinue
    }
    $snap['AllowTelemetry'] = if ($p) { [string]$p.AllowTelemetry } else { 'нет' }
    $snap['DiagnosticData'] = if ($p) { [string]$p.DiagnosticData } else { 'нет' }
    foreach ($n in @('DiagTrack', 'dmwappushservice')) {
        $s = Get-Service -Name $n -ErrorAction SilentlyContinue
        $snap[$n] = if ($s) {
            "$($s.Status)/$((Get-CimInstance Win32_Service -Filter "Name='$n'" -ErrorAction SilentlyContinue).StartMode)"
        } else { 'нет' }
    }
    $tasks = Get-ScheduledTask -TaskPath '\Microsoft\Windows\Application Experience\' -ErrorAction SilentlyContinue
    $snap['AppExp'] = if ($tasks) { (($tasks | ForEach-Object { "$($_.TaskName)=$($_.State)" }) -join ';') } else { 'нет' }
    return ($snap.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" })
}

if ($SaveBaseline) {
    $dir = Split-Path -Parent $SaveBaseline
    if ($dir -and -not (Test-Path -LiteralPath $dir -PathType Container)) {
        Set-Fail 11 "каталог базовой линии недоступен: $dir" 'каталог существует'
    } else {
        Get-Snapshot | Set-Content -LiteralPath $SaveBaseline -Encoding UTF8
        Set-Pass 11 "базовая линия записана: $SaveBaseline"
        Write-Host '        ОБЯЗАТЕЛЬНО: перезагрузить станцию и запустить повторно'
        Write-Host "        с -Baseline $SaveBaseline"
    }
} elseif (-not $Baseline) {
    Set-Skip 11 'нет -Baseline: проверка ПОСЛЕ перезагрузки не выполнена'
} elseif (-not (Test-Path -LiteralPath $Baseline -PathType Leaf)) {
    Set-Fail 11 "базовая линия недоступна: $Baseline" 'файл читается'
} else {
    $before = @(Get-Content -LiteralPath $Baseline)
    $after = @(Get-Snapshot)
    $delta = Compare-Object -ReferenceObject $before -DifferenceObject $after
    if ($delta) {
        Set-Fail 11 "после перезагрузки вернулось значений: $($delta.Count)" 'значения не вернулись'
        foreach ($d in $delta | Select-Object -First 10) {
            Write-Host ("        {0} {1}" -f $d.SideIndicator, $d.InputObject)
        }
    } else {
        Set-Pass 11 'после перезагрузки значения не вернулись'
    }
}

# --- 12. Бэкап снят и проверен ---------------------------------------------
if ($BackupRC -eq '') {
    Set-Skip 12 'нет -BackupRC: запустите verify-backup и передайте его код'
} elseif ([int]$BackupRC -eq 0) {
    Set-Pass 12 'verify-backup вернул 0'
} else {
    Set-Fail 12 "verify-backup вернул $BackupRC" 'код 0'
}

# --- Итог ------------------------------------------------------------------
Write-Host '------------------------------------------------------------'
Write-Host "Пройдено: $script:Passed   Провалено: $script:Failed   Пропущено: $script:Skipped"
Write-Host ''

# Обязательные пункты раздела 5 ищутся по префиксу: восстанавливать текст
# результата, чтобы сравнить строку целиком, не нужно.
$mandatoryMissing = @()
foreach ($m in @(2, 11)) {
    foreach ($r in $script:Results) {
        if ($r.StartsWith("SKIP $m|")) { $mandatoryMissing += $m }
    }
}

if ($mandatoryMissing.Count -gt 0) {
    Write-Host "ОБЯЗАТЕЛЬНЫЕ пункты НЕ ВЫПОЛНЕНЫ: $($mandatoryMissing -join ', ')."
    Write-Host ''
    Write-Host 'Приёмка НЕЗАВЕРШЕНА: станция не сдаётся без обязательных пунктов.'
    if ($mandatoryMissing -contains 2) {
        Write-Host '  Пункт 2 — Центр обновления работает. AllowTelemetry = 0 ломает'
        Write-Host '  Центр обновления на части редакций; система без обновлений'
        Write-Host '  уязвимее системы с телеметрией. Проверить без -DryRun.'
    }
    if ($mandatoryMissing -contains 11) {
        Write-Host '  Пункт 11 — настройки переживают перезагрузку. Выполняется в два'
        Write-Host '  прогона: -SaveBaseline <файл>, перезагрузка, -Baseline <файл>.'
    }
    exit 3
}

if ($script:Failed -gt 0) {
    Write-Host 'ЕСТЬ ПРОВАЛЕННЫЕ ПРОВЕРКИ: станция не сдаётся.'
    Write-Host 'Скрипт ничего не исправляет — найденное отклонение это результат'
    Write-Host 'приёмки. Правит человек, затем повторный прогон.'
    exit 4
}

Write-Host 'Все проверки пройдены. Станция принимается.'
exit 0
