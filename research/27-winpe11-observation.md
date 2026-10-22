# 27. Наблюдение WinPE 11 (x64) 2026.02.05: съёмка интерфейса и пакет `_TEMP`

Дата: 2026-10-22. Тип: AUDIT-наблюдение факта носителя.

## 1. Источники и метод

- **Съёмка.** 32 кадра экрана ноутбука (MSI), файл `IMG_20261022_110804_877.pdf`
  (32 страницы, PDF 1.7, producer `iLovePDF`, текстового слоя нет; кадры
  1240×1653 и 1240×930, фото экрана, не скриншоты). Сессия 2026-10-22,
  сборка `WinPE 11-10-8 Sergei Strelec 2026.02.05` RU, выбрано ядро
  **WinPE 11 x64** (водяной знак, кадр 01).
- **Пакет `_TEMP`** (коммит `c30f36d` в `origin/main`): 21 файл
  `DiskPart_Scripts` (8) и `Tweaks` (13), прочитаны полностью.
- **Решения владельца 2026-10-22.** Фото принято как факт носителя (вариант B);
  находка N55 — инстанс B-03; находки N56–N59 — инстансы B-03, `n` по факту.
- **Веб-сверка.** `sergeistrelec.name` (история версий), выписки состава
  2026.02.05 (RU и EN), `sergeistrelec.ru/faq.html` (MInst, профили, образец
  DiskPart). Веб-выписки расходятся с наблюдением (см. N57) — принято
  наблюдение.

Съёмка и файлы дополняют друг друга: кадры дают топологию меню и подписи
ярлыков, файлы — точные имена и содержимое (кадр 02 подтвердил имя
`UEFI_with_WinRE_ang_Boot_partition.dps`, включая «ang»).

## 2. Разметка съёмки (32 кадра)

Маппинг кадр → группа меню: кадр `NN` = группа `NN-7` для NN = 8…31
(кадр 08 = группа 1 «Бэкап и восстановление», кадр 31 = группа 24 «Шифрование»).

| Кадр | Что показано |
|---|---|
| 01 | Рабочий стол (фрагмент): водяной знак `sergeistrelec.name`, «Windows PE 11 (x64) Sergei Strelec», часы 11:07:41, ENG — ядро подтверждено |
| 02 | Проводник `DiskPart_Scripts` (8 элементов); в навигаторе буквы дисков: `C: Windows`, `D: Ventoy`, `E: SYSTEM`, `F: Tools_SD400`, `G: DVD`, `I:`, `J: BIOS_RVY`, `K: VTOYEFI`, `X: Boot` |
| 03 | Проводник `Tweaks` (11 элементов) |
| 04 | `Tweaks\Windows 10` (2 файла) |
| 05 | `Tweaks\Windows 11` (2 файла) |
| 06 | Меню Пуск: Программы WinPE ▶, Этот компьютер, MInstAll, Командная строка, Выполнить…, Перезагрузка, Выключение |
| 07 | «Программы WinPE»: список 24 групп |
| 08 | «Бэкап и восстановление» — 19 пунктов (список — `strelec-tools.md`) |
| 09 | «Жёсткий диск» — 14 пунктов (список — `strelec-tools.md`) |
| 10 | «Диагностика» — 26 пунктов (список — `strelec-tools.md`) |
| 11 | «Установка Windows» — 2 пунктов (список — `strelec-tools.md`) |
| 12 | «Сеть» — 16 пунктов (список — `strelec-tools.md`) |
| 13 | «Удалённый доступ и VPN» — 14 пунктов (список — `strelec-tools.md`) |
| 14 | «Редакторы BCD, утилиты» — 5 пунктов (список — `strelec-tools.md`) |
| 15 | «Восстановление данных» — 13 пунктов (список — `strelec-tools.md`) |
| 16 | «Средство восстановления Windows» — 1 пунктов (список — `strelec-tools.md`) |
| 17 | «Драйверы» — 12 пунктов (список — `strelec-tools.md`) |
| 18 | «Форматирование» — 2 пунктов (список — `strelec-tools.md`) |
| 19 | «Утилиты» — 17 пунктов (список — `strelec-tools.md`) |
| 20 | «Сброс паролей» — 6 пунктов (список — `strelec-tools.md`) |
| 21 | «Дефрагментация» — 2 пунктов (список — `strelec-tools.md`) |
| 22 | «HEX редакторы» — 3 пунктов (список — `strelec-tools.md`) |
| 23 | «Видео, аудио, графика» — 6 пунктов (список — `strelec-tools.md`) |
| 24 | «Документы» — 3 пунктов (список — `strelec-tools.md`) |
| 25 | «Файловые менеджеры» — 5 пунктов (список — `strelec-tools.md`) |
| 26 | «Поиск файлов» — 1 пунктов (список — `strelec-tools.md`) |
| 27 | «CD утилиты» — 3 пунктов (список — `strelec-tools.md`) |
| 28 | «Антивирусы» — 7 пунктов (список — `strelec-tools.md`) |
| 29 | «Системные» — 11 пунктов (список — `strelec-tools.md`) |
| 30 | «Консольные утилиты» — 11 пунктов (список — `strelec-tools.md`) |
| 31 | «Шифрование» — 2 пунктов (список — `strelec-tools.md`) |
| 32 | Рабочий стол целиком: 16 ярлыков (в т.ч. Admin_Login, Registry Editor PE, Раскладка клавиатуры, MonitorOff, WiFi, Установка Windows) ||

