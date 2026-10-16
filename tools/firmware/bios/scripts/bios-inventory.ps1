<#
.SYNOPSIS
    bios-inventory.ps1 — фиксация версий прошивок платы ДО любых изменений.

.DESCRIPTION
    Парная версия bios-inventory.sh. Скрипт НИЧЕГО не прошивает: он только
    записывает то, что потом не восстановить по памяти. Обновление BIOS
    возвращает настройки UEFI к значениям по умолчанию, поэтому снимок
    настроек обязателен до, а не после.

    Intel ME из Linux штатно не читается — этот снимок единственный способ
    зафиксировать его версию средствами ОС.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File bios-inventory.ps1
    powershell -ExecutionPolicy Bypass -File bios-inventory.ps1 -OutDir E:\tools\firmware\reports

.OUTPUTS
    0 — успех, 1 — ошибка, 2 — нет нужных средств, 3 — каталог недоступен.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [string]$OutDir = [IO.Path]::GetTempPath()
)

# Строгий режим: без него обращение к необъявленной переменной молча даёт
# $null, и опечатка в имени превращается в тихое неверное поведение
# (CONVENTIONS.md, раздел 5).
Set-StrictMode -Version Latest

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

if (-not (Test-Path -LiteralPath $OutDir -PathType Container)) {
    Write-Error "Каталог недоступен: $OutDir"
    exit 3
}

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$report = Join-Path $OutDir "bios-inventory-$stamp.txt"
Write-Host "Отчёт: $report"

# Каждый блок самостоятелен: absence средства не должно обрывать снимок.
function Section([string]$Title) { "`n## $Title" }

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('# Снимок прошивок и настроек UEFI')
$lines.Add("# Дата: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$lines.Add('# Снято до изменений. После прошивки сверить с этим файлом.')

$lines.Add((Section 'Плата и BIOS'))
try {
    $cs = Get-CimInstance -ClassName Win32_ComputerSystem -ErrorAction Stop
    $bio = Get-CimInstance -ClassName Win32_BIOS -ErrorAction Stop
    $bb = Get-CimInstance -ClassName Win32_BaseBoard -ErrorAction Stop
    $lines.Add("Производитель : $($cs.Manufacturer)")
    $lines.Add("Модель        : $($cs.Model)")
    $lines.Add("Плата         : $($bb.Product)")
    $lines.Add("Серийный      : $($cs.SerialNumber)")
    $lines.Add("Версия BIOS   : $($bio.SMBIOSBIOSVersion)")
    $lines.Add("Дата BIOS     : $($bio.ReleaseDate)")
} catch {
    $lines.Add("  (WMI недоступен: $($_.Exception.Message))")
}

$lines.Add((Section 'Режим загрузки и Secure Boot'))
try {
    $lines.Add("Secure Boot   : $((Confirm-SecureBootUEFI) -replace 'True','включён' -replace 'False','выключен')")
} catch {
    $lines.Add("Secure Boot   : не определён (Legacy/CSM или нет прав)")
}
try {
    $lines.Add('Загрузочные записи (bcdedit /enum firmware):')
    $lines += (bcdedit /enum firmware 2>&1 | Out-String).TrimEnd() -split "`r?`n"
} catch {
    $lines.Add('  (bcdedit недоступен — загрузочные записи не сняты)')
}

$lines.Add((Section 'TPM'))
try {
    $tpm = Get-CimInstance -Namespace 'root\CIMV2\Security\MicrosoftTpm' `
        -ClassName Win32_Tpm -ErrorAction Stop
    $lines.Add("TPM           : версия $($tpm.SpecVersion), производитель $($tpm.Manufacturer)")
    $lines.Add("Включён       : $($tpm.IsEnabled_InitialValue)")
} catch {
    $lines.Add('  (TPM не виден через WMI)')
}

$lines.Add((Section 'BitLocker'))
try {
    $vols = Get-BitLockerVolume -ErrorAction Stop
    if ($vols) {
        foreach ($v in $vols) {
            $lines.Add("$($v.MountPoint): $($v.ProtectionStatus), ключей: $($v.KeyProtector.Count)")
        }
        $lines.Add('Правило проекта: перед прошивкой BitLocker приостановить ОДИН раз')
        $lines.Add('на всё время работ и возобновить после проверки.')
    } else {
        $lines.Add('  (шифрование не включено)')
    }
} catch {
    $lines.Add('  (Get-BitLockerVolume недоступен)')
}

$lines.Add((Section 'Intel Management Engine'))
try {
    $me = Get-CimInstance -Namespace 'root\WMI' -ClassName MEVersion -ErrorAction Stop
    foreach ($m in $me) {
        $lines.Add("ME            : $($m.MEV) (ревизия $($m.MajorVersion).$($m.MinorVersion))")
    }
} catch {
    $lines.Add('  (класс MEVersion недоступен — нужен драйвер Intel ME Interface)')
    $lines.Add('  Альтернатива: MEInfoWin из Intel ME System Tools, либо HWiNFO из Strelec.')
}

$lines.Add((Section 'Накопители'))
try {
    foreach ($d in Get-PhysicalDisk -ErrorAction Stop) {
        $lines.Add("$($d.DeviceId) $($d.FriendlyName) | прошивка $($d.FirmwareVersion) | $($d.MediaType) | S/N $($d.SerialNumber)")
    }
} catch {
    $lines.Add('  (Get-PhysicalDisk недоступен)')
    try {
        foreach ($d in Get-Disk -ErrorAction Stop) {
            $lines.Add("$($d.Number) $($d.FriendlyName) | прошивка $($d.FirmwareVersion)")
        }
    } catch {
        $lines.Add('  (и Get-Disk недоступен)')
    }
}

$lines.Add((Section 'Настройки UEFI, которые надо вернуть после прошивки'))
$lines += @(
    'Прошивка возвращает настройки UEFI к значениям по умолчанию. До прошивки',
    'записать от руки, после — вернуть:',
    '',
    '  [ ] Secure Boot: состояние и режим ключей (Standard / Custom)',
    '  [ ] Порядок загрузки и загрузочная запись Windows',
    '  [ ] CSM / Legacy: выключен или включён',
    '  [ ] Intel VMD controller: Enabled / Disabled  <-- критично для установки',
    '      Windows на MSI 11-го поколения и новее: при VMD=Enabled нужен драйвер',
    '      IRST/VMD в образе, иначе установщик не видит накопитель',
    '  [ ] SATA Mode: AHCI / RAID',
    '  [ ] Fast Boot',
    '  [ ] Пароль BIOS, если задан',
    '  [ ] XMP/EXPO и прочие профили памяти'
)

try {
    Set-Content -LiteralPath $report -Value $lines -Encoding UTF8 -ErrorAction Stop
} catch {
    Write-Error "Не удалось записать отчёт: $($_.Exception.Message)"
    exit 1
}

Write-Host "Готово: $report (строк: $($lines.Count))"
Write-Host 'Скопировать на Tools: и приложить к algorithm.md станции.'
exit 0
