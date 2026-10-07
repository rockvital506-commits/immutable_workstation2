<#
.SYNOPSIS
    check-flash.ps1 — сверка содержимого флешки с репозиторием.

.DESCRIPTION
    Парная версия scripts/check-flash.sh для Windows.
    Проверяет:
      * раздел VENTOY доступен, есть \ventoy\ventoy.json и \ISO
      * ventoy.json на флешке совпадает с версией из репозитория
      * каждому ISO на флешке соответствует заглушка в репозитории и наоборот
      * SHA256 образов совпадает с manifest.csv (-Verify)
      * набор групп на разделе TOOLS совпадает с tools\ в репозитории
      * свободное место на разделах

.PARAMETER Ventoy
    Буква или путь раздела VENTOY, например E: или E:\

.PARAMETER Tools
    Буква или путь раздела TOOLS, например F:

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\check-flash.ps1 -Ventoy E: -Tools F:
    powershell -ExecutionPolicy Bypass -File scripts\check-flash.ps1 -Ventoy E: -Verify

.OUTPUTS
    Код возврата 0 — расхождений нет, 1 — есть расхождения, 2 — флешка не найдена.
#>
#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Ventoy,
    [string]$Tools = '',
    [switch]$Verify,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$RepoRoot     = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'manifest.csv'

$script:Errors = 0; $script:Warnings = 0; $script:Oks = 0
function Write-Ok   { param([string]$M) $script:Oks++;      if (-not $Json) { Write-Host '  OK   ' -ForegroundColor Green  -NoNewline; Write-Host $M } }
function Write-Warn { param([string]$M) $script:Warnings++; if (-not $Json) { Write-Host '  WARN ' -ForegroundColor Yellow -NoNewline; Write-Host $M } }
function Write-Fail { param([string]$M) $script:Errors++;   if (-not $Json) { Write-Host '  FAIL ' -ForegroundColor Red   -NoNewline; Write-Host $M } }
function Write-Head { param([string]$M) if (-not $Json) { Write-Host ''; Write-Host $M -ForegroundColor Cyan } }