Итог по меню: 24 группы, **201 пункт**; полные списки — в
`tools/diagnostics/strelec-tools.md` (раздел «Таксономия меню Пуск»).

## 3. Находки

Все пять находок — вхождения механизма B-03 (утверждение о содержимом без
чтения содержимого): состав сборки был каталогизирован по веб-описаниям и
помечен «не сверен с самим образом», но в `strelec-registry.csv`, `PLAN.md`
и `CONVENTIONS.md` отдельные утверждения поданы как факт.

### N55. «Шифрования в Strelec нет вообще» — ложно

Утверждение: `PLAN.md` (абзац «Strelec закрывает сканеры…»),
`tools/strelec-registry.csv` (строка VeraCrypt, `own_copy_reason`),
`research/10-security-scanners-audit-encryption.md` («Аудит и шифрование не
закрыты ничем», таблица `encryption/` → «нет»). Опровержение: кадр 31 —
группа «Шифрование»: **DiskCryptor 1.4.0 beta**, **VeraCrypt 1.26.24**.
Исправлено: PLAN.md, registry (`in_strelec=yes`, `strelec_version=1.26.24`,
основание своей копии «в сборке 1.26.24, у нас 1.26.29 — свежее»), research/10,
`strelec-tools.md` (группа «Шифрование»). Класс: B-03 (решение владельца
2026-10-22).

### N56. «В x64-образе нет Victoria» — ложно

Утверждение: `tools/diagnostics/strelec-tools.md` и заглушка ISO
(«в x64-образе 2026.02.05 нет Victoria, HD Tune Pro, Western Digital Data
Lifeguard и RWEverything»). Опровержение: кадр 10 — «Диагностика» ядра
WinPE 11 x64 содержит **Victoria 5.37**. Частично утверждение верно: HD Tune Pro,
WD Data Lifeguard и RWEverything в меню x64 не обнаружены. Исправлено в обоих
файлах. Класс: B-03.

### N57. Версии каталога не соответствуют сборке

Утверждение: `strelec-tools.md` («версии HWiNFO 8.34, CPU-Z 2.17 …
соответствуют именно этой сборке»), а также ячейки `O&O Defrag 23.0`,
`Active Disk Editor 25.0.7`, `DiskCopy 1.4.4.0`, `Reset Windows Password 7.0.5.702`,
`PCunlocker 5.6`, `Everything 1.4.1.1022`. Опровержение (кадры 10, 14, 21, 22,
25, 26): **HWiNFO 8.40.5900**, **CPU-Z 2.18**, **O&O Defrag 24.0**,
**Active Disk Editor 24.0.0**, **DiskCopy 1.4.5.0**, **Reset Windows Password
9.3.0.937**, **PCUnlocker 6.1**, **Everything 1.4.1.1028**. Исправлено:
каталог перестроен по наблюдённым подписям меню. Класс: B-03.

### N58. «Полный перечень утилит этой сборки» — ложно на момент записи

Утверждение: заглушка ISO (`ventoy-partition/ISO/winpe/…iso.md`): «Полный
перечень утилит этой сборки — в `tools/diagnostics/strelec-tools.md`».
Опровержение: каталог содержал 11 задачных разделов с частичными списками
(например, «Диагностика» — 8 строк при 26 пунктах группы) и не содержал
целых групп (OCCT, AIDA64, NirLauncher, DiskCryptor и др.). Исправлено:
каталог дополнен полной таксономией 24 групп / 201 пункт — утверждение стало
верным. Класс: B-03.

