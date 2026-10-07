# scripts/ — автоматизация

Каждая задача реализована **двумя** файлами: `.ps1` для Windows и `.sh` для Linux.
Поведение и аргументы совпадают — правило дуальности из `/CONVENTIONS.md`, раздел 5.

| Задача | Linux | Windows | Что делает |
|--------|-------|---------|-----------|
| Валидация репозитория | `repo-validate.sh` | `repo-validate.ps1` | Проверяет соответствие `CONVENTIONS.md`: обязательные файлы, отсутствие бинарников, именование, формат заглушек, `manifest.csv`, `ventoy.json` |
| Каркас утилиты | `new-tool.sh` | `new-tool.ps1` | Создаёт `tools/<группа>/<подкатегория>/<Утилита>/` с `README.md` из шаблона, индексы группы и подкатегории, строку в `manifest.csv` |
| Заглушка под ISO | `new-iso-stub.sh` | `new-iso-stub.ps1` | Создаёт `ventoy-partition/ISO/<категория>/<файл>.iso.md`, `README.md` категории, строку в `manifest.csv` |
| Сверка с флешкой | `check-flash.sh` | `check-flash.ps1` | Сравнивает реальное содержимое флешки с репозиторием: структура, `ventoy.json`, ISO против заглушек, SHA256, группы TOOLS, свободное место |
| Разбор manifest.csv | `csv-check.py` | (используется `.sh`) | Проверка колонок `manifest.csv` с корректным учётом кавычек |

## Порядок применения

```bash
# 1. Добавить утилиту или образ
bash scripts/new-tool.sh     --group diagnostics --subgroup disk --name Victoria
bash scripts/new-iso-stub.sh --category windows  --file Win11_24H2_x64_RU.iso --url <URL>

# 2. Заполнить README и заглушки вручную

# 3. Проверить репозиторий — без ошибок коммитить нельзя
bash scripts/repo-validate.sh

# 4. После записи на флешку — сверить
bash scripts/check-flash.sh --ventoy /mnt/ventoy --tools /mnt/tools --verify
```

```powershell
# то же в Windows
powershell -ExecutionPolicy Bypass -File scripts\new-tool.ps1     -Group diagnostics -Subgroup disk -Name Victoria
powershell -ExecutionPolicy Bypass -File scripts\new-iso-stub.ps1 -Category windows  -File Win11_24H2_x64_RU.iso -Url <URL>
powershell -ExecutionPolicy Bypass -File scripts\repo-validate.ps1
powershell -ExecutionPolicy Bypass -File scripts\check-flash.ps1 -Ventoy E: -Tools F: -Verify
```

## Соглашения по скриптам

- `--dry-run` / `-WhatIf` — показать действия, ничего не меняя.
- `--force` / `-Force` — разрешить перезапись существующего.
- Код возврата: `0` — успех, `1` — найдены ошибки/расхождения, `2` — флешка не найдена.
- Разрушающих операций (форматирование, запись на диск) в этих скриптах **нет**:
  они только читают и создают текстовые файлы.

## Зависимости

| Скрипт | Требуется |
|--------|-----------|
| `*.sh` | bash 4+, `awk`, `find`, `grep`, `sed`, `comm`, `df`; для проверки `ventoy.json` и `manifest.csv` — `python3` |
| `check-flash.sh --verify` | `sha256sum` (coreutils) |
| `*.ps1` | Windows PowerShell 5.1+ или PowerShell 7+ |
| `csv-check.py` | Python 3.8+ (только стандартная библиотека) |

Если `python3` отсутствует, `repo-validate.sh` проверит `manifest.csv` только по
заголовку и `ventoy.json` не проверит вовсе — выдаст предупреждение, а не ошибку.
