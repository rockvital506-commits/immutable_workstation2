# Состав WinPE 11-10-8 Sergei Strelec — сборка 2026.02.05

Справочник того, что уже есть в `ISO/winpe/WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso`.
Нужен, чтобы не класть на раздел `Tools` вторую копию того, что и так лежит
в WinPE, и чтобы при работе знать, за каким инструментом перезагружаться.

> **Источник списка.** Первоисточник внутри ISO — `\MInst\profiles\*.ini`.
> **Список не сверен с самим образом**: съёмка 2026-10-22 покрыла меню Пуск
> ядра **WinPE 11 x64** (разметка — `research/27-winpe11-observation.md`) и
> файлы `DiskPart_Scripts`/`Tweaks` пакета `_TEMP`, но сверка имён файлов и
> версий по `\MInst\profiles\*.ini` и содержимому ISO не выполнена — метка
> ярлыка может расходиться с версией файла. Прежние версии из веб-описаний
> (HWiNFO 8.34, CPU-Z 2.17) оказались неверны и заменены наблюдёнными (N57).

Сборка содержит пять ядер: `WinPE 11 x64`, `WinPE 10 x64`, `WinPE 10 x86`,
`WinPE 8 x86`, `WinPE 8 x86 (Native)`. Состав программ между ядрами различается
(по описанию автора). Съёмка показала **Victoria 5.37 в ядре WinPE 11 x64** —
прежняя запись «в x64-образе нет Victoria» была ошибочной (N56); HD Tune Pro,
Western Digital Data Lifeguard и RWEverything в меню WinPE 11 x64 не обнаружены.

## Таксономия меню Пуск (WinPE 11 x64, наблюдено 2026-10-22)

24 группы, 201 пункт — полный перечень утилит сборки по группам меню.
Ниже — ярлыки так, как они подписаны в меню. Соответствие кадров съёмки
группам — в `research/27-winpe11-observation.md`.

### Бэкап и восстановление (19)

- Acronis True Image 30.1.1 Build 42386
- Acronis True Image 2019 Build 17750
- Acronis True Image 2016 Build 6595
- Acronis True Image 2014 Build 6673
- Acronis Cyber Protect 15
- AOMEI Backupper 8.1.0
- R-Drive Image 7.3.7312
- Macrium Reflect 10.0.8750
- Macrium Reflect 8.1.8631
- TeraByte Image for Windows 4.10
- Hasleo Backup Suite 5.6.2.0
- QILING Disk Master 8.7
- EaseUS Todo Backup 16.3.0
- Active Disk Image 25.0.6
- Veritas System Recovery 22.0.0.62226
- StorageCraft Recovery Environment 5.2.5.37836
- Drive SnapShot 1.50.0.1839
- Disk2vhd 2.02
- Symantec Ghost 12.0.0.11761

### Жёсткий диск (14)

- Acronis Disk Director 12.5 Build 163
- MiniTool Partition Wizard 13.5
- EaseUS Partition Master 19.23.0
- Paragon Hard Disk Manager 17.20.17
- AOMEI Partition Assistant 10.10.0
- AOMEI Dynamic Disk Manager 1.2.0
- DiskGenius 6.0.1.1645
- NIUBI Partition Editor 10.2.0
- Paragon Hard Disk Manager 15 10.1.25.1137
- Active Partition Manager 26.0.0
- Сценарий Microsoft DiskPart.dps
- Управление дисками, системное
- DiskCopy 1.4.5.0
- Diskpart GUI Micro

### Диагностика (26)

- AIDA64 8.20.8100
- Hard Disk Sentinel 6.30
- HD Tune 6.00
- Check Disk GUI
- OCCT 4.5.1
- OCCT 11
- BurnInTest 8.1 Build 1025
- PerformanceTest 10.2 Build 1002
- IsMyLcdOK
- Keyboard Test Utility
- NirLauncher
- HDD Regenerator 2024
- Drevitalize 4.10
- Linpack Xtreme 1.1.8
- LinX 0.6.5
- Victoria 5.37
- Sound Check
- HDDScan 4.1.0.29
- PassMark MonitorTest 4.0 Build 1002
- Core Temp 1.18.1
- PC3000 Disk Analyzer 2.2.4
- CrystalDiskInfo 9.7.2
- CrystalDiskMark 9.0.1
- CPU-Z 2.18
- HWiNFO 8.40.5900
- HWMonitor 1.55

### Установка Windows (2)

- WinNTSetup 5.4.2
- Установка Windows (только x64)

### Сеть (16)

- Opera
- FileZilla
- qBittorrent
- µTorrent
- Download Master
- Advanced IP Scanner 2.5.4594.1
- FtpUse
- iSCSI Initiator
- PPPoE
- Импорт WLAN профилей
- Сетевые подключения
- Создать подключение
- Состояние сети
- Включить файрвол
- Отключить файрвол
- PE Network

### Удалённый доступ и VPN (14)

- AnyDesk
- Supremo
- RustDesk
- HopToDesk
- Ammyy Admin 3.9
- AeroAdmin 4.9 Build 3612
- TeamViewer 15 (only Admin user)
- Radmin Server
- Radmin VPN and Viewer
- RDP клиент
- TightVNC
- UltraVNC
- PuTTY
- OpenVPN

