# 05. Векторы инициализации мусора

Полный перечень каналов, по которым мусор попадает в систему и возвращается в неё.
Каждый вектор снабжён точкой контроля и способом обнаружения.

Легенда приоритета: **И** — инициатор (будильник/активатор), **В** — вторичный
(инициализируемый/исполняемый). Приоритет обработки: И >> В.

---

## V1. Планировщик задач (Task Scheduler) — основной канал

**Природа:** таймер или событие запускает исполняемый файл. Это **инициатор**.

### V1.1 Ветки телеметрии и диагностики — И

| Путь задачи | Исполнитель | Эффект |
|-------------|-------------|--------|
| `\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser` | `CompatTelRunner.exe` | Сбор данных совместимости, дисковая активность |
| `\...\Application Experience\ProgramDataUpdater` | `CompatTelRunner.exe` | Обновление телеметрии |
| `\...\Application Experience\StartupAppTask` | — | Оценка времени запуска приложений |
| `\...\Application Experience\PcaPatchDbTask` | `PcaSvc` | Патч БД совместимости |
| `\...\Customer Experience Improvement Program\Consolidator` | `wsqmcons.exe` | CEIP-консолидация |
| `\...\Customer Experience Improvement Program\UsbCeip` | — | CEIP по USB |
| `\...\Customer Experience Improvement Program\KernelCeipTask` | — | CEIP по ядру |
| `\...\Feedback\Siuf\DmClient` | `DmClient.exe` | Отправка отзывов |
| `\...\Feedback\Siuf\DmClientOnScenarioDownload` | `DmClient.exe` | Отзывы по сценариям |
| `\...\Windows Error Reporting\QueueReporting` | `wermgr.exe` | Отправка отчётов об ошибках |
| `\...\DiskDiagnostic\Microsoft-Windows-DiskDiagnosticDataCollector` | — | Дисковая телеметрия |
| `\...\CloudExperienceHost\*` | — | Облачный OOBE-опыт |
| `\...\Autochk\Proxy` | `acproxy.dll` | Прокси телеметрии автопроверки |
| `\...\Maintenance\WinSAT` | `winsat.exe` | Оценка производительности |
| `\...\Speech\SpeechModelDownloadTask` | — | Загрузка речевых моделей |

Источник состава: `github.com/SysAdminDoc/Debloat-Win11`, `winslop.io/how-to`.

### V1.2 Обновление и самовосстановление — И (критично)

| Путь задачи | Эффект |
|-------------|--------|
| `\Microsoft\Windows\WindowsUpdate\Scheduled Start` | Запуск службы WU |
| `\Microsoft\Windows\UpdateOrchestrator\*` (`Schedule Scan`, `UpdateModelTask`, `USO_UxBroker`) | Оркестрация обновлений |
| `\Microsoft\Windows\WaaSMedic\PerformRemediation` | **Восстанавливает** работоспособность Windows Update |
| `\Microsoft\Windows\Windows Activation Technologies\ValidationTask` | Проверка активации |
| `\Microsoft\Windows\Application Experience\Microsoft Compatibility Appraiser` (повтор после обновления) | Возврат телеметрии |
| `MicrosoftEdgeUpdateTaskMachineCore` / `...MachineUA` (в корне планировщика) | Обновление Edge |
| `\Microsoft\Windows\InstallService\*` | Служба установки/возврата компонентов |

### V1.3 OEM-агенты и вендорский мусор — И

На станции MSI ожидаемы (состав уточняется на месте — **НЕ ПРОВЕРЕНО ЗДЕСЬ**):
`MSI\*`, `MSI Center`, `NahimicSvc*`, `NahimicTask*`, `SteelSeries*`,
`Realtek\*`, `Intel\*` (Intel Driver & Support Assistant, Intel Telemetry).

**Точка контроля:** `Get-ScheduledTask | Where State -ne 'Disabled'` — полный
дамп в отчёт до и после.

---

## V2. Службы (Services)

### V2.1 Службы-инициаторы — И

| Служба | Роль |
|--------|------|
| `DiagTrack` | Connected User Experiences and Telemetry — собирает и отправляет |
| `dmwappushservice` | WAP Push Message Routing — приём внешних команд |
| `WaaSMedicSvc` | Windows Update Medic — **восстанавливает** WU |
| `UsoSvc` | Update Orchestrator Service — управляет обновлениями |
| `wuauserv` | Windows Update |
| `DoSvc` | Delivery Optimization — P2P-раздача обновлений |
| `InventorySvc` | Inventory and Compatibility Appraisal |
| `DPS` | Diagnostic Policy Service — включает диагностические сценарии |
| `WdiSystemHost` / `WdiServiceHost` | Diagnostic System/Service Host |
| `WerSvc` | Windows Error Reporting |
| `PcaSvc` | Program Compatibility Assistant |
| `CDPSvc` / `CDPUserSvc_*` | Connected Devices Platform |
| `SysMain` | Superfetch — предзагрузка, I/O-активность |
| `WSearch` | Индексирование — постоянная дисковая активность |
| `wisvc` | Windows Insider Service |
| `MapsBroker` | Downloaded Maps Manager |
| `RetailDemo` | Retail Demo Service |
| `TrkWks` | Distributed Link Tracking Client |
| `lfsvc` | Geolocation Service |

