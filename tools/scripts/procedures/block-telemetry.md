# Блокировка телеметрии и вендорского мусора

**Шаг 9 станционного алгоритма.** Выполняется после базовой настройки, **при
отключённой сети**. Порядок групп фиксирован:
**P0 → P1a → P1b → P2 → T → P3 → P5**.

> **База пути.** Непомеченные пути в этом документе считаются от корня
> репозитория. Префиксы `CONVENTIONS.md` §10.1 применяются там, где путь
> указывает на раздел флешки.

## Перед началом

| Условие | Проверка |
|---------|----------|
| Шаг 8 выполнен | [`basic-setup.md`](basic-setup.md) |
| Сеть физически отключена | Шаг 3 алгоритма |
| Дамп снят | [`../system-audit.ps1`](../system-audit.ps1) `-OutDir E:\reports` |
| Профиль настроен | [`../apply-blocking.conf`](../apply-blocking.conf) |

Без дампа `apply-blocking` отклонит применение с кодом `3`. Это не
формальность: таблица «применили / откатили» в
[`../../../research/06-services-blocklist.md`](../../../research/06-services-blocklist.md)
опирается на значения из дампа.

## Шаг 1. Настроить профиль

Профиль — единственный управляющий файл. Перечни механизмов зашиты в скрипт:
это данные из `research/06`, а не настройка.

Открыть [`../apply-blocking.conf`](../apply-blocking.conf) и проверить:

| Ключ | По умолчанию | Комментарий |
|------|--------------|-------------|
| `P0`–`P2` | `1` | Инициаторы и исполнители телеметрии |
| `T` | `1` | Скриптом не выполняется, см. шаг 5 |
| `P3` | `0` | Каждая позиция ломает рабочую функцию |
| `P3_ENABLE` | пусто | Перечислить явно под профиль заказчика |
| `P5` | `1` | Enforcement-задача |
| `EXCLUDE_SERVICES` | `icssvc,SharedAccess` | Точка доступа — рабочий инструмент выездного мастера |

Неизвестный ключ — ошибка, а не молчаливое игнорирование: опечатка не должна
превращаться в «профиль не сработал».

## Шаг 2. Пробный прогон

```powershell
& E:\tools\scripts\apply-blocking.ps1 -DryRun
```

Показывает все действия и обратные команды, ничего не меняя. Проверить, что в
списке нет того, что нужно сохранить.

## Шаг 3. Применение

```powershell
& E:\tools\scripts\apply-blocking.ps1 -Audit E:\reports\<дамп> -ReportDir E:\reports
```

Скрипт применит группы в фиксированном порядке и запишет отчёт о фактически
применённом. Код `4` означает «применено не всё»: смотрите вывод, там по одной
обратной команде на каждое проваленное действие.

**Автоматический откат не выполняется.** Откат без спроса падает по той же
причине, по которой упало применение — так поступил Win11Debloat (PR #613 был
реализован и отклонён именно по этому основанию).

## Шаг 4. Provisioned и установленные пакеты — нужны оба действия

Одного из двух недостаточно:

```powershell
# Для новых пользователей станции
Get-AppxProvisionedPackage -Online | Where-Object { $_.DisplayName -match '<маска>' } |
    Remove-AppxProvisionedPackage -PackageName { $_.PackageName }

# Для текущей учётной записи
Get-AppxPackage | Where-Object { $_.Name -match '<маска>' } | Remove-AppxPackage
```

Без удаления provisioned-пакета приложение вернётся для каждого нового
пользователя (гипотеза H5 из `research/06`).

## Шаг 5. Точечные запреты и локальные политики — отдельный шаг

`apply-blocking` **не подменяет системные исполняемые файлы**: wrapper-подмена
ломает проверку целостности (SFC, `DISM /Verify`) и не откатывается дампом.
Запреты отдельных команд (`DISM /RestoreHealth`, `powercfg /hibernate on`,
`fsutil behavior set DisableDeleteNotify 1`, `vssadmin delete shadows`,
`bcdedit /set recoveryenabled No`) реализуются локальной политикой.

