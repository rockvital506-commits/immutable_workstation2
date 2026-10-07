<#
.SYNOPSIS
    verify-backup.ps1 — проверка целостности бэкапа по манифесту SHA256.

.DESCRIPTION
    Читает _manifest.sha256.csv из каталога бэкапа и сверяет хэш каждого файла.
    Отдельно сообщает о файлах, которых нет в манифесте (посторонние) и о файлах
    из манифеста, которых нет на диске (утерянные).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File verify-backup.ps1 -Path T:\backup\profiles\chrome_2026-10-07_12-00-00

.OUTPUTS
    0 — копия цела, 1 — есть расхождения, 3 — манифест не найден.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Path,
    [string]$ManifestName = '_manifest.sha256.csv'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
    Write-Error "Каталог не найден: $Path"
    exit 3
}

$manifest = Join-Path $Path $ManifestName
if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
    Write-Error "Манифест не найден: $manifest"
    exit 3
}

$rows   = Import-Csv -LiteralPath $manifest
$errors = 0
$ok     = 0

foreach ($r in $rows) {
    $full = Join-Path $Path $r.path
    if (-not (Test-Path -LiteralPath $full -PathType Leaf)) {
        Write-Host "  FAIL отсутствует: $($r.path)" -ForegroundColor Red
        $errors++
        continue
    }
    $actual = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -eq $r.sha256.ToLowerInvariant()) {
        $ok++
    } else {
        Write-Host "  FAIL хэш не совпадает: $($r.path)" -ForegroundColor Red
        $errors++
    }
}

$listed = $rows | ForEach-Object { $_.path }
$extra = @(Get-ChildItem -LiteralPath $Path -Recurse -File |
    ForEach-Object { $_.FullName.Substring($Path.Length).TrimStart('\') } |
    Where-Object { $listed -notcontains $_ -and $_ -ne $ManifestName -and $_ -notlike '_RESTORE_NOTES.md' })

foreach ($e in $extra) {
    Write-Host "  WARN не в манифесте: $e" -ForegroundColor Yellow
}

Write-Host ''
Write-Host ("Итог: совпало {0}, расхождений {1}, вне манифеста {2}" -f $ok, $errors, $extra.Count)
if ($errors -gt 0) {
    Write-Host 'Копия повреждена или неполна — использовать её нельзя.' -ForegroundColor Red
    exit 1
}
Write-Host 'Копия цела.' -ForegroundColor Green
exit 0
