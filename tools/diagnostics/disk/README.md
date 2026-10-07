# disk/ — накопители: SMART, поверхность, температура

## Состав

| Утилита | Версия | Что даёт | Лицензия |
|---------|--------|----------|----------|
| [`smartmontools/`](smartmontools/) | 7.5 | `smartctl` — SMART в файл, NVMe self-test, атрибутика | GPL-2.0 |
| [`CrystalDiskInfo/`](CrystalDiskInfo/) | 9.9.2 | Карточка здоровья на экране, вердикт «Хорошо / Тревога / Плохо» | MIT |

## Разделение ролей

| Нужно | Чем |
|-------|-----|
| Лог SMART в отчёт | `smartctl -x > reports\smart_<дата>.txt` |
| Показать заказчику | CrystalDiskInfo |
| Сравнить состояние между визитами | `smartctl` — текстовый вывод сравнивается построчно |
| Температура NVMe | `smartctl -a` или `nvme smart-log` в Live Mint |

## Что берётся из Strelec, а не отсюда

Тест поверхности, переназначение секторов, прогноз ресурса — всё это есть в
WinPE и на раздел `Tools` не дублируется:

| Задача | Утилита в Strelec |
|--------|-------------------|
| Тест поверхности HDD | Victoria 5.37 (x86) / MHDD 4.6 / HDAT2 7.6 (DOS) |
| Переназначение секторов | HDD Regenerator 2024, DRevitalize 4.10 |
| Прогноз остатка ресурса | Hard Disk Sentinel 6.30 |
| Скорость чтения/записи | CrystalDiskMark 9.0.1 |
| Глубокая диагностика | PC3000 Disk Analyzer 2.2.4 |

Полный список — в [`../strelec-tools.md`](../strelec-tools.md).

## Критерий «диск годен к работе»

По SMART, до любых разрушающих действий:

| Атрибут | Норма |
|---------|-------|
| `Reallocated_Sector_Ct` (5) | 0 |
| `Current_Pending_Sector` (197) | 0 |
| `Offline_Uncorrectable` (198) | 0 |
| `Reported_Uncorrect` (187) | 0 |
| NVMe `Percentage Used` | < 90% |
| `SMART overall-health` | PASSED |

Ненулевое значение в первых четырёх — сначала образ диска, потом всё остальное.
