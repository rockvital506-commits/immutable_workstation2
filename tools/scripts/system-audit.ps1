<#
.SYNOPSIS
    system-audit.ps1 — дамп состояния Windows ДО и ПОСЛЕ изменений.

.DESCRIPTION
    Парная версия system-audit.sh. Скрипт НИЧЕГО не меняет.

    Это не отчёт «для галочки»: по research/06-services-blocklist.md исходные
    значения фиксируются дампом на первом шаге, и БЕЗ НЕГО ОТКАТ НЕВОЗМОЖЕН.
    Поэтому дамп обязателен до применения блокировок, а не после.

    Снимает: службы, задачи планировщика, Run/RunOnce/Active Setup,
    IFEO, политики HKLM, WMI-подписки, provisioned-пакеты. Раздел «Сетевые
    соединения» помечен информационным и в сравнении не участвует: соединения
    меняются между снятиями даже на неизменённой системе.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File system-audit.ps1 -OutDir E:\reports
    powershell -ExecutionPolicy Bypass -File system-audit.ps1 -OutDir E:\reports -Diff E:\reports\system-audit-20261014-1200.txt

.OUTPUTS
    0 — успех, 1 — ошибка, 2 — нет нужных средств, 3 — каталог или файл
    недоступны, 4 — найдены отклонения при сравнении.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [ValidateScript({ Test-Path -LiteralPath $_ -PathType Container })]
    [string]$OutDir = (Get-Location).Path,
    [string]$Diff
)

$ErrorActionPreference = 'Continue'

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