### Редакторы BCD, утилиты (5)

- EasyUEFI 6.2.0
- EasyBCD 2.4.0.237
- BOOTICE
- BootSectGui
- BCDBootGUI

### Восстановление данных (13)

- R-Studio 9.5.191686
- EaseUS Data Recovery Wizard 20.1.0
- Active Partition Recovery 26.0.2
- Active File Recovery 26.0.3
- Runtime GetDataBack 5.76
- Runtime GetDataBack for NTFS 4.33
- Runtime GetDataBack for FAT 4.33
- Runtime Raid Reconstructor 5.16
- Recover Keys 12.0.6.311
- ShadowCopyView
- TestDisk 7.3
- ShowKeyPlus
- Восстановить WLAN пароли

### Средство восстановления Windows (1)

- Средство восстановления Windows

### Драйверы (12)

- Установить доп. драйверы MassStorage
- Установить драйверы из хост. системы
- Установить все драйвера (Авто)
- Установить только WLAN драйвера
- Установить только VIDEO драйвера
- Установить только LAN драйвера
- Установить драйвер Paragon APFS
- Установить драйвер Paragon HFS+
- Установить драйвер Paragon Linux
- Check Device 1.0.1.70
- Double Driver 4.1.0
- DrvIndex

### Форматирование (2)

- Active KillDisk 25.0.23
- HDD Low Level Format Tool 4.50

### Утилиты (17)

- TreeSize
- Acronis Shell Extension
- Dism++
- OemKey
- HardLink ShellExtension
- Unlocker 1.9.2
- Настройка Ram-диска
- Экранная клавиатура
- 7-Zip
- GImageX 2.2.0
- Синхронизировать буквы дисков (выбор системы)
- CMOS De-Animator 3
- TeraCopy 3.6.0.4
- USB Safely Remove
- Удаленный реестр (ручной выбор OS)
- WinDirStat 2.5.0
- Экранная лупа

### Сброс паролей (6)

- Windows Login Unlocker 2.3
- Reset Windows Password 9.3.0.937
- Разблокировка BitLocker
- Simplix Password Reset 5.1
- Elcomsoft System Recovery 7.2.628
- PCUnlocker 6.1

### Дефрагментация (2)

- Defraggler 2.22.995
- O&O Defrag 24.0

### HEX редакторы (3)

- CIHexViewer 2.0
- Active Disk Editor 24.0.0
- WinHex 20.8 SR1

### Видео, аудио, графика (6)

- Media Player Classic
- FastStone Capture
- IrfanView
- Ножницы
- Запись звука
- Webcam Recorder

### Документы (3)

- Microsoft Office 2007
- STDU Viewer
- Блокнот

### Файловые менеджеры (5)

- Total Commander
- MSDaRT Explorer
- Компьютер
- Far Manager 3.0 Build 6161
- Runtime Captain Nemo 7.04

### Поиск файлов (1)

- Everything 1.4.1.1028

### CD утилиты (3)

- UltraISO Premium
- PowerISO 9.2
- gBurner 5.7

### Антивирусы (7)

- Ramdisk (Запустить перед Dr.Web CureIt! и Kaspersky Virus Removal Tool)
- Скачать и запустить Dr.Web CureIt!
- Запустить Dr.Web CureIt!
- Скачать и запустить Kaspersky Virus Removal Tool
- Запустить Kaspersky Virus Removal Tool
- Скачать и запустить SmartFix Tool
- Запустить SmartFix Tool

### Системные (11)

- Блокнот
- Диспетчер задач WinPE
- Диспетчер устройств WinPE
- Калькулятор
- Командная строка
- Настройка мыши
- Параметры быстродействия WinPE
- Сетевые подключения
- Службы WinPE
- Управление дисками
- Управление питанием

### Консольные утилиты (11)

- bcdboot
- BootRec
- bootsect
- devcon
- imagex
- MBR2GPT
- mountvol
- PING
- refutil
- subst
- TRACERT

### Шифрование (2)

- DiskCryptor 1.4.0 beta
- VeraCrypt 1.26.24

## DOS-программы (съёмкой не сверены)

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
## Антивирусы — важная особенность сборки

В `SSTR/MInst/Portable/Antivirus` вместо самих программ лежат **пустышки**.
Перед работой скачать актуальные версии с официальных сайтов и положить вместо
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

Группа «Антивирусы» меню Пуск (7 пунктов) подтверждена съёмкой 2026-10-22:
Ramdisk-подготовка и пары «Скачать и запустить»/«Запустить» для Dr.Web CureIt!,
Kaspersky Virus Removal Tool и SmartFix Tool.

## Чего в Strelec нет и что берём из Tools

| Задача | Утилита на разделе Tools |
|--------|--------------------------|
| SMART-лог в файл одной командой из живой ОС | `smartmontools` (`smartctl -x`) |
| Тест ОЗУ свежее, чем 7.20 в сборке | `MemTest86+` 8.10 |
| Стресс CPU из живой Windows без перезагрузки | `Prime95` 30.19b20 |
| Стресс CPU/памяти/IO в Linux | `stress-ng` 0.22.01 |
| SMART и температура без GUI, в отчёт | `smartmontools`, `nvme-cli` в Live Mint |
