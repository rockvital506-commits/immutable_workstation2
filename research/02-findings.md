# 02. Результаты исследований

Формат: факт → источник. Утверждения без источника помечены **[вывод]**.

---

## A. Ventoy: персистентность Linux

- **A1.** Ventoy поддерживает персистентность Live-дистрибутивов через плагин
  `persistence`: файл-бэкенд кладётся на **первый раздел**, привязка задаётся в
  `ventoy.json`. Раздел создавать не нужно, параметры загрузки не правятся.
  Источник: `ventoy.net/en/plugin_persistence.html`.
- **A2.** Синтаксис привязки:
  ```json
  { "persistence": [
      { "image": "/ISO/linuxmint-22-xfce-64bit.iso",
        "backend": "/persistence/linuxmint_22_casper-rw.dat",
        "autosel": 1, "timeout": 10 }
  ] }
  ```
  `backend` может быть массивом; `autosel` — индекс автовыбора; `timeout` — секунды.
  Источник: `ventoy.net/en/plugin_persistence.html`, `ventoy.net/en/doc_news.html`.
- **A3.** Бэкенд — это **дисковый образ с меткой**. Готовые файлы:
  `github.com/ventoy/backend/releases`. Своими руками:
  `CreatePersistentImg.sh [-s SIZE_MB] [-t FSTYPE] [-l LABEL] [-c CFG]`,
  по умолчанию `1 ГБ / ext4 / casper-rw`. Поддерживаются `ext2/3/4` и `xfs`.
  Источник: `ventoy.net/en/plugin_persistence.html`.
- **A4.** Метка зависит от дистрибутива: Ubuntu и **Linux Mint → `casper-rw`**,
  MX Linux → `MX-Persist`, Debian/Kali/Clonezilla требуют внутри файл
  `persistence.conf` с одной строкой `/ union` (создаётся ключом `-c`).
  Источник: `ventoy.net/en/plugin_persistence.html`.
- **A5.** Расширение без потери данных: `ExtendPersistentImg.sh <file> <добавить_МБ>`.
  Источник: `ventoy.net/en/doc_news.html`, gist LukeZGD.
- **A6.** Поддержка персистентности определяется **сборкой ISO**, а не Ventoy:
  часть современных Live-ISO изменения не сохраняет. Источник: techstoreon.com.
- **A7.** Если ISO лежит не на флешке Ventoy, а на локальном диске, прямые пути в
  `backend` не работают — нужны `.vlnk`-файлы. Источник: forums.ventoy.net, tid=2421.

**[вывод A]** Для Linux Mint схема рабочая и недорогая: один `.dat` на 4–8 ГБ с
меткой `casper-rw`, привязка в `ventoy.json`, при выборе образа Ventoy сам
предложит пункт с персистентностью.

---

## B. Ventoy: персистентность WinPE и Windows

- **B1.** У Ventoy **нет** плагина персистентности для ISO Windows/WinPE. Плагин
  `persistence` описан только для Live-Linux. Источник: `ventoy.net/en/plugin_persistence.html`.
- **B2.** Штатный способ получить «Windows с сохранением изменений» — загрузка
  **VHD/VHDX** через плагин VHD Boot: файл `ventoy_vhdboot.img` кладётся в
  `/ventoy/` на первом разделе. Поддерживаются Legacy BIOS и UEFI, fixed и
  dynamic VHD(x), Windows 7+. Источник: `ventoy.net/en/plugin_vhdboot.html`.
- **B3.** Ограничения VHD Boot: для Windows 10 v1803 и старше раздел с VHD должен
  быть **NTFS**; для v1809+ допустим exFAT, но требует дополнительных настроек;
  в UEFI поддерживается только 64-разрядная Windows. Источник: `ventoy.net/cn|en/plugin_vhdboot.html`.
- **B4.** На первом разделе флешки у нас **exFAT** → для VHD-загрузки Windows
  применим путь v1809+ с оговорками, либо перенос VHD на раздел `Tools` (NTFS).
  **[вывод]** Раздел `Tools_SD400` имеет ФС **NTFS** — это естественное место для
  VHDX с «живой» Windows, если такая среда понадобится.
