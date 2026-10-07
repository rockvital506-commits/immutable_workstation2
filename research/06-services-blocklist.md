# 06. Службы и процессы: приоритизированный перечень обработки

## Правило приоритизации

```
приоритет = роль в цепочке запуска

инициатор / будильник / активатор  >>  инициализируемый / будимый / активируемый
```

Классы приоритета:

| Класс | Обозначение | Что это | Обработка |
|-------|-------------|---------|-----------|
| **P0** | Критический инициатор | Запускает или **восстанавливает** другие механизмы мусора | Отключается первым, всегда |
| **P1** | Инициатор | Таймер/событие, порождающее активность | Отключается до исполнителей |
| **P2** | Исполнитель | Запускается кем-то другим | Отключается после своих инициаторов |
| **P3** | Пассивный/условный | Активен только при наличии триггера или сценария | Отключается по ситуации |
| **T** | Точечный запрет | Инструмент полезен, запрещается **команда**, а не инструмент | Wrapper/фильтр аргументов |

---

## P0. Критические инициаторы (обрабатывать первыми)

| Имя | Тип | Роль | Действие | Риск |
|-----|-----|------|----------|------|
| `WaaSMedicSvc` | служба | **Восстанавливает** работоспособность Windows Update | `Disabled` + удалить задачу `\Microsoft\Windows\WaaSMedic\PerformRemediation` | WU не поднимется автоматически — это и есть цель |
| `UsoSvc` | служба | Update Orchestrator — управляет сканированием/установкой | `Manual`→`Disabled` | Ручная проверка обновлений станет невозможна |
| `wuauserv` | служба | Windows Update | `Manual`, не `Disabled` | **Оставить управляемым**: для установки security-патчей включаем по требованию |
| `DoSvc` | служба | Delivery Optimization, P2P-раздача | `Disabled` | Утечки памяти 10–20 ГБ устраняются |
| `InstallService` | служба | Установка/возврат компонентов и Store-приложений | `Manual` | Возврат UWP блокируется |
| `Get-AppxProvisionedPackage` | канал | Provisioned appx для новых пользователей | `Remove-AppxProvisionedPackage` | Без этого appx вернётся (H5) |
| `ContentDeliveryManager\SilentInstalledAppsEnabled` | реестр | Тихая установка рекламных приложений | `0` | Основной канал «мусор появился сам» |
| Active Setup `Installed Components` | реестр | Одноразовый запуск на каждого нового пользователя | Аудит → очистка OEM-записей | Проверять каждую запись до удаления |

---

## P1. Инициаторы телеметрии и диагностики

### P1a. Задачи планировщика (отключать **раньше** исполнителей)

| Задача | Порождает |
|--------|-----------|
| `\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser` | `CompatTelRunner.exe` |
| `\...\Application Experience\ProgramDataUpdater` | `CompatTelRunner.exe` |
| `\...\Application Experience\StartupAppTask` | оценка запуска |
| `\...\Application Experience\PcaPatchDbTask` | `PcaSvc` |
| `\...\Customer Experience Improvement Program\Consolidator` | `wsqmcons.exe` |
| `\...\Customer Experience Improvement Program\UsbCeip` | USB-телеметрия |
| `\...\Customer Experience Improvement Program\KernelCeipTask` | телеметрия ядра |
| `\...\Feedback\Siuf\DmClient`, `DmClientOnScenarioDownload` | `DmClient.exe` |
| `\...\Windows Error Reporting\QueueReporting` | `wermgr.exe` |
| `\...\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector` | дисковая телеметрия |
| `\...\CloudExperienceHost\*` | облачный OOBE |
| `\...\Maintenance\WinSAT` | `winsat.exe` |
| `\...\Speech\SpeechModelDownloadTask` | загрузка моделей |
| `MicrosoftEdgeUpdateTaskMachineCore`, `MicrosoftEdgeUpdateTaskMachineUA` | обновление Edge |
| `\Microsoft\Windows\Maps\MapsToastTask`, `MapsUpdateTask` | `MapsBroker` |
| `\Microsoft\Windows\Autochk\Proxy` | `acproxy.dll` |

