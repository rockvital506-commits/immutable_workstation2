# en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso

> **Это заглушка.** Образ `en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/windows/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso` |
| Категория | `ISO/windows` |
| Версия | IoT LTSC 2024 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://www.microsoft.com/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Основная целевая ОС станции MSI B12M-211RU. Поддержка до 2034-10-10.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\windows\en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/windows/en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