- **B5.** Создание Windows To Go в VHD: `diskpart` → `create vdisk ... maximum=N`
  → `attach vdisk` → Rufus пишет ISO в режиме *Windows To Go* на этот VHD →
  `detach vdisk` → первый запуск в VM с EFI → файл на флешку.
  Источник: kbhost.nl/knowledgebase/ventoy-windows-11-to-go.
- **B6.** Известная проблема VHD-загрузки: накопительные обновления Windows
  пытаются править BCD и завершаются ошибкой, поскольку `ventoy_vhdboot.img`
  предстаёт системе не как накопитель, а как CD-ROM.
  Источник: reddit.com/r/Ventoy (Windows To Go on Ventoy).
- **B7.** WinPE Strelec грузится из Ventoy **двумя** способами: обычный ISO-режим
  и `wimboot` (нужен `ventoy_wimboot.img`); загрузка отдельных `.wim` из сборки
  подтверждена для WinPE 10 x64, для WinPE 11 x64 в UEFI — работает, в Legacy
  BIOS — требует обновления `ventoy_wimboot.img`.
  Источник: forums.ventoy.net, pid=8303.
- **B8.** Размер RAM-диска в сборке Strelec меняется заменой файла
  `Windows\fbwf.cfg` внутри ядра сборки (архив `sstr_fbwf.cfg.zip` с сайта автора),
  ядро перепаковывается 7-Zip. Источник: sergeistrelec.name/faq.html.
- **B9.** Актуальная на дату выдачи сборка: **WinPE 11-10 Sergei Strelec 2026.09.08**,
  ядро WinPE 11 обновлено до `22621.4387`; требования: 16 ГБ RAM (рекоменд.),
  8 ГБ места. Источник: appdoze.net/winpe-sergei-strelec.
  **Решение заказчика (2026-10-07):** на флешке используется сборка
  **2026.02.05**, а не последняя. В `manifest.csv` и в справочнике состава
  зафиксирована именно она. Состав — `tools/diagnostics/strelec-tools.md`.

**[вывод B]** «Strelec с сохранением изменений» реализуем **тремя** путями, цена
растёт: (1) увеличить RAM-диск через `fbwf.cfg` — изменения живут до перезагрузки;
(2) хранить всё ценное на разделе `Tools` и подхватывать стартовыми скриптами —
изменения переживают перезагрузку без правки ISO; (3) полноценный VHDX с Windows
To Go на NTFS-разделе — максимальная цена и риск (B6). Рекомендуемая связка — **(2)**,
пункты (1) и (3) как опции.

---

## C. Целевая ОС

- **C1.** Windows 11 IoT Enterprise LTSC 2024 построен на кодовой базе
  **Windows 11 24H2**; доступность OEM — 22.05.2024, начало поддержки — 01.10.2024,
  **конец поддержки — 10.10.2034** (10 лет). Источник: invgate.com/itdb/windows-iot-enterprise-ltsc-2024.
- **C2.** Отличие IoT LTSC от обычного Enterprise LTSC 2024: **10 лет** против
  **5 лет** поддержки. Источник: licendi.com.
- **C3.** IoT LTSC 2024: x64 и ARM64; допустима работа **без TPM 2.0 и Secure Boot**;
  минимальные конфигурации от 2 ГБ RAM / 16 ГБ хранилища для специальных сценариев.
  Источник: licendi.com.
- **C4.** IoT LTSC не содержит Store-приложений и потребительского bloatware;
  включает механизмы lockdown (Shell Launcher, фильтры записи и клавиатуры,
  multi-app kiosk). Источник: licendi.com.
- **C5.** Обновления — только quality/security, функциональных обновлений нет.
  Источник: invgate.com, dev.to.

**[вывод C1]** Имя каталога `MSI_B12M-211RU_Win11_LTSC_IoT_24H2` **соответствует**
факту: `...windows_11_iot_enterprise_ltsc_2024...` — это Windows **11**, база 24H2.
Формулировка заказчика «вин10 лтсц иот 24ш2» — это Windows 10 IoT LTSC, у которого
24H2 не существует (у Win10 IoT LTSC актуальна 21H2). См. «Конфликты интерпретации».

**[вывод C2]** Для домашне-малобизнесовой станции IoT LTSC 2024 даёт максимум:
10 лет security-обновлений, отсутствие Store-мусора из коробки, штатные механизмы
lockdown — то есть **меньше работы по debloat**, чем на Pro.

