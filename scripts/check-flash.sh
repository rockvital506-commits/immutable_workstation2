#!/usr/bin/env bash
# ============================================================
# check-flash.sh — сверка содержимого флешки с репозиторием
#
# Запуск:
#   bash scripts/check-flash.sh --ventoy /mnt/ventoy --tools /mnt/tools
#   bash scripts/check-flash.sh --ventoy /mnt/ventoy --verify
#   bash scripts/check-flash.sh --ventoy /mnt/ventoy --json
#
# Проверяет:
#   * раздел VENTOY смонтирован, есть /ventoy/ventoy.json и /ISO
#   * ventoy.json на флешке совпадает с версией из репозитория
#   * каждому ISO на флешке соответствует заглушка в репозитории и наоборот
#   * SHA256 образов и бинарников совпадает с manifest.csv (--verify,
#     все типы сущностей: образы на разделе VENTOY, утилиты на TOOLS)
#   * набор групп на разделе TOOLS совпадает с tools/ в репозитории
#   * свободное место на разделах
#
# Коды возврата: 0 — расхождений нет, 1 — есть расхождения, 2 — флешка не найдена.
#
# Парная версия для Windows: scripts/check-flash.ps1
# ============================================================
set -euo pipefail

# Лог в файл (CONVENTIONS.md, раздел 5). Скрипт перезапускает сам себя через
# tee, а не через process substitution: `wait` в trap виснет, если `set -e`
# обрывает скрипт внутри функции, а tee ещё жив. Код возврата возвращается
# через PIPESTATUS, поэтому для вызывающего поведение не меняется.
LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
if [ -z "${_LOGGED_SELF:-}" ]; then
    _LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi
echo "=== ${0##*/} $(date '+%Y-%m-%d %H:%M:%S') ==="


REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENTOY_MOUNT='' TOOLS_MOUNT='' VERIFY=0 JSON=0

usage() { sed -n '2,21p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -V|--ventoy)      VENTOY_MOUNT="${2:?}"; shift 2 ;;
        -T|--tools)       TOOLS_MOUNT="${2:?}";  shift 2 ;;
        --verify)         VERIFY=1; shift ;;
        --json)           JSON=1;   shift ;;
        -h|--help)        usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

[ -n "$VENTOY_MOUNT" ] || { echo 'Нужен --ventoy <точка монтирования раздела VENTOY>' >&2; usage 1; }

ERRORS=0 WARNINGS=0 OKS=0
ok()   { OKS=$((OKS + 1));       [ "$JSON" -eq 0 ] && printf '  \033[32mOK\033[0m   %s\n' "$1"; }
warn() { WARNINGS=$((WARNINGS + 1)); [ "$JSON" -eq 0 ] && printf '  \033[33mWARN\033[0m %s\n' "$1"; }
err()  { ERRORS=$((ERRORS + 1));  [ "$JSON" -eq 0 ] && printf '  \033[31mFAIL\033[0m %s\n' "$1"; }
head2(){ [ "$JSON" -eq 0 ] && printf '\n\033[1m%s\033[0m\n' "$1"; }

printf '\033[1mcheck-flash\033[0m — репозиторий %s\n' "$REPO_ROOT"
printf '  раздел VENTOY: %s\n  раздел TOOLS:  %s\n' "$VENTOY_MOUNT" "${TOOLS_MOUNT:-<не задан>}"

# ------------------------------------------------------------
head2 '[1/5] Раздел VENTOY: базовая структура'
# ------------------------------------------------------------
if [ ! -d "$VENTOY_MOUNT" ]; then
    printf '\033[31mТочка монтирования %s не существует — флешка не подключена?\033[0m\n' "$VENTOY_MOUNT"
    exit 2
fi

if [ -d "$VENTOY_MOUNT/ventoy" ]; then
    ok 'каталог /ventoy присутствует'
else
    err 'нет каталога /ventoy — Ventoy не установлен или смонтирован не тот раздел'
fi

if [ -d "$VENTOY_MOUNT/ISO" ]; then
    ok 'каталог /ISO присутствует'
else
    err 'нет каталога /ISO (VTOY_DEFAULT_SEARCH_ROOT указывает на него)'
fi

if [ -d "$VENTOY_MOUNT/backup" ]; then
    ok 'каталог /backup присутствует'
else
    warn 'нет каталога /backup — бэкапы MBR/GPT некуда складывать'
fi

# ------------------------------------------------------------
head2 '[2/5] ventoy.json: флешка против репозитория'
# ------------------------------------------------------------
FLASH_JSON="$VENTOY_MOUNT/ventoy/ventoy.json"
REPO_JSON='ventoy-partition/ventoy/ventoy.json'
if [ -f "$FLASH_JSON" ]; then
    if [ -f "$REPO_JSON" ] && cmp -s "$FLASH_JSON" "$REPO_JSON"; then
        ok 'ventoy.json совпадает с версией из репозитория'
    else
        err 'ventoy.json на флешке отличается от репозитория — обновите один из них'
    fi
    if command -v python3 >/dev/null 2>&1; then
        if python3 -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" "$FLASH_JSON" 2>/dev/null; then
            ok 'ventoy.json на флешке — валидный JSON'
        else
            err 'ventoy.json на флешке невалиден — Ventoy проигнорирует весь конфиг'
        fi
    fi