### N59. «Ни RustDesk среди них нет» — ложно; «семь средств удалённого доступа» — неверно

Утверждение: `CONVENTIONS.md` §7.2.1 оговорка 2 («В сборке есть пять средств
сброса пароля и семь средств удалённого доступа, но ни `NTPWEdit`, ни `RustDesk`
среди них нет») и `tools/strelec-registry.csv` (RustDesk, `in_strelec=no`).
Опровержение: кадр 13 — группа «Удалённый доступ и VPN» (**14 пунктов**)
содержит **RustDesk**. Часть утверждения верна: `NTPWEdit` в группе «Сброс
паролей» (6 пунктов, кадр 20) отсутствует, «пять средств сброса пароля»
подтверждается. Исправлено: CONVENTIONS.md (оговорка 2), registry
(`in_strelec=yes`, `strelec_version=не указана`). Класс: B-03.

## 4. Особенности пакета Strelec (не дефекты репозитория)

Свойства чужого пакета: фиксируем, чтобы не переносить ошибки в каталог.
В пул дефектов не входят — это не утверждения нашего репозитория.

#### F1. Имя в readme не совпадает с файлом

`DiskPart_Scripts/readme.txt` называет схему
`UEFI_with_WindowsRE_and_Recovery_image_partition.dps`, фактическое имя файла —
`UEFI_with_WinRE_Boot_and_Recovery_partition.dps`.

#### F2. Скрипт без описания

`BIOS_Simply.dps` в readme не описан (из шести схем описаны пять).

#### F3. Опечатка в имени системна

`UEFI_with_WinRE_ang_Boot_partition.dps` («ang» вместо «and») — так же в readme;
кадр 02 подтвердил имя.

#### F4. Буквы дисков в схемах