---

## D. Debloat: службы, планировщик, реестр

- **D1.** Подтверждённые наборы служб для отключения (телеметрия/диагностика):
  `DiagTrack`, `dmwappushservice`, `DPS`, `WdiSystemHost`, `WdiServiceHost`,
  `InventorySvc`, `WaaSMedicSvc`. Источник: github.com/SysAdminDoc/Debloat-Win11.
- **D2.** Игровые и неиспользуемые: `XblAuthManager`, `XblGameSave`, `XboxGipSvc`,
  `XboxNetApiSvc`, `GamingServices`, `GamingServicesNet`, `CDPSvc`, `CDPUserSvc`,
  `DoSvc`, `TrkWks`, `NPSMSvc`, `RmSvc`, `OneSyncSvc`, `lmhosts`. Там же.
- **D3.** Прочий bloat: `lfsvc`, `Fax`, `WMPNetworkSvc`, `icssvc`, `WerSvc`,
  `wisvc`, `RetailDemo`, `MapsBroker`, `PhoneSvc`, `AJRouter`, `WalletService`,
  `RemoteRegistry`, `WpcMonSvc`, `SharedAccess`, `MessagingService`, `PcaSvc`,
  `SEMgrSvc`, `SmsRouter`. Там же.
- **D4.** Отдельно аргументированы для SSD: `SysMain` (Superfetch — на NVMe не
  нужен, зафиксированы утечки памяти), `DoSvc` (утечки 10–20+ ГБ),
  `WSearch` (дисковые всплески; замена — Everything). Источник: github.com/ckdvs99/windows-debloat.
- **D5.** Задачи планировщика к отключению: `XblGameSaveTask`,
  `MicrosoftEdgeUpdateTaskMachineCore*`, `MicrosoftEdgeUpdateTaskMachineUA*`,
  `Consolidator`, `UsbCeip`, `Microsoft Compatibility Appraiser`,
  `ProgramDataUpdater`, `KernelCeipTask`, `AitAgent`, `PcaPatchDbTask`,
  `SdbinstMergeDbTask`, `QueueReporting`, `Uploader`, `DmClient`,
  `DmClientOnScenarioDownload`, `MapsToastTask`, `MapsUpdateTask`,
  `StartupAppTask`, `CleanupTemporaryState`, `SpeechModelDownloadTask`,
  `FamilySafety*`, `CreateObjectTask`. Источник: SysAdminDoc/Debloat-Win11.
- **D6.** Целые ветки планировщика: `\Microsoft\Windows\Customer Experience
  Improvement Program\*`, `\Application Experience\*`, `\Feedback\Siuf\*`,
  `\Windows Error Reporting\*`, `\DiskDiagnostic\*`, `\CloudExperienceHost\*`. Там же.
- **D7.** Реестр телеметрии:
  `HKLM\SOFTWARE\Policies\Microsoft\Windows\DataCollection\AllowTelemetry=0`,
  `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\DataCollection\AllowTelemetry=0`,
  `Policies\Microsoft\Windows\AppCompat\{AITEnable=0, DisableInventory=1, DisableUAR=1}`,
  `Policies\Microsoft\SQMClient\Windows\CEIPEnable=0`. Источник: winslop.io/how-to.
- **D8.** Реестр потребительского контента (HKCU):
  `ContentDeliveryManager\{SubscribedContent-310093/338387/338388/338389/338393/
  353694/353696Enabled=0, SilentInstalledAppsEnabled=0, SoftLandingEnabled=0}`,
  `AdvertisingInfo\Enabled=0`, `Policies\Microsoft\Windows\CloudContent\
  DisableWindowsConsumerFeatures=1`. Источник: SysAdminDoc/Debloat-Win11, prosoftkeys.com.
- **D9.** **Конфликт в источниках по `AllowTelemetry`:** часть руководств требует
  `0`, другие прямо предупреждают, что `0` ломает Windows Update и облачную
  защиту Defender, и рекомендуют `1` (Basic). Для редакций Enterprise/LTSC
  допустим уровень *Security*. **[вывод]** На IoT LTSC выставлять `AllowTelemetry=0`
  допустимо (редакция Enterprise), но это **обязательный пункт проверки** после
  установки: контроль работоспособности Windows Update.