else
    err "нет $FLASH_JSON"
fi

# ------------------------------------------------------------
head2 '[3/5] Образы ISO: заглушки против фактических файлов'
# ------------------------------------------------------------
# Разбор manifest.csv с учётом кавычек
parse_manifest() {
    awk 'NR>1 {
        line=$0; out=""; nf=0; n=split("", F)
        while (length(line)) {
            if (substr(line,1,1) == "\"") {
                line=substr(line,2); val=""
                while (1) {
                    p=index(line, "\"")
                    if (p==0) { val=val line; line=""; break }
                    if (substr(line,p+1,1) == "\"") { val=val substr(line,1,p); line=substr(line,p+2) }
                    else { val=val substr(line,1,p-1); line=substr(line,p+2); break }
                }
            } else {
                p=index(line, ",")
                if (p==0) { val=line; line="" } else { val=substr(line,1,p-1); line=substr(line,p+1) }
            }
            F[++nf]=val
            if (line=="") break
            if (substr(line,1,1)==",") line=substr(line,2)
        }
        if (F[1]=="" ) next
        print F[1] "|" F[2] "|" F[3] "|" F[4] "|" F[6] "|" F[7] "|" F[10]
    }' manifest.csv
}
MANIFEST_PARSED="$(parse_manifest)"

# Что должно быть на флешке (по заглушкам в репозитории)
REPO_STUBS="$(find ventoy-partition/ISO -type f -name '*.iso.md' 2>/dev/null | sed 's|^ventoy-partition/||; s|\.md$||' | sort)"
# Что есть на флешке
if [ -d "$VENTOY_MOUNT/ISO" ]; then
    FLASH_ISOS="$(find "$VENTOY_MOUNT/ISO" -type f -iname '*.iso' 2>/dev/null \
                  | sed "s|^$VENTOY_MOUNT/||" | sort)"
else
    FLASH_ISOS=''
fi

N_STUBS=$(printf '%s\n' "$REPO_STUBS"  | grep -c . || true)
N_ISOS=$(printf '%s\n' "$FLASH_ISOS"   | grep -c . || true)

if [ "$N_STUBS" -eq 0 ] && [ "$N_ISOS" -eq 0 ]; then
    ok 'образов нет ни на флешке, ни в репозитории (Этап 2 ещё не выполнялся)'
else
    MISSING_ON_FLASH="$(comm -23 <(printf '%s\n' "$REPO_STUBS"  | grep . || true) \
                                 <(printf '%s\n' "$FLASH_ISOS" | grep . || true) || true)"
    ORPHAN_ON_FLASH="$(comm -13 <(printf '%s\n' "$REPO_STUBS"  | grep . || true) \
                                <(printf '%s\n' "$FLASH_ISOS" | grep . || true) || true)"
    if [ -n "$MISSING_ON_FLASH" ]; then
        while IFS= read -r f; do
            [ -n "$f" ] && warn "в репозитории заявлен, на флешке отсутствует: $f"
        done <<< "$MISSING_ON_FLASH"
        WARNINGS=$((WARNINGS + $(printf '%s\n' "$MISSING_ON_FLASH" | grep -c . || true)))
    fi
    if [ -n "$ORPHAN_ON_FLASH" ]; then
        while IFS= read -r f; do
            [ -n "$f" ] && err "на флешке есть, в репозитории не описан: $f"
        done <<< "$ORPHAN_ON_FLASH"
        ERRORS=$((ERRORS + $(printf '%s\n' "$ORPHAN_ON_FLASH" | grep -c . || true)))
    fi
    [ -z "$MISSING_ON_FLASH" ] && [ -z "$ORPHAN_ON_FLASH" ] \
        && ok "образы на флешке и заглушки совпадают ($N_ISOS шт.)"
fi

# ------------------------------------------------------------
head2 '[4/5] Контрольные суммы (--verify)'
# ------------------------------------------------------------
# Сверяются ВСЕ типы сущностей, а не только ISO: в манифесте 30 строк с
# заполненным полем file, из них 23 — утилиты. Образы лежат на разделе VENTOY,
# утилиты — на разделе TOOLS, поэтому база пути зависит от типа.
if [ "$VERIFY" -eq 0 ]; then
    ok 'проверка SHA256 пропущена (запустите с --verify)'
