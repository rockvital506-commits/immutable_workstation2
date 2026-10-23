# WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso

> **Это заглушка.** Образ `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` в git не хранится.
> Скачайте его по ссылке ниже и положите в `/winpe/` на разделе VENTOY флешки.

> **База пути.** Непомеченные пути в этом документе считаются от корня
> репозитория. Префиксы `CONVENTIONS.md` §10.1 применяются там, где путь
> указывает на раздел флешки.

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

Полный перечень утилит этой сборки — в [`tools/diagnostics/strelec-tools.md`](../../../tools/diagnostics/strelec-tools.md)
(таксономия 24 групп меню / 201 пункт, сверено съёмкой 2026-10-22 —
[`research/27-winpe11-observation.md`](../../../research/27-winpe11-observation.md)).

Сборка содержит пять ядер: `WinPE 11 x64`, `WinPE 10 x64`, `WinPE 10 x86`,
`WinPE 8 x86`, `WinPE 8 x86 (Native)`. Состав программ между ядрами различается
(по описанию автора). Съёмка меню WinPE 11 x64 2026-10-22 показала Victoria 5.37
в ядре x64 — прежняя запись «в x64 нет Victoria» ошибочна (N56); HD Tune Pro,
Western Digital Data Lifeguard и RWEverything в меню x64 не обнаружены.

Антивирусы в `SSTR/MInst/Portable/Antivirus` лежат **пустышками** — перед
работой заменить актуальными версиями с официальных сайтов.

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
