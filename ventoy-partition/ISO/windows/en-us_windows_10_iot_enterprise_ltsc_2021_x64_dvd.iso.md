# en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso

> **Это заглушка.** Образ `en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/windows/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso` |
| Категория | `ISO/windows` |
| Версия | IoT LTSC 21H2 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://www.microsoft.com/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Вторая равноправная целевая ОС: старый парк и случаи, где Win11 не проходит по требованиям.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\windows\en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/windows/en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
