#!/usr/bin/env bash
# ============================================================
# repo-validate.sh — проверка репозитория на соответствие CONVENTIONS.md
#
# Запуск:  bash scripts/repo-validate.sh
# Коды возврата: 0 — всё в порядке, 1 — найдены ошибки.
#
# Парная версия для Windows: scripts/repo-validate.ps1
# ============================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

ERRORS=0
WARNINGS=0
CHECKS=0

ok()   { CHECKS=$((CHECKS + 1)); printf '  \033[32mOK\033[0m   %s\n' "$1"; }
warn() { WARNINGS=$((WARNINGS + 1)); printf '  \033[33mWARN\033[0m %s\n' "$1"; }
err()  { ERRORS=$((ERRORS + 1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
head2(){ printf '\n\033[1m%s\033[0m\n' "$1"; }

# Вывод строк как ошибок. Цикл через here-string, а не через pipe,
# иначе счётчик $ERRORS остаётся в сабшелле и обнуляется.
err_lines() {
    local line
    while IFS= read -r line; do
        [ -n "$line" ] && err "$1$line"
    done <<< "$2"
}

# Расширения, которые не должны попадать в git (CONVENTIONS.md, раздел 2)
BINARY_EXT='iso|wim|esd|swm|vhd|vhdx|img|vtoy|efi|rom|bin|dat|exe|msi|msu|dll|sys|com|scr|deb|rpm|zip|7z|rar|gz|xz|bz2|zst|tar|cab|pf2|png|jpg|jpeg|gif|bmp|ico|ttf|otf|woff|woff2|mp3|mp4|mkv|avi|wav|pdf|doc|docx|xls|xlsx'

printf '\033[1mrepo-validate\033[0m — %s\n' "$REPO_ROOT"

# ------------------------------------------------------------
head2 '[1/6] Обязательные файлы корня'
# ------------------------------------------------------------
for f in README.md PLAN.md CONVENTIONS.md .gitignore manifest.csv \
         ventoy-partition/ventoy/ventoy.json ventoy-partition/ISO/README.md \
         tools/README.md; do
    if [ -f "$f" ]; then ok "есть $f"; else err "отсутствует обязательный файл $f"; fi
done

for t in UTILITY_README.md SCRIPT_README.md MODULE_README.md; do
    if [ -f "tools/_templates/$t" ]; then ok "есть шаблон tools/_templates/$t"
    else err "отсутствует шаблон tools/_templates/$t"; fi
done

# ------------------------------------------------------------
head2 '[2/6] Бинарные файлы не должны быть в git'
# ------------------------------------------------------------
BIN_FOUND=0
while IFS= read -r f; do
    [ -z "$f" ] && continue
    BIN_FOUND=$((BIN_FOUND + 1))
    err "бинарный файл в рабочем дереве: $f (нужна заглушка $f.md)"
done < <(find . -path ./.git -prune -o -type f -print \
         | sed 's|^\./||' \
         | grep -Ei "\.($BINARY_EXT)$" || true)
[ "$BIN_FOUND" -eq 0 ] && ok "бинарных файлов не найдено (проверено $(find . -path ./.git -prune -o -type f -print | wc -l | tr -d ' ') файлов)"

# ------------------------------------------------------------
head2 '[3/6] Именование: только латиница, цифры, - _ .'
# ------------------------------------------------------------
BAD_NAMES=0
while IFS= read -r p; do
    [ -z "$p" ] && continue
    base="$(basename "$p")"
    if ! printf '%s' "$base" | LC_ALL=C grep -Eq '^[A-Za-z0-9._-]+$'; then
        BAD_NAMES=$((BAD_NAMES + 1))
        err "недопустимое имя: $p"
    fi
done < <(find . -path ./.git -prune -o -mindepth 1 -print | sed 's|^\./||')
[ "$BAD_NAMES" -eq 0 ] && ok "все имена файлов и каталогов соответствуют правилу"

# ------------------------------------------------------------
head2 '[4/6] Заглушки: <имя>.<расширение>.md + README рядом'
# ------------------------------------------------------------
STUBS=0
while IFS= read -r stub; do
    [ -z "$stub" ] && continue
    STUBS=$((STUBS + 1))
    dir="$(dirname "$stub")"
    # 4.1 имя заглушки: минимум две точки, последняя часть .md
    if ! printf '%s' "$stub" | grep -Eq '\.[A-Za-z0-9]+\.md$'; then
        err "неверный формат имени заглушки: $stub (ожидается <имя>.<расширение>.md)"
    fi
    # 4.2 README.md в том же каталоге
    if [ ! -f "$dir/README.md" ]; then
        err "рядом с заглушкой $stub нет README.md"
    fi
    # 4.3 обязательные поля внутри заглушки
    for field in 'SHA256' 'Источник'; do
        if ! grep -q "$field" "$stub"; then
            err "в заглушке $stub нет поля «$field»"
        fi
    done
done < <(find . -path ./.git -prune -o -type f -name '*.md' -print \
         | sed 's|^\./||' | grep -Ei "\.($BINARY_EXT)\.md$" || true)

if [ "$STUBS" -eq 0 ]; then
    ok "заглушек пока нет (заполняется на Этапах 2 и 4)"
else
    ok "заглушек проверено: $STUBS"
fi

# ------------------------------------------------------------
head2 '[5/6] manifest.csv — структура и полнота'
# ------------------------------------------------------------
MANIFEST='manifest.csv'
EXPECTED_HEADER='type,category,name,file,url,sha256,size_bytes,version,added,status'
if [ ! -f "$MANIFEST" ]; then
    err "нет $MANIFEST"
else
    header="$(head -n1 "$MANIFEST" | tr -d '\r')"
    if [ "$header" = "$EXPECTED_HEADER" ]; then
        ok "заголовок manifest.csv корректен"
    else
        err "заголовок manifest.csv не совпадает с эталоном"
        printf '         эталон: %s\n         факт:   %s\n' "$EXPECTED_HEADER" "$header"
    fi

    ROWS=$(($(grep -c . "$MANIFEST" | tr -d ' ') - 1))
    if [ "$ROWS" -lt 0 ]; then ROWS=0; fi

    if [ "$ROWS" -eq 0 ]; then
        ok "записей в manifest.csv пока нет (заполняется на Этапах 2 и 4)"
    else
        # Разбор CSV с учётом кавычек: значения вида "a, b" не должны ломать счёт полей.
        if ! command -v python3 >/dev/null 2>&1; then
            warn "python3 не найден — manifest.csv проверен только по заголовку"
            CSV_PROBLEMS=''
        else
            CSV_PROBLEMS=$(python3 "$SCRIPT_DIR/csv-check.py" "$MANIFEST")
        fi
        if [ -z "$CSV_PROBLEMS" ]; then
            ok "все $ROWS записей manifest.csv корректны"
        else
            err_lines 'manifest.csv — ' "$CSV_PROBLEMS"
        fi
    fi
fi

# ------------------------------------------------------------
head2 '[6/6] ventoy/ventoy.json — синтаксис и структура'
# ------------------------------------------------------------
VJSON='ventoy-partition/ventoy/ventoy.json'
if [ -f "$VJSON" ]; then
    VALIDATOR=''
    command -v python3 >/dev/null 2>&1 && VALIDATOR='python3'
    [ -z "$VALIDATOR" ] && command -v python >/dev/null 2>&1 && VALIDATOR='python'

    if [ -n "$VALIDATOR" ]; then
        OUT=$($VALIDATOR - "$VJSON" <<'PY'
import json, sys
path = sys.argv[1]
try:
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
except Exception as exc:
    print('FAIL_JSON', exc); sys.exit(0)

problems = []
if not isinstance(data, dict):
    problems.append('корень JSON должен быть объектом')
ctrl = data.get('control')
if ctrl is not None:
    if not isinstance(ctrl, list):
        problems.append('control должен быть массивом объектов, а не объектом')
    else:
        for item in ctrl:
            if not isinstance(item, dict) or len(item) != 1:
                problems.append('элемент control должен быть объектом с одним ключом: %r' % (item,))
            else:
                k, v = next(iter(item.items()))
                if not k.startswith('VTOY_'):
                    problems.append('неизвестный ключ control: %s' % k)
                if not isinstance(v, str):
                    problems.append('значение %s должно быть строкой в кавычках' % k)
alias = data.get('menu_alias')
if alias is not None:
    if not isinstance(alias, list):
        problems.append('menu_alias должен быть массивом')
    else:
        for item in alias:
            if not isinstance(item, dict) or 'alias' not in item:
                problems.append('элемент menu_alias без поля alias: %r' % (item,))
for comment in ('//', '/*'):
    if comment in open(path, encoding='utf-8').read():
        problems.append('парсер Ventoy не поддерживает комментарии (%s)' % comment)

if problems:
    print('FAIL_STRUCT'); [print(' -', p) for p in problems]
else:
    keys = [next(iter(i)) for i in data.get('control', []) if isinstance(i, dict) and len(i) == 1]
    print('OK_STRUCT %d control-опций, %d menu_alias' % (len(keys), len(alias or [])))
PY
)
        case "$OUT" in
            OK_STRUCT*)  ok "ventoy.json валиден: ${OUT#OK_STRUCT }" ;;
            FAIL_JSON*)  err "ventoy.json — невалидный JSON: ${OUT#FAIL_JSON }" ;;
            FAIL_STRUCT) err "ventoy.json — структура не соответствует требованиям Ventoy:"
                         printf '%s\n' "$OUT" | tail -n +2 | sed 's/^/         /' ;;
        esac
    else
        warn "python3 не найден — синтаксис ventoy.json не проверен"
    fi
fi

# ------------------------------------------------------------
printf '\n\033[1mИтог:\033[0m проверок — %d, предупреждений — %d, ошибок — %d\n' \
       "$CHECKS" "$WARNINGS" "$ERRORS"
if [ "$ERRORS" -gt 0 ]; then
    printf '\033[31mРепозиторий не соответствует CONVENTIONS.md — коммитить нельзя.\033[0m\n'
    exit 1
fi
printf '\033[32mВсе проверки пройдены.\033[0m\n'
exit 0