### P1b. Службы-инициаторы

| Служба | Действие | Обоснование |
|--------|----------|-------------|
| `DiagTrack` | `Disabled` | Ядро телеметрии |
| `dmwappushservice` | `Disabled` | Приём внешних push-команд |
| `InventorySvc` | `Disabled` | Compatibility Appraisal |
| `DPS` | `Disabled` | Diagnostic Policy Service |
| `WdiSystemHost`, `WdiServiceHost` | `Disabled` | Diagnostic Hosts |
| `diagnosticshub.standardcollector.service` | `Disabled` | Сборщик диагностики |
| `WerSvc` | `Disabled` | Windows Error Reporting |
| `PcaSvc` | `Disabled` | Program Compatibility Assistant |
| `CDPSvc`, `CDPUserSvc_*` | `Disabled` | Connected Devices Platform |
| `wisvc` | `Disabled` | Windows Insider Service |
| `SysMain` | `Disabled` | На NVMe бесполезен, всплески I/O |
| `WSearch` | `Disabled` | Постоянная индексация; замена — Everything |
| `MapsBroker` | `Disabled` | Загруженные карты |
| `lfsvc` | `Disabled` | Geolocation |
| `TrkWks` | `Disabled` | Distributed Link Tracking |

---

## P2. Исполнители (обрабатывать после своих инициаторов)

| Объект | Тип | Инициатор | Действие |
|--------|-----|-----------|----------|
| `CompatTelRunner.exe` | процесс | `Microsoft Compatibility Appraiser` | IFEO-заглушка (двойная защита) |
| `wsqmcons.exe` | процесс | `Consolidator` | IFEO-заглушка |
| `DmClient.exe` | процесс | `DmClient*` | IFEO-заглушка |
| `wermgr.exe`, `WerFault.exe` | процессы | `WerSvc`, `QueueReporting` | Только после отключения `WerSvc`; **не** глушить `WerFault` глобально — на нём держится SilentProcessExit |
| `acproxy.dll` | модуль | `Autochk\Proxy` | Отключение задачи |
| `XblAuthManager`, `XblGameSave`, `XboxGipSvc`, `XboxNetApiSvc`, `GamingServices`, `GamingServicesNet` | службы | Store/игры | `Disabled` |
| `NPSMSvc`, `RmSvc`, `OneSyncSvc`, `lmhosts`, `Fax`, `WMPNetworkSvc`, `icssvc`, `AJRouter`, `WalletService`, `WpcMonSvc`, `MessagingService`, `SEMgrSvc`, `SmsRouter`, `WSAIFabricSvc` | службы | — | `Disabled` |
| `RemoteRegistry` | служба | — | `Disabled` (безопасность) |
| `SharedAccess` | служба | — | `Disabled`, если не используется ICS |
| `RetailDemo` | служба | — | `Disabled` |

**Важно:** `icssvc` (Mobile Hotspot) и `SharedAccess` (ICS) отключать только если
точка доступа с ноутбука не нужна. Для выездного мастера **точка доступа может
быть рабочим инструментом** — вынести в отдельный профиль «полевые работы».

---

## P3. Пассивные и ситуативные

| Объект | Условие отключения |
|--------|--------------------|
| `TabletInputService` | Нет сенсорного ввода |
| `lfsvc` | Не нужны геозависимые функции |
| Службы Hyper-V (`vmms`, `vmcompute`, `HvHost`) | Не используются VM; **внимание**: нужны для VBS/Credential Guard |
| `Spooler` | Нет принтеров; **риск**: CVE-поверхность, но печать сломается |
| `WMPNetworkSvc` | Не используется медиа-шаринг |
| `AJRouter`, `SEMgrSvc`, `WalletService` | Нет NFC/платежей |
| `PhoneSvc`, `MessagingService` | Нет связи с телефоном |

---

## T. Точечные запреты (инструмент остаётся, команда запрещается)

