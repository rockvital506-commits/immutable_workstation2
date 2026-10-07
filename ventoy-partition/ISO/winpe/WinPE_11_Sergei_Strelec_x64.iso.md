# WinPE_11_Sergei_Strelec_x64.iso

> **Это заглушка.** Образ `WinPE_11_Sergei_Strelec_x64.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/winpe/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `WinPE_11_Sergei_Strelec_x64.iso` |
| Категория | `ISO/winpe` |
| Версия | 2026.01 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://example.com, с запятой |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Аварийная среда

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\winpe\WinPE_11_Sergei_Strelec_x64.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/winpe/WinPE_11_Sergei_Strelec_x64.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
