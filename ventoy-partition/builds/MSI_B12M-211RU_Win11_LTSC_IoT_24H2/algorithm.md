# algorithm.md — MSI Modern 15 B12M-211RU → Windows 11 IoT Enterprise LTSC 2024

**Цель алгоритма:** безопасно подготовить станцию и выполнить миграцию на
выбранную ОС с сохранением необходимых данных и проверкой результата.

**Критерии успеха алгоритма:** необходимые данные восстановимы; целевая ОС,
драйверы и согласованные настройки проверены; ограничения лицензирования
зафиксированы; финальная проверка и резервная копия подтверждены.
Сам факт выполнения команд не означает достижения этих критериев.

**Навигация:** [паспорт](#0-паспорт) · [порядок шагов](#2-порядок-шагов) ·
[Шаг 1](#msi-diag-01) · [полевые результаты](field-notes.md) ·
[валидация](#5-валидация-развёрнутой-системы).
Приведение остальных элементов к CONVENTIONS §7.5 выполняется поэтапно;
их прежнее оформление не означает подтверждения практикой.

## 0. Паспорт

| Поле | Значение |
|------|----------|
| Станция | MSI Modern 15 B12M-211RU, выпуск 10/2022 |
| Целевая ОС | Windows 11 IoT Enterprise LTSC 2024 (база 24H2), EOL 2034-10-10 |
| Источник | `ISO/windows/en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso` |
| CPU / GPU | Intel Core i3-1215U / Intel UHD (встроенная) |
| ОЗУ | 8 ГБ DDR4-3200, **распаяна** — апгрейд невозможен |
| Накопитель | NVMe 256 ГБ |
| Экран | 15.6" IPS FHD |
| Сеть | Wi-Fi 6 (Intel AX211) + BT 5.2 (Realtek), проводного порта нет |
| Питание | USB-C PD |
| Предустановлено | Windows 11 Home + утилиты MSI |
| Дата алгоритма | 2026-10-15 |
| Версия | 1.4 |

## 1. Область покрытия

**Покрывает:** диагностику живой системы, первоначальный бэкап, переразметку
NVMe, чистую установку LTSC, установку драйверов, блокировку телеметрии и
вендорского мусора, снижение износа SSD, валидацию и эксплуатацию.

**Не покрывает и требует вскрытия корпуса** (в цикл работ не входит):
замена накопителя, добавление памяти, чистка системы охлаждения, замена
термоинтерфейса.

Ограничение железа: ОЗУ распаяна, 8 ГБ — потолок. Это влияет на разметку
(размер файла подкачки) и на состав софта — тяжёлые среды разработки на этой
станции работают впритык.

## 2. Порядок шагов

| # | Шаг | Инструмент | Сеть | Точка отката | Критерий успеха |
|---|-----|-----------|------|--------------|-----------------|
| 1 | [Бережная диагностика](#msi-diag-01) | Strelec WinPE / уже полученные сведения живой ОС | не требуется | не требуется | SMART, схема разделов, температуры, заключение с ограничениями |
| 2 | Первоначальный бэкап | `tools/backup/initial_backup` | online → **offline** | нет копии — работы не начинаются | образ диска + драйверы + Chrome + VS Code, все прошли `verify-backup` |
| 3 | Физическое отключение сети | Wi-Fi off в BIOS / выключить роутер | **offline** | — | в ОС нет адреса, индикатор Wi-Fi погашен |
| 4 | Загрузка с Ventoy | Ventoy, пункт ISO | **offline** | — | загрузка в UEFI-режиме |
| 5 | Разметка NVMe | `diskpart` | **offline** | образ диска (шаг 2) | 4 раздела (WinRE, System, MSR, Windows), выравнивание 4096 |
| 6 | Установка LTSC | `autounattend.xml` из `answer/` | **offline** | образ диска | OOBE пройден без сети, учётная запись создана |
| 7 | Драйверы | `drivers/`, `DISM /Add-Driver` | **offline** | образ диска | `pnputil /enum-devices /problem` → 0 |
| 8 | Базовая настройка | `config/`, `scripts/` | **offline** | образ диска | параметры применены, реестр выгружен в `.reg` |
| 9 | Блокировка телеметрии и мусора | `config/`, GPO, планировщик, hosts | **offline** | `.reg` из шага 8 | ключи = 0, службы Stopped, задачи Disabled |
| 10 | Оптимизация под SSD и 8 ГБ | `powercfg`, `fsutil`, pagefile | **offline** | `.reg` из шага 8 | TRIM=0, гибернация off, pagefile фиксирован |
| 11 | Первое включение сети | — | **online (под контролем)** | откат настроек шага 9 | подключение есть, трафик на телеметрию отсутствует |
| 12 | Ключ продукта и активация | `slmgr`, `slui 4` | **online** | `slmgr /upk` | `slmgr /dlv` → License Status: Licensed |
| 13 | Валидация развёрнутой системы | раздел 5 | **online** | — | все 12 проверок в норме |
| 14 | Обновления Windows | Центр обновления | **online** | точка восстановления | обновления находятся и устанавливаются |
| 15 | Финальный бэкап эталона | `tools/backup/initial_backup` | online | — | `verify-backup` код 0, образ помечен как эталон |

Значения колонки «Сеть»: `online` — сеть доступна; `offline` — сеть физически
отключена; `online (под контролем)` — сеть есть, телеметрия уже заблокирована.

## 3. Правило сети

> Телеметрия уходит в сеть **до** того, как её заблокировали. Поэтому всё, что
> происходит между включением станции и применением блокирующих политик
> (шаги 3–10), выполняется при физически отключённой сети.

На этой станции проводного порта нет, сеть только Wi-Fi. Отключение выполняется
одним из способов, в порядке предпочтения:

1. **Wi-Fi выключен в BIOS/UEFI** — самый надёжный, переживает переустановку ОС.
2. Адаптер отключён в `OOBE` до первого подключения (LTSC позволяет пропустить).
3. Роутер выключен или станция вне зоны действия.

Исключение — шаги 11–13, где сеть нужна по сути. Они идут **строго после**
шага 9.

Если станцию нельзя отключить физически (например, корпоративный сегмент),
блокировка выполняется на маршрутизаторе до первого включения новой ОС.

### Карта сущностей

Единый перечень всего, что применяется в алгоритме. По этой таблице можно
собрать всё необходимое для работы, не читая шаги. Правило — `CONVENTIONS.md` §10.

| Сущность | Тип | Путь на флешке | Шаг |
|---|---|---|---|
| [`en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso`](../../../ventoy-partition/ISO/windows/) | образ | `VENTOY:/ISO/windows/` | 4, 6 |
| [`WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso`](../../../ventoy-partition/ISO/winpe/) | образ | `VENTOY:/ISO/winpe/` | 4, 5 |
| [`ventoy.json`](../../../ventoy-partition/ventoy/ventoy.json) | конфигурация | `VENTOY:/ventoy/ventoy.json` | 4, 6 |
| [`answer/autounattend-ltsc-2024.xml`](answer/autounattend-ltsc-2024.xml) | файл ответа | `BUILD:/answer/` | 6 |
| [`answer/autounattend-ltsc-2024-bypass.xml`](answer/autounattend-ltsc-2024-bypass.xml) | файл ответа | `BUILD:/answer/`, при обходе требований | 6 |
| [`drivers/`](drivers/) | каталог | `BUILD:/drivers/` | 2, 7 |
| [`reports/`](reports/) | каталог | `BUILD:/reports/` | 1, 12, 13 |
| [`backup/`](backup/) | каталог | `BUILD:/backup/` | 2, 15 |
| [`export-drivers.ps1`](../../../tools/backup/initial_backup/scripts/export-drivers.ps1) | скрипт | `TOOLS:/backup/initial_backup/scripts/` | 2, 15 |
| [`backup-chrome.ps1`](../../../tools/backup/initial_backup/scripts/backup-chrome.ps1) | скрипт | `TOOLS:/backup/initial_backup/scripts/` | 2, 15 |
| [`backup-vscode.ps1`](../../../tools/backup/initial_backup/scripts/backup-vscode.ps1) | скрипт | `TOOLS:/backup/initial_backup/scripts/` | 2, 15 |
| [`verify-backup.ps1`](../../../tools/backup/initial_backup/scripts/verify-backup.ps1) | скрипт | `TOOLS:/backup/initial_backup/scripts/` | 2, 15 |
| [`disk-image.sh`](../../../tools/backup/disk_image/scripts/disk-image.sh) | скрипт | `TOOLS:/backup/disk_image/scripts/` | 2, 15 |
| [`integrate-drivers.sh`](../../../tools/drivers/export/scripts/integrate-drivers.sh) | скрипт | `TOOLS:/drivers/export/scripts/` | 7 |
| [`basic-setup.md`](../../../tools/scripts/procedures/basic-setup.md) | процедура | `TOOLS:/scripts/procedures/` | 8 |
| [`block-telemetry.md`](../../../tools/scripts/procedures/block-telemetry.md) | процедура | `TOOLS:/scripts/procedures/` | 9, 14 |
| [`ssd-ram-tuning.md`](../../../tools/scripts/procedures/ssd-ram-tuning.md) | процедура | `TOOLS:/scripts/procedures/` | 10 |
| [`validation.md`](../../../tools/scripts/procedures/validation.md) | процедура | `TOOLS:/scripts/procedures/` | 13 |
| [`apply-blocking.ps1`](../../../tools/scripts/apply-blocking.ps1) | скрипт | `TOOLS:/scripts/` | 9 |
| [`apply-blocking.conf`](../../../tools/scripts/apply-blocking.conf) | профиль | `TOOLS:/scripts/` | 9, 14 |
| [`tune-ssd-ram.ps1`](../../../tools/scripts/tune-ssd-ram.ps1) | скрипт | `TOOLS:/scripts/` | 10 |
| [`validate-system.ps1`](../../../tools/scripts/validate-system.ps1) | скрипт | `TOOLS:/scripts/` | 13 |
| [`tools/diagnostics/strelec-tools.md`](../../../tools/diagnostics/strelec-tools.md) | перечень утилит Strelec | `TOOLS:/diagnostics/` | 1 |
| [`research/07-blocking-mechanisms.md`](../../../research/07-blocking-mechanisms.md) | исследование | `REPO:/research/`, на флешку не копируется | 9 |
| `diskpart`, `DISM`, `pnputil`, `slmgr`, `slui`, `powercfg`, `fsutil`, `wmic` | средство ОС | `SYSTEM:` | 1, 5—14 |

**Как читать пути.** Префикс объявляет систему отсчёта — `CONVENTIONS.md` §10.1:

| Префикс | Откуда считается |
|---|---|
| `VENTOY:/` | корень раздела Ventoy, exFAT, 340.72 ГБ |
| `TOOLS:/` | корень раздела Tools, NTFS, 128.00 ГБ |
| `BUILD:/` | каталог этой сборки, `VENTOY:/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/` |
| `REPO:/` | корень репозитория — на флешку не копируется |
| `SYSTEM:` | команда или путь ОС, не сущность флешки |

Ссылка в первом столбце ведёт на файл в репозитории: это единственный адрес,
который можно проверить. Путь на флешке дан рядом, потому что `tools/` и
`builds/` лежат на разных разделах.

## 4. Шаги подробно

<a id="msi-diag-01"></a>
### Шаг 1. Бережная диагностика

**Цель:** получить достаточную исходную картину состояния MSI и внутреннего
NVMe без искусственной нагрузки и разрушительных действий, чтобы определить
допустимые дальнейшие действия. Выявленная неисправность не является
неуспехом диагностики, если результат достоверен и решение обосновано.

**Критерии успеха:** оборудование и внутренний диск идентифицированы; схема
разделов и SMART получены; температуры и доступные флаги троттлинга рассмотрены
с указанием среды и длительности; ограничения отражены в заключении.
Отчёты сохранены на рабочем столе. Внешняя копия проверяется отдельно;
неподтверждённая копия не объявляется существующей или восстановимой.

**Границы:** только диагностика. Экспорт браузеров, Wi-Fi, пользовательских
секретов, лицензий и резервное копирование относятся к отдельному
предустановочному сбору. Сеть для аппаратной диагностики не требуется.
Не менять ради шага настройки BIOS, драйверы, разделы или параметры питания.

**Средства.**

| Средство | Расположение |
|---|---|
| DiskPart | `SYSTEM:` |
| CrystalDiskInfo, HWiNFO, Hard Disk Sentinel | `VENTOY:/ISO/winpe/` — имеющийся Strelec |

DiskPart; CrystalDiskInfo, HWiNFO, при необходимости Hard Disk
Sentinel из имеющегося Strelec 2026.02.05. Ничего дополнительно не скачивать.
Состав меню: [каталог Strelec](../../../tools/diagnostics/strelec-tools.md).

**Остановка:** зависание, исчезновение накопителя, ошибка ввода-вывода,
критическое SMART-предупреждение или достижение указанного утилитой
температурного предела. Зафиксировать симптом и согласовать продолжение;
не повторять запросы автоматически. Тесты поверхности, self-test, бенчмарки,
стрессы и исправление файловой системы в этот шаг не входят.

<a id="msi-diag-01-map"></a>
#### Схема накопителей — MSI-DIAG-01-MAP

**Цель:** сопоставить физические устройства и разделы без изменений.

**Критерии успеха:** модель внутреннего диска подтверждена, получены типы,
размеры и смещения разделов; внешние устройства отличены по модели и меткам.

В CMD от администратора выполнить `diskpart`, затем `list disk` и
`list volume`. По размеру выбрать кандидата: `select disk N`, затем
`detail disk`. Только после подтверждения модели выполнить `list partition`.
Номер N не переносить с другой станции или предыдущей загрузки.
Завершить `exit`. Все эти команды только просматривают сведения.

В MSI-практике команды выполнялись через текстовый сценарий `/s`, вывод
сохранялся в `%USERPROFILE%\Desktop\reports` живой Windows. В WinPE буквы
проверять заново: RAM-диск X: и его рабочий стол непостоянны. Не считать
«Исправен» из DiskPart заключением о физическом здоровье.

<a id="msi-diag-01-smart"></a>
#### SMART — MSI-DIAG-01-SMART

**Цель:** получить показатели именно внутреннего NVMe и отделить их от
данных внешнего носителя.

**Критерии успеха:** модель подтверждена, сохранены критические предупреждения,
запас, процент использования, ошибки целостности, журнал ошибок и температуры.
Если SMART недоступен, это явно записано как ограничение.

В CrystalDiskInfo выбрать внутренний диск по модели и объёму. Через
«Правка → Копировать» сохранить текст в Блокноте как
`Desktop\reports\nvme_smart_initial.txt` живой Windows. Полный отчёт с
серийным номером не публиковать. В WinPE сохранять результат не только на X:.
При неоднозначности допустим просмотр того же устройства в Hard Disk Sentinel
без запуска тестов. Недоступность SMART через USB не доказывает неисправность.

Не трактовать процент здоровья как гарантию, а число записей журнала — как
число повреждений данных. Сравнивать raw-значения с одинаковым основанием
счисления; неизвестную причину записей оставлять ограничением, а не поводом
для бесконечного перебора средств. Дополнительное исследование согласовывать.

<a id="msi-diag-01-idle"></a>
#### Температуры — MSI-DIAG-01-IDLE

**Цель:** наблюдать CPU и NVMe без искусственной нагрузки.

**Критерии успеха:** указаны среда, питание, поверхность, длительность,
температуры и доступные признаки троттлинга. Интервал статистики отделён от
общей длительности наблюдения; недоступные датчики не подменяются похожими.

Приоритет — HWiNFO из Strelec, Sensors-only. Ноутбук на твёрдой поверхности,
питание от блока. После завершения стартовой активности наблюдать CPU Package,
тепловой троттлинг и датчики внутреннего NVMe. Плановый интервал — 10 минут
после сброса Min/Max, без копирования, сканирования и тестов.
Сохранить снимки Current/Min/Max/Avg. При случайном сбросе указать фактические
интервалы; повторять наблюдение только если данных недостаточно для решения.
Результат WinPE не выдавать за характеристику простоя установленной Windows.

<a id="msi-diag-01-verdict"></a>
#### Заключение и переход — MSI-DIAG-01-VERDICT

**Цель:** принять ограниченное полученными свидетельствами решение.

**Критерии успеха:** перечислены факты, неопределённости, допустимые действия
и статус сохранения отчётов; дальнейшая нагрузка не назначена без необходимости.

Записать результаты отдельно в [field-notes.md](field-notes.md), без ключей,
паролей и полных серийных номеров. Внешнюю копию хранить на проверенном по метке
носителе; сравнить состав и SHA256 файлов с исходниками. Этот перенос и его
проверка в текущей практике ещё не подтверждены. Не использовать CUSU как
единственный экземпляр критичных данных при неустановленном здоровье носителя.

Отсутствие выявленных критических признаков позволяет перейти к согласованию
сохранения данных, но не разрешает разметку или переустановку без проверенного
бэкапа. Новые исследования не добавлять автоматически: достаточную первичную
диагностику завершать с явно указанными ограничениями.

**Статус практики:** диагностическая часть подтверждена владельцем 2026-10-23.
Критических признаков отказа внутреннего NVMe и перегрева не выявлено; причина
прироста журнала ошибок неизвестна, здоровье CUSU не установлено.
Диагностических данных достаточно; внешняя копия отчётов
не подтверждена. Одноразовые аппаратные проверки повторно не выполнять только
ради второго документа. Итоги и ошибки процедуры — в полевом журнале.

---

### Шаг 2. Первоначальный бэкап

**Цель.** Сделать станцию полностью восстановимой до любых разрушающих действий.

**Сеть.** online в начале (если нужны недостающие инструменты), **offline**
к моменту окончания.

**Средства.** Все пять лежат на разделе Tools, но не в `tools/scripts/`:

| Сущность | Что делает | Путь на флешке |
|---|---|---|
| [`export-drivers.ps1`](../../../tools/backup/initial_backup/scripts/export-drivers.ps1) | выгружает драйверы живой ОС | `TOOLS:/backup/initial_backup/scripts/` |
| [`backup-chrome.ps1`](../../../tools/backup/initial_backup/scripts/backup-chrome.ps1) | копия профиля Chrome | `TOOLS:/backup/initial_backup/scripts/` |
| [`backup-vscode.ps1`](../../../tools/backup/initial_backup/scripts/backup-vscode.ps1) | копия настроек VS Code | `TOOLS:/backup/initial_backup/scripts/` |
| [`disk-image.sh`](../../../tools/backup/disk_image/scripts/disk-image.sh) | образ диска из Clonezilla Live | `TOOLS:/backup/disk_image/scripts/` |
| [`verify-backup.ps1`](../../../tools/backup/initial_backup/scripts/verify-backup.ps1) | проверка каждой копии | `TOOLS:/backup/initial_backup/scripts/` |

Описание модулей — [`tools/backup/initial_backup/`](../../../tools/backup/initial_backup/)
и [`tools/backup/disk_image/`](../../../tools/backup/disk_image/).

**Действия.**
```powershell
# 2.1 Драйверы рабочей ОС (скрипт — tools/backup/initial_backup/scripts/)
export-drivers.ps1 -Destination <флешка>\builds\MSI_B12M-211RU_Win11_LTSC_IoT_24H2\drivers

# 2.2 Закрыть Chrome, затем профиль (скрипт — tools/backup/initial_backup/scripts/)
backup-chrome.ps1 -Destination <флешка>\builds\MSI_B12M-211RU_Win11_LTSC_IoT_24H2\backup\profiles

# 2.3 Закрыть VS Code, затем настройки (скрипт — tools/backup/initial_backup/scripts/)
backup-vscode.ps1 -Destination <флешка>\builds\MSI_B12M-211RU_Win11_LTSC_IoT_24H2\backup\profiles
```
```bash
# 2.4 Образ диска из Clonezilla Live (скрипт — tools/backup/disk_image/scripts/)
sudo bash disk-image.sh --device /dev/nvme0n1 \
    --destination /home/partimg --name MSI_B12M-211RU_before
```

**Проверка.**
```powershell
verify-backup.ps1 -Path <каждая копия>   # код 0 по каждой; tools/backup/initial_backup/scripts/
```
Код не 0 — бэкап переделать, работы не начинать.

**Откат.** Точки отката нет: это шаг, создающий точку отката.

---

### Шаг 3. Физическое отключение сети

**Цель.** Исключить отправку телеметрии до блокировки.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| Настройка Wi-Fi в BIOS | средство прошивки | `SYSTEM:` |
| `Get-NetAdapter`, `ipconfig`, `Test-Connection` | средство ОС | `SYSTEM:` |

Своих сущностей шаг не использует: отключение физическое, иначе оно ничего
не гарантирует.

**Действия.** Wi-Fi off в BIOS → перезагрузка → проверка в ОС.

**Проверка.**
```powershell
Get-NetAdapter | Select Name, Status        # все Disconnected
ipconfig /all                               # нет IPv4-адреса
Test-Connection 8.8.8.8 -Count 1            # не проходит
```

**Откат.** Включить Wi-Fi в BIOS.

---

### Шаг 4. Загрузка с Ventoy

**Цель.** Получить рабочую среду установки.

**Сеть.** offline.

**Средства.**

| Сущность | Где лежит на флешке |
|---|---|
| [`WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso`](../../../ventoy-partition/ISO/winpe/) | `VENTOY:/ISO/winpe/` |
| [`en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso`](../../../ventoy-partition/ISO/windows/) | `VENTOY:/ISO/windows/` |
| [`ventoy.json`](../../../ventoy-partition/ventoy/ventoy.json) | `VENTOY:/ventoy/ventoy.json` |

**Действия.** F11 / F7 при включении → boot menu → USB → выбрать пункт
`WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` (для разметки) или сразу
`en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso` (для установки).

Secure Boot: Ventoy работает с ним при `VTOY_SECURE_BOOT_POLICY` в
`ventoy.json`. IoT Enterprise LTSC допускает работу без TPM и Secure Boot.

**Проверка.** Загрузка в режиме UEFI, флешка видна, ISO запускается.

**Откат.** Не требуется.

---

### Шаг 5. Разметка NVMe

**Цель.** Получить чистую оптимальную разметку вместо заводской.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| `diskpart` | средство ОС | `SYSTEM:` |
| [`WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso`](../../../ventoy-partition/ISO/winpe/) | образ | `VENTOY:/ISO/winpe/` |
| [`answer/autounattend-ltsc-2024.xml`](answer/autounattend-ltsc-2024.xml) | эталон разметки | `BUILD:/answer/` |

Размеры разделов в командах ниже обязаны совпадать с разметкой файла ответа.
Расхождение между ними уже было найдено и исправлено в версии 1.3.

**Действия.**
```
diskpart
list disk
select disk <N>            # НЕ 0: см. предупреждение ниже
clean
convert gpt
create partition primary size=500
format quick fs=ntfs label="WinRE"
set id=de94bba4-06d1-4d40-a16a-bfd50179d6ac
gpt attributes=0x8000000000000001
create partition efi size=260
format quick fs=fat32 label="System"
assign letter=S
create partition msr size=128
create partition primary
format quick fs=ntfs label="Windows"
assign letter=W
exit
```

Разметка — **та же, что задаёт файл ответа** на шаге 6: WinRE 500 МБ, EFI
260 МБ, MSR 128 МБ, остаток под Windows. Совпадение обязательно: если разметка
шага 5 и разметка файла ответа различаются, результат зависит от того, какой
путь отработал, а станция должна получаться одинаковой в обоих случаях.

Размер EFI-раздела — 260 МБ: на 4Kn-дисках меньше 260 МБ нельзя, и на NVMe это
ничего не стоит. WinRE занимает 500 МБ из 256 ГБ — это 0.2 %, а без раздела
восстановления станция лишается среды восстановления.

**Предупреждение про `select disk`.** Файл ответа выбирает диск переменной
`$$VT_WINDOWS_DISK_NONVTOY_CLOSEST_256$$`, а `diskpart` — номером. Номер 0
может оказаться флешкой, и `clean` сотрёт носитель. Перед `clean` сверить
размер и модель — нужен именно NVMe на 256 ГБ.

**Критично для этого железа.** Установщик Windows может не увидеть NVMe на
Intel 11-го поколения и новее. Два решения:
- `Enable VMD controller = Disabled` в BIOS (предпочтительно), либо
- подсунуть драйвер Intel IRST/VMD в установщик (F6 или интеграция в образ).

**Проверка.**
```
diskpart → list volume       # четыре раздела: WinRE, System, MSR, Windows
```
Выравнивание — 4096 (стандарт для GPT + `create partition` без указания смещения).

**Откат.** Образ диска из шага 2 → `ocs-sr ... restoredisk`.

---

### Шаг 6. Установка LTSC

**Цель.** Поставить ОС без мусора и без походов через OOBE вручную.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`answer/autounattend-ltsc-2024.xml`](answer/autounattend-ltsc-2024.xml) | файл ответа | `BUILD:/answer/` |
| [`answer/autounattend-ltsc-2024-bypass.xml`](answer/autounattend-ltsc-2024-bypass.xml) | файл ответа, обход требований | `BUILD:/answer/` |
| [`ventoy.json`](../../../ventoy-partition/ventoy/ventoy.json) | конфигурация Ventoy | `VENTOY:/ventoy/ventoy.json` |
| [`en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso`](../../../ventoy-partition/ISO/windows/) | образ | `VENTOY:/ISO/windows/` |
| [`CONVENTIONS.md`](../../../CONVENTIONS.md) | правило файла ответа | `REPO:/CONVENTIONS.md` |

**Действия.** Файл ответа берётся из каталога сборки
[`answer/`](answer/), а не из общего `/ventoy/autoinstall/`: он учитывает NVMe
256 ГБ этой станции, конкретный образ LTSC 2024 и ТЗ владельца
([`CONVENTIONS.md` §6](../../../CONVENTIONS.md)).

**6.1. Выбрать файл.**

| Ситуация | Файл |
|----------|------|
| Целевая станция (i3-1215U, TPM 2.0, 8 ГБ, NVMe 256 ГБ) | [`answer/autounattend-ltsc-2024.xml`](answer/autounattend-ltsc-2024.xml) |
| Неподдерживаемое железо, обход требований | [`answer/autounattend-ltsc-2024-bypass.xml`](answer/autounattend-ltsc-2024-bypass.xml) |

**6.2. Скопировать на флешку** в каталог сборки на разделе Ventoy, под именем
`autounattend.xml`:

```
/mnt/ventoy/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/answer/autounattend-ltsc-2024.xml
  ->  <буква>:\builds\MSI_B12M-211RU_Win11_LTSC_IoT_24H2\autounattend.xml
```

Имя при копировании меняется намеренно: установщик Windows подхватывает только
`autounattend.xml`.

**НЕ В КОРЕНЬ ФЛЕШКИ.** Файл ответа в корневом каталоге применяется ко всем ISO
и отказаться от него нельзя (дефект Ventoy 1.1.05, `research/16`, N3).

**6.3. Отредактировать [`ventoy.json`](../../../ventoy-partition/ventoy/ventoy.json)** — блок `auto_install` в корне раздела
Ventoy. Текущая запись ведёт на общий каталог и **для этой станции неверна**:

```json
"auto_install": [
    {
        "parent": "/ISO/windows",
        "template": "/ventoy/autoinstall/autounattend.xml"
    }
]
```

Заменить на:

```json
"auto_install": [
    {
        "parent": "/ISO/windows",
        "template": "/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/autounattend.xml"
    }
]
```

Правится **одна строка** — значение `template`. Ключ `parent` остаётся
`/ISO/windows`: сопоставление по `image` не работает (`research/16`, K3).

**НЕ ДОБАВЛЯТЬ** ключи `timeout` и `autosel`. При заданном `autosel` и
отсутствующем `timeout` меню не появляется вовсе и шаблон применяется без
спроса (`research/16`, N5). Нужен именно режим ожидания выбора.

**6.4. Проверить конфигурацию до загрузки.** `F5 → Tools menu → Check plugin
json configuration (ventoy.json)` — покажет, распознан ли блок.

**6.5. Загрузить.** Ventoy → `/ISO/windows/` → образ LTSC 2024 → выбрать пункт
«boot with /builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/autounattend.xml». Обычная загрузка ISO остаётся
доступной — это способ поставить систему вручную, если шаблон не сработал.

**Проверка.**

| Что | Как | Норма |
|-----|-----|-------|
| Шаблон применился | `C:\Windows\Panther\unattend.xml` существует | файл есть |
| Разметка | `Get-Partition` | 4 раздела: WinRE 500 МБ, System 260 МБ, MSR 128 МБ, Windows |
| Установка на NVMe, не на флешку | `Get-Disk \| Select Number, FriendlyName` | системный диск — NVMe |
| Учётная запись | `Get-LocalUser` | `user`, группа Administrators |
| Сеть не запрашивалась | — | OOBE прошёл без запроса сети |

Если шаблон не применился, начинать диагностику с `C:\Windows\Panther\`, а не
с правки файла: чужой `autounattend.xml` от Rufus или Ventoy выше в порядке
поиска и молча перекрывает наш (`research/16`, N4).

**Откат.** Образ диска из шага 2. Точка невозврата — **начало** установки:
в файле стоит `WillWipeDisk = true`, данные накопителя уничтожаются до
завершения установки, а не после.

---

### Шаг 7. Драйверы

**Цель.** Завести всё железо из проверенных INF, без драйвер-паков.

**Сеть.** offline.

**Средства.** Драйверы — каталог [`drivers/`](drivers/) в сборке (на флешке
`builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/drivers/`), заполняется на шаге 2.1.
Скрипт интеграции — [`integrate-drivers.sh`](../../../tools/drivers/export/scripts/integrate-drivers.sh).
`DISM` и `pnputil` — средства установленной ОС.

**Действия.**
```powershell
DISM /Online /Add-Driver /Driver:<флешка>\builds\MSI_B12M-211RU_Win11_LTSC_IoT_24H2\drivers /Recurse
# либо по одному
pnputil /add-driver oem*.inf /install
```

Ожидаемый состав для B12M:

| Устройство | Hardware ID | INF |
|------------|-------------|-----|
| Wi-Fi Intel AX211 | `PCI\VEN_8086&DEV_51F0` | `netwtw08.inf` / `netwtw6e.inf` |
| Bluetooth Realtek | `USB\VID_0BDA&PID_D723` | `rtkfilter.inf` |
| Аудио Realtek | `INTELAUDIO\FUNC_01&VEN_10EC&DEV_0256` | `hdxsstmsi.inf` |
| Intel DTT / IPF | `DEV_461D` | `ipf_cpu.inf` |
| Intel GNA | `DEV_464F` | `gna.inf` |
| Чипсет Alder Lake | `DEV_4601` | `alderlakesystem.inf` |
| Накопитель | — | Intel IRST/VMD, если VMD включён в BIOS |

**Проверка.**
```powershell
pnputil /enum-devices /problem     # ожидается 0 проблемных
Get-NetAdapter | Select Name, Status, LinkSpeed
```

**Откат.** `DISM /Online /Remove-Driver /Driver:oemN.inf` по published name;
крайний случай — образ диска.

---

### Шаг 8. Базовая настройка

**Цель.** Применить профиль настроек до блокировки телеметрии.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`basic-setup.md`](../../../tools/scripts/procedures/basic-setup.md) | процедура | `TOOLS:/scripts/procedures/` |
| [`config/`](config/) | каталог политик сборки | `BUILD:/config/` |
| [`scripts/`](scripts/) | каталог скриптов сборки | `BUILD:/scripts/` |

**Действия.** Процедура — [`basic-setup.md`](../../../tools/scripts/procedures/basic-setup.md).

Порядок инструментов обязателен: WinUtil → Win11Debloat → Sophia точечно
→ свои скрипты. От порядка зависит одно конкретное значение реестра
(`NoAutoRebootWithLoggedOnUsers`), которое WinUtil удаляет.

Скрипты — [`tools/scripts/`](../../../tools/scripts/), политика — из `config/`.

**Проверка.** Все применённые значения выгружены в `.reg`-файл отката:
```powershell
reg export HKLM\SOFTWARE\Policies\Microsoft\Windows config\policies-before.reg
```

**Откат.** Импорт `config\policies-before.reg`.

---

### Шаг 9. Блокировка телеметрии и вендорского мусора

**Цель.** Убрать сбор данных и механизмы его самовосстановления.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`block-telemetry.md`](../../../tools/scripts/procedures/block-telemetry.md) | процедура | `TOOLS:/scripts/procedures/` |
| [`apply-blocking.ps1`](../../../tools/scripts/apply-blocking.ps1) | скрипт | `TOOLS:/scripts/` |
| [`apply-blocking.conf`](../../../tools/scripts/apply-blocking.conf) | профиль групп блокировки | `TOOLS:/scripts/` |
| [`research/07-blocking-mechanisms.md`](../../../research/07-blocking-mechanisms.md) | механизмы M1—M12 | `REPO:/research/` |
| [`LGPO.exe`](../../../tools/os/windows/gpo_lock/LGPO/LGPO.exe.md) | утилита | `TOOLS:/os/windows/gpo_lock/LGPO/` |

**Действия.** Процедура — [`block-telemetry.md`](../../../tools/scripts/procedures/block-telemetry.md).
Скрипт — [`apply-blocking.ps1`](../../../tools/scripts/apply-blocking.ps1), профиль —
[`apply-blocking.conf`](../../../tools/scripts/apply-blocking.conf). Порядок групп фиксирован:
P0 → P1a → P1b → P2 → T → P3 → P5.

Ниже — состав шага. Применять через скрипт, а не этими командами вручную:
скрипт печатает обратную команду до каждого изменения и пишет отчёт.

```powershell
# Реестр
Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' `
    -Name AllowTelemetry -Value 0 -Type DWord
Set-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection' `
    -Name DiagnosticData -Value 0 -Type DWord

# Службы
Set-Service DiagTrack        -StartupType Disabled; Stop-Service DiagTrack
Set-Service dmwappushservice -StartupType Disabled; Stop-Service dmwappushservice

# Задачи
Get-ScheduledTask -TaskPath '\Microsoft\Windows\Application Experience\' |
    Disable-ScheduledTask
```
Плюс: снятие provisioned-пакетов `DISM /Online /Remove-ProvisionedAppxPackage`
(для новых пользователей) **и** `Remove-AppxPackage` (для текущих) — одного
из двух недостаточно. Удаление утилит MSI. Блокировка endpoints телеметрии на
уровне hosts/роутера. Механизмы самовосстановления — по
[`research/07-blocking-mechanisms.md`](../../../research/07-blocking-mechanisms.md) (M1–M12): enforcement-задачи, IFEO,
WMI-подписки.

**Проверка.**
```powershell
(Get-ItemProperty 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\DataCollection').AllowTelemetry   # 0
Get-Service DiagTrack, dmwappushservice | Select Name, Status, StartType
Get-ScheduledTask -TaskPath '\Microsoft\Windows\Application Experience\' | Select TaskName, State
```

**Откат.** Импорт `.reg` из шага 8, `Enable-ScheduledTask`,
`Set-Service -StartupType Manual`.

---

### Шаг 10. Оптимизация под SSD и 8 ГБ ОЗУ

**Цель.** Снизить износ накопителя и уложиться в память.

**Сеть.** offline.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`ssd-ram-tuning.md`](../../../tools/scripts/procedures/ssd-ram-tuning.md) | процедура | `TOOLS:/scripts/procedures/` |
| [`tune-ssd-ram.ps1`](../../../tools/scripts/tune-ssd-ram.ps1) | скрипт | `TOOLS:/scripts/` |
| `powercfg`, `fsutil` | средство ОС | `SYSTEM:` |

**Действия.** Процедура — [`ssd-ram-tuning.md`](../../../tools/scripts/procedures/ssd-ram-tuning.md).
Скрипт — [`tune-ssd-ram.ps1`](../../../tools/scripts/tune-ssd-ram.ps1).

```powershell
powercfg /hibernate off                       # отключает и Fast Startup
fsutil behavior query DisableDeleteNotify     # ожидается 0 (TRIM включён)
```
Файл подкачки **не отключать**: при 8 ГБ распаянной памяти это прямой путь к
падениям. Ставится фиксированный размер, чтобы система не пересоздавала файл.

Свободное место на диске — не менее 10–15%. Кэш браузера и временные файлы
ограничить по размеру. Гибернация выключена, значит `hiberfil.sys` не занимает
место и не пишется.

**Проверка.** `powercfg /a` — гибернация недоступна; `DisableDeleteNotify` = 0;
размер `pagefile.sys` фиксирован.

**Откат.** `powercfg /hibernate on`, вернуть автоматический размер pagefile.

---

### Шаг 11. Первое включение сети

**Цель.** Подключить станцию, когда телеметрия уже заблокирована.

**Сеть.** online (под контролем).

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| Настройка Wi-Fi в BIOS | средство прошивки | `SYSTEM:` |
| Журнал роутера | средство владельца | `SYSTEM:` |

Своих сущностей шаг не использует. Журнал роутера — единственный независимый
способ увидеть, что станция никуда не обращается: средства самой станции
к этому моменту уже ограничены политиками шага 9.

**Действия.** Включить Wi-Fi в BIOS или подключить адаптер в ОС.

**Проверка.** Подключение установлено. Желательно параллельно смотреть
журнал роутера: запросов к доменам телеметрии быть не должно.

**Откат.** Откат настроек шага 9, затем повторный разбор.

---

### Шаг 12. Ключ продукта и активация

**Цель.** Поставить лицензию владельца. До этого шага система не
активирована, и это ожидаемое состояние.

**Сеть.** online.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| `slmgr`, `slui` | средство ОС | `SYSTEM:` |
| Ключ владельца | данные | не на флешке — ключ в репозиторий не кладётся |
| Значение ключа из прошивки | данные | записано на шаге 1 в `BUILD:/reports/` |

Ключ продукта в репозиторий и на флешку не копируется: `CONVENTIONS.md` §9
запрещает лицензионные ключи в открытом виде. GVLK в файле ответа — исключение,
он опубликован Microsoft и лицензией не является.

**Почему ключ не подхватился сам.** В прошивке станции зашит ключ
Windows 11 Home (OEM:OA3, лежит в ACPI-таблице MSDM). Файл ответа задаёт ключ
явно, поэтому установщик его не использует: ключ Home не подходит ни по
редакции, ни по каналу лицензирования для IoT Enterprise LTSC. Значение в
файле ответа — GVLK, он указывает редакции искать KMS-узел и **лицензией не
является**.

**Что проверить до ввода.** Какой ключ у владельца на руках. Таблица — про
**этот билд**, Windows 11 IoT Enterprise LTSC 2024; для других образов с
флешки она другая.

| Тип ключа | Канал | Годится для этого билда | Что делать |
|-----------|-------|-------------------------|------------|
| MAK для Windows 11 IoT Enterprise LTSC 2024 | Volume Licensing | **да** | ввести как есть |
| GVLK + доступный KMS-узел | Volume Licensing | **да**, если узел есть | GVLK уже стоит; нужна сеть до KMS-узла |
| OEM-ключ IoT Enterprise LTSC для этой станции | OEM | **да** | ввести как есть |
| Ключ из прошивки этой станции (Win11 Home, OEM) | OEM | **нет** | редакция другая; файл ответа его игнорирует |
| Retail-ключ Windows 11 Pro / Home | Retail | **нет** | редакция другая, активация не пройдёт |
| Retail-ключ Windows 11 Enterprise | Retail | **не проверено** | см. раздел 8, на станции не проверялось |
| Ключ Windows 10 IoT Enterprise LTSC 2021 | Volume Licensing / OEM | **не проверено** | возможен путь обновления, не исследован |
| Ничего из перечисленного | — | — | активация невозможна, см. примечание в конце |

Отвязка Retail-ключа ниже нужна для случаев, когда на флешке выбран образ
потребительской редакции (Pro, Home), а не этот билд. Для IoT Enterprise LTSC
она не применяется — Retail-ключ эту редакцию не активирует.

Проверить, что стоит сейчас:

```
slmgr /dlv
```

**Отвязка Retail-ключа от предыдущей станции.** Выполняется **на старой
станции**, и она должна быть доступна. Retail-лицензию можно перенести, но
только если она одновременно используется на одной машине.

На старой станции, в командной строке от имени администратора:

```
slmgr /upk
slmgr /cpky
```

`/upk` убирает ключ из системы, `/cpky` стирает его из реестра. Если старая
станция недоступна физически, переходить к телефонной активации ниже.

Если на старой станции была цифровая лицензия, привязанная к учётной записи
Microsoft, — сама по себе она переносится только тогда, когда исходная
лицензия была Retail. Цифровая лицензия, произошедшая от OEM, не переносится.

**Ввод ключа на этой станции.**

```
slmgr /ipk XXXXX-XXXXX-XXXXX-XXXXX-XXXXX
slmgr /ato
```

**Проверка.**

```
slmgr /dlv
slmgr /xpr
```

Ожидается `License Status: Licensed` и сообщение о бессрочной активации.
Тип лицензии в выводе `/dlv` должен совпадать с тем, что ввёл владелец:
`RETAIL`, `OEM` или `VOLUME_MAK`. Если там `VOLUME_KMSCLIENT` — ключ не
применился и стоит прежний GVLK.

**Если ключ уже используется — ошибка `0xC004C008`.**

1. Убедиться, что на старой станции выполнены `/upk` и `/cpky`.
2. Перезагрузить эту станцию.
3. Выполнить `slui 4`, выбрать регион, пройти телефонную активацию.

**Откат.**

```
slmgr /upk
```

Возврат к неактивированному состоянию. Данные и настройки не затрагиваются.

**Примечание о лицензировании.** Windows 11 IoT Enterprise LTSC 2024
распространяется по каналам OEM и Volume Licensing. Retail-ключ потребительских
редактур (Home, Pro) эту редакцию **не активирует** — не потому, что ключ
плохой, а потому, что редакция другая. Перед закупкой лицензии это надо
уточнить; вопрос не исследован до конца и записан в раздел 8.

**Проверить после активации.** Активация обращается к серверам Microsoft, а
телеметрия заблокирована на шаге 9. Убедиться, что блокировка не мешает:
`slmgr /ato` завершается успешно. Если нет — это надо зафиксировать, а не
обходить молча.

---

### Шаг 13. Валидация развёрнутой системы

**Цель.** Сдать станцию по 12 проверкам, а не на глаз.

**Сеть.** online.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`validation.md`](../../../tools/scripts/procedures/validation.md) | процедура | `TOOLS:/scripts/procedures/` |
| [`validate-system.ps1`](../../../tools/scripts/validate-system.ps1) | скрипт, 12 проверок | `TOOLS:/scripts/` |
| [`reports/`](reports/) | куда складывать отчёты | `BUILD:/reports/` |

Процедура — [`validation.md`](../../../tools/scripts/procedures/validation.md). Скрипт — [`validate-system.ps1`](../../../tools/scripts/validate-system.ps1).

См. раздел 5. Без прохождения всех пунктов станция не сдаётся.

Приёмка выполняется в **три прогона**, а не в один: пункт 11 физически
не проверяется до перезагрузки. Пункт 10 (`DISM /ScanHealth`) выполняется
минуты и запускается только по явному `-ScanHealth` — перед сдачей
выполнить с ним.

---

### Шаг 14. Обновления Windows

**Цель.** Убедиться, что блокировка телеметрии не убила Центр обновления.

**Сеть.** online.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| Центр обновления Windows | средство ОС | `SYSTEM:` |
| [`apply-blocking.conf`](../../../tools/scripts/apply-blocking.conf) | профиль блокировки | `TOOLS:/scripts/apply-blocking.conf` |
| [`block-telemetry.md`](../../../tools/scripts/procedures/block-telemetry.md) | процедура | `TOOLS:/scripts/procedures/` |

Профиль и процедура нужны для отката: если обновления не работают, ослабляют
блокировку точечно по группам профиля, а не отключают её целиком.

**Действия.** Запустить поиск обновлений, дождаться результата, установить.

**Проверка.** Обновления находятся и устанавливаются; в журнале нет ошибок
доступа к серверам.

**Откат.** Если обновления не работают — точечно ослабить блокировку, найти
конфликтующую политику, вернуть остальное.

---

### Шаг 15. Финальный бэкап эталона

**Цель.** Зафиксировать рабочую систему как точку восстановления и эталон.

**Сеть.** online.

**Средства.**

| Сущность | Тип | Путь на флешке |
|---|---|---|
| [`disk-image.sh`](../../../tools/backup/disk_image/scripts/disk-image.sh) | скрипт образа | `TOOLS:/backup/disk_image/scripts/` |
| [`verify-backup.ps1`](../../../tools/backup/initial_backup/scripts/verify-backup.ps1) | проверка копии | `TOOLS:/backup/initial_backup/scripts/` |
| [`backup/`](backup/) | куда складывать копию | `BUILD:/backup/` |
| [`reports/`](reports/) | отметка об эталоне | `BUILD:/reports/` |

**Действия.** Повторить шаг 2.4 с именем `MSI_B12M-211RU_clean`.

**Проверка.** `verify-backup` код 0, в `reports/` отметка об эталонном образе.

**Откат.** Не требуется.

## 5. Валидация развёрнутой системы

| # | Проверка | Команда / способ | Норма | Результат |
|---|----------|------------------|-------|-----------|
| 1 | Сбор телеметрии отключён | `AllowTelemetry`, `DiagnosticData` | 0 | |
| 2 | **Центр обновления работает** | поиск обновлений | находятся и ставятся | |
| 3 | Службы из блэклиста остановлены | `Get-Service DiagTrack, dmwappushservice` | Stopped / Disabled | |
| 4 | Задачи телеметрии отключены | `Get-ScheduledTask` (Application Experience) | Disabled | |
| 5 | Драйверы без проблем | `pnputil /enum-devices /problem` | 0 проблемных | |
| 6 | Wi-Fi и Bluetooth работают | `Get-NetAdapter`, подключение BT-устройства | Connected | |
| 7 | TRIM включён | `fsutil behavior query DisableDeleteNotify` | 0 | |
| 8 | Гибернация выключена | `powercfg /a` | недоступна | |
| 9 | Файл подкачки фиксирован | свойства системы / WMI | фиксированный размер | |
| 10 | Целостность хранилища | `DISM /Online /Cleanup-Image /ScanHealth` | без ошибок | |
| 11 | Настройки переживают перезагрузку | перезагрузка → повтор п.1–4 | значения не вернулись | |
| 12 | Бэкап снят и проверен | `verify-backup` | код 0 | |

Пункт 2 — **обязателен**. `AllowTelemetry = 0` ломает Центр обновления на части
редакций, а система без обновлений уязвимее системы с телеметрией.

Пункт 11 — обязателен: часть механизмов самовосстановления возвращает значения
после перезагрузки или по расписанию.

## 6. Точки отката

| Точка | Когда создана | Как использовать |
|-------|---------------|------------------|
| Образ диска до работ | шаг 2 | `ocs-sr ... restoredisk MSI_B12M-211RU_before` |
| Драйверы рабочей ОС | шаг 2 | `DISM /Add-Driver` |
| Профили Chrome и VS Code | шаг 2 | копирование в `%LOCALAPPDATA%` / `%APPDATA%` |
| Реестр до блокировки | шаг 8 | импорт `config\policies-before.reg` |
| Эталонный образ чистой системы | шаг 15 | восстановление и база для других станций |

## 7. Рекомендации по дальнейшей эксплуатации

**Регламент бэкапов.**
- Профили Chrome и VS Code — раз в месяц, `backup-chrome.ps1` / `backup-vscode.ps1`.
- Образ системы — раз в полгода и после крупных изменений, `disk-image.sh`.
- Каждая копия проверяется `verify-backup` в момент создания. Непроверенная
  копия равна отсутствию копии.

**Обновления.** Проверять раз в месяц. При отказе Центра обновления — сначала
проверить, не вернулись ли блокирующие политики, а не отключать их насовсем.

**Драйверы.** Только с сайта MSI и Intel. Драйвер-паки и «Driver Booster»-подобные
утилиты запрещены: они приносят телеметрию и неподписанные версии.

**Запрещено к установке.** MSI Center и прочие вендорские утилиты (источник
мусора и самовосстановления), «ускорители» и «чистильщики» реестра, сторонние
антивирусы с телеметрией. Защитник Windows на LTSC достаточен для профиля
«домашний ПК / малый бизнес».

**Учёт 8 ГБ распаянной памяти.** Держать закрытыми лишние вкладки и тяжёлые
среды разработки одновременно; при просадках — проверить размер pagefile, а не
отключать его.

**Износ SSD.** Следить за свободным местом (не менее 10–15%), не переносить
кэш и временные файлы на этот же накопитель без ограничения размера,
гибернацию не включать.

**Признаки отката настроек.** Телеметрия вернулась, если `AllowTelemetry` снова
не 0, служба `DiagTrack` снова Running, или в журнале роутера появились запросы
к доменам телеметрии. Действие: свериться с [`research/07-blocking-mechanisms.md`](../../../research/07-blocking-mechanisms.md),
найти сработавший механизм самовосстановления, устранить причину, а не только
значение.

**Сроки.** Контрольная проверка по разделу 5 — через 3 месяца после сдачи,
далее раз в полгода.

## 8. Не проверено на месте

| Пункт | Почему не проверено | Как проверить |
|-------|--------------------|---------------|
| Реальные Hardware ID устройств | взяты из базы по модели, не с этой машины | шаг 1, `Get-PnpDevice` |
| Влияние `AllowTelemetry = 0` на Центр обновления в IoT LTSC 2024 | поведение различается по редакциям | шаг 14 на реальной установке |
| Имена INF в экспорте драйверов | состав экспорта зависит от текущей ОС | шаг 2, `export-drivers.ps1` |
| Видимость NVMe установщиком при включённом VMD | зависит от версии BIOS | шаг 5 |
| Фактический размер занятого места под образ | станция не снималась | шаг 2.4, отчёт `ocs-sr` |
| Состав provisioned appx в образе `f6b14814` | образ у владельца, не распаковывался | `DISM /Image:...  /Get-ProvisionedAppxPackages` |
| Актуальность сборки Strelec на дату работ | сборки обновляются | сверка версии на сайте автора |
| Правомерность установки IoT Enterprise LTSC на произвольное железо владельца | редакция распространяется по каналам OEM и Volume Licensing; вопрос не исследован | уточнить у лицензионного партнёра Microsoft |
| Применимость Retail-ключа Windows 11 Enterprise к редакции IoT Enterprise LTSC | Retail-ключи потребительских редакций (Home, Pro) эту редакцию не активируют; про Enterprise не проверялось | шаг 12, `slmgr /dlv` |
| Путь обновления с ключа Windows 10 IoT Enterprise LTSC 2021 на LTSC 2024 | не исследован | лицензионный партнёр Microsoft |
| Доступность MAK и OEM-ключей IoT Enterprise LTSC для частного лица в Латвии/ЕС | каналы OEM и Volume Licensing; фактическая доступность не проверялась | лицензионный партнёр Microsoft |
| Ключ, фактически зашитый в прошивку этой станции | не читался | `wmic path SoftwareLicensingService get OA3xOriginalProductKey` |
| Влияние блокировки телеметрии на серверы активации | шаг 9 выполняется до шага 12, взаимодействие не проверялось | шаг 12, `slmgr /ato` |

## 9. История изменений

| Дата | Версия | Что изменилось |
|------|--------|----------------|
| 2026-10-07 | 1.0 | Первый выпуск: полный цикл от живой ОС до валидации |
| 2026-10-15 | 1.4 | Приведён к правилу навигации `CONVENTIONS.md` §10: во всех 15 шагах раздел «Средства», пути с префиксами базы пути, карта сущностей из 25 строк, ссылка на `LGPO.exe`, многоточие в названии пункта меню Ventoy заменено полным путём. Было 10 ссылок, стало 79 |
| 2026-10-15 | 1.3 | Шаг 5 приведён к разметке файла ответа: WinRE 500 МБ добавлен, MSR 16 -> 128 МБ, `select disk 0` заменён на выбор по размеру и модели — `clean` на флешке стирает носитель. Расхождение нашёл сквозной тест Этапа 10 |
| 2026-10-15 | 1.2 | Шаг 1 читает ключ из прошивки (`OA3xOriginalProductKey`). В шаге 12 — явная таблица, какой тип ключа годится для этого билда: MAK, GVLK+KMS и OEM для IoT — да; ключ из прошивки и Retail Pro/Home — нет; Retail Enterprise и ключ LTSC 2021 — не проверено |
| 2026-10-15 | 1.1 | Добавлен шаг 12 «Ключ продукта и активация» с отвязкой Retail-ключа от предыдущей станции; шаги 12—14 сдвинуты на 13—15. В файлы ответа внесён явный `ProductKey` (GVLK), чтобы установщик не подхватывал ключ из прошивки |