Требование заказчика: сохранить полную свободу инструмента, запретив отдельные
команды. Реализуется wrapper-исполняемым файлом (механизм M8) или IFEO с
фильтром аргументов.

| Инструмент | Запрещённые команды | Разрешено | Обоснование запрета |
|-----------|---------------------|-----------|---------------------|
| `DISM.exe` | `/RestoreHealth`, `/Cleanup-Image /StartComponentCleanup`, `/ResetBase`, `/SP-` | `/Get-*`, `/Export-Driver`, `/Add-Driver`, `/Get-ProvisionedAppxPackages`, `/Remove-ProvisionedAppxPackage`, `/Add-Package` | `/RestoreHealth` тянет образ из WU; `/StartComponentCleanup` и `/ResetBase` создают длительную I/O-нагрузку и необратимость |
| `powercfg.exe` | `/hibernate on`, `/h on` | `/hibernate off`, `/a`, `/requests`, `/energy`, `/sleepstudy` | Защита от возврата `hiberfil.sys` на SSD |
| `fsutil.exe` | `behavior set DisableDeleteNotify 1` | `behavior query ...` | Защита от отключения TRIM |
| `vssadmin.exe` | `delete shadows` | `list shadows`, `list shadowstorage` | Защита теневых копий от вымогателей и случайного удаления |
| `bcdedit.exe` | `/set ... recoveryenabled No`, `/deletevalue` | `/enum`, `/export` | Запрет неявного изменения параметров восстановления |
| `schtasks.exe` | `/Change ... /Enable` для задач из чёрного списка | Всё остальное | Защита enforcement-состояния (P5) |
| `sc.exe` | `config <служба из P0/P1> start= auto` | Всё остальное | То же |
| `wmic.exe` | — | Только чтение | Инструмент устарел, замена — PowerShell CIM |
| `cleanmgr.exe` | Автоматический запуск по расписанию | Ручной запуск | Управляемая, а не фоновая чистка |

**Механика wrapper'а:** на флешке и в системе лежит `DISM.exe`-заместитель
(собственный бинарник или скрипт-обёртка), который:
1. разбирает аргументы;
2. при совпадении с запрещённым паттерном — пишет запись в лог, возвращает
   код `1` и сообщение «команда запрещена политикой станции, см. <путь к регламенту>»;
3. иначе — прозрачно передаёт вызов оригиналу, лежащему под другим именем
   (например `DISM.real.exe`), и возвращает его код возврата.

---

## Порядок применения (алгоритм)

```
1. Аудит:  дамп служб, задач, Run/Active Setup, IFEO, GPO, WMI-subscriptions  → отчёт
2. P0:     самовосстановление WU + provisioned appx + Active Setup + ContentDeliveryManager
3. P1a:    задачи планировщика
4. P1b:    службы-инициаторы
5. P2:     исполнители + IFEO-заглушки
6. T:      wrapper'ы точечных запретов
7. P3:     ситуативные — по профилю заказчика
8. Enforcement-задача (паттерн P5) + лог
9. Контроль: повторный аудит → diff с шагом 1 → отчёт
```

## Обязательная обратимость

Для каждого шага хранится пара «применить / откатить»:

| Применили | Откат |
|-----------|-------|
| `Set-Service X -StartupType Disabled` | `Set-Service X -StartupType <исходное из дампа шага 1>` |
| `schtasks /Change /TN X /Disable` | `schtasks /Change /TN X /Enable` |
| `Remove-AppxPackage` / `Remove-AppxProvisionedPackage` | Переустановка из образа/Store |
| Ключ IFEO | `reg delete ...\Image File Execution Options\<exe>` |
| Реестровый ключ политики | `reg delete` / `Remove-ItemProperty` |
| ACL Deny | `icacls <путь> /remove:d <субъект>` |
| Запись в `hosts` | Удаление строки |
| Правило firewall | `Remove-NetFirewallRule -DisplayName ...` |

Исходные значения **обязательно** фиксируются дампом на шаге 1 — без него откат
невозможен.
