# Autoruns.zip — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `Autoruns.zip` |
| Назначение | Всё, что стартует вместе с системой; `Autorunsc.exe` даёт отчёт в CSV |
| Версия | **не закреплена** — сверить с первоисточником нельзя, `microsoft.com` недоступен |
| Источник | https://download.sysinternals.com/files/Autoruns.zip |
| SHA256 | `7b3a8eed819f732a3e4c134aecaeaebb8d643a46490ccddb82cc8a1a745c4cf7` |
| Размер | около 3 МБ |
| Лицензия | Microsoft Sysinternals Software License, freeware включая бизнес |
| Статус | `planned` |

## Как получить

Официальный адрес загрузки Sysinternals, всегда отдаёт актуальную версию. Архив распаковать; установки не требует, в реестр не пишет.

## Проверка подлинности

Сверить SHA256 скачанного файла с ожидаемым значением из таблицы выше — они обязаны совпасть:

```powershell
Get-FileHash -Algorithm SHA256 "E:\tools\security\audit\Autoruns\Autoruns.zip"
```

```bash
sha256sum "/mnt/tools/security/audit/Autoruns/Autoruns.zip"
```

Сверить, что архив распаковывается и `Autoruns64.exe` подписан Microsoft Corporation. Снимок подписи виден в свойствах файла.

## Куда положить на флешке

`Tools:\security\audit\Autoruns\ — распакованным каталогом.`

Лицензия разрешает использовать утилиту в работе, но **запрещает коммерческое распространение и снятие брендирования Microsoft**. Носить на своей флешке можно, включать в продаваемый продукт — нет.
