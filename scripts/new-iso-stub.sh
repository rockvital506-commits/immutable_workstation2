#!/usr/bin/env bash
# ============================================================
# new-iso-stub.sh — создать заглушку под ISO и запись в manifest.csv
#
# Запуск:
#   bash scripts/new-iso-stub.sh --category windows --file Win11_24H2_x64_RU.iso \
#        --url https://www.microsoft.com/software-download \
#        --sha256 PENDING --size 0 --version 24H2 --notes "Основной образ для парка"
#
# Результат:
#   ventoy-partition/ISO/<category>/<file>.md   — заглушка
#   manifest.csv                                — строка type=iso, status=planned
#
# Парная версия для Windows: scripts/new-iso-stub.ps1
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VALID_CATEGORIES='windows linux winpe diagnostics security network backup firmware dos _scratch'

CATEGORY='' FILE='' URL='' SHA256='PENDING' SIZE='0' VERSION='' NOTES='' FORCE=0 DRYRUN=0

usage() { sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -c|--category) CATEGORY="${2:?}"; shift 2 ;;
        -f|--file)     FILE="${2:?}";     shift 2 ;;
        -u|--url)      URL="${2:?}";      shift 2 ;;
        --sha256)      SHA256="${2:?}";   shift 2 ;;
        -s|--size)     SIZE="${2:?}";     shift 2 ;;
        -v|--version)  VERSION="${2:?}";  shift 2 ;;
        -N|--notes)    NOTES="${2:?}";    shift 2 ;;
        --force)       FORCE=1; shift ;;
        --dry-run)     DRYRUN=1; shift ;;
        -h|--help)     usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die() { echo "ОШИБКА: $*" >&2; exit 1; }

# Собрать строку CSV из произвольного числа аргументов (экранирование кавычек).
csv_add_row() {
    local out='' first=1 v
    for v in "$@"; do
        case "$v" in
            *,*|*'"'*) v='"'$(printf '%s' "$v" | sed 's/"/""/g')'"' ;;
        esac
        if [ "$first" -eq 1 ]; then out="$v"; first=0; else out="$out,$v"; fi
    done
    printf '%s\n' "$out" >> "$MANIFEST"
}

[ -n "$CATEGORY" ] && [ -n "$FILE" ] || { echo 'Нужны --category и --file' >&2; usage 1; }

echo "$VALID_CATEGORIES" | tr ' ' '\n' | grep -qxF "$CATEGORY" \
    || die "категория «$CATEGORY» вне списка. Допустимые: $VALID_CATEGORIES"
printf '%s' "$FILE" | LC_ALL=C grep -Eq '^[A-Za-z0-9][A-Za-z0-9._-]*\.iso$' \
    || die "имя файла «$FILE» должно заканчиваться на .iso и содержать только латиницу, цифры, . _ -"
if [ "$SHA256" != 'PENDING' ]; then
    printf '%s' "$SHA256" | LC_ALL=C grep -Eq '^[0-9a-fA-F]{64}$' \
        || die "sha256 «$SHA256» не является 64-символьным hex (или укажите PENDING)"
fi
printf '%s' "$SIZE" | LC_ALL=C grep -Eq '^[0-9]+$' || die "size «$SIZE» должно быть целым числом байт"

ISO_DIR="ventoy-partition/ISO/$CATEGORY"
STUB="$ISO_DIR/$FILE.md"

if [ -e "$STUB" ] && [ "$FORCE" -ne 1 ]; then
    die "$STUB уже существует. Повторите с --force для перезаписи."
fi

TODAY="$(date +%Y-%m-%d)"
NAME="${FILE%.iso}"

echo "Заглушка: $STUB"

if [ "$DRYRUN" -eq 1 ]; then
    echo "  [dry-run] создать $STUB"
    echo "  [dry-run] manifest.csv += iso,ISO/$CATEGORY,$NAME,$FILE,$URL,$SHA256,$SIZE,$VERSION,$TODAY,planned"
    echo
    echo 'Ничего не изменено (--dry-run).'
    exit 0
fi

mkdir -p "$ISO_DIR"

# README категории — обязателен, иначе repo-validate вернёт ошибку
if [ ! -f "$ISO_DIR/README.md" ]; then
    cat > "$ISO_DIR/README.md" <<EOF
# $CATEGORY/ — категория образов

> Индекс создаётся автоматически скриптом \`scripts/new-iso-stub.sh\`.
> Опишите, какие образы здесь лежат и в каких ситуациях они применяются.

## Образы

| Файл | Назначение | Версия |
|------|-----------|--------|
| \`$FILE\` | — | $VERSION |

Правила именования и хранения — \`/ventoy-partition/ISO/README.md\`.
EOF
    echo "  создан $ISO_DIR/README.md"
fi

cat > "$STUB" <<EOF
# $FILE

> **Это заглушка.** Образ \`$FILE\` в git не хранится.
> Скачайте его по ссылке ниже и положите в \`/$CATEGORY/\` на разделе VENTOY флешки.

| Поле | Значение |
|------|----------|
| Имя файла | \`$FILE\` |
| Категория | \`ISO/$CATEGORY\` |
| Версия | $VERSION |
| Размер | $SIZE байт |
| SHA256 | \`$SHA256\` |
| Источник | $URL |
| Лицензия | — |
| Добавлено | $TODAY |
| Статус | planned |

## Назначение

$NOTES

## Способ загрузки

- Режим Ventoy: **normal** (если нужен другой — суффикс \`_VTWIMBOOT\` / \`_VTMEMDISK\` к имени файла)
- UEFI: да / нет — **уточнить**
- Legacy BIOS: да / нет — **уточнить**
- Secure Boot: — **уточнить**

## Проверка целостности

Windows (PowerShell):

\`\`\`powershell
Get-FileHash -Algorithm SHA256 "E:\\ISO\\$CATEGORY\\$FILE"
\`\`\`

Linux:

\`\`\`bash
sha256sum "/mnt/ventoy/ISO/$CATEGORY/$FILE"
\`\`\`

Ожидаемое значение: \`$SHA256\`

## Заметки по эксплуатации

<Особенности загрузки на конкретном железе, известные проблемы, порядок применения.>
EOF
echo "  создан $STUB"

MANIFEST='manifest.csv'
if grep -q "^iso,ISO/$CATEGORY,$NAME,$FILE," "$MANIFEST" 2>/dev/null; then
    echo "  manifest.csv: запись для $FILE уже есть, пропускаю"
else
    # Строка manifest.csv: type,category,name,file,url,sha256,size_bytes,version,added,status
    csv_add_row iso "ISO/$CATEGORY" "$NAME" "$FILE" "$URL" "$SHA256" "$SIZE" "$VERSION" "$TODAY" planned
    echo "  manifest.csv: добавлена запись $FILE"
fi

echo
echo 'Готово. Дальше:'
echo "  1. Скачайте образ, положите в $ISO_DIR/ на флешке."
echo "  2. Заполните SHA256 и размер, поменяйте статус на present."
echo "  3. bash scripts/repo-validate.sh && bash scripts/check-flash.sh --verify"
