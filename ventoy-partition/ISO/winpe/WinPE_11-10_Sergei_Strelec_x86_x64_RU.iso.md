# WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso

> **Это заглушка.** Образ `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/winpe/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` |
| Категория | `ISO/winpe` |
| Версия | 2026.09.08 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://sergeistrelec.name/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Аварийная среда: разметка, бэкап, восстановление данных и загрузчика. Загружается в обычном ISO-режиме.

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
