# LGPO.exe — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `LGPO.exe` |
| Назначение | Применение и резервное копирование локальной групповой политики без редактора `gpedit.msc` |
| Версия | `PENDING` — не проверена |
| Источник | https://www.microsoft.com/en-us/download/details.aspx?id=55319 |
| SHA256 | `PENDING` |
| Размер | `PENDING` |
| Лицензия | Proprietary (Freeware) |
| Статус | `planned` |

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

Опубликованной Microsoft контрольной суммы для этого файла найти не удалось,
поэтому сверять не с чем — сумма фиксирует только неизменность нашей копии.

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
| Версия | В каталоге загрузки версия не читалась |
| Размер архива и файла | Не измерялся |
| Точный текст лицензионных условий | Прочитано описание «Proprietary (Freeware), лицензионного сбора нет» в стороннем каталоге (VA TRM); сам текст Microsoft не проверен |
| Поведение на IoT Enterprise LTSC 2024 | Не запускался |
| Состав архива `LGPO.zip` | Не проверялся; кроме `.exe` там могут быть примеры политик |
