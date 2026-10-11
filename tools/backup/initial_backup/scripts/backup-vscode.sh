#!/usr/bin/env bash
# ============================================================
# backup-vscode.sh — резервная копия настроек и расширений VS Code (Linux)
#
# Парная версия backup-vscode.ps1. Применяется, когда данные снимаются из
# Live-среды Linux Mint: и при установленном в ней VS Code, и при копировании
# профиля с примонтированного Windows-раздела.
#
# Запуск:
#   bash backup-vscode.sh --user-dir "$HOME/.config/Code/User" \
#        --extensions-dir "$HOME/.vscode/extensions" \
#        --destination /mnt/tools/backup/profiles
#   bash backup-vscode.sh -u <путь> -e <путь> -d <путь> --dry-run
#
# Значения по умолчанию — пути VS Code в Linux. Для профиля с
# Windows-раздела передать --user-dir и --extensions-dir явно:
#   --user-dir "/mnt/win/Users/NAME/AppData/Roaming/Code/User"
#   --extensions-dir "/mnt/win/Users/NAME/.vscode/extensions"
#
# Коды возврата: 0 — успех, 1 — ошибка, 3 — ни один каталог не найден.
# ============================================================
set -euo pipefail

# Лог в файл (CONVENTIONS.md, раздел 5). tee в process substitution сохраняет
# текущую оболочку, поэтому счётчики и переменные не теряются в сабшелле.
# Закрытие дескрипторов и wait в trap гарантируют, что файл дописан до выхода.
LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
exec > >(tee -a "$LOG_FILE") 2>&1
trap 'exec >&- 2>&-; wait' EXIT
echo "=== ${0##*/} $(date '+%Y-%m-%d %H:%M:%S') ==="


USER_DIR="${USER_DIR:-$HOME/.config/Code/User}"
EXT_DIR="${EXT_DIR:-$HOME/.vscode/extensions}"
DEST='' NAME='vscode' DRYRUN=0

usage() { sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -u|--user-dir)       USER_DIR="${2:?}"; shift 2 ;;
        -e|--extensions-dir) EXT_DIR="${2:?}";  shift 2 ;;
        -d|--destination)    DEST="${2:?}";     shift 2 ;;
        -n|--name)           NAME="${2:?}";     shift 2 ;;
        --dry-run)           DRYRUN=1; shift ;;
        -h|--help)           usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

[ -n "$DEST" ] || { echo 'Нужен --destination' >&2; usage 1; }

HAS_USER=0; HAS_EXT=0
[ -d "$USER_DIR" ] && HAS_USER=1
[ -d "$EXT_DIR" ]  && HAS_EXT=1

if [ "$HAS_USER" -eq 0 ] && [ "$HAS_EXT" -eq 0 ]; then
    echo "ОШИБКА: не найдены ни $USER_DIR, ни $EXT_DIR — VS Code не установлен?" >&2
    exit 3
fi

STAMP="$(date '+%Y-%m-%d_%H-%M-%S')"
TARGET="$DEST/${NAME}_${STAMP}"

echo "Настройки:   $USER_DIR (найден: $HAS_USER)"
echo "Расширения:  $EXT_DIR (найден: $HAS_EXT)"
echo "Назначение:  $TARGET"

if [ "$DRYRUN" -eq 1 ]; then
    [ "$HAS_USER" -eq 1 ] && echo "  [dry-run] cp -a '$USER_DIR/.' '$TARGET/User/'"
    [ "$HAS_EXT" -eq 1 ]  && echo "  [dry-run] cp -a '$EXT_DIR/.' '$TARGET/extensions/'"
    echo "  [dry-run] список расширений -> $TARGET/extensions-list.txt"
    echo "  [dry-run] манифест SHA256 -> $TARGET/_manifest.sha256.csv"
    echo 'Ничего не изменено (--dry-run).'
    exit 0
fi

mkdir -p "$TARGET" || exit 1

if [ "$HAS_USER" -eq 1 ]; then
    mkdir -p "$TARGET/User" || exit 1
    cp -a "$USER_DIR/." "$TARGET/User/" || exit 1
    echo "Скопированы настройки: $USER_DIR"
fi
if [ "$HAS_EXT" -eq 1 ]; then
    mkdir -p "$TARGET/extensions" || exit 1
    cp -a "$EXT_DIR/." "$TARGET/extensions/" || exit 1
    echo "Скопированы расширения: $EXT_DIR"
fi

LIST="$TARGET/extensions-list.txt"
if command -v code >/dev/null 2>&1; then
    code --list-extensions --show-versions > "$LIST" || true
    echo 'Список расширений получен от code --list-extensions'
elif [ "$HAS_EXT" -eq 1 ]; then
    find "$EXT_DIR" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort > "$LIST"
    echo 'CLI code недоступен: список собран по именам каталогов'
fi

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

COUNT=$(find "$TARGET" -type f ! -name '_RESTORE_NOTES.md' | wc -l | tr -d ' ')
# du -sb даёт точный размер содержимого; du -sm округляет до мегабайта
# в большую сторону и на мелкой копии показывает 1 МБ вместо 6 КБ.
SIZE=$(du -sb "$TARGET" | awk '{print $1}')
SIZE_KB=$(awk -v b="$SIZE" 'BEGIN {printf "%.1f", b/1024}')
echo "Файлов в копии: $COUNT, объём: $SIZE байт ($SIZE_KB КБ)"
echo "Манифест: $MANIFEST"

cat > "$TARGET/_RESTORE_NOTES.md" <<EOF
# Восстановление настроек VS Code

Скопировано: $STAMP
Настройки: \`$USER_DIR\`
Расширения: \`$EXT_DIR\`

## Порядок восстановления (Windows)

1. Полностью закрыть VS Code.
2. Установить VS Code.
3. Заменить \`%APPDATA%\\Code\\User\` содержимым каталога \`User\` этой копии.
4. Расширения ставить списком, а не копированием каталога:
   \`Get-Content extensions-list.txt | ForEach-Object { code --install-extension \$_ }\`

## Порядок восстановления (Linux)

1. Полностью закрыть VS Code.
2. Заменить \`~/.config/Code/User\` содержимым каталога \`User\` этой копии.
3. Расширения тем же списком:
   \`xargs -a extensions-list.txt -I{} code --install-extension {}\`

## Ограничение

Копировать каталог расширений целиком не равно reinstall: часть расширений
хранит состояние вне него. Список \`extensions-list.txt\` — основной способ
переноса, каталог \`extensions\` нужен как запасной.
EOF

echo "Копия: $TARGET"
exit 0
