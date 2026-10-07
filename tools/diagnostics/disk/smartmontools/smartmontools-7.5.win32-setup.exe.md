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
| SHA256 | `PENDING` — вносится после скачивания |
| Размер | ≈ 1.5 МБ |
| Лицензия | GPL-2.0 |
| Статус | `planned` |

## Как получить

```
# Прямая ссылка на релиз GitHub
curl -LO https://github.com/smartmontools/smartmontools/releases/download/RELEASE_7_5/smartmontools-7.5.win32-setup.exe
```

После скачивания заполнить SHA256 и размер в `/manifest.csv` и поменять
`status` на `present`.

## Проверка подлинности

В релизе на GitHub рядом с файлом лежат `.asc`-подписи. Проверка:

```
gpg --verify smartmontools-7.5.win32-setup.exe.asc smartmontools-7.5.win32-setup.exe
```

## Куда положить на флешке

`Tools:\diagnostics\disk\smartmontools\`
