<#
.SYNOPSIS
    new-tool.ps1 — создать каркас утилиты/скрипта/модуля в tools/.

.DESCRIPTION
    Парная версия scripts/new-tool.sh для Windows.
    1. Создаёт tools\<group>\<subgroup>\<Name>\
    2. Кладёт README.md из шаблона (utility | script | module)
    3. Создаёт README.md в группе и подкатегории, если их ещё нет
    4. Добавляет строку в manifest.csv (status=planned)

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\new-tool.ps1 -Group diagnostics -Subgroup disk -Name Victoria
    powershell -ExecutionPolicy Bypass -File scripts\new-tool.ps1 -Group rescue -Subgroup password -Name NtpwEdit -Kind module -Force
    powershell -ExecutionPolicy Bypass -File scripts\new-tool.ps1 -Group scripts -Subgroup windows -Name Cleanup -WhatIf
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Group,
    [Parameter(Mandatory = $true)][string]$Subgroup,
    [Parameter(Mandatory = $true)][string]$Name,
    [ValidateSet('utility', 'script', 'module')][string]$Kind = 'utility',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$RepoRoot     = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'manifest.csv'

$ValidGroups = @('os','rescue','diagnostics','security','network','drivers','backup',
                 'deployment','scripts','docs-offline','_scratch')

if ($ValidGroups -notcontains $Group) {
    throw "группа «$Group» вне списка. Допустимые: $($ValidGroups -join ', ')"
}
if ($Subgroup -notmatch '^[a-z0-9][a-z0-9_-]*$') {
    throw "subgroup «$Subgroup» должен быть в нижнем регистре: a-z 0-9 _ -"
}
if ($Name -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') {
    throw "name «$Name» содержит недопустимые символы (латиница, цифры, . _ -)"
}

$Target = Join-Path $RepoRoot "tools\$Group\$Subgroup\$Name"
$Template = switch ($Kind) {
    'utility' { 'UTILITY_README.md' }
    'script'  { 'SCRIPT_README.md' }
    'module'  { 'MODULE_README.md' }
}
$TemplatePath = Join-Path $RepoRoot "tools\_templates\$Template"
if (-not (Test-Path -LiteralPath $TemplatePath)) { throw "нет шаблона $TemplatePath" }

if ((Test-Path -LiteralPath $Target) -and -not $Force -and -not $WhatIfPreference) {
    throw "$Target уже существует. Повторите с -Force, чтобы перезаписать README.md"
}

$Today = Get-Date -Format 'yyyy-MM-dd'

function Add-CsvRow {
    param([string[]]$Fields)
    $escaped = foreach ($f in $Fields) {
        if ($f -match '[,"]') { '"' + ($f -replace '"', '""') + '"' } else { $f }
    }
    Add-Content -LiteralPath $ManifestPath -Value ($escaped -join ',') -Encoding UTF8
}

Write-Host "Создание: tools\$Group\$Subgroup\$Name (kind=$Kind)"

if ($PSCmdlet.ShouldProcess($Target, 'Создать каталог утилиты')) {
    New-Item -ItemType Directory -Path $Target -Force | Out-Null

    $readmePath = Join-Path $Target 'README.md'
    if ((Test-Path -LiteralPath $readmePath) -and -not $Force) {
        Write-Host "  пропускаю $readmePath (уже есть, нужен -Force)"
    } else {
        $body = (Get-Content -LiteralPath $TemplatePath -Raw -Encoding UTF8) `
            -replace '<Название утилиты>', $Name `
            -replace '<Название скрипта или набора скриптов>', $Name `
            -replace '<Название модуля>', $Name `
            -replace '<ГГГГ-ММ-ДД>', $Today
        Set-Content -LiteralPath $readmePath -Value $body -Encoding UTF8
        Write-Host "  создан $readmePath"
    }
}

# --- индексы группы и подкатегории (литеральные here-строки + маркеры) ---
$groupBody = @'
# {{GROUP}}/ — группа «{{GROUP}}»

> Индекс создаётся автоматически скриптом `scripts/new-tool.ps1`.
> Заполните описание группы: что здесь лежит и когда применяется.

## Подкатегории

| Подкатегория | Содержимое |
|--------------|-----------|
| `{{SUBGROUP}}/` | — |

## Правила

- Одна утилита = один каталог с `README.md`.
- Бинарники хранятся заглушками `<имя>.<расширение>.md` (см. `/CONVENTIONS.md`).
- Каждая утилита регистрируется в `/manifest.csv`.
'@

$subBody = @'
# {{SUBGROUP}}/ — подкатегория группы «{{GROUP}}»

> Индекс создаётся автоматически скриптом `scripts/new-tool.ps1`.
> Опишите, какие задачи закрывают утилиты этой подкатегории.

## Состав

| Каталог | Назначение |
|---------|-----------|
| `{{NAME}}/` | — |
'@

$indexes = @(
    @{ Dir = (Join-Path $RepoRoot "tools\$Group");                  Body = $groupBody },
    @{ Dir = (Join-Path $RepoRoot "tools\$Group\$Subgroup");        Body = $subBody }
)

foreach ($item in $indexes) {
    $index = Join-Path $item.Dir 'README.md'
    if ($PSCmdlet.ShouldProcess($index, 'Создать индекс каталога')) {
        New-Item -ItemType Directory -Path $item.Dir -Force | Out-Null
        if (-not (Test-Path -LiteralPath $index)) {
            $text = $item.Body -replace '\{\{GROUP\}\}', $Group `
                               -replace '\{\{SUBGROUP\}\}', $Subgroup `
                               -replace '\{\{NAME\}\}', $Name
            Set-Content -LiteralPath $index -Value $text -Encoding UTF8
            Write-Host "  создан $index"
        }
    }
}

# --- строка manifest.csv ---
$existing = Import-Csv -LiteralPath $ManifestPath |
    Where-Object { $_.type -eq 'tool' -and $_.category -eq "$Group/$Subgroup" -and $_.name -eq $Name }

if ($existing) {
    Write-Host "  manifest.csv: запись для $Name уже есть, пропускаю"
} elseif ($PSCmdlet.ShouldProcess($ManifestPath, "Добавить запись $Name")) {
    # Порядок полей строго как в заголовке:
    # type,category,name,file,url,sha256,size_bytes,version,added,status
    Add-CsvRow -Fields @('tool', "$Group/$Subgroup", $Name, '', '', 'PENDING', '0', 'PENDING', $Today, 'planned')
    Write-Host "  manifest.csv: добавлена запись $Name"
}

Write-Host ''
Write-Host 'Готово. Дальше:'
Write-Host "  1. Заполните $Target\README.md (уберите все <...>)."
Write-Host '  2. Положите бинарник на флешку и создайте заглушку <имя>.<расширение>.md.'
Write-Host '  3. scripts\repo-validate.ps1 — проверить и закоммитить.'
