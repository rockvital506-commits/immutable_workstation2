#!/usr/bin/env bash
# ============================================================
# backup-chrome.sh — резервная копия профиля Google Chrome (Linux)
#
# Парная версия backup-chrome.ps1. Применяется, когда данные снимаются из
# Live-среды Linux Mint, а профиль лежит на примонтированном Windows-разделе.
#
# Запуск:
#   bash backup-chrome.sh --source "/mnt/win/Users/NAME/AppData/Local/Google/Chrome/User Data" \
#        --destination /mnt/tools/backup/profiles
#   bash backup-chrome.sh --source <путь> --destination <путь> --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 3 — профиль не найден.
# ============================================================
set -uo pipefail

SOURCE='' DEST='' NAME='chrome' DRYRUN=0

usage() { sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -s|--source)      SOURCE="${2:?}"; shift 2 ;;
        -d|--destination) DEST="${2:?}";   shift 2 ;;
        -n|--name)        NAME="${2:?}";   shift 2 ;;
        --dry-run)        DRYRUN=1; shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

[ -n "$SOURCE" ] && [ -n "$DEST" ] || { echo 'Нужны --source и --destination' >&2; usage 1; }
[ -d "$SOURCE" ] || { echo "ОШИБКА: профиль не найден: $SOURCE" >&2; exit 3; }

STAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
TARGET="$DEST/${NAME}_${STAMP}"

echo "Источник:   $SOURCE"
echo "Назначение: $TARGET"

if [ "$DRYRUN" -eq 1 ]; then
    echo "  [dry-run] cp -a '$SOURCE/.' '$TARGET/'"
    echo "  [dry-run] манифест SHA256 -> $TARGET/_manifest.sha256.csv"
    echo 'Ничего не изменено (--dry-run).'
    exit 0
fi

mkdir -p "$TARGET" || exit 1
cp -a "$SOURCE/." "$TARGET/" || exit 1

MANIFEST="$TARGET/_manifest.sha256.csv"
{
    echo 'path,sha256,size_bytes,captured_at'
    find "$TARGET" -type f ! -name '_manifest.sha256.csv' ! -name '_RESTORE_NOTES.md' -print0 |
    while IFS= read -r -d '' f; do
        rel="${f#"$TARGET"/}"
        h="$(sha256sum "$f" | awk '{print $1}')"
        sz="$(stat -c%s "$f")"
        echo "$rel,$h,$sz,$STAMP"
    done
} > "$MANIFEST"

COUNT=$(find "$TARGET" -type f | wc -l | tr -d ' ')
echo "Скопировано файлов: $COUNT"
echo "Манифест: $MANIFEST"

cat > "$TARGET/_RESTORE_NOTES.md" <<EOF
# Восстановление профиля Chrome

Скопировано: $STAMP
Источник: \`$SOURCE\`

## Порядок восстановления (Windows)

1. Полностью закрыть Chrome.
2. Установить Chrome той же или более новой версии.
3. Заменить \`%LOCALAPPDATA%\\Google\\Chrome\\User Data\` содержимым этой копии.

## Ограничение по паролям

\`Default/Login Data\` зашифрован DPAPI в контексте исходной учётной записи.
На другой машине пароли из копии не расшифруются. Перенос паролей — только
штатным экспортом: \`chrome://settings/passwords\` -> «Экспорт паролей».
EOF

echo "Копия: $TARGET"
exit 0