`C:` для Windows назначает только `BIOS_Simply`, остальные — `W:`; WinRE —
`R:` (BIOS) или `T:` (UEFI); recovery — без буквы (`rem assign letter="R"`).
`Tweaks` ожидают `C:` (`set disk=C:\`, readme советует сменить букву в WinPE).

#### F5. Пары `Prevent_Device_Encryption` / `Disable_Prevent_Device_Encryption` идентичны

Оба файла ставят `Control\BitLocker\PreventDeviceEncryption=1`; различие —
одна пустая строка (690/691 байт). Обратного действия нет; readme описывает
только `Disable_Prevent_Device_Encryption` и не упоминает `Prevent_Device_Encryption`.

#### F6. Неверный путь куста в `Disable_WinDefender.cmd`

Строки 67–70 пишут в `HKLM\WIM_Default\WIM_Software\…`; после `reg load`
корень NTUSER смонтирован в `HKLM\WIM_Default`, правильно
`HKLM\WIM_Default\Software\…` (как в `Disable_Outlook_New.cmd`). Четыре
записи — холостые, создают мусорные ключи.

#### F7. Мелочи

В `Disable_Services.cmd` закомментированный `Spooler` продублирован; в
`readme.txt` DiskPart_Scripts опечатка «пользультесь».

## 5. Факты пакета `_TEMP` (SHA256 посчитаны по `c30f36d`)

`DiskPart_Scripts` — 7 схем разметки (`.dps`) + `readme.txt`; UTF-8 без BOM,
переводы строк LF. Схемы: `List_Disk` (`list disk`, безопасный);
`BIOS_Simply` (MBR: 100 МБ FAT32 `MBR_BOOT` + `Windows` C:);
`BIOS_no_WindowsRE_Partition` (MBR: 250 МБ `System` + `Windows` W:);
`BIOS_with_WindowsRE_Partition` (MBR: 1024 МБ WinRE id=27 + 250 МБ `System` +
`Windows` W:); `UEFI_only_Boot_partition` (GPT: EFI 100 + MSR 128 + `Windows` W:);
`UEFI_with_WinRE_ang_Boot_partition` (GPT: WinRE 1024 + EFI 100 + MSR 128 +
`Windows` W:); `UEFI_with_WinRE_Boot_and_Recovery_partition` (GPT: WinRE 1024 +
EFI 100 + MSR 128 + `Windows` (shrink 15000) + `Recovery image`).
Шаблоны — адаптация `CreatePartitions-UEFI/BIOS.txt` Microsoft (rem-комментарии
и NOTE про 4Kn идентичны образцу); отличия от версии в FAQ Стрельца:
WinRE 1024 вместо 300, буква recovery закомментирована. Во всех схемах
`select disk x` — плейсхолдер, требует правки.

`Tweaks` — офлайн-правка кустов целевой Windows из WinPE (`reg load HKLM\WIM_*`
из `%disk%Windows\System32\config\…`, `set disk=C:\`, удаление
транзакционных логов после правок, `pause`). Состав: `Disable/Enable_WinDefender`
(полное отключение/включение Защитника и SmartScreen), `Disable/Enable_UAC`
(`EnableLUA` 0/1, служба `luafv` 4/0), `Prevent_Device_Encryption` (см. F5),
`Disable_Services` (`DiagTrack`, `WSearch`, `TrkWks`, `WerSvc`, `MapsBroker`,
`lfsvc` → `Start=4`; `Spooler` закомментирован), `sfc_scannow`
(`sfc /scannow /offbootdir=C:\ /offwindir=C:\windows`),
`Windows 10|11\Disable_Outlook_New` (общие `HideNewOutlookToggle=1` и
`NewOutlookMigrationUserSetting=0` в `NTUSER.DAT`; различие — Win10 ставит
`BlockedOobeUpdaters=["MS_Outlook"]`, Win11 удаляет ключ
`UScheduler_Oobe\OutlookUpdate`).

| Файл | Байт | SHA256 |
|---|---|---|
| `_TEMP/DiskPart_Scripts/BIOS_Simply.dps` | 218 | `a40f0543786797ef98ce850666bc4718b6354f0126d9be7b0ffa2c16a5c18a3a` |
| `_TEMP/DiskPart_Scripts/BIOS_no_WindowsRE_Partition.dps` | 214 | `740a2068d109becb1c8a8926a03da3c6d30277b14846a28305edd0ac12e63dc2` |
| `_TEMP/DiskPart_Scripts/BIOS_with_WindowsRE_Partition.dps` | 325 | `d1be785b484b7a0977dee1c1d0d52ea3494742312fbb492a0d2b24460e89424a` |
| `_TEMP/DiskPart_Scripts/List_Disk.dps` | 9 | `dc552a90745d1474359ef009f6f07bf72da0ddf01071342bef951895bd95bbf7` |
| `_TEMP/DiskPart_Scripts/UEFI_only_Boot_partition.dps` | 622 | `88d7c80e0a92e9e673974f8caf5c5cb40bb90600319173d8840629b108fbd9a1` |
| `_TEMP/DiskPart_Scripts/UEFI_with_WinRE_Boot_and_Recovery_partition.dps` | 1262 | `399f6550db0935bf1f59d5ab76ab71553fb76a72ee4b5c20d9d9f3b1a49743bb` |
| `_TEMP/DiskPart_Scripts/UEFI_with_WinRE_ang_Boot_partition.dps` | 855 | `4d492f30ee8069d67a8b2023d0eeec10cf8fcf889c3f7474a5b05d6e4f939a5f` |
| `_TEMP/DiskPart_Scripts/readme.txt` | 2543 | `a6fc8cb97c62391442d656807b5e7ab7c23e720a13560486bba54139162a6031` |
| `_TEMP/Tweaks/Disable_Prevent_Device_Encryption.cmd` | 690 | `6cbe0794479e7cd1bcff21360b062d71b31109d8cf2c60fc076192d45b322b66` |
| `_TEMP/Tweaks/Disable_Services.cmd` | 1509 | `b70208760bdd2ab59e709cfe182217bd913a651254b4cd87baa3a3460ea40c43` |
| `_TEMP/Tweaks/Disable_UAC.cmd` | 865 | `38a85553c8e86336a2414049341cd27ca3c24f64327f12d689bcd9d9a37cd762` |
| `_TEMP/Tweaks/Disable_WinDefender.cmd` | 7415 | `0a1173516815cc469b41d577f1964d5e248defb4ada1088b9ea14fa1b619adb2` |
| `_TEMP/Tweaks/Enable_UAC.cmd` | 864 | `9502beb9791110ad35d15d02c8beab60389ac7ee6a642edd4ae282a71fa5799f` |
| `_TEMP/Tweaks/Enable_WinDefender.cmd` | 4877 | `22033629c3fad4a6f5590f2481c0cd4b6fb1f568dcd789cbc5277727b95ebb31` |
| `_TEMP/Tweaks/Prevent_Device_Encryption.cmd` | 691 | `45f1cd488ca88d9e925845bdedce787c15b2fc927e1cb868341f86c867b2d1f3` |
| `_TEMP/Tweaks/Windows 10/Disable_Outlook_New.cmd` | 934 | `989750dae09999923b411aceabdd73cbb8e475598679e703ba7c79f5fca2ebbb` |
| `_TEMP/Tweaks/Windows 10/readme.txt` | 111 | `8d4a4cefcd72272f82ae80be05f6b3d9d0cde01cc552aff342c67028d56ba3c9` |
| `_TEMP/Tweaks/Windows 11/Disable_Outlook_New.cmd` | 880 | `8fee8e11a5bceb317d70918e72fbdcc50dfe89dc65d3994bcfe03ca6fecd5e5a` |
| `_TEMP/Tweaks/Windows 11/readme.txt` | 111 | `8d4a4cefcd72272f82ae80be05f6b3d9d0cde01cc552aff342c67028d56ba3c9` |
| `_TEMP/Tweaks/readme.txt` | 2206 | `e03689cbdedeaad684df870e42542547f9c3c25d3e96722634e56814957aa5c9` |
| `_TEMP/Tweaks/sfc_scannow.cmd` | 60 | `63f67915f48f348ea3a88d5a2fe3ff23d325f0f6311a0644385adc8fb89d9b0b` ||

## 6. Что это даёт проекту

- Схемы `UEFI_with_WinRE_ang_Boot` и `UEFI_with_WinRE_Boot_and_Recovery` —
  кандидаты для шагов разметки алгоритма MSI (вторая совпадает по идее с
  OEM-разделом `J: BIOS_RVY` на машине). **Ретрофит шагов не выполнялся:
  затвор `respect_gate` в силе.**
- Приём офлайн-правки кустов (`reg load` + чистка транзакционных логов) —
  кандидат в процедуры `apply-blocking`/защиты настроек.
- `PreventDeviceEncryption=1` — кандидат в процедуру развёртывания
  (пересекается с решением «VeraCrypt + BitLocker»); решение — за владельцем.
- `Disable_Services` (`DiagTrack=4`) согласуется с `AllowTelemetry = 0`;
  `Disable_WinDefender`, `Disable_UAC` **противоречат** политике защиты
  настроек и не применяются.
- `OemKey` (группа «Утилиты») и `ShowKeyPlus`/`Recover Keys` («Восстановление
  данных») — средства чтения ключей в сборке (шаги 1 и 12 алгоритма).

## 7. Не проверено

- **DMDE.** Заявлен в `research/23` и `strelec-registry.csv`
  (`in_strelec=yes`) как присутствующий в сборке; в меню 24 групп **не
  обнаружен**. Утверждение не подтверждено и окончательно не опровергнуто:
  возможны ярлык вне меню или содержимое вне меню. Сверка по
  `\MInst\profiles\*.ini` или файлам ISO — очередь B. До сверки в пул не
  вносится (не подтверждено).
- **MemTest86Plus 7.20** в меню GUI отсутствует (ожидаемо для DOS-утилиты);
  DOS-программы съёмкой не сверены.
- **Sysinternals** (Autoruns, ProcessExplorer, TCPView) в группах «Утилиты»,
  «Системные», «Консольные утилиты» не обнаружены — утверждение «Sysinternals
  нет» не опровергнуто.
- Метка ярлыка ≠ версия файла: наблюдённые версии требуют сверки по файлам
  или `MInst/profiles`.
- Ядра WinPE 10/8 x86 и Native, DOS-меню, окно MInstAll — не снимались.
- `CONVENTIONS.md` §7.2.1 оговорка 1 («вывод «в сборке есть» действителен
  только после сверки по `MInst/profiles/strelec64Windows10.ini`») вступает в
  натяжение с решением владельца 2026-10-22 (фото = факт носителя для
  наблюдаемого меню). Оговорка не переписана — вопрос к владельцу/очередь B.
- Даты изменения файлов из кадров (25.01.2026, 29.12.2024 и др.) в git не
  сохраняются — факт только из съёмки.
