<#
.SYNOPSIS
    apply-blocking.ps1 — применение блокировок телеметрии и самовосстановления.

.DESCRIPTION
    Порядок применения фиксирован (research/06-services-blocklist.md):
    P0 -> P1a -> P1b -> P2 -> T -> P3 -> P5.
    Инициаторы отключаются раньше исполнителей: иначе исполнитель поднимет
    своего инициатора обратно, и применение окажется видимым, но не действующим.

    Профиль — НЕ в этом файле, а в apply-blocking.conf рядом. Обе половины
    пары (.sh и .ps1) читают один файл, поэтому профиль станции не
    разъезжается между Linux и Windows.

    ОТКАТ НЕ ВЫПОЛНЯЕТСЯ АВТОМАТИЧЕСКИ. Откат без спроса может упасть по той
    же причине, по которой упало применение (Win11Debloat: PR #613 был
    реализован и отклонён именно по этому основанию). При сбое печатается
    путь к дампу и точная обратная команда для именно этого действия.

    Обязателен дамп аудита: исходные значения фиксируются дампом на первом
    шаге, без него откат невозможен.

.PARAMETER Audit
    Путь к дампу system-audit.ps1, снятому ДО изменений. Без него применение
    отклоняется (код 3).

.PARAMETER DryRun
    Показать, что было бы сделано. Ничего не изменяет, дамп не требуется.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File apply-blocking.ps1 -Audit E:\reports\system-audit-20261014-1200.txt
    powershell -ExecutionPolicy Bypass -File apply-blocking.ps1 -DryRun -Groups P1a,P1b

.OUTPUTS
    0 — успех, 1 — ошибка, 2 — нет нужных средств, 3 — дамп не предоставлен
    или недоступен, 4 — применено не всё.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Conf,
    [string]$Audit,
    [string[]]$SelectedGroups,
    [string]$ReportDir,
    [switch]$DryRun,
    [switch]$NoAudit
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

# --- Профиль ---------------------------------------------------------------

$KnownKeys = @('P0', 'P1a', 'P1b', 'P2', 'T', 'P3', 'P5', 'VERIFY_WU',
    'EXCLUDE_SERVICES', 'P3_ENABLE', 'REPORT_DIR')
# Числовые (0/1) ключи перечислены явно: срез по индексам захватывал P5 как
# числовой и пропускал P3.
$numericKeys = @('P0', 'P1a', 'P1b', 'P2', 'T', 'P3', 'P5', 'VERIFY_WU')

function Read-BlockingProfile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Write-Error "Профиль недоступен: $Path"
        exit 1
    }
    $cfg = @{}
    $seen = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#')) { continue }
        if ($line -notmatch '=') {
            Write-Error "Строка профиля без '=': $line"
            exit 1
        }
        $k, $v = $line -split '=', 2
        $k = $k.Trim()
        # Пустое значение допустимо (P3_ENABLE = означает «ничего из P3»),
        # поэтому список чистится от пустых элементов, а не от пробелов.
        $v = $v.Trim()
        if ($KnownKeys -notcontains $k) {
            Write-Error "Неизвестный ключ профиля: '$k'. Допустимые: $($KnownKeys -join ' ')"
            exit 1
        }
        if ($numericKeys -contains $k -and $v -notin @('0', '1')) {
            Write-Error "$k должен быть 0 или 1, получено '$v'"
            exit 1
        }
        $cfg[$k] = $v
        $seen[$k] = $true
    }
    foreach ($k in $KnownKeys) {
        if (-not $seen.ContainsKey($k)) {
            Write-Error "В профиле нет обязательного ключа: $k"
            exit 1
        }
    }
    return $cfg
}

# --- Перечни (research/06-services-blocklist.md, без изменений) ------------