- **D10.** Паттерн «самовосстановления мусора»: службы и настройки возвращаются
  после крупных обновлений; практическое решение — **enforcement-задача**
  планировщика, которая периодически возвращает отключённое состояние и пишет лог.
  Источник: github.com/ckdvs99/windows-debloat, windowsdebloater.com.

---

## E. Механизм IFEO

- **E1.** Ключ
  `HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\<имя.exe>`
  со значением `Debugger` приводит к тому, что целевой EXE **не запускается**, а
  вместо него стартует указанный файл, получая исходную командную строку аргументом.
  Источник: habr.com/en/articles/544456, bc-programming.com.
- **E2.** Классическая заглушка — `%SystemRoot%\System32\systray.exe` (ничего не
  делает и завершается). Либо свой логгер, фиксирующий все попытки запуска.
  Источник: bc-programming.com.
- **E3.** Обход: `CreateProcess` с флагами `DEBUG_PROCESS` /
  `DEBUG_ONLY_THIS_PROCESS` (бит `IFEOSkipDebugger` в `PS_CREATE_INFO`) — IFEO не
  применяется. Следовательно IFEO — **не** security-механизм, а удобный
  административный. Источник: stackoverflow.com/questions/54453249, habr.
- **E4.** Ограничения: проверяется **только имя файла**, маски недопустимы;
  одинаковые имена в разных путях срабатывают одинаково, если не задан
  `UseFilter` (и там тоже без масок). Источник: habr.com/en/articles/544456.
- **E5.** Требуется HKLM → права администратора. Источник: red.infiltr8.io.
- **E6.** Альтернативная ветвь — мониторинг завершения:
  `...\Image File Execution Options\<exe>\GlobalFlag=512` +
  `...\SilentProcessExit\<exe>\{ReportingMode=1, MonitorProcess=<payload>}` —
  payload стартует родителем `WerFault.exe` при закрытии процесса. Там же.
- **E7.** Прикладной пример блокировки: `IFEO\PSEXESVC.exe\Debugger = svchost.exe`
  — служба стартует, но как служба не поднимается, SCM сообщает об ошибке.
  Источник: guyrleech.wordpress.com.

**[вывод E]** IFEO — самый дешёвый и обратимый слой «удушения» отдельных EXE
(телеметрия-агенты, OEM-агенты, `CompatTelRunner.exe`). Ограничение по имени файла
без масок означает, что список целей **перечислим**, а не вычисляем.

---

## F. Аппаратная платформа MSI Modern 15 B12M

- **F1.** Подтверждённый состав устройств для B12M: **Intel Wi-Fi 6E AX211**
  (`PCI\VEN_8086&DEV_51F0`, INF `netwtw08.inf`/`netwtw6e.inf`), **Realtek
  Bluetooth** (`USB\VID_0BDA&PID_D723`, `rtkfilter.inf`), **Realtek Audio**
  (`INTELAUDIO\FUNC_01&VEN_10EC&DEV_0256`, `hdxsstmsi.inf`), **Intel Dynamic
  Tuning / Innovation Platform Framework** (`PCI\VEN_8086&DEV_461D`, `ipf_cpu.inf`),
  **Intel GNA** (`PCI\VEN_8086&DEV_464F`, `gna.inf`), чипсет Alder Lake
  (`alderlakesystem.inf`, `PCI\VEN_8086&DEV_4601`). Источник: drvhub.net/laptops/msi/modern-15-b12m.
- **F2.** **Критично для установки:** на ноутбуках MSI с Intel 11-го поколения и
  новее установщик Windows может **не видеть накопитель**. Два решения: загрузить
  драйвер **Intel IRST** (или VMD) через «Загрузить драйвер», либо отключить в
  BIOS `Advanced → Enable VMD controller → Disabled` (отключение VMD убирает
  возможность RAID). Источник: ru.msi.com/support/technical_details/NB_Installation_Unrecognizable.
- **F3.** RAM распаяна (8 ГБ) → увеличение объёма невозможно; все решения по
  памяти — только настройкой pagefile и отключением лишних служб. **[вывод]** из
  профиля станции.