else
    CHECKED=0 NOSHA=0 MISSF=0 NOTOOLS=0
    while IFS='|' read -r mtype mcat mname mfile msha msize mstatus; do
        [ -n "$mfile" ] || continue

        # Куда положить файл на флешке: образы — на VENTOY, остальное — на TOOLS
        case "$mtype" in
            iso) base="$VENTOY_MOUNT" ;;
            *)   base="$TOOLS_MOUNT"  ;;
        esac
        if [ -z "$base" ]; then
            [ "$mtype" = 'iso' ] || NOTOOLS=$((NOTOOLS + 1))
            continue
        fi

        target="$base/$mcat/$mfile"
        if [ ! -f "$target" ]; then
            warn "manifest: $mtype $mcat/$mfile отсутствует на флешке"
            MISSF=$((MISSF + 1))
            continue
        fi
        if [ "$msha" = 'PENDING' ] || [ -z "$msha" ]; then
            warn "manifest: для $mcat/$mfile нет SHA256 — сверить нечем"
            NOSHA=$((NOSHA + 1))
            continue
        fi
        actual="$(sha256sum "$target" 2>/dev/null | awk '{print $1}')"
        CHECKED=$((CHECKED + 1))
        if [ "$(printf '%s' "$actual" | tr 'A-F' 'a-f')" = "$(printf '%s' "$msha" | tr 'A-F' 'a-f')" ]; then
            ok "SHA256 совпадает: $mtype $mcat/$mfile"
        else
            err "SHA256 НЕ совпадает: $mcat/$mfile (ожидалось ${msha:0:12}..., факт ${actual:0:12}...)"
        fi
    done <<EOF
$MANIFEST_PARSED
EOF

    printf '  Итог сверки сумм: сверено %s, без суммы %s, отсутствует %s' \
           "$CHECKED" "$NOSHA" "$MISSF"
    [ "$NOTOOLS" -gt 0 ] && printf ', не проверено %s (не задан --tools)' "$NOTOOLS"
    printf '\n'
    if [ "$CHECKED" -eq 0 ]; then
        warn 'ни одна контрольная сумма не была сверена с реальным файлом'
    else
        ok "сверено с реальными файлами: $CHECKED"
    fi
fi

# ------------------------------------------------------------
head2 '[5/5] Раздел TOOLS и свободное место'
# ------------------------------------------------------------
if [ -z "$TOOLS_MOUNT" ]; then
    warn 'раздел TOOLS не проверялся (не задан --tools)'
elif [ ! -d "$TOOLS_MOUNT" ]; then
    err "точка монтирования $TOOLS_MOUNT не существует"
else
    REPO_GROUPS="$(find tools -mindepth 1 -maxdepth 1 -type d ! -name '_templates' -printf '%f\n' 2>/dev/null | sort)"
    FLASH_GROUPS="$(find "$TOOLS_MOUNT" -mindepth 1 -maxdepth 1 -type d ! -name 'System Volume Information' -printf '%f\n' 2>/dev/null | sort)"

    MISS_G="$(comm -23 <(printf '%s\n' "$REPO_GROUPS"  | grep . || true) \
                       <(printf '%s\n' "$FLASH_GROUPS" | grep . || true) || true)"
    EXTRA_G="$(comm -13 <(printf '%s\n' "$REPO_GROUPS"  | grep . || true) \
                        <(printf '%s\n' "$FLASH_GROUPS" | grep . || true) || true)"

    if [ -n "$MISS_G" ]; then
        while IFS= read -r g; do [ -n "$g" ] && warn "группа из репозитория отсутствует на флешке: $g"; done <<< "$MISS_G"
        WARNINGS=$((WARNINGS + $(printf '%s\n' "$MISS_G" | grep -c . || true)))
    fi
    if [ -n "$EXTRA_G" ]; then
        while IFS= read -r g; do [ -n "$g" ] && err "группа на флешке не описана в репозитории: $g"; done <<< "$EXTRA_G"
        ERRORS=$((ERRORS + $(printf '%s\n' "$EXTRA_G" | grep -c . || true)))
    fi
    [ -z "$MISS_G" ] && [ -z "$EXTRA_G" ] && ok 'набор групп TOOLS совпадает с репозиторием'
fi

if [ "$JSON" -eq 0 ]; then
    printf '  Свободное место:\n'
    df -h "$VENTOY_MOUNT" ${TOOLS_MOUNT:+"$TOOLS_MOUNT"} 2>/dev/null | sed 's/^/    /' || true
fi

# ------------------------------------------------------------
if [ "$JSON" -eq 1 ]; then
    printf '{"errors":%d,"warnings":%d,"ok":%d,"iso_on_flash":%d,"iso_stubs_in_repo":%d}\n' \
           "$ERRORS" "$WARNINGS" "$OKS" "$N_ISOS" "$N_STUBS"
else
    printf '\n\033[1mИтог:\033[0m совпадений — %d, предупреждений — %d, расхождений — %d\n' \
           "$OKS" "$WARNINGS" "$ERRORS"
    if [ "$ERRORS" -gt 0 ]; then
        printf '\033[31mФлешка не соответствует репозиторию.\033[0m\n'
    else
        printf '\033[32mФлешка соответствует репозиторию.\033[0m\n'
    fi
fi

[ "$ERRORS" -eq 0 ] || exit 1
exit 0