function Resolve-Root {
    param([string]$Path)
    if ($Path -match '^[A-Za-z]:$') { return "$Path\" }
    return (Resolve-Path -LiteralPath $Path).Path.TrimEnd('\')
}

$VentoyRoot = Resolve-Root $Ventoy
if (-not (Test-Path -LiteralPath $VentoyRoot)) {
    Write-Host "Раздел $VentoyRoot не найден — флешка не подключена?" -ForegroundColor Red
    exit 2
}
$ToolsRoot = if ($Tools) { Resolve-Root $Tools } else { '' }

if (-not $Json) {
    Write-Host "check-flash — репозиторий $RepoRoot" -ForegroundColor White
    Write-Host "  раздел VENTOY: $VentoyRoot"
    Write-Host "  раздел TOOLS:  $(if ($ToolsRoot) { $ToolsRoot } else { '<не задан>' })"
}

# ------------------------------------------------------------
Write-Head '[1/5] Раздел VENTOY: базовая структура'
# ------------------------------------------------------------
foreach ($d in @(@('ventoy', $true), @('ISO', $true), @('backup', $false))) {
    $path = Join-Path $VentoyRoot $d[0]
    if (Test-Path -LiteralPath $path -PathType Container) {
        Write-Ok "каталог \$($($d[0])) присутствует"
    } elseif ($d[1]) {
        Write-Fail "нет каталога \$($($d[0])) — Ventoy не установлен или выбран не тот раздел"
    } else {
        Write-Warn "нет каталога \$($($d[0])) — бэкапы MBR/GPT некуда складывать"
    }
}

# ------------------------------------------------------------
Write-Head '[2/5] ventoy.json: флешка против репозитория'
# ------------------------------------------------------------
$FlashJson = Join-Path $VentoyRoot 'ventoy\ventoy.json'
$RepoJson  = Join-Path $RepoRoot 'ventoy-partition\ventoy\ventoy.json'
if (Test-Path -LiteralPath $FlashJson -PathType Leaf) {
    $a = (Get-Content -LiteralPath $FlashJson -Raw)
    $b = (Get-Content -LiteralPath $RepoJson  -Raw)
    if ($a -eq $b) { Write-Ok 'ventoy.json совпадает с версией из репозитория' }
    else { Write-Fail 'ventoy.json на флешке отличается от репозитория — обновите один из них' }
    try { $null = $a | ConvertFrom-Json; Write-Ok 'ventoy.json на флешке — валидный JSON' }
    catch { Write-Fail "ventoy.json на флешке невалиден: $($_.Exception.Message)" }
} else {
    Write-Fail "нет $FlashJson"
}

# ------------------------------------------------------------
Write-Head '[3/5] Образы ISO: заглушки против фактических файлов'
# ------------------------------------------------------------
$RepoIsoRoot = Join-Path $RepoRoot 'ventoy-partition\ISO'
$RepoStubs = @()
if (Test-Path -LiteralPath $RepoIsoRoot) {
    $RepoStubs = @(Get-ChildItem -LiteralPath $RepoIsoRoot -Recurse -File -Filter '*.iso.md' |
        ForEach-Object {
            $rel = $_.FullName.Substring($RepoIsoRoot.Length).TrimStart('\')
            ($rel -replace '\.md$', '') -replace '\\', '/'
        } | Sort-Object)
}

$FlashIsoRoot = Join-Path $VentoyRoot 'ISO'
$FlashIsos = @()
if (Test-Path -LiteralPath $FlashIsoRoot) {
    $FlashIsos = @(Get-ChildItem -LiteralPath $FlashIsoRoot -Recurse -File -Filter '*.iso' |
        ForEach-Object {
            ($_.FullName.Substring($FlashIsoRoot.Length).TrimStart('\')) -replace '\\', '/'
        } | Sort-Object)
}

if ($RepoStubs.Count -eq 0 -and $FlashIsos.Count -eq 0) {
    Write-Ok 'образов нет ни на флешке, ни в репозитории (Этап 2 ещё не выполнялся)'
} else {
    $missing = @($RepoStubs | Where-Object { $FlashIsos -notcontains $_ })
    $orphan  = @($FlashIsos | Where-Object { $RepoStubs -notcontains $_ })
    foreach ($m in $missing) { Write-Warn "в репозитории заявлен, на флешке отсутствует: ISO/$m" }
    foreach ($o in $orphan)  { Write-Fail "на флешке есть, в репозитории не описан: ISO/$o" }
    if ($missing.Count -eq 0 -and $orphan.Count -eq 0) {
        Write-Ok "образы на флешке и заглушки совпадают ($($FlashIsos.Count) шт.)"
    }
}

# ------------------------------------------------------------
Write-Head '[4/5] Контрольные суммы образов (-Verify)'
# ------------------------------------------------------------
if (-not $Verify) {
    Write-Ok 'проверка SHA256 пропущена (запустите с -Verify)'
} else {
    $checked = 0
    foreach ($row in (Import-Csv -LiteralPath $ManifestPath)) {
        if ($row.type -ne 'iso' -or [string]::IsNullOrWhiteSpace($row.file)) { continue }
        $target = Join-Path $VentoyRoot ($row.category -replace '/', '\')
        $target = Join-Path $target $row.file
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
            Write-Warn "manifest: $($row.category)/$($row.file) отсутствует на флешке"
            continue
        }
        if ($row.sha256 -eq 'PENDING' -or [string]::IsNullOrWhiteSpace($row.sha256)) {
            Write-Warn "manifest: для $($row.file) нет SHA256 — сверить нечем"
            continue
        }
        $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        $checked++
        if ($actual -eq $row.sha256.ToLowerInvariant()) {
            Write-Ok "SHA256 совпадает: $($row.file)"
        } else {
            Write-Fail "SHA256 НЕ совпадает: $($row.file) (ожидалось $($row.sha256.Substring(0,12))..., факт $($actual.Substring(0,12))...)"
        }
    }
    if ($checked -eq 0) { Write-Warn 'ни один образ не был сверен по SHA256' }
}

# ------------------------------------------------------------
Write-Head '[5/5] Раздел TOOLS и свободное место'
# ------------------------------------------------------------
if (-not $ToolsRoot) {
    Write-Warn 'раздел TOOLS не проверялся (не задан -Tools)'
} elseif (-not (Test-Path -LiteralPath $ToolsRoot)) {
    Write-Fail "раздел $ToolsRoot не найден"
} else {
    $RepoGroups = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'tools') -Directory |
        Where-Object { $_.Name -ne '_templates' } | ForEach-Object { $_.Name } | Sort-Object)
    $FlashGroups = @(Get-ChildItem -LiteralPath $ToolsRoot -Directory |
        Where-Object { $_.Name -ne 'System Volume Information' } | ForEach-Object { $_.Name } | Sort-Object)

    $missG  = @($RepoGroups  | Where-Object { $FlashGroups -notcontains $_ })
    $extraG = @($FlashGroups | Where-Object { $RepoGroups  -notcontains $_ })
    foreach ($g in $missG)  { Write-Warn "группа из репозитория отсутствует на флешке: $g" }
    foreach ($g in $extraG) { Write-Fail "группа на флешке не описана в репозитории: $g" }
    if ($missG.Count -eq 0 -and $extraG.Count -eq 0) {
        Write-Ok 'набор групп TOOLS совпадает с репозиторием'
    }
}

if (-not $Json) {
    Write-Host '  Свободное место:'
    foreach ($root in @($VentoyRoot, $ToolsRoot) | Where-Object { $_ }) {
        $letter = $root.Substring(0, 1)
        $drive = Get-PSDrive -Name $letter -ErrorAction SilentlyContinue
        if ($drive) {
            Write-Host ("    {0}: свободно {1:N1} ГБ из {2:N1} ГБ" -f $letter,
                ($drive.Free / 1GB), (($drive.Free + $drive.Used) / 1GB))
        }
    }
}

# ------------------------------------------------------------
if ($Json) {
    @{
        errors           = $script:Errors
        warnings         = $script:Warnings
        ok               = $script:Oks
        iso_on_flash     = $FlashIsos.Count
        iso_stubs_in_repo = $RepoStubs.Count
    } | ConvertTo-Json -Compress
} else {
    Write-Host ''
    Write-Host "Итог: совпадений — $($script:Oks), предупреждений — $($script:Warnings), расхождений — $($script:Errors)" -ForegroundColor White
    if ($script:Errors -gt 0) { Write-Host 'Флешка не соответствует репозиторию.' -ForegroundColor Red }
    else { Write-Host 'Флешка соответствует репозиторию.' -ForegroundColor Green }
}

if ($script:Errors -gt 0) { exit 1 }
exit 0
