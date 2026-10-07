# WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso

> **Это заглушка.** Образ `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/winpe/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` |
| Категория | `ISO/winpe` |
| Версия | 2026.02.05 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://sergeistrelec.name/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Аварийная среда: разметка, бэкап, восстановление данных и загрузчика. Загружается в обычном ISO-режиме.

## Состав сборки

Полный перечень утилит этой сборки — в [`tools/diagnostics/strelec-tools.md`](../../../tools/diagnostics/strelec-tools.md).

Сборка содержит пять ядер: `WinPE 11 x64`, `WinPE 10 x64`, `WinPE 10 x86`,
`WinPE 8 x86`, `WinPE 8 x86 (Native)`. Состав программ между ядрами различается:
в x64-образе 2026.02.05 нет Victoria, HD Tune Pro, Western Digital Data
Lifeguard и RWEverything, которые есть в x86-образе.

Антивирусы в `SSTR/MInst/Portable/Antivirus` лежат **пустышками** — перед
выездом заменить актуальными версиями с официальных сайтов.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\winpe\WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/winpe/WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
