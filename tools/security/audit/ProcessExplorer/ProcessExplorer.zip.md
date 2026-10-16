# ProcessExplorer.zip — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `ProcessExplorer.zip` |
| Назначение | Процессы, потоки, DLL, дескрипторы, цифровые подписи |
| Версия | **не закреплена** — в источниках 17.1 и 17.14, первоисточник недоступен |
| Источник | https://download.sysinternals.com/files/ProcessExplorer.zip |
| SHA256 | `746770d3f54326dd7da16c2b2815803ab131f348cba24a91cb6a38cfd2f7073f` |
| Размер | около 3,3 МБ |
| Лицензия | Microsoft Sysinternals Software License, freeware включая бизнес |
| Статус | `planned` |

## Как получить

Официальный адрес загрузки Sysinternals. По сторонним данным в архиве `procexp.exe` (x86), `procexp64.exe` (x64) и `procexp64a.exe` (ARM64), на обычной станции нужен `procexp64.exe`. **Состав не проверен** — `download.sysinternals.com` недоступен, имена уточнить после распаковки.

## Проверка подлинности

Сверить SHA256 скачанного файла с ожидаемым значением из таблицы выше — они обязаны совпасть:

```powershell
Get-FileHash -Algorithm SHA256 "E:\tools\security\audit\ProcessExplorer\ProcessExplorer.zip"
```

```bash
sha256sum "/mnt/tools/security/audit/ProcessExplorer/ProcessExplorer.zip"
```

Сверить подпись Microsoft Corporation в свойствах `procexp64.exe`.

## Куда положить на флешке

`Tools:\security\audit\ProcessExplorer\ — распакованным каталогом.`

То же ограничение лицензии: использовать можно, распространять коммерчески — нет.