# P0. Критические инициаторы: запускают или ВОССТАНАВЛИВАЮТ остальное.
# wuauserv -> Manual, НЕ Disabled: канал security-патчей обязан остаться.
$P0Services = [ordered]@{
    'WaaSMedicSvc'  = 'Disabled'
    'UsoSvc'        = 'Disabled'
    'wuauserv'      = 'Manual'
    'DoSvc'         = 'Disabled'
    'InstallService' = 'Manual'
}
$P0Task = '\Microsoft\Windows\WaaSMedic\PerformRemediation'
$P0Reg = @(
    @{
        Path  = 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
        Name  = 'SilentInstalledAppsEnabled'
        Value = 0
        Why   = 'тихая установка рекламных приложений'
    }
    @{
        Path  = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\CloudContent'
        Name  = 'DisableWindowsConsumerFeatures'
        Value = 1
        Why   = 'потребительские предложения'
    }
)
# P1a. Задачи-инициаторы — отключаются РАНЬШЕ служб-исполнителей.
$P1aTasks = @(
    '\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser',
    '\Microsoft\Windows\Application Experience\ProgramDataUpdater',
    '\Microsoft\Windows\Application Experience\StartupAppTask',
    '\Microsoft\Windows\Application Experience\PcaPatchDbTask',
    '\Microsoft\Windows\Customer Experience Improvement Program\Consolidator',
    '\Microsoft\Windows\Customer Experience Improvement Program\UsbCeip',
    '\Microsoft\Windows\Customer Experience Improvement Program\KernelCeipTask',
    '\Microsoft\Windows\Feedback\Siuf\DmClient',
    '\Microsoft\Windows\Feedback\Siuf\DmClientOnScenarioDownload',
    '\Microsoft\Windows\Windows Error Reporting\QueueReporting',
    '\Microsoft\Windows\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector',
    '\Microsoft\Windows\Maintenance\WinSAT',
    '\Microsoft\Windows\Speech\SpeechModelDownloadTask',
    '\Microsoft\Windows\Maps\MapsToastTask',
    '\Microsoft\Windows\Maps\MapsUpdateTask',
    '\Microsoft\Windows\Autochk\Proxy',
    'MicrosoftEdgeUpdateTaskMachineCore',
    'MicrosoftEdgeUpdateTaskMachineUA'
)
# P1b. Службы-инициаторы телеметрии и диагностики.
$P1bServices = @(
    'DiagTrack', 'dmwappushservice', 'InventorySvc', 'DPS', 'WdiSystemHost',
    'WdiServiceHost', 'diagnosticshub.standardcollector.service', 'WerSvc',
    'PcaSvc', 'CDPSvc', 'wisvc', 'SysMain', 'WSearch', 'MapsBroker',
    'lfsvc', 'TrkWks'
)
# P2. Исполнители. IFEO-заглушки — двойная защита поверх отключённых задач.
# WerFault глобально НЕ глушится: на нём держится SilentProcessExit.
$P2Ifeo = @('CompatTelRunner.exe', 'wsqmcons.exe', 'DmClient.exe', 'wermgr.exe')
$P2Services = @(
    'XblAuthManager', 'XblGameSave', 'XboxGipSvc', 'XboxNetApiSvc',
    'GamingServices', 'GamingServicesNet', 'NPSMSvc', 'RmSvc', 'OneSyncSvc',
    'lmhosts', 'Fax', 'WMPNetworkSvc', 'AJRouter', 'WalletService',
    'WpcMonSvc', 'MessagingService', 'SEMgrSvc', 'SmsRouter',
    'WSAIFabricSvc', 'RemoteRegistry', 'RetailDemo'
)
# P3. Ситуативные — только по явному P3_ENABLE, каждая ломает рабочую функцию.
$P3Map = [ordered]@{
    'TabletInputService' = @('TabletInputService')
    'lfsvc'              = @('lfsvc')
    'hyperv'             = @('vmms', 'vmcompute', 'HvHost')
    'Spooler'            = @('Spooler')
    'WMPNetworkSvc'      = @('WMPNetworkSvc')
    'nfc'                = @('AJRouter', 'SEMgrSvc', 'WalletService')
    'phone'              = @('PhoneSvc', 'MessagingService')
}