if ($Diff -and -not (Test-Path -LiteralPath $Diff -PathType Leaf)) {
    Write-Error "Нет файла для сравнения: $Diff"
    exit 3
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = Join-Path $OutDir "system-audit-$stamp.txt"
Write-Host "Отчёт: $report"

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Дамп состояния системы')
$lines.Add("# Дата: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add("# Узел: $env:COMPUTERNAME")
$lines.Add('# Снят ДО изменений. Откат выполняется по этому файлу.')
$lines.Add('')

# Каждый блок самостоятелен: отсутствие средства не должно обрывать дамп,
# иначе снимок получится неполным и непригодным для отката.
$lines.Add('## Службы')
try {
    foreach ($s in Get-CimInstance Win32_Service -ErrorAction Stop |
            Sort-Object Name) {
        $lines.Add("$($s.Name)|$($s.State)|$($s.StartMode)|$($s.StartName)")
    }
} catch {
    $lines.Add("  (Win32_Service недоступен: $($_.Exception.Message))")
}
$lines.Add('')

$lines.Add('## Задачи планировщика')
try {
    foreach ($t in Get-ScheduledTask -ErrorAction Stop | Sort-Object TaskName) {
        $lines.Add("$($t.TaskPath)$($t.TaskName)|$($t.State)")
    }
} catch {
    $lines.Add('  (Get-ScheduledTask недоступен)')
}
$lines.Add('')

$lines.Add('## Автозапуск: Run, RunOnce, Active Setup')
$runKeys = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run',
    'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\RunOnce',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce'
)
foreach ($k in $runKeys) {
    if (Test-Path -LiteralPath $k) {
        $lines.Add("--- $k")
        $props = Get-ItemProperty -LiteralPath $k -ErrorAction SilentlyContinue
        if ($props) {
            foreach ($n in $props.PSObject.Properties.Name |
                    Where-Object { $_ -notmatch '^PS' } | Sort-Object) {
                $lines.Add("$n = $($props.$n)")
            }
        }
    }
}
$asKey = 'HKLM:\SOFTWARE\Microsoft\Active Setup\Installed Components'
if (Test-Path -LiteralPath $asKey) {
    $lines.Add("--- $asKey")
    foreach ($sub in Get-ChildItem -LiteralPath $asKey -ErrorAction SilentlyContinue |
            Sort-Object PSChildName) {
        $p = Get-ItemProperty -LiteralPath $sub.PSPath -ErrorAction SilentlyContinue
        $lines.Add("$($sub.PSChildName)|$($p.'(default)')|$($p.StubPath)")
    }
}
$lines.Add('')

$lines.Add('## IFEO (Image File Execution Options)')
foreach ($ifeo in @(
        'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options',
        'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows NT\CurrentVersion\Image File Execution Options')) {
    if (Test-Path -LiteralPath $ifeo) {
        foreach ($sub in Get-ChildItem -LiteralPath $ifeo -ErrorAction SilentlyContinue |
                Sort-Object PSChildName) {
            $p = Get-ItemProperty -LiteralPath $sub.PSPath -ErrorAction SilentlyContinue
            # Пустых разделов IFEO в системе десятки тысяч; в дамп идут только
            # те, у которых что-то задано, иначе файл раздувается впустую.
            if ($p.Debugger -or $p.GlobalFlag -or $p.'UseFilter') {
                $lines.Add("$($sub.PSChildName)|Debugger=$($p.Debugger)|GlobalFlag=$($p.GlobalFlag)|UseFilter=$($p.'UseFilter')")
            }
        }
    }
}
$lines.Add('')

$lines.Add('## Политики HKLM')
$polRoot = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows'
if (Test-Path -LiteralPath $polRoot) {
    foreach ($sub in Get-ChildItem -LiteralPath $polRoot -Recurse -ErrorAction SilentlyContinue |
            Sort-Object Name) {
        $p = Get-ItemProperty -LiteralPath $sub.PSPath -ErrorAction SilentlyContinue
        foreach ($n in $p.PSObject.Properties.Name |
                Where-Object { $_ -notmatch '^PS' } | Sort-Object) {
            $lines.Add("$($sub.Name)|$n|$($p.$n)")
        }
    }
} else {
    $lines.Add('  (политик нет)')
}
$lines.Add('')

$lines.Add('## WMI-подписки (постоянные потребители событий)')
try {
    foreach ($c in Get-CimInstance -Namespace 'root\subscription' `
            -ClassName __EventConsumer -ErrorAction Stop) {
        $lines.Add("$($c.CimClass.CimClassName)|$($c.Name)|$($c.ScriptText)$($c.CommandLineTemplate)")
    }
} catch {
    $lines.Add('  (подписок нет или нет доступа)')
}
$lines.Add('')

$lines.Add('## Provisioned-пакеты')
try {
    foreach ($p in Get-AppxProvisionedPackage -Online -ErrorAction Stop |
            Sort-Object DisplayName) {
        $lines.Add($p.DisplayName)
    }
} catch {
    $lines.Add('  (Get-AppxProvisionedPackage недоступен)')
}
$lines.Add('')

$lines.Add('## Сетевые соединения (информационно, в сравнении не участвует)')
$lines.Add('# INFO-BEGIN')
try {
    foreach ($c in Get-NetTCPConnection -ErrorAction Stop |
            Sort-Object LocalAddress, LocalPort) {
        $lines.Add("$($c.State)|$($c.LocalAddress):$($c.LocalPort)|$($c.RemoteAddress):$($c.RemotePort)|PID=$($c.OwningProcess)")
    }
} catch {
    $lines.Add('  (Get-NetTCPConnection недоступен)')
}
$lines.Add('# INFO-END')

try {
    Set-Content -LiteralPath $report -Value $lines -Encoding UTF8 -ErrorAction Stop
} catch {
    Write-Error "Не удалось записать дамп: $($_.Exception.Message)"
    exit 1
}
Write-Host "Дамп: $report (строк: $($lines.Count))"

if ($Diff) {
    $diffPath = Join-Path $OutDir "system-audit-diff-$stamp.txt"
    # Нормализуем дату и убираем информационный раздел: иначе сравнение
    # показывает расхождение там, где изменилось только время снятия.
    $norm = {
        param($file)
        $inInfo = $false
        Get-Content -LiteralPath $file | Where-Object {
            if ($_ -eq '# INFO-BEGIN') { $inInfo = $true }
            if ($_ -eq '# INFO-END') { $inInfo = $false; return $false }
            if ($inInfo) { return $false }
            if ($_ -like '# Дата:*') { return $false }
            if ($_ -like '# Снят *') { return $false }
            return $true
        }
    }
    $before = & $norm $Diff
    $after = & $norm $report
    $delta = Compare-Object -ReferenceObject $before -DifferenceObject $after
    if ($delta) {
        $out = $delta | ForEach-Object {
            "$($_.SideIndicator) $($_.InputObject)"
        }
        Set-Content -LiteralPath $diffPath -Value $out -Encoding UTF8
        Write-Host "Diff: $diffPath (расхождений: $($delta.Count))"
        Write-Host 'ЕСТЬ ОТКЛОНЕНИЯ от исходного дампа.'
        Write-Host 'Если изменения не планировались, сработал механизм возврата.'
        exit 4
    }
    Write-Host 'Отклонений нет: состояние совпадает с исходным дампом.'
}

Write-Host 'Готово. Скопировать в reports/ станции.'
exit 0