Инструмент — `LGPO.exe` из Security Compliance Toolkit, лежит в
[`../../os/windows/gpo_lock/`](../../os/windows/gpo_lock/).

```powershell
# 1. Резервная копия текущей локальной политики — это штатный откат слоя GPO
& E:\tools\os\windows\gpo_lock\LGPO.exe /b E:\reports\gpo-backup

# 2. Применение
& E:\tools\os\windows\gpo_lock\LGPO.exe /g E:\config\station-policy
```

GPO намеренно вынесены из скрипта: у политики свой механизм отката
(`LGPO.exe /b`), и смешивать два механизма в одном скрипте — значит потерять
понимание, что именно откатывать.

## Шаг 6. Блокировка endpoints

На уровне `hosts` и роутера — по
[`../../../research/06-services-blocklist.md`](../../../research/06-services-blocklist.md).
Блокировка на роутере предпочтительнее: она переживает переустановку ОС и
покрывает все устройства в сети, а не одну станцию.

## Шаг 7. Enforcement-задача

Ставится автоматически при `P5 = 1` (паттерн P5 из
[`../../../research/03-patterns.md`](../../../research/03-patterns.md)): запуск
от SYSTEM, при старте с задержкой ~2 мин и далее раз в 6 часов, идемпотентна,
пишет лог «что вернулось».

```powershell
Get-ScheduledTask -TaskName 'ImmutableStation-Enforcement'
```

Лог задачи — готовый артефакт для отчёта и для ответа на вопрос «почему мусор
вернулся».

## Шаг 8. Контроль

```powershell
& E:\tools\scripts\system-audit.ps1 -OutDir E:\reports
& E:\tools\scripts\system-audit.ps1 -OutDir E:\reports -Diff E:\reports\<исходный дамп>
```

Код `4` — «найдены отклонения». Здесь это означает, что **что-то вернулось**:
сработал механизм самовосстановления. Смотреть надо его, а не повторять
применение.

## Проверка

| Что | Команда | Норма |
|-----|---------|-------|
| Телеметрия | `(Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection').AllowTelemetry` | 0 |
| Службы | `Get-Service DiagTrack, dmwappushservice \| Select Name, Status, StartType` | Stopped / Disabled |
| Задачи | `Get-ScheduledTask -TaskPath '\Microsoft\Windows\Application Experience\' \| Select TaskName, State` | Disabled |
| Enforcement-задача | `Get-ScheduledTask -TaskName 'ImmutableStation-Enforcement'` | Ready |
| Отчёт | `E:\reports\apply-blocking-*.txt` | существует |

## Откат

1. Значения реестра и состояния служб — по дампу `system-audit` и таблице
   «применили / откатили» в `research/06`;
2. задачи — `Enable-ScheduledTask`;
3. службы — `Set-Service -StartupType Manual` (исходный тип запуска взят из
   дампа, а не «Manual по умолчанию»);
4. политики — восстановить из копии `LGPO.exe /b`;
5. enforcement-задача — `Unregister-ScheduledTask -TaskName 'ImmutableStation-Enforcement' -Confirm:$false`;
6. удалённые приложения копией реестра **не возвращаются** — только Store или
   `winget`.

## Не проверено на месте

| Пункт | Что нужно |
|-------|-----------|
| Порядок P0–P3 на живой системе | Ни разу не прогонялся; очерёдность обоснована исследованием, а не практикой |
| `apply-blocking.ps1` | PowerShell в рабочей среде отсутствует |
| Имена provisioned-пакетов на IoT Enterprise LTSC 2024 | Состав отличается от потребительской редакции |
| Точные условия лицензии LGPO.exe | Прочитано описание «Proprietary (Freeware), лицензионного сбора нет», текст условий Microsoft не проверен |
| Версия LGPO.exe | В manifest записана 3.3 как ориентир; фактическая версия в архиве не проверена |
| Маска для отбора «мусорных» appx | Подбирается по факту на станции |