**[вывод F]** Полный офлайн-набор драйверов для станции **небольшой** (6–8 INF-пакетов)
и полностью экспортируется из текущей рабочей ОС командой
`DISM /Online /Export-Driver /Destination:...` — это и есть «чистые драйверы»
для бэкапа, без скачивания сторонних сборников.

---

## G. Резервное копирование

- **G1.** Clonezilla: partclone для поддерживаемых ФС (копируются только
  занятые блоки), `dd` для неподдерживаемых; MBR и GPT; загрузка в BIOS и UEFI;
  переустановка grub/syslinux; образ может лежать на локальном диске, ssh, samba,
  NFS, WebDAV. Источник: clonezilla.org.
- **G2.** Ограничения Clonezilla: целевой раздел ≥ исходного; **нет**
  инкрементальных/дифференциальных бэкапов; **нет** онлайн-клонирования (раздел
  должен быть размонтирован); образ нельзя смонтировать и достать один файл. Там же.
- **G3.** Битые/нетипичные таблицы разделов лечатся резервированием MBR/GPT:
  `dd if=/dev/sda of=MBR.img bs=512 count=1`, для GPT — `bs=2048 count=1` или
  `sgdisk --backup=...` / восстановление `sgdisk --load-backup=...`.
  Источник: tecmint.com, sourceforge.net/p/clonezilla/discussion.
- **G4.** Для NVMe в grub-меню Clonezilla вместо `sda` нужно `nvme0n1p`.
  Источник: rmprepusb.com/tutorials/142.
- **G5.** BitLocker-том Clonezilla берёт через `dd` → образ размером с весь том;
  практичнее **приостановить/расшифровать** BitLocker до съёма образа.
  Источник: rmprepusb.com, tecmint.com (комментарии).

---

## H. Обслуживание образа и драйверов

- **H1.** `DISM /Online /Export-Driver /Destination:<путь>` и
  `DISM /Image:<путь> /Export-Driver /Destination:<путь>` выгружают **все
  сторонние INF-пакеты**; выгруженное можно вернуть через `/Add-Driver`.
  Источник: learn.microsoft.com (DISM Driver Servicing).
- **H2.** DISM работает **только с INF-пакетами**: EXE/MSI-установщики вендоров
  не выгружаются и не добавляются. Альтернативы: `pnputil /export-driver` (online),
  `Export-WindowsDriver` (PowerShell, online+offline). Источник: mundobytes.com,
  learn.microsoft.com.
