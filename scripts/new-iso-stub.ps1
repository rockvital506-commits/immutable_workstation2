<#
.SYNOPSIS
    new-iso-stub.ps1 — создать заглушку под ISO и запись в manifest.csv.

.DESCRIPTION
    Парная версия scripts/new-iso-stub.sh для Windows.
    Создаёт ventoy-partition\ISO\<Category>\<File>.md и строку type=iso в manifest.csv.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\new-iso-stub.ps1 `
        -Category windows -File Win11_24H2_x64_RU.iso `
        -Url https://www.microsoft.com/ru-ru/software-download -Version 24H2 `
        -Notes "Основной образ для установки Windows 11"

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\new-iso-stub.ps1 -Category winpe -File WinPE_11.iso -WhatIf
#>
#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $true)][string]$Category,
    [Parameter(Mandatory = $true)]$File,
    [string]$Url = '',
    [ValidatePattern('^(PENDING|[0-9a-fA-F]{64})$')][string]$Sha256 = 'PENDING',
    [ValidatePattern('^[0-9]+$')][string]$Size = '0',
    [string]$Version = '',
    [string]$Notes = '',
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$RepoRoot     = Split-Path -Parent $PSScriptRoot
$ManifestPath = Join-Path $RepoRoot 'manifest.csv'

$ValidCategories = @('windows','linux','winpe','diagnostics','security','network',
                     'backup','firmware','dos','_scratch')

if ($ValidCategories -notcontains $Category) {
    throw "категория «$Category» вне списка. Допустимые: $($ValidCategories -join ', ')"
}
if ($File -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*\.iso$') {
    throw "имя файла «$File» должно заканчиваться на .iso и содержать только латиницу, цифры, . _ -"
}

$IsoDir   = Join-Path $RepoRoot "ventoy-partition\ISO\$Category"
$StubPath = Join-Path $IsoDir "$File.md"

if ((Test-Path -LiteralPath $StubPath) -and -not $Force -and -not $WhatIfPreference) {
    throw "$StubPath уже существует. Повторите с -Force для перезаписи."
}

$Today = Get-Date -Format 'yyyy-MM-dd'
$Name  = "$File" -replace '\.iso$', ''

function Add-CsvRow {
    param([string[]]$Fields)
    $escaped = foreach ($f in $Fields) {
        if ($f -match '[,"]') { '"' + ($f -replace '"', '""') + '"' } else { $f }
    }
    Add-Content -LiteralPath $ManifestPath -Value ($escaped -join ',') -Encoding UTF8
}

Write-Host "Заглушка: ventoy-partition\ISO\$Category\$File.md"

# Литеральные here-строки: значения подставляются маркерами {{...}},
# чтобы бэктики Markdown и тройные бэктики блоков кода не экранировать.
$stubBody = @'
# {{FILE}}

> **Это заглушка.** Образ `{{FILE}}` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/{{CATEGORY}}/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `{{FILE}}` |
| Категория | `ISO/{{CATEGORY}}` |
| Версия | {{VERSION}} |
| Размер | {{SIZE}} байт |
| SHA256 | `{{SHA256}}` |
| Источник | {{URL}} |
| Лицензия | — |
| Добавлено | {{TODAY}} |
| Статус | planned |

## Назначение

{{NOTES}}

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\{{CATEGORY}}\{{FILE}}"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/{{CATEGORY}}/{{FILE}}"
```

Ожидаемое значение: `{{SHA256}}`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
'@

$categoryBody = @'
# {{CATEGORY}}/ — категория образов

> Индекс создаётся автоматически скриптом `scripts/new-iso-stub.ps1`.
> Опишите, какие образы здесь лежат и в каких ситуациях они применяются.

## Образы

| Файл | Назначение | Версия |
|------|-----------|--------|
| `{{FILE}}` | — | {{VERSION}} |

Правила именования и хранения — `/ventoy-partition/ISO/README.md`.
'@

$replacements = @(
    @('{{FILE}}',     "$File"),
    @('{{CATEGORY}}', $Category),
    @('{{VERSION}}',  $Version),
    @('{{SIZE}}',     $Size),
    @('{{SHA256}}',   $Sha256),
    @('{{URL}}',      $Url),
    @('{{NOTES}}',    $Notes),
    @('{{TODAY}}',    $Today)
)

function Expand-Markers {
    param([string]$Text)
    foreach ($pair in $replacements) { $Text = $Text.Replace($pair[0], $pair[1]) }
    return $Text
}

if ($PSCmdlet.ShouldProcess($StubPath, 'Создать заглушку ISO')) {
    New-Item -ItemType Directory -Path $IsoDir -Force | Out-Null

    $catReadme = Join-Path $IsoDir 'README.md'
    if (-not (Test-Path -LiteralPath $catReadme)) {
        Set-Content -LiteralPath $catReadme -Value (Expand-Markers $categoryBody) -Encoding UTF8
        Write-Host "  создан $catReadme"
    }

    Set-Content -LiteralPath $StubPath -Value (Expand-Markers $stubBody) -Encoding UTF8
    Write-Host "  создан $StubPath"
}

$existing = Import-Csv -LiteralPath $ManifestPath |
    Where-Object { $_.type -eq 'iso' -and $_.category -eq "ISO/$Category" -and $_.file -eq "$File" }

if ($existing) {
    Write-Host "  manifest.csv: запись для $File уже есть, пропускаю"
} elseif ($PSCmdlet.ShouldProcess($ManifestPath, "Добавить запись $File")) {
    # Порядок полей строго как в заголовке:
    # type,category,name,file,url,sha256,size_bytes,version,added,status
    Add-CsvRow -Fields @('iso', "ISO/$Category", $Name, "$File", $Url, $Sha256, $Size, $Version, $Today, 'planned')
    Write-Host "  manifest.csv: добавлена запись $File"
}

Write-Host ''
Write-Host 'Готово. Дальше:'
Write-Host "  1. Скачайте образ, положите в ventoy-partition\ISO\$Category\ на флешке."
Write-Host '  2. Заполните SHA256 и размер, поменяйте статус на present.'
Write-Host '  3. scripts\repo-validate.ps1; scripts\check-flash.ps1 -Verify'