$script:Failed = 0
$script:Applied = 0
$script:Skipped = 0
$script:Journal = New-Object System.Collections.Generic.List[string]

function Write-Step { param([string]$Msg) Write-Host $Msg }
function Write-Head { param([string]$Msg) Write-Host ''; Write-Host "=== $Msg ===" }

function Test-Excluded {
    param([string]$Name)
    foreach ($e in $script:Exclude) {
        if ($Name -eq $e) { return $true }
    }
    return $false
}

# --- Действия --------------------------------------------------------------
# Каждое действие печатает обратную команду ДО изменения: если команда упадёт,
# обратная команда уже на экране и в транскрипте.

function Set-ServiceState {
    param([string]$Name, [string]$Target)
    if (Test-Excluded $Name) {
        Write-Step "  $Name — в EXCLUDE_SERVICES, пропуск"
        $script:Skipped++
        return
    }
    $svc = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if (-not $svc) {
        Write-Step "  [пропуск] $Name — нет в системе"
        $script:Skipped++
        return
    }
    $cur = (Get-CimInstance Win32_Service -Filter "Name='$Name'" -ErrorAction SilentlyContinue).StartMode
    $back = "Set-Service -Name $Name -StartupType $cur"
    Write-Step "  $Name: сейчас '$cur' -> $Target"
    Write-Step "    откат: $back"
    $script:Journal.Add("service|$Name|$cur|$Target")
    if ($DryRun) {
        Write-Step '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        Set-Service -Name $Name -StartupType $Target -ErrorAction Stop
        # Служба со старым типом запуска может быть уже запущена; Disabled
        # требует остановки, иначе состояние останется смешанным.
        if ($Target -eq 'Disabled' -and $svc.Status -eq 'Running') {
            Stop-Service -Name $Name -Force -ErrorAction Stop
        }
        $script:Applied++
        Write-Step '    применено'
    } catch {
        Write-Step "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Step "    ОТКАТ ВРУЧНУЮ: $back"
        Write-Step "    Дамп исходного состояния: $script:AuditPath"
        $script:Failed++
    }
}

function Disable-ScheduledTask {
    param([string]$Path)
    $task = Get-ScheduledTask -TaskPath (Split-Path $Path -Parent) `
        -TaskName (Split-Path $Path -Leaf) -ErrorAction SilentlyContinue
    if (-not $task) {
        Write-Step "  [пропуск] $Path — нет в системе"
        $script:Skipped++
        return
    }
    $back = "Enable-ScheduledTask -TaskPath '$(Split-Path $Path -Parent)\' -TaskName '$(Split-Path $Path -Leaf)'"
    Write-Step "  $Path: сейчас '$($task.State)' -> Disabled"
    Write-Step "    откат: $back"
    $script:Journal.Add("task|$Path|$($task.State)|Disabled")
    if ($DryRun) {
        Write-Step '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        Disable-ScheduledTask -TaskPath (Split-Path $Path -Parent) `
            -TaskName (Split-Path $Path -Leaf) -ErrorAction Stop | Out-Null
        $script:Applied++
        Write-Step '    применено'
    } catch {
        Write-Step "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Step "    ОТКАТ ВРУЧНУЮ: $back"
        Write-Step "    Дамп исходного состояния: $script:AuditPath"
        $script:Failed++
    }
}