- **H3.** В WinPE ключ `/Online` **не работает** — «Error 50: DISM does not
  support running Windows PE with the /online option»; нужен `/Image:<буква>:\`.
  Источник: mundobytes.com.
- **H4.** `/Remove-Driver` принимает **published name** (`Oem0.inf`, `Oem1.inf`...),
  а не исходное имя; удаление boot-critical драйвера делает образ незагружаемым.
  Источник: learn.microsoft.com.
- **H5.** Appx: `/Get-ProvisionedAppxPackages`, `/Remove-ProvisionedAppxPackage
  /PackageName:...` — убирают установку для **новых** пользователей; уже
  зарегистрированным пользователям пакет снимается `Remove-AppxPackage`. Для
  полного удаления нужны **оба** действия. Источник: learn.microsoft.com (DISM App Package).
- **H6.** `/Optimize-ProvisionedAppxPackages` уменьшает след appx за счёт
  hard-link общих файлов. Источник: learn.microsoft.com / MicrosoftDocs feedback.
- **H7.** Рабочие PowerShell-паттерны очистки: `Get-AppxPackage -AllUsers -Name X |
  Remove-AppxPackage` + `Get-AppxProvisionedPackage -Online | Where {$_.DisplayName
  -in $apps} | Remove-AppxProvisionedPackage -Online`. Источник: memstechtips.com.

---

## I. Износ SSD

- **I1.** `powercfg /hibernate off` удаляет `hiberfil.sys` (≈ объём RAM) и
  устраняет связанные записи; **побочно отключает Fast Startup**.
  Источник: windowsforum.com, pcworld.com.
- **I2.** TRIM проверяется `fsutil behavior query DisableDeleteNotify`
  (`0` = включён), включается `fsutil behavior set DisableDeleteNotify 0`.
  Источник: pcworld.com.
- **I3.** Pagefile: **не** отключать полностью — ломаются crash dump и
  стабильность при нехватке памяти; корректный путь — фиксированный разумный
  размер либо перенос. Для 16 ГБ RAM рекомендуется 4096–8192 МБ; при 8 ГБ RAM
  **[вывод]** ориентир 2048–4096 МБ фиксированно.
  Источник: windowsforum.com (399446, 399384), solvemix.com.
- **I4.** Держать 10–15% свободного места (over-provisioning), обновлять
  прошивку SSD, write caching включать, **flush не отключать** без UPS.
  Источник: windowsforum.com, pcworld.com.
- **I5.** `SysMain` на NVMe бесполезен и даёт всплески I/O; `WSearch` — дисковые
  всплески, замена `Everything`. Источник: github.com/ckdvs99/windows-debloat, solvemix.com.
- **I6.** `DISM /Online /Cleanup-Image /StartComponentCleanup` — штатная чистка
  WinSxS от вытеснённых компонентов; в публичной выдаче упоминается как
  безопасная операция (в отличие от `/ResetBase`, после которой обновления
  нельзя откатить). Источник: learn.microsoft.com/answers (5619791).

---

## J. Инструменты debloat

- **J1.** **Win11Debloat (Raphire)**: только реестр и групповые политики — теми же
  механизмами, что использует Microsoft; не патчит системные файлы; каждая правка
  имеет undo-файл; 39 000+ звёзд; GUI добавлен в 02.2026; после крупных
  обновлений часть приложений возвращается — скрипт безопасен к повторному запуску.
  Источник: windowsdebloater.com, rain-city.tech, nerdtechy.com.
- **J2.** **Chris Titus WinUtil**: запуск `irm christitus.com/win | iex`; шире,
  чем debloat — установка софта, твики, обновления, сборка ISO; автоматически
  создаёт точку восстановления. Источник: rain-city.tech, smarttechfixer.com, nerdtechy.com.
- **J3.** **Sophia Script**: 150+ твиков, каждый выбирается в preset-файле, на
  каждый есть функция возврата; использует **только документированные** методы
  (реестр, GPO, PowerShell API); заявлены поддержка Windows 11 **LTSC 2024**,
  GPO, ARM64; распространяется через WinGet/Chocolatey/Scoop.
  Источник: rain-city.tech.
- **J4.** **Конфликт:** другой источник указывает, что свежий релиз Sophia Script
  (05.09.2026) «требует Windows 11 25H2 или новее», при этом там же заявлены
  сборки standard/ARM/**LTSC 2024**. Источник: nerdtechy.com.
  **[вывод]** Версию Sophia Script под LTSC 2024 нужно **закрепить** и проверить
  на тестовой машине до включения в регламент; в репозитории фиксируется
  конкретная версия + SHA256, а не «последняя».
  **[2026-10-07 — конфликт закрыт]** Официальный README
  `github.com/farag2/Sophia-Script-for-Windows` содержит таблицу поддерживаемых
  редакций, где `Windows 11 Enterprise LTSC 2024` — отдельная строка; для LTSC
  2024 выпускаются отдельные пакеты под PowerShell 5.1 и 7. Формулировка
  «Windows 11 25H2+» относится к обычным редакциям, а не к LTSC. Номер версии
  в сторонних источниках расходится (7.1.4 против 7.3.0) — брать из релизов
  GitHub на дату выезда. Подробности: `08-settings-attack-vectors.md`, B3.
- **J5.** Общий риск всех сторонних скриптов: выполнение произвольного кода,
  необратимость части правок на OEM-машинах, ложные срабатывания антивируса на
  PowerShell-скрипты. Источник: windowsforum.com (405139), rain-city.tech.

---

## K. Автоустановка через Ventoy

- **K1.** Плагин `auto_install` подсовывает `autounattend.xml` установщику, **не
  меняя ISO**. Файл ответа лежит в `Templates/` в корне флешки, ISO — в `ISO/Windows/`.
  Источник: deepwiki.com/memstechtips/UnattendedWinstall, github.com/memstechtips/UnattendedWinstall.
- **K2.** Конфигурация:
  ```json
  { "auto_install": [ { "parent": "/ISO/windows",
      "template": ["/ventoy/autoinstall/autounattend.xml"],
      "timeout": 10, "autosel": 1 } ] }
  ```
  Источник: github.com/ventoy/Ventoy/issues/1177.
- **K3.** **Дефект:** сопоставление по `"image"` (в том числе с glob `*.iso`)
  может не срабатывать — не появляется меню выбора файла ответа; по `"parent"`
  работает штатно. Источник: github.com/ventoy/Ventoy/discussions/3002.
  **[вывод]** В нашем `ventoy.json` для `auto_install` использовать **только `parent`**.
- **K4.** Известный дефект `timeout` в `auto_install` (Ventoy 1.0.56): переход к
  файлу ответа без ожидания. Источник: github.com/ventoy/Ventoy/issues/1177.
  **[вывод]** На ответственные установки timeout не ставить — выбор вручную.
- **K5.** Генератор файлов ответа: Schneegans Unattend Generator — обход
  TPM/SecureBoot/сети, отключение Defender, удаление `Windows.old`, скрытие
  настройки Edge. Источник: osmanonurkoc.com.

---

## L. Перенос пользовательских данных

- **L1.** Chrome: профиль в `%LOCALAPPDATA%\Google\Chrome\User Data`. Ключевое:
  `Default\Bookmarks` (JSON), `Default\Login Data` (SQLite, **шифруется DPAPI**),
  `Default\Cookies`, `Default\History`, `Default\Web Data` (автозаполнение),
  `Default\Preferences`, `Default\Extensions\`, `Default\Local Extension Settings\`,
  `Local State`. Источник: alexhost.com, ava.hosting.
- **L2.** Копировать можно только при **закрытом** Chrome — SQLite-файлы
  заблокированы/несогласованы. Проверка `Get-Process chrome` перед копированием.
  Источник: alexhost.com (пример с abort при запущенном Chrome).
- **L3.** Полнота расширений: `Extensions\` + `Local Extension Settings\` +
  `Local Storage\` + `Sync Extension Settings\`. Источник: superuser.com/questions/1238372.
- **L4.** Ограничение: `Login Data` защищён DPAPI в контексте учётной записи —
  на **другой** машине/профиле пароли не расшифруются. Надёжный путь — штатный
  экспорт `chrome://settings/passwords` → «Экспорт паролей» (CSV).
  Источник: vk.com/@stxastdigr..., superuser.com.
