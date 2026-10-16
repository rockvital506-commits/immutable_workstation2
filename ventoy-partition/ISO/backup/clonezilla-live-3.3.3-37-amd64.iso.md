# clonezilla-live-3.3.3-37-amd64.iso

> **Это заглушка.** Образ `clonezilla-live-3.3.3-37-amd64.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/backup/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `clonezilla-live-3.3.3-37-amd64.iso` |
| Категория | `ISO/backup` |
| Версия | 3.3.3-37 |
| Размер | 0 байт |
| SHA256 | `PENDING` |
| Источник | https://sourceforge.net/projects/clonezilla/files/clonezilla_live_stable/3.3.3-37/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Образы дисков и разделов, partclone, MBR/GPT. Стабильная ветка от 2026-09-13.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\backup\clonezilla-live-3.3.3-37-amd64.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/backup/clonezilla-live-3.3.3-37-amd64.iso"
```

Ожидаемое значение: `PENDING`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
