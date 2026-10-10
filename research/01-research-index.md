# 01. Поисковые запросы и карта покрытия

## Методология

Сформировано **46 поисковых запросов**. Запросы сгруппированы в **13 тематических
кластеров**; поиск выполнялся по кластеру (один поисковый вызов на кластер, глубина
извлечения 2), а не по каждому запросу отдельно, — это устраняет дублирование выдачи
по пересекающимся формулировкам и снижает риск противоречивых трактовок.

Каждый кластер ниже помечен статусом:
- **ВЫПОЛНЕН** — поиск выполнен в этой сессии, результаты в `02-findings.md`
- **ПОКРЫТ** — ответ получен в рамках выдачи другого кластера (указано, какого)

Источники, недоступные из рабочей среды (домены вне разрешённого списка хостов),
помечены **НЕ ПРОВЕРЕНО ЗДЕСЬ** — утверждение по ним выведено из доступной выдачи
и требует сверки на машине заказчика.

---

## Кластер A. Ventoy: персистентность Linux (запросы 1–4) — ВЫПОЛНЕН

1. `Ventoy persistence plugin image_conf.json datfile Linux Mint casper-rw casper-home-rw настройка`
2. `Ventoy CreatePersistentImg.sh ExtendPersistentImg.sh размер label casper-rw`
3. `Ventoy persistence Linux Mint 22 xfce cinnamon работает ли сохранение изменений`
4. `Ventoy ventoy.json persistence autosel timeout backend несколько dat файлов`

## Кластер B. Ventoy: персистентность WinPE / Windows (запросы 5–8) — ВЫПОЛНЕН

5. `Ventoy WinPE ISO сохранение изменений persistence vhd vdisk`
6. `Sergei Strelec WinPE 11 сохранение изменений fbwf RAMDISK размер`
7. `Ventoy VHD boot plugin ventoy_vhdboot.img Windows To Go VHDX загрузка`
8. `Ventoy wimboot plugin strelec wim загрузка напрямую`

## Кластер C. Целевая ОС и её жизненный цикл (запросы 9–12) — ВЫПОЛНЕН

9. `Windows 11 IoT Enterprise LTSC 2024 f6b14814 support lifecycle`
10. `Windows 11 IoT Enterprise LTSC 2024 отличия от Windows 11 Enterprise LTSC 5 лет`
11. `Windows 10 IoT Enterprise LTSC 2021 21H2 срок поддержки` — **ПОКРЫТ** кластером C
12. `Windows 11 IoT LTSC 2024 требования TPM Secure Boot обход` — **ПОКРЫТ** кластером C

## Кластер D. Debloat: службы и планировщик (запросы 13–17) — ВЫПОЛНЕН

13. `Windows 11 LTSC debloat scheduled tasks telemetry services disable list`
14. `DiagTrack dmwappushservice DPS WdiSystemHost InventorySvc отключение последствия`
15. `SysMain DoSvc WSearch WerSvc PcaSvc CDPSvc отключение SSD память утечки`
16. `ContentDeliveryManager SilentInstalledAppsEnabled SubscribedContent bloat возврат`
17. `Microsoft Compatibility Appraiser ProgramDataUpdater Consolidator UsbCeip schtasks Disable`

## Кластер E. Механизм IFEO (запросы 18–20) — ВЫПОЛНЕН

18. `IFEO Image File Execution Options Debugger блокировка запуска exe Windows debloat`
19. `IFEO GlobalFlag 512 SilentProcessExit MonitorProcess механизм`
20. `IFEO ограничения маски UseFilter обход DEBUG_PROCESS`

## Кластер F. Аппаратная платформа станции (запросы 21–24) — ВЫПОЛНЕН

21. `MSI Modern 15 B12M драйверы Windows 11 Intel AX211 Realtek`
22. `MSI Modern 15 B12M BIOS VMD Intel IRST NVMe не видно при установке`
23. `Intel Core i3-1215U драйвер чипсет Intel DTT Innovation Platform Framework`
24. `Realtek RTL8822 Bluetooth USB VID_0BDA PID_D723 драйвер`

## Кластер G. Резервное копирование диска (запросы 25–27) — ВЫПОЛНЕН