function Set-RegValue {
    param([string]$Path, [string]$Name, [int]$Value, [string]$Why)
    $had = $false
    $old = $null
    if (Test-Path -LiteralPath $Path) {
        $item = Get-ItemProperty -LiteralPath $Path -Name $Name -ErrorAction SilentlyContinue
        if ($item) { $had = $true; $old = $item.$Name }
    }
    if ($had) {
        $back = "Set-ItemProperty -LiteralPath '$Path' -Name $Name -Value $old"
    } else {
        $back = "Remove-ItemProperty -LiteralPath '$Path' -Name $Name"
    }
    Write-Step "  $Path\$Name -> $Value ($Why)"
    Write-Step "    откат: $back"
    $script:Journal.Add("reg|$Path|$Name|$old|$Value")
    if ($DryRun) {
        Write-Step '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        if (-not (Test-Path -LiteralPath $Path)) {
            New-Item -Path $Path -Force -ErrorAction Stop | Out-Null
        }
        Set-ItemProperty -LiteralPath $Path -Name $Name -Value $Value -Type DWord -ErrorAction Stop
        $script:Applied++
        Write-Step '    применено'
    } catch {
        Write-Step "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Step "    ОТКАТ ВРУЧНУЮ: $back"
        Write-Step "    Дамп исходного состояния: $script:AuditPath"
        $script:Failed++
    }
}

function Set-IfeoStub {
    param([string]$Exe)
    $key = "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\$Exe"
    $had = Test-Path -LiteralPath $key
    $old = $null
    if ($had) {
        $p = Get-ItemProperty -LiteralPath $key -Name Debugger -ErrorAction SilentlyContinue
        if ($p) { $old = $p.Debugger }
    }
    # IFEO принимает только имя файла, а не путь: значение с полным путём
    # молча не срабатывает.
    $back = if ($old) {
        "Set-ItemProperty -LiteralPath '$key' -Name Debugger -Value '$old'"
    } elseif ($had) {
        "Remove-ItemProperty -LiteralPath '$key' -Name Debugger"
    } else {
        "Remove-Item -LiteralPath '$key'"
    }
    Write-Step "  IFEO $Exe -> Debugger=DisableTaskmgr-заглушка"
    Write-Step "    откат: $back"
    $script:Journal.Add("ifeo|$Exe|$old|set")
    if ($DryRun) {
        Write-Step '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        if (-not $had) { New-Item -Path $key -Force -ErrorAction Stop | Out-Null }
        Set-ItemProperty -LiteralPath $key -Name Debugger -Value 'systray.exe' -ErrorAction Stop
        $script:Applied++
        Write-Step '    применено'
    } catch {
        Write-Step "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Step "    ОТКАТ ВРУЧНУЮ: $back"
        Write-Step "    Дамп исходного состояния: $script:AuditPath"
        $script:Failed++
    }
}

function Register-EnforcementTask {
    # Паттерн P5 (research/03-patterns.md): задача от SYSTEM, при старте с
    # задержкой ~2 мин и далее раз в 6 часов, идемпотентна, пишет лог
    # «что вернулось». Без неё часть отключённого вернётся после обновлений.
    $name = 'ImmutableStation-Enforcement'
    $self = $MyInvocation.ScriptName
    if (-not $self) { $self = $PSCommandPath }
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    Write-Step "  Enforcement-задача: $name"
    Write-Step "    откат: Unregister-ScheduledTask -TaskName $name -Confirm:`$false"
    $script:Journal.Add("enforcement|$name|$([bool]$existing)|registered")
    if ($DryRun) {
        Write-Step '    [dry-run] не изменено'
        $script:Applied++
        return
    }
    try {
        $action = New-ScheduledTaskAction -Execute 'powershell.exe' `
            -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$self`" -Conf `"$script:ConfPath`" -Groups P0,P1a,P1b,P2 -NoAudit"
        $trigger1 = New-ScheduledTaskTrigger -AtStartup
        $trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) `
            -RepetitionInterval (New-TimeSpan -Hours 6)
        $principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
        if ($existing) {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop
        }
        Register-ScheduledTask -TaskName $name -Action $action `
            -Trigger @($trigger1, $trigger2) -Principal $principal `
            -Settings $settings -Description 'Возврат целевого состояния блокировок и лог отклонений (P5)' `
            -ErrorAction Stop | Out-Null
        $script:Applied++
        Write-Step '    применено'
    } catch {
        Write-Step "    ПРОВАЛ: $($_.Exception.Message)"
        Write-Step "    ОТКАТ ВРУЧНУЮ: Unregister-ScheduledTask -TaskName $name -Confirm:`$false"
        Write-Step "    Дамп исходного состояния: $script:AuditPath"
        $script:Failed++
    }
}

