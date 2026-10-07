# ISO/ — образы загрузочных систем

Корневой каталог поиска Ventoy (`VTOY_DEFAULT_SEARCH_ROOT = /ISO`).
Здесь лежат **только** образы и их заглушки — ничего лишнего, иначе Ventoy
тратит время на сканирование при каждом старте.

## Категории

Заполнены на Этапе 3: `windows/`, `linux/`, `winpe/`, `backup/`.
Зарезервированы и появятся по мере наполнения: `diagnostics/`, `security/`,
`network/`, `firmware/`, `dos/`, `_scratch/`.

## Текущий состав

| Категория | Образ | Назначение |
|-----------|-------|-----------|
| `windows/` | `en-us_windows_11_iot_enterprise_ltsc_2024_x64_dvd_f6b14814.iso` | Основная целевая ОС |
| `windows/` | `en-us_windows_10_iot_enterprise_ltsc_2021_x64_dvd.iso` | Вторая целевая ОС |
| `windows/` | `ru-ru_windows_11_pro_x64.iso` | Pro без IoT-лицензии |
| `windows/` | `ru-ru_windows_10_pro_x64.iso` | Pro, старое железо |
| `winpe/` | `WinPE_11-10_Sergei_Strelec_x86_x64_RU.iso` | Аварийная среда |
| `linux/` | `linuxmint-22.3-cinnamon-64bit.iso` | Live с персистентностью 16 ГБ |
| `backup/` | `clonezilla-live-3.3.3-37-amd64.iso` | Образы дисков и разделов |

Все семь образов зарегистрированы в `/manifest.csv` и имеют заглушки `*.iso.md`.

## Категории (полный перечень)

| Каталог | Содержимое | Примеры |
|---------|-----------|---------|
| `windows/` | Установочные ISO Windows | Win 10/11 LTSC, Pro, Server 2019–2025 |
| `linux/` | Установочные и live-дистрибутивы | Ubuntu, Debian, Proxmox, Rocky |
| `winpe/` | Аварийные среды Windows | WinPE 10/11, Sergei Strelec, Hiren's BootCD PE |
| `diagnostics/` | Диагностика железа | MemTest86, Victoria Live, HDDScan, Ultimate Boot CD |
| `security/` | Антивирусные и аудиторские сканеры | Kaspersky Rescue Disk, Dr.Web LiveDisk, Kali |
| `network/` | Сетевые системы | SystemRescue, Clonezilla с сетью, iPXE-сборки |
| `backup/` | Клонирование и образы | Clonezilla, Rescuezilla, Acronis |
| `firmware/` | Прошивка BIOS/UEFI и дисков | FreeDOS-сборки с утилитами вендоров |
| `dos/` | DOS и низкоуровневые утилиты | FreeDOS, MHDD |
| `_scratch/` | Временные образы «на один выезд» | В git не попадает, чистится регулярно |

## Правила

1. Один образ = один файл `<имя>.iso` на флешке **и** одна заглушка
   `<имя>.iso.md` в репозитории рядом.
2. Имя файла: `<Продукт>_<Версия>_<Арх>_<Язык>[_<Дата>].iso`, латиница,
   без пробелов. Пример: `Win11_24H2_x64_RU_2026-01.iso`.
3. Каждый образ зарегистрирован строкой в `/manifest.csv` (`type=iso`).
4. Хэш SHA256 сверяется после каждой перезаписи образа:
   `scripts/check-flash.sh --verify`.
5. Дубликаты образов разных версий держать только если старая версия реально
   требуется для старого парка; иначе — `status=deprecated` и удаление.

## Суффиксы управления загрузкой Ventoy

Добавляются к имени файла **перед** расширением и меняют способ загрузки
без правки конфига:

| Суффикс | Эффект |
|---------|--------|
| `_VTISO` | Принудительно ISO-режим |
| `_VTNORM` / `_VTNORMAL` | Обычный режим без вторичного меню |
| `_VTWIMBOOT` | Загрузка через wimboot (для WinPE) |
| `_VTMEMDISK` | Загрузка в режиме memdisk (для мелких DOS/Floppy-образов) |
| `_VTGRUB2` | Передать образ grub2 |

## Заглушки в этом каталоге

Список заполняется на Этапе 2. Формат заглушки — `CONVENTIONS.md`, раздел 2.