- **L5.** VS Code: настройки `%APPDATA%\Code\User\settings.json` (+ `keybindings.json`,
  `snippets\`), расширения `%USERPROFILE%\.vscode\extensions`; альтернатива —
  Settings Sync. Источник: reddit.com/r/vscode (перенос настроек).

---

## Конфликты интерпретации — РЕШЕНЫ заказчиком

| # | Конфликт | Решение | Где применяется |
|---|----------|---------|-----------------|
| 1 | «вин10 лтсц иот 24ш2» против файла `windows_11_iot_enterprise_ltsc_2024` | **[2026-10-07 — решение заказчика]** Win10 IoT LTSC 21H2 **полностью исключён** из контекста и целей проекта. Единственная целевая ОС — **Win11 IoT Enterprise LTSC 2024**. Заглушка ISO, строка в `manifest.csv` и упоминания в документации подлежат удалению | `ventoy-partition/ISO/`, `manifest.csv`, Этап 4.3 |
| 2 | `AllowTelemetry=0` против риска сломать Windows Update | **`AllowTelemetry = 0`** + **обязательный пост-тест работоспособности Центра обновления** после установки; тест входит в финальный контроль и фиксируется в `reports/` | `06-services-blocklist.md` P0/P1b, Этап 7 (debloat), Этап 9 (контроль) |
| 3 | Sophia Script: поддержка LTSC 2024 против требования 25H2+ | **[2026-10-07 — закрыт]** Официальный README проекта содержит отдельную строку для `Windows 11 Enterprise LTSC 2024`; выпускаются отдельные пакеты под LTSC 2024. Версия закрепляется по релизам GitHub на дату выезда | `02-findings.md` J4, `08-settings-attack-vectors.md` B3 |
| 4 | Имя каталога `bilds` против конвенции именования | **Переименовано в `builds`** — соответствует `CONVENTIONS.md`; исключение из конвенции не требуется | `ventoy-partition/builds/`, корневой `README.md`, `PLAN.md` |