Источник состава: `github.com/SysAdminDoc/Debloat-Win11`, `github.com/ckdvs99/windows-debloat`.

### V2.2 Службы-исполнители — В

`XblAuthManager`, `XblGameSave`, `XboxGipSvc`, `XboxNetApiSvc`,
`GamingServices`, `GamingServicesNet`, `NPSMSvc`, `RmSvc`, `OneSyncSvc`,
`lmhosts`, `Fax`, `WMPNetworkSvc`, `icssvc`, `AJRouter`, `WalletService`,
`RemoteRegistry`, `WpcMonSvc`, `SharedAccess`, `MessagingService`,
`SEMgrSvc`, `SmsRouter`, `WSAIFabricSvc`.

**Точка контроля:** `Get-Service | Select Name,StartType,Status`.

---

## V3. Реестр автозагрузки

### V3.1 Run / RunOnce — И

| Ключ | Область |
|------|---------|
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | Все пользователи |
| `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce` | Однократно |
| `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run` | 32-бит на 64-бит |
| `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run` | Текущий пользователь |
| `HKLM\...\Policies\Explorer\Run` | Политическая автозагрузка (часто игнорируется аудитами) |
| `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit` / `Shell` | Подмена оболочки/инициализации — канал OEM-агентов |

### V3.2 Active Setup — И (недооценённый канал)

`HKLM\SOFTWARE\Microsoft\Active Setup\Installed Components\{GUID}` со значением
`StubPath` — исполняется **один раз для каждого нового пользователя**. Именно так
OEM-агенты и Edge возвращаются в новые профили.

### V3.3 Прочие точки запуска — И

