# TCPView.zip — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `TCPView.zip` |
| Назначение | Все TCP/UDP-соединения с привязкой к процессу |
| Версия | 4.19 — **не сверена с первоисточником** |
| Источник | https://download.sysinternals.com/files/TCPView.zip |
| SHA256 | `4fc5ceba3e1b27ad95a24df35d094b454ec5f9478e12a8ca2b1b222705b9683b` |
| Размер | около 1,5 МБ |
| Лицензия | Microsoft Sysinternals Software License, freeware включая бизнес |
| Статус | `planned` |

## Как получить

Официальный адрес загрузки Sysinternals. В архиве графическая утилита и `Tcpvcon.exe` для вывода в файл; **точный состав и имена файлов не проверены** — `download.sysinternals.com` недоступен из рабочей среды.

## Проверка подлинности

Сверить SHA256 скачанного файла с ожидаемым значением из таблицы выше — они обязаны совпасть:

```powershell
Get-FileHash -Algorithm SHA256 "E:\tools\security\audit\TCPView\TCPView.zip"
```

```bash
sha256sum "/mnt/tools/security/audit/TCPView/TCPView.zip"
```

Каталог Softonic публикует SHA256 `4fc5ceba3e1b27ad95a24df35d094b454ec5f9478e12a8ca2b1b222705b9683b` для файла `TCPView_V4.19.zip`. Имя файла отличается от официального `TCPView.zip`, поэтому сумма может не сойтись; это ориентир, а не подтверждение.

## Куда положить на флешке

`Tools:\security\audit\TCPView\ — распакованным каталогом.`

То же ограничение лицензии Sysinternals.
