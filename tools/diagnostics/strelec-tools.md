# Состав WinPE 11-10-8 Sergei Strelec — сборка 2026.02.05

Справочник того, что уже есть в `ISO/winpe/WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso`.
Нужен, чтобы не класть на раздел `Tools` вторую копию того, что и так лежит
в WinPE, и чтобы в выезд знать, за каким инструментом перезагружаться.

> **Источник списка.** Состав собран по описанию сборки 2026.02.05 и по истории
> версий на `sergeistrelec.name` (версии HWiNFO 8.34, CPU-Z 2.17,
> CrystalDiskInfo 9.7.2, CrystalDiskMark 9.0.1, IsMyLcdOK 6.11 соответствуют
> именно этой сборке). **Список не сверен с самим образом.** Достоверный
> источник внутри ISO — `\MInst\profiles\strelec64Windows10.ini`, где сопоставлены
> названия программ и имена файлов. Перед выездом сверить по нему.

Сборка содержит пять ядер: `WinPE 11 x64`, `WinPE 10 x64`, `WinPE 10 x86`,
`WinPE 8 x86`, `WinPE 8 x86 (Native)`. Состав программ между ядрами
**различается**: в x64-образе 2026.02.05 отсутствуют Victoria, HD Tune Pro,
Western Digital Data Lifeguard и RWEverything, которые есть в x86-образе.

## Диагностика — ядро WinPE (GUI)

| Утилита | Версия в 2026.02.05 | Назначение | x86 | x64 |
|---------|--------------------|------------|-----|-----|
| Victoria | 5.37 | Поверхность, SMART, мелкий ремонт | да | **нет** |
| CrystalDiskInfo | 9.7.2 | SMART, температура, здоровье | да | да |
| CrystalDiskMark | 9.0.1 | Скорость чтения/записи | да | да |
| Hard Disk Sentinel | 6.30 | SMART с прогнозом, температура | да | да |
| HD Tune / HD Tune Pro | 6.00 / 5.75 | Тесты, скан поверхности | да | HD Tune 6.00 |
| HDDScan | 4.1.0.29 | Тесты накопителей | да | да |
| HDD Regenerator | 2024 и 2011 | Переназначение секторов | да | да |
| PC3000 Disk Analyzer | 2.2.4 | Глубокая диагностика | да | да |
| Check Disk GUI | — | Обёртка над chkdsk | да | да |
| AIDA64 | 7.70.7500 (x86) / 8.20.8100 (x64) | Полный осмотр железа, стресс | да | да |
| CPU-Z | 2.17 | CPU, чипсет, память | да | да |
| HWiNFO | 8.34 | Датчики, температуры, HWID | да | да |
| HWMonitor | 1.55 | Температуры, напряжения | — | x64 |
| OCCT | 10.0.5 (x64) / OCCT Perestroika 4.5.1 (x86) | Стресс CPU/GPU/памяти | да | да |
| LinX | 0.6.5 | Стресс на Linpack | да | да |
| Linpack Xtreme | 1.1.8 | Стресс CPU, AVX | да | да |
| BurnIn Test | 8.1 Build 1025 | Комплексный прогрев | да | да |
| PerformanceTest | 10.2 Build 1002 | Бенчмарк | да | да |
| R.tester | 1.20.11.21 | Тест памяти | да | да |
| Drevitalize | 4.10 | Ремонт секторов | да | да |
| RWEverything | 1.7 | Доступ к регистрам железа | да | **нет** |
| PassMark MonitorTest | 4.0 Build 1002 | Тест матрицы | да | да |
| IsMyLcdOK | 6.11 | Тест матрицы | да | да |
| Keyboard Test Utility | 1.4.0 | Тест клавиатуры | да | да |
| Check Device | 1.0.1.70 | Проверка устройств | — | x64 |
| Double Driver | 4.1.0 | Резервное копирование драйверов | — | x64 |

## DOS-программы

Работают без Windows, грузятся отдельным пунктом меню. Нужны, когда диск не
отдаётся ОС или когда надо исключить влияние драйверов.

| Утилита | Версия | Назначение |
|---------|--------|-----------|
| MemTest86 | 11.5.1000 | Тест ОЗУ, UEFI |
| Memtest86+ | 7.20 | Тест ОЗУ, UEFI и DOS |
| GoIdMemory PRO | 7.85 | Тест ОЗУ |
| MHDD | 4.6 | Поверхность, низкоуровневый доступ |
| Victoria | 3.52 | Поверхность (DOS-ветка) |
| HDAT2 | 7.6 | Поверхность, ATA-команды |
| HDD Regenerator | 2011 | Переназначение секторов |
| HDDaRTs | 20.03.2025 | Пакет диагностики Ander_73 |
| BIBM++ | 1.92 | BootIt Bare Metal, разделы |
| Hard Disk Sentinel for DOS | 1.21 | SMART |
| DRevitalize | 3.32 | Ремонт секторов |
| CHZ Monitor Test | 2.0 | Тест матрицы |
| Ghost | 11.5 | Образы разделов |
| Active Password Changer Professional | 5.0 | Сброс пароля |
| Kon-Boot for Windows | 2.5.0 | Обход пароля |
| Eassos PartitionGuru | — | Разделы |