| Механизм | Где смотреть |
|----------|--------------|
| Службы (см. V2) | `services.msc` |
| Драйверы-фильтры и boot-start | `HKLM\SYSTEM\CurrentControlSet\Services` (`Start=0..2`) |
| COM / COM+ activation | `HKLM\SOFTWARE\Classes\CLSID\...\InprocServer32` |
| Winlogon Notify / GP Extensions | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon\Notify` |
| AppInit_DLLs | `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Windows\AppInit_DLLs` |
| Print Monitors | `HKLM\SYSTEM\CurrentControlSet\Control\Print\Monitors` |
| LSA/Authentication Packages | `HKLM\SYSTEM\CurrentControlSet\Control\Lsa` |
| Image Hijacks (IFEO) | см. V5 — используется и мусором, и нами |
| Startup Approved | `HKCU\...\Explorer\StartupApproved\Run` — фактическое состояние «вкл/выкл» в Диспетчере задач |

---

## V4. Пакеты приложений (Appx / Provisioned)

| Канал | Эффект | Точка контроля |
|-------|--------|----------------|
| `Get-AppxPackage -AllUsers` | Установленные UWP | Удаление через `Remove-AppxPackage` |
| `Get-AppxProvisionedPackage -Online` | Установка для **новых** пользователей | `Remove-AppxProvisionedPackage` |
| `HKLM\...\ContentDeliveryManager\SilentInstalledAppsEnabled` | **Тихая установка** рекламных приложений | Значение `0` (D8) |
| `SubscribedContent-3xx Enabled` | Подсказки/предложения в Пуске и Проводнике | Значения `0` (D8) |
| `Policies\...\CloudContent\DisableWindowsConsumerFeatures` | Потребительские функции | Значение `1` (D8) |
| Feature updates (для не-LTSC) | Полный возврат всего удалённого | Неактуально для LTSC |

**Ключевой вывод:** удаление appx **без** снятия provisioned-пакета даёт возврат
мусора каждому новому пользователю (H5). Оба действия обязательны.

---

## V5. Image File Execution Options (IFEO)

Используется и мусором (persisted-агенты), и нами (заглушки).

| Ключ | Эффект |
|------|--------|
| `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<exe>\Debugger` | Подмена запуска (E1) |
| `...\IFEO\<exe>\GlobalFlag` + `...\SilentProcessExit\<exe>\MonitorProcess` | Запуск payload при завершении процесса (E6) |
| `...\IFEO\<exe>\UseFilter` | Правила по полному пути (E4) |

**Аудит обязан включать IFEO на чтение:** наличие «чужих» `Debugger`-записей —
признак persisted-агента.

---

## V6. Локальные групповые политики

| Канал | Эффект |
|-------|--------|
| `HKLM\SOFTWARE\Policies\Microsoft\...` | Всё, что задано через `gpedit.msc` |
| `HKLM\SOFTWARE\Microsoft\PolicyManager` | MDM-политики (в т.ч. принесённые OOBE) |
| `C:\Windows\System32\GroupPolicy\` (`.adm/.admx`, `scripts.ini`, `Registry.pol`) | Скрипты и политики, применяемые при входе |
| `C:\Windows\System32\GroupPolicy\Machine\Scripts\Startup` | **Скрипты при старте** — канал возврата мусора |
| `LGPO.exe` | Перенос локальных политик между машинами (рабочая группа) |

**Важно:** политики имеют приоритет над обычными ключами реестра — правка
«обычного» ключа при активной политике эффекта не даст.

---

## V7. Сетевые каналы

| Канал | Что приносит |
|-------|--------------|
| Windows Update / Delivery Optimization | Обновления, драйверы, возврат компонентов |
| Microsoft Store / `InstallService` | Возврат UWP-приложений |
| Edge Update (`msedge --update`, задачи `MicrosoftEdgeUpdate*`) | Обновление и переустановка Edge |
| Телеметрия: `vortex.data.microsoft.com`, `settings-win.data.microsoft.com`, `watson.telemetry.microsoft.com` | Исходящий трафик диагностики |
| OEM-облака (MSI Center, Intel DSA) | Загрузка вендорских агентов |
| DNS без фильтрации | Рекламный и трекинговый контент |

**Точка контроля:** `hosts`, правила Windows Defender Firewall (исходящие),
DNS-настройки адаптера.

---

## V8. Драйверы из Windows Update

| Канал | Контроль |
|-------|----------|
| Политика «Исключать драйверы из обновлений Windows» (`ExcludeWUDriversInQualityUpdate`, с 1607) | GPO, `learn.microsoft.com/ru-ru/windows/deployment/update/waas-wu-settings` |
| `DenyDeviceIDs` + `DenyDeviceIDsRetroactive=1` | `HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceInstall\Restrictions` |
| `DenyDeviceClasses` (по GUID класса) | Там же |
| «Задать порядок поиска драйверов» → «Не искать на сайте Центра обновления» | GPO |
| `Prevent device metadata retrieval from the Internet` | GPO |

**Риск:** блокировка по Hardware ID запрещает и **ручное** обновление этого
устройства — нужно снимать политику на время ручной установки.

---

## V9. Профиль пользователя и OOBE

| Канал | Эффект |
|-------|--------|
| `C:\Users\Default` + `NTUSER.DAT` | Всё, что лежит в дефолтном профиле, тиражируется на новых пользователей |
| `unattend.xml`-секция `OOBE` | Скрытые установки при первом входе |
| Active Setup (V3.2) | Одноразовый запуск на каждого нового пользователя |
| `Provisioned Appx` (V4) | UWP для новых пользователей |

**Практика:** настройка эталона ведётся в **отдельном** профиле, затем
тиражируется через `C:\Users\Default` — иначе мусор текущего профиля разъедет по
всем новым учёткам.

---

## V10. Планировщик событий и WMI

| Канал | Эффект |
|-------|--------|
| `HKLM\SOFTWARE\Microsoft\WBEM\CIMOM\Autorecover MOFs` | Автокомпенсация WMI-подписок |
| `__EventFilter` / `__EventConsumer` / `__FilterToConsumerBinding` | WMI-персистенция, переживает перезагрузку |
| `Event Viewer`-подписки | Запуск по событию журнала |

**Аудит:** `Get-WMIObject -Namespace root\subscription -Class __EventConsumer`.

---

## Сводная таблица приоритетов обработки векторов

| Приоритет | Векторы | Основание |
|-----------|---------|-----------|
| 1 (сначала) | V1.2 (самовосстановление WU), V4 (provisioned appx), V3.2 (Active Setup) | Без их нейтрализации остальные слои откатываются |
| 2 | V1.1 (телеметрия-триггеры), V2.1 (службы-инициаторы), V8 (драйверы из WU) | Убирают причину активности |
| 3 | V3.1 (Run), V6 (GPO-скрипты), V7 (сеть) | Убирают каналы доставки |
| 4 | V2.2 (службы-исполнители), V5 (чужой IFEO), V10 (WMI) | Зачистка следствий |
| 5 (последним) | V9 (профиль/OOBE) | Фиксация результата в эталоне |
