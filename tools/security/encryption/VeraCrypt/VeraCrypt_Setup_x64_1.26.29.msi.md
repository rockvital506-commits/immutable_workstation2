# VeraCrypt_Setup_x64_1.26.29.msi — заглушка

Бинарный файл в git не хранится (см. `/CONVENTIONS.md`, раздел 2).

| Поле | Значение |
|------|----------|
| Имя файла | `VeraCrypt_Setup_x64_1.26.29.msi` |
| Назначение | Шифрование контейнеров, разделов, флешек и системного диска |
| Версия | 1.26.29, релиз 2026-06-12 — **сверена с первоисточником** через API GitHub |
| Источник | https://github.com/veracrypt/VeraCrypt/releases/download/VeraCrypt_1.26.29/VeraCrypt_Setup_x64_1.26.29.msi |
| SHA256 | `5ba6426983123cfb92bc1f09bd888fdbc0f53f300d0d9c5da52ce3aee8d474f0` |
| Размер | **52 789 248 байт** |
| Лицензия | TrueCrypt License 3.0 + Apache 2.0; коммерческое использование разрешено |
| Статус | `planned` |

## Как получить

Инсталлятор x64 с официального релиза GitHub. Рядом лежит подпись `VeraCrypt_Setup_x64_1.26.29.msi.sig` (566 байт) — скачать и проверить её тоже. Поддерживается портативный режим `/portable` без установки.

## Проверка подлинности

Сверить SHA256 скачанного файла с ожидаемым значением из таблицы выше — они обязаны совпасть:

```powershell
Get-FileHash -Algorithm SHA256 "E:\tools\security\encryption\VeraCrypt\VeraCrypt_Setup_x64_1.26.29.msi"
```

```bash
sha256sum "/mnt/tools/security/encryption/VeraCrypt/VeraCrypt_Setup_x64_1.26.29.msi"
```

Размер должен быть ровно 52 789 248 байт — это значение получено из API GitHub и подтверждает, что скачан именно этот ассет. SHA256 в рабочей среде не вычислить: `release-assets.githubusercontent.com` вне белого списка.

## Куда положить на флешке

`Tools:\security\encryption\VeraCrypt\`

Взять версию не ниже 1.26.29: в ней закрыт `CVE-2026-54073` — быстрое форматирование скрытого тома раскрывало его наличие (регрессия с 1.26.6).