## Жесткий диск и разделы

| Утилита | Версия |
|---------|--------|
| Acronis Disk Director | 12.5 Build 163 |
| Paragon Hard Disk Manager | 17.20.17 / 15 (10.1.25.1137) |
| MiniTool Partition Wizard | 12.9 |
| QILING Disk Master | 8.5 |
| DiskGenius | — |
| Diskpart GUI Micro | 2.0 |
| EasyUEFI | 6.0 |
| EasyBCD | 2.4.0.237 |
| Format Tool | 4.50 |
| HDD Low Level Format Tool | 4.50 |
| Active KillDisk | 25.0.23 |
| Active Disk Editor | 25.0.7 |
| DiskCopy | 1.4.4.0 |
| Bootice | — |
| WinNTSetup | — |
| Dism++ | 10.1.1002.1 |

## Бэкап и восстановление

| Утилита | Версия |
|---------|--------|
| Acronis True Image | 30.1.1 Build 42386 / 2019 17750 / 2016 23.0.0.0 |
| AOMEI Backupper | 8.1.0 |
| TeraByte Image for Windows | 4.10 |
| Hasleo Backup Suite | 5.6.2.0 (x64) |
| Drive SnapShot | — |
| Veritas System Recovery | 22.0.0.62226 |
| Disk2vhd | 2.02 |
| Defraggler | 2.22.995 |
| O&O Defrag | 23.0 |

## Восстановление данных

| Утилита | Версия |
|---------|--------|
| R-Studio | — |
| TestDisk | — |
| R.saver | — |
| Runtime GetDataBack / Captain Nemo / RAID Reconstructor | — |
| DMDE / Data Recovery Wizard | — |

## Сброс паролей

`Windows Login Unlocker 2.3.0.6404`, `Reset Windows Password 7.0.5.702`,
`PCunlocker 5.6`, `OO User Manager 1.0.1.5491`, `Simplix Password Reset 5.1`.

## Сеть и удалённый доступ

`Opera`, `Download Master`, `PENetwork 0.59.B12`, `TeamViewer 15`,
`Ammyy Admin 3.9 / 3.5.2.1`, `AeroAdmin 4.9`, `AnyDesk`, `Radmin 3.5.2.1`,
`Radmin VPN 2.0.4899.9`, `Advanced IP Scanner 2.5.4594.1`, `FtpUse 2.2`,
`PuTTY`, `FileZilla`, `UltraVNC`, `TightVNC`.

## Прочее, что важно в выезде

| Утилита | Зачем |
|---------|-------|
| Total Commander 9.00 / Far Manager 3.0 | Файловые операции |
| 7-ZIP | Архивы |
| ShowKeyPlus 1.1.18.0 | Ключ Windows из BIOS/реестра |
| OemKey | OEM-ключ |
| Recover Keys | Лицензии установленного софта |
| Everything 1.4.1.1022 | Поиск файлов |
| WinDirStat / TreeSize | Чем занято место |
| Registry Editor PE | Офлайн-правка реестра |
| CIHexViewer / WinHex | Шестнадцатеричный просмотр |
| TeraCopy / FastCopy | Копирование с проверкой |
| UltraISO / PowerISO / gBurner | Образы |
| NirLauncher 1.23.67 | Набор мелких утилит |
| Media Player Classic | Проверка звука/видео |
| CMOS De-Animator 3 | Сброс CMOS |

## Антивирусы — важная особенность сборки

В `SSTR/MInst/Portable/Antivirus` вместо самих программ лежат **пустышки**.
Перед выездом скачать актуальные версии с официальных сайтов и положить вместо
пустышек:

| Программа | Источник |
|-----------|----------|
| SmartFix Tool | `simplix.pro` |
| Dr.Web CureIt! | `download.geo.drweb.com/pub/drweb/cureit/cureit.exe` |
| Kaspersky Virus Removal Tool | `devbuilds.kaspersky-labs.com/devbuilds/KVRT/latest/full/KVRT.exe` |
| Kaspersky Rescue Disk | ISO распаковать в `Linux/krd2018` |
| Dr.Web LiveDisk | ISO распаковать в `Linux/DrWeb` |

При наличии сети актуальные версии скачиваются и запускаются прямо из WinPE —
в меню Пуск есть соответствующие ярлыки.

## Чего в Strelec нет и что берём из Tools

| Задача | Утилита на разделе Tools |
|--------|--------------------------|
| SMART-лог в файл одной командой из живой ОС | `smartmontools` (`smartctl -x`) |
| Тест ОЗУ свежее, чем 7.20 в сборке | `MemTest86+` 8.10 |
| Стресс CPU из живой Windows без перезагрузки | `Prime95` 31.06 |
| Стресс CPU/памяти/IO в Linux | `stress-ng` 0.22.01 |
| SMART и температура без GUI, в отчёт | `smartmontools`, `nvme-cli` в Live Mint |
