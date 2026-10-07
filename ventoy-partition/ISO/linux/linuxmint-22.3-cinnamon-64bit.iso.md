# linuxmint-22.3-cinnamon-64bit.iso

> **Это заглушка.** Образ `linuxmint-22.3-cinnamon-64bit.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/linux/` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | `linuxmint-22.3-cinnamon-64bit.iso` |
| Категория | `ISO/linux` |
| Версия | 22.3 |
| Размер | 0 байт |
| SHA256 | `a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4` |
| Источник | https://mirrors.edge.kernel.org/linuxmint/stable/22.3/ |
| Лицензия | — |
| Добавлено | 2026-10-07 |
| Статус | planned |

## Назначение

Live-среда с персистентностью: сеть, браузер, работа с файлами. Релиз 2026-01-13, поддержка до 04/2029.

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс `_VTWIMBOOT` / `_VTMEMDISK` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

```powershell
Get-FileHash -Algorithm SHA256 "E:\ISO\linux\linuxmint-22.3-cinnamon-64bit.iso"
```

Linux:

```bash
sha256sum "/mnt/ventoy/ISO/linux/linuxmint-22.3-cinnamon-64bit.iso"
```

Ожидаемое значение: `a081ab202cfda17f6924128dbd2de8b63518ac0531bcfe3f1a1b88097c459bd4`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
