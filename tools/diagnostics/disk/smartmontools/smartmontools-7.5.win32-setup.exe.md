# smartmontools-7.5.win32-setup.exe — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).
Этот файл — учётная карточка: что должно лежать рядом и откуда брать.

| Поле | Значение |
|------|----------|
| Имя файла | `smartmontools-7.5.win32-setup.exe` |
| Назначение | Установщик smartmontools для Windows: `smartctl`, `smartd` |
| Версия | 7.5 (2025-05-12) |
| Источник | https://github.com/smartmontools/smartmontools/releases/download/RELEASE_7_5/smartmontools-7.5.win32-setup.exe |
| Зеркало | https://sourceforge.net/projects/smartmontools/files/ |
| SHA256 | `896337fcc253220614cf8cdbd5cf2321c5aa326a37a04160a672a281e6104c70` |
| Размер | 1 508 408 байт (1,4 МБ) |
| Лицензия | GPL-2.0 |
| Статус | `present` |

## Как получить

```
# Прямая ссылка на релиз GitHub
curl -LO https://github.com/smartmontools/smartmontools/releases/download/RELEASE_7_5/smartmontools-7.5.win32-setup.exe
```

Сумма и размер внесены в `/manifest.csv` и в эту заглушку: сумма — из
манифеста пакетного менеджера `microsoft/winget-pkgs`, пакет
`smartmontools.smartmontools` версии 7.5, размер — из API релизов GitHub.
После скачивания сверить SHA256 файла с ожидаемым значением из таблицы выше —
они обязаны совпасть.

## Проверка подлинности

В релизе на GitHub рядом с файлом лежат `.asc`-подписи. Проверка:

```
gpg --verify smartmontools-7.5.win32-setup.exe.asc smartmontools-7.5.win32-setup.exe
```

## Куда положить на флешке

`Tools:\diagnostics\disk\smartmontools\`
