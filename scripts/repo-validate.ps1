<#
.SYNOPSIS
    repo-validate.ps1 — проверка репозитория на соответствие CONVENTIONS.md.

.DESCRIPTION
    Парная версия scripts/repo-validate.sh для Windows.
    Проверяет: обязательные файлы, отсутствие бинарников в git, именование,
    формат заглушек, manifest.csv, синтаксис и структуру ventoy.json.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\repo-validate.ps1

.OUTPUTS
    Код возврата 0 — всё в порядке, 1 — найдены ошибки.
#>
#Requires -Version 5.1
[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$script:Errors   = 0
$script:Warnings = 0
$script:Checks   = 0

function Write-Ok   { param([string]$M) $script:Checks++;   Write-Host "  OK   " -ForegroundColor Green  -NoNewline; Write-Host $M }
function Write-Warn { param([string]$M) $script:Warnings++; Write-Host "  WARN " -ForegroundColor Yellow -NoNewline; Write-Host $M }
function Write-Fail { param([string]$M) $script:Errors++;   Write-Host "  FAIL " -ForegroundColor Red   -NoNewline; Write-Host $M }
function Write-Head { param([string]$M) Write-Host ""; Write-Host $M -ForegroundColor Cyan }

# Расширения, которые не должны попадать в git (CONVENTIONS.md, раздел 2)
$BinaryExt = @(
    'iso','wim','esd','swm','vhd','vhdx','img','vtoy','efi','rom','bin','dat',
    'exe','msi','msu','dll','sys','com','scr','deb','rpm',
    'zip','7z','rar','gz','xz','bz2','zst','tar','cab',
    'pf2','png','jpg','jpeg','gif','bmp','ico','ttf','otf','woff','woff2',
    'mp3','mp4','mkv','avi','wav','pdf','doc','docx','xls','xlsx'
)

Write-Host "repo-validate — $RepoRoot" -ForegroundColor White

$AllFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -Force |
    Where-Object { $_.FullName -notmatch '[\\/]\.git[\\/]' }

function Get-RelPath { param([System.IO.FileInfo]$F) $F.FullName.Substring($RepoRoot.Length).TrimStart('\','/') }

# ------------------------------------------------------------
Write-Head '[1/6] Обязательные файлы корня'
# ------------------------------------------------------------
$RequiredFiles = @(
    'README.md','PLAN.md','CONVENTIONS.md','.gitignore','manifest.csv',
    'ventoy-partition/ventoy/ventoy.json','ventoy-partition/ISO/README.md',
    'tools/README.md'
)
foreach ($f in $RequiredFiles) {
    $full = Join-Path $RepoRoot ($f -replace '/', '\')
    if (Test-Path -LiteralPath $full -PathType Leaf) { Write-Ok "есть $f" } else { Write-Fail "отсутствует обязательный файл $f" }
}
foreach ($t in @('UTILITY_README.md','SCRIPT_README.md','MODULE_README.md')) {
    $full = Join-Path $RepoRoot "tools\_templates\$t"
    if (Test-Path -LiteralPath $full -PathType Leaf) { Write-Ok "есть шаблон tools/_templates/$t" }
    else { Write-Fail "отсутствует шаблон tools/_templates/$t" }
}

# ------------------------------------------------------------
Write-Head '[2/6] Бинарные файлы не должны быть в git'
# ------------------------------------------------------------
$BinFound = @($AllFiles | Where-Object { $BinaryExt -contains $_.Extension.TrimStart('.').ToLowerInvariant() })
if ($BinFound.Count -eq 0) {
    Write-Ok "бинарных файлов не найдено (проверено $($AllFiles.Count) файлов)"
} else {
    foreach ($b in $BinFound) { Write-Fail "бинарный файл в рабочем дереве: $(Get-RelPath $b) (нужна заглушка $(Get-RelPath $b).md)" }
}

# ------------------------------------------------------------
Write-Head '[3/6] Именование: только латиница, цифры, - _ .'
# ------------------------------------------------------------
$BadNames = @()
$AllEntries = Get-ChildItem -Path $RepoRoot -Recurse -Force |
    Where-Object { $_.FullName -notmatch '[\\/]\.git([\\/]|$)' }
foreach ($e in $AllEntries) {
    if ($e.Name -notmatch '^[A-Za-z0-9._-]+$') { $BadNames += (Get-RelPath $e) }
}
if ($BadNames.Count -eq 0) { Write-Ok 'все имена файлов и каталогов соответствуют правилу' }
else { foreach ($n in $BadNames) { Write-Fail "недопустимое имя: $n" } }

# ------------------------------------------------------------
Write-Head '[4/6] Заглушки: <имя>.<расширение>.md + README рядом'
# ------------------------------------------------------------
$StubPattern = '\.(' + ($BinaryExt -join '|') + ')\.md$'
$Stubs = @($AllFiles | Where-Object { (Get-RelPath $_) -imatch $StubPattern })
if ($Stubs.Count -eq 0) {
    Write-Ok 'заглушек пока нет (заполняется на Этапах 2 и 4)'
} else {
    foreach ($s in $Stubs) {
        $rel  = Get-RelPath $s
        $dir  = Split-Path -Parent $s.FullName
        $name = Split-Path -Leaf $rel

        if ($name -notmatch '\.[A-Za-z0-9]+\.md$') {
            Write-Fail "неверный формат имени заглушки: $rel (ожидается <имя>.<расширение>.md)"
        }
        if (-not (Test-Path -LiteralPath (Join-Path $dir 'README.md') -PathType Leaf)) {
            Write-Fail "рядом с заглушкой $rel нет README.md"
        }
        $body = Get-Content -LiteralPath $s.FullName -Raw -Encoding UTF8
        foreach ($field in @('SHA256','Источник')) {
            if ($body -notmatch [regex]::Escape($field)) { Write-Fail "в заглушке $rel нет поля «$field»" }
        }
    }
    Write-Ok "заглушек проверено: $($Stubs.Count)"
}

# ------------------------------------------------------------
Write-Head '[5/6] manifest.csv — структура и полнота'
# ------------------------------------------------------------
$ManifestPath = Join-Path $RepoRoot 'manifest.csv'
$ExpectedHeader = 'type,category,name,file,url,sha256,size_bytes,version,added,status'
if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    Write-Fail 'нет manifest.csv'
} else {
    $Rows = Import-Csv -LiteralPath $ManifestPath
    $FirstLine = (Get-Content -LiteralPath $ManifestPath -TotalCount 1)
    if ($FirstLine -eq $ExpectedHeader) { Write-Ok 'заголовок manifest.csv корректен' }
    else {
        Write-Fail 'заголовок manifest.csv не совпадает с эталоном'
        Write-Host "         эталон: $ExpectedHeader"
        Write-Host "         факт:   $FirstLine"
    }

    if (@($Rows).Count -eq 0) {
        Write-Ok 'записей в manifest.csv пока нет (заполняется на Этапах 2 и 4)'
    } else {
        $ValidTypes   = @('iso','tool','script','module')
        $ValidStatus  = @('planned','present','verified','deprecated')
        $RowBad = 0
        $Index  = 1
        foreach ($r in $Rows) {
            $Index++
            if ($ValidTypes  -notcontains $r.type)   { Write-Fail "manifest.csv — строка $Index : type=$($r.type) недопустим"; $RowBad++ }
            if ($ValidStatus -notcontains $r.status) { Write-Fail "manifest.csv — строка $Index : status=$($r.status) недопустим"; $RowBad++ }
            if ($r.size_bytes -notmatch '^[0-9]+$')  { Write-Fail "manifest.csv — строка $Index : size_bytes=$($r.size_bytes) не число"; $RowBad++ }
            if ($r.added -notmatch '^[0-9]{4}-[0-9]{2}-[0-9]{2}$') { Write-Fail "manifest.csv — строка $Index : added=$($r.added) не ГГГГ-ММ-ДД"; $RowBad++ }
            if ($r.status -ne 'planned' -and $r.sha256 -eq 'PENDING') { Write-Fail "manifest.csv — строка $Index : status=$($r.status) требует реальный SHA256"; $RowBad++ }
            if ($r.status -ne 'planned' -and $r.size_bytes -eq '0')   { Write-Fail "manifest.csv — строка $Index : status=$($r.status) требует реальный размер"; $RowBad++ }
            if ([string]::IsNullOrWhiteSpace($r.name)) {
                Write-Fail "manifest.csv — строка $Index : пустое name"; $RowBad++
            }
            if ([string]::IsNullOrWhiteSpace($r.file) -and $r.type -eq 'iso') {
                Write-Fail "manifest.csv — строка $Index : для type=iso обязательно поле file"; $RowBad++
            }
        }
        if ($RowBad -eq 0) { Write-Ok "все $(@($Rows).Count) записей manifest.csv корректны" }
    }
}

# ------------------------------------------------------------
Write-Head '[6/6] ventoy/ventoy.json — синтаксис и структура'
# ------------------------------------------------------------
$VJson = Join-Path $RepoRoot 'ventoy-partition\ventoy\ventoy.json'
if (Test-Path -LiteralPath $VJson -PathType Leaf) {
    $Raw = Get-Content -LiteralPath $VJson -Raw -Encoding UTF8
    try {
        $Data = $Raw | ConvertFrom-Json
    } catch {
        Write-Fail "ventoy.json — невалидный JSON: $($_.Exception.Message)"
        $Data = $null
    }
    if ($null -ne $Data) {
        $Problems = @()
        $ctrl = $Data.control
        if ($null -ne $ctrl -and $ctrl -isnot [System.Array]) {
            $Problems += 'control должен быть массивом объектов, а не объектом'
        }
        if ($ctrl -is [System.Array]) {
            foreach ($item in $ctrl) {
                $props = @($item.PSObject.Properties)
                if ($props.Count -ne 1) { $Problems += 'элемент control должен быть объектом с одним ключом' }
                else {
                    $k = $props[0].Name; $v = $props[0].Value
                    if ($k -notlike 'VTOY_*') { $Problems += "неизвестный ключ control: $k" }
                    if ($v -isnot [string])   { $Problems += "значение $k должно быть строкой в кавычках" }
                }
            }
        }
        $alias = $Data.menu_alias
        if ($null -ne $alias) {
            foreach ($item in $alias) {
                if ($null -eq $item.PSObject.Properties['alias']) { $Problems += 'элемент menu_alias без поля alias' }
            }
        }
        if ($Raw -match '/\*') { $Problems += 'парсер Ventoy не поддерживает комментарии (/*)' }

        if ($Problems.Count -gt 0) {
            foreach ($p in $Problems) { Write-Fail "ventoy.json — $p" }
        } else {
            $nCtrl  = if ($ctrl  -is [System.Array]) { @($ctrl).Count }  else { 0 }
            $nAlias = if ($alias -is [System.Array]) { @($alias).Count } else { 0 }
            Write-Ok "ventoy.json валиден: $nCtrl control-опций, $nAlias menu_alias"
        }
    }
} else {
    Write-Fail 'нет ventoy-partition/ventoy/ventoy.json'
}

# ------------------------------------------------------------
Write-Host ""
# 9. algorithm.md обязателен для каждой станционной сборки
$builds = Join-Path $ROOT 'ventoy-partition/builds'
if (Test-Path $builds) {
    $stations = @(Get-ChildItem $builds -Directory | Where-Object { $_.Name -ne '_templates' })
    foreach ($st in $stations) {
        $algo = Join-Path $st.FullName 'algorithm.md'
        if (-not (Test-Path $algo -PathType Leaf)) {
            $script:Errors++
            Write-Host ("  FAIL builds/{0}: нет algorithm.md (обязателен, CONVENTIONS.md раздел 6)" -f $st.Name) -ForegroundColor Red
            continue
        }
        $text = [IO.File]::ReadAllText($algo)
        foreach ($req in @('Порядок шагов', 'Валидация развернутой системы', 'Рекомендации по дальнейшей эксплуатации', 'Не проверено на месте')) {
            $probe = $req -replace 'е$', 'ё'
            $asHeading = '(?m)^## .*' + [regex]::Escape($req)
            $asProbe   = '(?m)^## .*' + [regex]::Escape($probe)
            if ($text -notmatch $asHeading -and $text -notmatch $asProbe) {
                $script:Errors++
                Write-Host ("  FAIL builds/{0}/algorithm.md: нет раздела-заголовка «{1}»" -f $st.Name, $req) -ForegroundColor Red
            }
        }
        $inSteps = $false
        $tbl = ''
        foreach ($l in ($text -split "`n")) {
            if ($l -match '^## .*Порядок шагов') { $inSteps = $true; continue }
            if ($inSteps -and $l -match '^## ') { break }
            if ($inSteps -and $l.StartsWith('|')) { $tbl += $l + "`n" }
        }
        if ($tbl -notmatch '\|\s*Сеть\s*\|') {
            $script:Errors++
            Write-Host ("  FAIL builds/{0}/algorithm.md: в таблице шагов нет колонки «Сеть»" -f $st.Name) -ForegroundColor Red
        }
        if ($tbl -notmatch 'online|offline') {
            $script:Errors++
            Write-Host ("  FAIL builds/{0}/algorithm.md: в таблице шагов нет статусов сети" -f $st.Name) -ForegroundColor Red
        }
    }
    if ($stations.Count -gt 0) {
        $script:Checks++
        Write-Host ("  OK   algorithm.md: проверено станций - {0}" -f $stations.Count) -ForegroundColor Green
    }
}

Write-Host "Итог: проверок — $($script:Checks), предупреждений — $($script:Warnings), ошибок — $($script:Errors)" -ForegroundColor White
if ($script:Errors -gt 0) {
    Write-Host 'Репозиторий не соответствует CONVENTIONS.md — коммитить нельзя.' -ForegroundColor Red
    exit 1
}
Write-Host 'Все проверки пройдены.' -ForegroundColor Green
exit 0