# --- Основной поток --------------------------------------------------------

Write-Host "=== apply-blocking.ps1 $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') ==="

if (-not $Conf) {
    $Conf = Join-Path (Split-Path -Parent $PSCommandPath) 'apply-blocking.conf'
}
$script:ConfPath = $Conf
Write-Host "Профиль: $Conf"
$cfg = Read-BlockingProfile -Path $Conf
foreach ($k in $KnownKeys) { Write-Host "  $k = $($cfg[$k])" }

$script:Exclude = @()
if ($cfg['EXCLUDE_SERVICES']) {
    $script:Exclude = $cfg['EXCLUDE_SERVICES'] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}
$script:P3Enable = @()
if ($cfg['P3_ENABLE']) {
    $script:P3Enable = $cfg['P3_ENABLE'] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
}
if (-not $ReportDir) { $ReportDir = $cfg['REPORT_DIR'] }
if (-not $SelectedGroups -or $SelectedGroups.Count -eq 0) {
    $SelectedGroups = @('P0', 'P1a', 'P1b', 'P2', 'T', 'P3', 'P5')
}
Write-Host "Группы к применению: $($SelectedGroups -join ' ')"
Write-Host "Исключено: $(if ($script:Exclude) { $script:Exclude -join ', ' } else { '<ничего>' })"

# Обязательный дамп: без него откат невозможен.
$script:AuditPath = if ($Audit) { $Audit } else { '<не предоставлен>' }
if (-not $DryRun -and -not $Audit -and -not $NoAudit) {
    Write-Host ''
    Write-Host 'ОШИБКА: не предоставлен дамп аудита.'
    Write-Host 'Сначала:  .\system-audit.ps1 -OutDir <каталог>'
    Write-Host 'Потом:    .\apply-blocking.ps1 -Audit <путь к дампу>'
    Write-Host 'Без дампа исходные значения не зафиксированы и откат невозможен.'
    Write-Host 'Осознанно обойти: -NoAudit (не рекомендуется).'
    exit 3
}
if ($Audit -and -not (Test-Path -LiteralPath $Audit -PathType Leaf)) {
    Write-Error "Дамп недоступен: $Audit"
    exit 3
}
if ($Audit) { Write-Host "Дамп исходного состояния: $Audit" }

# Средства: все действия требуют прав администратора.
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $DryRun -and -not $isAdmin) {
    Write-Host ''
    Write-Host 'ОШИБКА: нет прав администратора — службы, задачи и HKLM недоступны.'
    Write-Host 'Запустите PowerShell от администратора или используйте -DryRun.'
    exit 2
}

function Test-GroupWanted {
    param([string]$G)
    return (($SelectedGroups -contains $G) -and ($cfg[$G] -eq '1'))
}

