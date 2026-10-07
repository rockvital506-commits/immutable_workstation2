#!/usr/bin/env bash
# ============================================================
# new-tool.sh — создать каркас утилиты/скрипта/модуля в tools/
#
# Запуск:
#   bash scripts/new-tool.sh --group diagnostics --subgroup disk --name Victoria
#   bash scripts/new-tool.sh -g rescue -s password -n NtpwEdit -k module --force
#   bash scripts/new-tool.sh -g scripts -s windows -n Cleanup --dry-run
#
# Что делает:
#   1. Создаёт tools/<group>/<subgroup>/<Name>/
#   2. Кладёт README.md из шаблона (utility|script|module)
#   3. Создаёт README.md в группе и подкатегории, если их ещё нет
#   4. Добавляет строку в manifest.csv (status=planned)
#
# Парная версия для Windows: scripts/new-tool.ps1
# ============================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VALID_GROUPS='os rescue diagnostics security network drivers backup deployment scripts docs-offline _scratch'
VALID_KINDS='utility script module'

GROUP='' SUBGROUP='' NAME='' KIND='utility' FORCE=0 DRYRUN=0

usage() {
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-0}"
}

while [ $# -gt 0 ]; do
    case "$1" in
        -g|--group)     GROUP="${2:?}"; shift 2 ;;
        -s|--subgroup)  SUBGROUP="${2:?}"; shift 2 ;;
        -n|--name)      NAME="${2:?}"; shift 2 ;;
        -k|--kind)      KIND="${2:?}"; shift 2 ;;
        -f|--force)     FORCE=1; shift ;;
        --dry-run)      DRYRUN=1; shift ;;
        -h|--help)      usage 0 ;;
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

[ -n "$GROUP" ] && [ -n "$SUBGROUP" ] && [ -n "$NAME" ] || { echo 'Нужны --group, --subgroup и --name' >&2; usage 1; }

# --- валидация ---
echo "$VALID_GROUPS" | tr ' ' '\n' | grep -qxF "$GROUP" \
    || die "группа «$GROUP» вне списка. Допустимые: $VALID_GROUPS"
echo "$VALID_KINDS" | tr ' ' '\n' | grep -qxF "$KIND" \
    || die "kind «$KIND» вне списка. Допустимые: $VALID_KINDS"
printf '%s' "$SUBGROUP" | LC_ALL=C grep -Eq '^[a-z0-9][a-z0-9_-]*$' \
    || die "subgroup «$SUBGROUP» должен быть в нижнем регистре: a-z 0-9 _ -"
printf '%s' "$NAME" | LC_ALL=C grep -Eq '^[A-Za-z0-9][A-Za-z0-9._-]*$' \
    || die "name «$NAME» содержит недопустимые символы (латиница, цифры, . _ -)"

TARGET="tools/$GROUP/$SUBGROUP/$NAME"

case "$KIND" in
    utility) TEMPLATE='tools/_templates/UTILITY_README.md' ;;
    script)  TEMPLATE='tools/_templates/SCRIPT_README.md'  ;;
    module)  TEMPLATE='tools/_templates/MODULE_README.md'  ;;
esac
[ -f "$TEMPLATE" ] || die "нет шаблона $TEMPLATE"

if [ -e "$TARGET" ] && [ "$FORCE" -ne 1 ]; then
    die "$TARGET уже существует. Повторите с --force, чтобы перезаписать README.md"
fi

TODAY="$(date +%Y-%m-%d)"
CATEGORY="$GROUP/$SUBGROUP"

run() {
    if [ "$DRYRUN" -eq 1 ]; then echo "  [dry-run] $*"; else eval "$@"; fi
}

echo "Создание: $TARGET (kind=$KIND)"

run "mkdir -p '$TARGET'"

# --- README.md утилиты из шаблона ---
if [ -e "$TARGET/README.md" ] && [ "$FORCE" -ne 1 ] && [ "$DRYRUN" -ne 1 ]; then
    echo "  пропускаю $TARGET/README.md (уже есть, нужен --force)"
else
    if [ "$DRYRUN" -eq 1 ]; then
        echo "  [dry-run] README.md из $TEMPLATE"
    else
        sed -e "s|<Название утилиты>|$NAME|g" \
            -e "s|<Название скрипта или набора скриптов>|$NAME|g" \
            -e "s|<Название модуля>|$NAME|g" \
            -e "s|<ГГГГ-ММ-ДД>|$TODAY|g" \
            "$TEMPLATE" > "$TARGET/README.md"
        echo "  создан $TARGET/README.md"
    fi
fi

# --- README.md группы и подкатегории ---
ensure_index() {
    local dir="$1" body="$2"
    if [ ! -f "$dir/README.md" ]; then
        if [ "$DRYRUN" -eq 1 ]; then
            echo "  [dry-run] создать $dir/README.md"
        else
            printf '%s\n' "$body" > "$dir/README.md"
            echo "  создан $dir/README.md"
        fi
    fi
}

GROUP_BODY="# ${GROUP}/ — группа «${GROUP}»

> Индекс создаётся автоматически скриптом \`scripts/new-tool.sh\`.
> Заполните описание группы: что здесь лежит и когда применяется.

## Подкатегории

| Подкатегория | Содержимое |
|--------------|-----------|
| \`${SUBGROUP}/\` | — |

## Правила

- Одна утилита = один каталог с \`README.md\`.
- Бинарники хранятся заглушками \`<имя>.<расширение>.md\` (см. \`/CONVENTIONS.md\`).
- Каждая утилита регистрируется в \`/manifest.csv\`.
"

SUB_BODY="# ${SUBGROUP}/ — подкатегория группы «${GROUP}»

> Индекс создаётся автоматически скриптом \`scripts/new-tool.sh\`.
> Опишите, какие задачи закрывают утилиты этой подкатегории.

## Состав

| Каталог | Назначение |
|---------|-----------|
| \`${NAME}/\` | — |
"

run "mkdir -p 'tools/$GROUP' 'tools/$GROUP/$SUBGROUP'"
ensure_index "tools/$GROUP" "$GROUP_BODY"
ensure_index "tools/$GROUP/$SUBGROUP" "$SUB_BODY"

# --- строка в manifest.csv ---
MANIFEST='manifest.csv'
if grep -q "^tool,$CATEGORY,$NAME," "$MANIFEST" 2>/dev/null; then
    echo "  manifest.csv: запись для $NAME уже есть, пропускаю"
else
    if [ "$DRYRUN" -eq 1 ]; then
        echo "  [dry-run] manifest.csv += tool,$CATEGORY,$NAME,,,,PENDING,$TODAY,planned"
    else
        # Строка manifest.csv собирается из массива ровно 10 полей
        # в порядке заголовка: type,category,name,file,url,sha256,size_bytes,version,added,status
        csv_add_row tool "$CATEGORY" "$NAME" '' '' 'PENDING' '0' 'PENDING' "$TODAY" 'planned'
        echo "  manifest.csv: добавлена запись $NAME"
    fi
fi

if [ "$DRYRUN" -eq 1 ]; then
    echo
    echo 'Ничего не изменено (--dry-run).'
else
    echo
    echo 'Готово. Дальше:'
    echo "  1. Заполните $TARGET/README.md (уберите все <...>)."
    echo "  2. Положите бинарник на флешку и создайте заглушку <имя>.<расширение>.md."
    echo "  3. bash scripts/repo-validate.sh — проверить и закоммитить."
fi
