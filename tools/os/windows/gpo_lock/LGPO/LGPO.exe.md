# LGPO.exe — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `LGPO.exe` |
| Назначение | Применение и резервное копирование локальной групповой политики без редактора `gpedit.msc` |
| Версия | **3.0.2004.13001** |
| Источник | https://www.microsoft.com/en-us/download/details.aspx?id=55319 |
| SHA256 | `cb7159d134a0a1e7b1ed2ada9a3ce8ce8f4de391d14403d55438af824247cc55` — архив `LGPO.zip`, источник сторонний |
| Размер | 531635 байт — архив `LGPO.zip` |
| Лицензия | Proprietary (Freeware) |
| Статус | `planned` |

## Версия

**3.0.2004.13001** — это строка из собственного вывода утилиты: «LGPO.exe -
Local Group Policy Object Utility / Version 3.0.2004.13001 / Copyright (C)
2015-2020 Microsoft Corporation». Вывод приведён в трёх независимых источниках,
включая зеркало `JaxVN/LGPO` на GitHub. Версия 3.0 добавила ключи `/ef` и `/p`
и исправила захват назначений прав пользователя в `/b` — по официальному блогу
Microsoft Tech Community от 2020-09-04. На странице загрузки при этом стоит
«Version: 1.0» — это версия набора Security Compliance Toolkit, а не файла.

## Как получить

`LGPO.exe` распространяется Microsoft в составе **Security Compliance Toolkit**,
отдельно от него не выкладывается. Архив называется `LGPO.zip`.

```
https://www.microsoft.com/en-us/download/details.aspx?id=55319
```

Штатная установка через `winget`:

```powershell
winget install -e --id Microsoft.SecurityComplianceToolkit.LGPO
```

Для флешки `winget` не годится: он ставит в систему, а нужна закреплённая копия
с известной контрольной суммой. Скачивать архив и класть файл как есть.

## Проверка подлинности

После скачивания вычислить SHA256 и внести его в `/manifest.csv` и в эту
заглушку вместо `PENDING`:

```powershell
Get-FileHash -Algorithm SHA256 "E:\tools\os\windows\gpo_lock\LGPO\LGPO.exe"
```

```bash
sha256sum "/mnt/tools/os/windows/gpo_lock/LGPO/LGPO.exe"
```

Опубликованной Microsoft контрольной суммы для этого файла нет. Есть сумма из
стороннего источника — Ожидаемая сумма из **стороннего источника**: prefetch-блок BigFix (forum.bigfix.com, 2024-11-11) для `LGPO.zip` с `download.microsoft.com/download/8/5/C/85C25433-A1B0-4FFA-9429-7E023E7DA8D8/LGPO.zip`. Microsoft своих сумм не публикует, поэтому это не первоисточник: сумма служит ориентиром, а не доказательством.

Сумма относится к архиву `LGPO.zip`, а не к `LGPO.exe`: сверять надо архив
сразу после скачивания, до распаковки.

## Куда положить на флешке

`Tools:\os\windows\gpo_lock\LGPO\` — файл как есть, распаковка не требуется.

## Как используется в проекте

Две команды, обе — в процедуре
[`../../../../tools/scripts/procedures/block-telemetry.md`](../../../../scripts/procedures/block-telemetry.md):

```powershell
# Резервная копия текущей локальной политики — это штатный откат слоя GPO
& E:\tools\os\windows\gpo_lock\LGPO\LGPO.exe /b E:\reports\gpo-backup

# Применение политики из каталога с .inf и .inf-секциями
& E:\tools\os\windows\gpo_lock\LGPO\LGPO.exe /g E:\config\station-policy
```

`/b` делает резервную копию локальной политики — именно поэтому применение
политик вынесено из `apply-blocking` в отдельный шаг: у GPO свой механизм
отката, и смешивать его с откатом по дампу реестра нельзя.

## Почему не `gpedit.msc`

Редактора локальной групповой политики в редакциях LTSC может не быть, а
`LGPO.exe` работает с теми же файлами напрямую и пригоден для переноса
готовой политики между станциями — что и нужно выездному мастеру.

## Не проверено

| Пункт | Что нужно |
|-------|-----------|
| Размер распакованного `LGPO.exe` | Не измерялся; 531635 байт — это архив |
| Точный текст лицензионных условий | Прочитано описание «Proprietary (Freeware), лицензионного сбора нет» в стороннем каталоге (VA TRM); сам текст Microsoft не проверен |
| Поведение на IoT Enterprise LTSC 2024 | Не запускался |
| Состав архива `LGPO.zip` | Не проверялся; кроме `.exe` там могут быть примеры политик |