25. `Clonezilla backup restore NVMe Windows 11 UEFI GPT образ диска partclone`
26. `Clonezilla ограничения GPT UEFI Secure Boot BitLocker dd MBR backup`
27. `AOMEI Backupper Macrium Reflect WinPE резервная копия MBR GPT` — **ПОКРЫТ** кластером G
    (Clonezilla как базовый инструмент; альтернативы — см. `04-software-inventory.md`)

## Кластер H. Обслуживание образа и драйверов (запросы 28–30) — ВЫПОЛНЕН

28. `DISM /Export-Driver экспорт драйверов /Get-ProvisionedAppxPackages Remove-ProvisionedAppxPackage offline`
29. `DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase последствия необратимость`
30. `pnputil /export-driver Export-WindowsDriver PowerShell альтернативы DISM`

## Кластер I. Износ SSD (запросы 31–33) — ВЫПОЛНЕН

31. `уменьшение износа SSD Windows 11 hibernation pagefile WinSxS TRIM`
32. `powercfg /hibernate off fsutil DisableDeleteNotify Storage Sense`
33. `pagefile фиксированный размер 8 ГБ RAM риск crash dump стабильность`

## Кластер J. Инструменты debloat (запросы 34–36) — ВЫПОЛНЕН

34. `сравнение debloat Chris Titus WinUtil Sophia Script Win11Debloat`
35. `Win11Debloat Raphire обратимость undo регистр безопасность`
36. `Sophia Script LTSC 2024 поддержка редакции ограничения`

## Кластер K. Автоустановка (запросы 37–38) — ВЫПОЛНЕН

37. `Ventoy auto_install plugin autounattend.xml Templates parent ISO Windows`
38. `autounattend.xml разметка диска GPT ESP MSR Recovery раздел DiskConfiguration`

## Кластер L. Перенос пользовательских данных (запросы 39–40) — ВЫПОЛНЕН

39. `Chrome User Data профиль резервная копия пути SQLite Login Data DPAPI`
40. `VS Code settings.json extensions перенос настроек пути AppData Roaming Code`

## Кластер M. Атака на применённые настройки (запросы 41–46) — ВЫПОЛНЕН 2026-10-07

Добавлен на Этапе 4.3 по требованию заказчика: перед внедрением новых правил
проекта провести исследование векторов отмены применённых настроек. Результаты
— в `08-settings-attack-vectors.md`.

41. `Windows 11 settings reset after feature update revert defaults registry`
42. `заблокировать Windows Update установка драйверов ExcludeWUDriversInQualityUpdate`
43. `Windows audit mode sysprep generalize CopyProfile default user profile`
44. `Win11Debloat WinUtil Sophia Script GTweak сравнение откат undo`
45. `удаление GroupPolicy Registry.pol сброс локальных групповых политик защита ACL`
46. `GTweak Greedeks debloat портативный лицензия`

---

## Запросы, оставшиеся без независимой проверки

| Тема | Статус | Причина |
|------|--------|---------|
| Точный состав appx-пакетов именно в `f6b14814` | **НЕ ПРОВЕРЕНО ЗДЕСЬ** | Требует `Get-AppxProvisionedPackage` на смонтированном образе; выполняется на Этапе 6 |
| Актуальная сборка WinPE Strelec на дату работ | **ЗАКРЫТО заказчиком**: на флешке сборка `2026.02.05`; в выдаче поиска встречалась и `2026.09.08` | Состав сборки 2026.02.05 — в `tools/diagnostics/strelec-tools.md`; сверить по `\MInst\profiles\strelec64Windows10.ini` внутри образа |
| Точный перечень драйверов под B12M с сайта MSI | **ЧАСТИЧНО**: состав компонентов подтверждён сторонним каталогом драйверов | Сверить с `ru.msi.com` на машине заказчика |
| Совместимость текущей сборки Sophia Script с LTSC 2024 | **ЗАКРЫТО 2026-10-07** | Официальный README проекта содержит отдельную строку для `Windows 11 Enterprise LTSC 2024`, пакеты под LTSC 2024 выпускаются отдельно. См. `02-findings.md` J4 и `08-settings-attack-vectors.md` B3 |
| Лицензия GTweak и наличие отката у каждой его правки | **НЕ ПРОВЕРЕНО** | Не найдено в выдаче. Пока не проверено, GTweak в регламент не входит. См. `08-settings-attack-vectors.md` B4 |
| Номер версии Sophia Script на дату выезда | **НЕ ПРОВЕРЕНО** | Источники дают 7.1.4 и 7.3.0. Брать из релизов GitHub при скачивании |