# --- P0 --------------------------------------------------------------------
if ($SelectedGroups -contains 'P0') {
    Write-Head 'P0. Критические инициаторы'
    if (Test-GroupWanted 'P0') {
        foreach ($n in $P0Services.Keys) { Set-ServiceState -Name $n -Target $P0Services[$n] }
        # Задача WaaSMedic восстанавливает работоспособность WU — без её
        # удаления отключение службы бессмысленно.
        Disable-ScheduledTask -Path $P0Task
        foreach ($r in $P0Reg) { Set-RegValue -Path $r.Path -Name $r.Name -Value $r.Value -Why $r.Why }
        # Provisioned appx: без удаления пакета appx вернётся для новых
        # пользователей (гипотеза H5 из research/06).
        if ($DryRun) {
            Write-Step '  [dry-run] provisioned appx: удаление не выполняется'
        } else {
            try {
                $junk = Get-AppxProvisionedPackage -Online -ErrorAction Stop |
                    Where-Object { $_.DisplayName -match 'Bing|Xbox|Zune|Solitaire|Candy|Disney|Spotify|TikTok' }
                foreach ($p in $junk) {
                    Write-Step "  provisioned: $($p.DisplayName)"
                    Write-Step "    откат: Add-AppxProvisionedPackage -Online -PackagePath <пакет> -SkipLicense"
                    $script:Journal.Add("appx|$($p.DisplayName)|present|removed")
                    Remove-AppxProvisionedPackage -PackageName $p.PackageName -ErrorAction Stop | Out-Null
                    $script:Applied++
                }
                if (-not $junk) { Write-Step '  provisioned appx: подходящих пакетов нет' }
            } catch {
                Write-Step "  ПРОВАЛ provisioned appx: $($_.Exception.Message)"
                Write-Step '    ОТКАТ ВРУЧНУЮ: Add-AppxProvisionedPackage -Online -PackagePath <пакет> -SkipLicense'
                $script:Failed++
            }
        }
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- P1a -------------------------------------------------------------------
if ($SelectedGroups -contains 'P1a') {
    Write-Head 'P1a. Задачи планировщика (раньше исполнителей)'
    if (Test-GroupWanted 'P1a') {
        foreach ($t in $P1aTasks) { Disable-ScheduledTask -Path $t }
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- P1b -------------------------------------------------------------------
if ($SelectedGroups -contains 'P1b') {
    Write-Head 'P1b. Службы-инициаторы телеметрии'
    if (Test-GroupWanted 'P1b') {
        foreach ($s in $P1bServices) { Set-ServiceState -Name $s -Target 'Disabled' }
        # CDPUserSvc_* создаётся на каждого пользователя с суффиксом, поэтому
        # отбирается по маске, а не по точному имени.
        foreach ($u in Get-Service -Name 'CDPUserSvc_*' -ErrorAction SilentlyContinue) {
            Set-ServiceState -Name $u.Name -Target 'Disabled'
        }
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- P2 --------------------------------------------------------------------
if ($SelectedGroups -contains 'P2') {
    Write-Head 'P2. Исполнители'
    if (Test-GroupWanted 'P2') {
        # WerFault.exe не глушится: на нём держится SilentProcessExit.
        foreach ($e in $P2Ifeo) { Set-IfeoStub -Exe $e }
        foreach ($s in $P2Services) { Set-ServiceState -Name $s -Target 'Disabled' }
        if (Test-Excluded 'SharedAccess') {
            Write-Step '  SharedAccess — в EXCLUDE_SERVICES: точка доступа может быть рабочим инструментом'
        } else {
            Set-ServiceState -Name 'SharedAccess' -Target 'Disabled'
        }
        if (Test-Excluded 'icssvc') {
            Write-Step '  icssvc — в EXCLUDE_SERVICES: точка доступа может быть рабочим инструментом'
        } else {
            Set-ServiceState -Name 'icssvc' -Target 'Disabled'
        }
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- T ---------------------------------------------------------------------
if ($SelectedGroups -contains 'T') {
    Write-Head 'T. Точечные запреты'
    if (Test-GroupWanted 'T') {
        # Wrapper-исполняемый файл (механизм M8) сюда не входит сознательно:
        # подмена системного исполняемого файла ломает проверку целостности
        # (SFC/DISM /Verify) и не откатывается дампом. Точечные запреты
        # реализуются локальной политикой — отдельный шаг через LGPO.exe
        # (research/07). Здесь фиксируется только факт, что группа включена.
        Write-Step '  Группа T включена профилем, но wrapper-подмена системных'
        Write-Step '  исполняемых файлов не выполняется: она ломает проверку'
        Write-Step '  целостности и не откатывается дампом. Реализация —'
        Write-Step '  локальная политика через LGPO.exe, отдельный шаг.'
        Write-Step '  См. research/07-blocking-mechanisms.md, механизм M8.'
        $script:Skipped++
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- P3 --------------------------------------------------------------------
if ($SelectedGroups -contains 'P3') {
    Write-Head 'P3. Ситуативные'
    if (Test-GroupWanted 'P3') {
        if ($script:P3Enable.Count -eq 0) {
            Write-Step '  P3_ENABLE пуст: ни одна ситуативная позиция не применяется.'
            Write-Step '  Это штатное состояние: каждая позиция P3 ломает рабочую'
            Write-Step '  функцию и включается явно под профиль владельца.'
        }
        foreach ($item in $script:P3Enable) {
            if (-not $P3Map.Contains($item)) {
                Write-Step "  ОШИБКА: неизвестная позиция P3: '$item'"
                Write-Step "    допустимые: $($P3Map.Keys -join ', ')"
                $script:Failed++
                continue
            }
            if ($item -eq 'hyperv') {
                Write-Step '  hyperv: ВНИМАНИЕ — vmms/vmcompute/HvHost нужны для'
                Write-Step '  VBS и Credential Guard. Отключение снижает защиту.'
            }
            foreach ($s in $P3Map[$item]) { Set-ServiceState -Name $s -Target 'Disabled' }
        }
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- P5 --------------------------------------------------------------------
if ($SelectedGroups -contains 'P5') {
    Write-Head 'P5. Enforcement-задача'
    if (Test-GroupWanted 'P5') {
        Register-EnforcementTask
    } else { Write-Step '  [выключено профилем или не выбрано]' }
}

# --- Итог ------------------------------------------------------------------
Write-Head 'Итог'
Write-Host "Действий выполнено: $script:Applied"
Write-Host "Пропущено: $script:Skipped"
Write-Host "Провалено: $script:Failed"

if ($ReportDir -and -not $DryRun) {
    if (-not (Test-Path -LiteralPath $ReportDir -PathType Container)) {
        Write-Error "Каталог отчётов недоступен: $ReportDir"
        exit 1
    }
    $report = Join-Path $ReportDir "apply-blocking-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $body = @()
    $body += '# Отчёт о применении блокировок'
    $body += "# Дата: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    $body += "# Профиль: $Conf"
    $body += "# Дамп исходного состояния: $script:AuditPath"
    $body += "# Группы: $($SelectedGroups -join ' ')"
    $body += "# Действий: $script:Applied, пропущено: $script:Skipped, провалено: $script:Failed"
    $body += '# Формат: тип|объект|было|стало'
    $body += '# Откат — по дампу и таблице «применили / откатили» в'
    $body += '# research/06-services-blocklist.md'
    $body += $script:Journal
    Set-Content -LiteralPath $report -Value $body -Encoding UTF8
    Write-Host "Отчёт: $report"
}

if ($script:Failed -gt 0) {
    Write-Host ''
    Write-Host 'ПРИМЕНЕНО НЕ ВСЁ. Автоматический откат НЕ выполняется:'
    Write-Host 'откат без спроса может упасть по той же причине, по которой'
    Write-Host 'упало применение. Решает человек.'
    Write-Host "  Дамп исходного состояния: $script:AuditPath"
    Write-Host "  Сравнить с текущим: .\system-audit.ps1 -OutDir <каталог> -Diff $script:AuditPath"
    Write-Host '  Обратные команды — в выводе выше, по одной на проваленное действие.'
    exit 4
}

if ($DryRun) {
    Write-Host ''
    Write-Host 'Ничего не изменено (-DryRun).'
    exit 0
}

Write-Host ''
if ($cfg['VERIFY_WU'] -eq '1') {
    Write-Host 'ОБЯЗАТЕЛЬНАЯ пост-проверка: Центр обновления должен остаться'
    Write-Host 'работоспособным для security-патчей (wuauserv = Manual, не Disabled).'
    Write-Host '  Get-Service wuauserv, UsoSvc, WaaSMedicSvc, DoSvc'
    Write-Host '  Проверка: .\validate-system.ps1'
}
Write-Host 'ОБЯЗАТЕЛЬНЫЙ следующий шаг — повторный аудит и сравнение:'
Write-Host "  .\system-audit.ps1 -OutDir <каталог> -Diff $script:AuditPath"
exit 0
