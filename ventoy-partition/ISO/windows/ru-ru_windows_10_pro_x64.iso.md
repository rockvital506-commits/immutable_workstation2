# ru-ru_windows_10_pro_x64.iso

> **Это заглушка.** Образ `ru-ru_windows_10_pro_x64.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/windows/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `ru-ru_windows_10_pro_x64.iso` |
| Категория | `ISO/windows` |
| Версия | 22H2 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://www.microsoft.com/ru-ru/software-download/windows10 |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Для заказчиков без IoT-лицензии, старое железо.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\windows\ru-ru_windows_10_pro_x64.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/windows/ru-ru_windows_10_pro_x64.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
