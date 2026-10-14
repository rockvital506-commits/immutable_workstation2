#!/usr/bin/env bash
# ============================================================
# system-audit.sh — дамп состояния системы ДО и ПОСЛЕ изменений
#
# Парная версия system-audit.ps1. Скрипт НИЧЕГО не меняет.
#
# Это не отчёт «для галочки»: по research/06-services-blocklist.md исходные
# значения фиксируются дампом на первом шаге, и БЕЗ НЕГО ОТКАТ НЕВОЗМОЖЕН.
# Поэтому дамп обязателен до применения блокировок, а не после.
#
# Запуск:
#   bash system-audit.sh --out ./reports                  # снять дамп
#   bash system-audit.sh --diff ./reports/before.txt --out ./reports
#   bash system-audit.sh --out ./reports --dry-run
#
# Коды возврата: 0 — успех, 1 — ошибка, 2 — нет нужных утилит,
#                3 — каталог или файл недоступны, 4 — найдены отклонения (diff).
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

OUT='.' BASE='' DRYRUN=0

usage() { sed -n '2,18p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        -o|--out)     OUT="${2:?}"; shift 2 ;;
        -d|--diff)    BASE="${2:?}"; shift 2 ;;
        --dry-run)    DRYRUN=1; shift ;;
        -h|--help)    usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

die() { echo "ОШИБКА: $*" >&2; exit "${2:-1}"; }

[ -d "$OUT" ] || die "каталог недоступен: $OUT" 3
[ -w "$OUT" ] || die "каталог не для записи: $OUT" 3
if [ -n "$BASE" ]; then
    [ -f "$BASE" ] || die "нет файла для сравнения: $BASE" 3
fi

# --- Что доступно ---------------------------------------------------------
# Каждый блок самостоятелен: отсутствие утилиты не должно обрывать дамп,
# иначе снимок получится неполным и непригодным для отката.
have() { command -v "$1" >/dev/null 2>&1; }

STAMP="$(date '+%Y%m%d-%H%M%S')"
REPORT="$OUT/system-audit-$STAMP.txt"

# Наличие бинарника systemctl ещё не означает, что systemd запущен: без него
# вызов виснет в ожидании D-Bus. Проверяем каталог рантайма, а не PATH.
systemd_running() { [ -d /run/systemd/system ]; }

dump() {
    echo "# Дамп состояния системы"
    echo "# Дата: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "# Узел: $(hostname 2>/dev/null || echo неизвестен)"
    echo "# Снят ДО изменений. Откат выполняется по этому файлу."
    echo

    echo "## Службы"
    if systemd_running; then
        # Формат «имя|состояние|автозапуск» — пригоден и для чтения, и для diff
        systemctl list-units --type=service --all --no-legend --plain 2>/dev/null \
            | awk '{
                name=$1; state=$4;
                print name "|" state
              }' | sort \
            || echo "  (systemctl ответил ошибкой — systemd не запущен или нет прав)"
    else
        echo "  (systemctl нет)"
    fi
    echo

    echo "## Задачи планировщика"
    if systemd_running; then
        systemctl list-timers --all --no-legend --plain 2>/dev/null | sort \
            || echo "  (таймеров нет, нет доступа или systemd не запущен)"
    fi
    [ -d /etc/cron.d ] && ls -1 /etc/cron.d 2>/dev/null | sort
    for f in /etc/crontab /var/spool/cron/crontabs/*; do
        [ -f "$f" ] || continue
        echo "--- $f"
        grep -v '^#' "$f" 2>/dev/null | grep -v '^[[:space:]]*$' || true
    done
    echo

    echo "## Автозапуск"
    for d in /etc/xdg/autostart /etc/xdg/autostart.disabled; do
        [ -d "$d" ] || continue
        echo "--- $d"
        ls -1 "$d" 2>/dev/null | sort
    done
    for f in /etc/rc.local; do
        [ -f "$f" ] || continue
        echo "--- $f"
        grep -v '^#' "$f" 2>/dev/null | grep -v '^[[:space:]]*$' || true
    done
    echo

    echo "## Модули ядра"
    if have lsmod; then
        lsmod 2>/dev/null | awk 'NR>1 {print $1}' | sort
    else
        echo "  (lsmod нет)"
    fi
    echo

    # Соединения меняются между снятиями даже на неизменённой системе
    # (TIME-WAIT, FIN-WAIT), поэтому раздел помечен информационным и в diff
    # не участвует — иначе каждое сравнение показывало бы ложные отклонения.
    echo "## Сетевые соединения (информационно, в diff не участвует)"
    echo "# INFO-BEGIN"
    if have ss; then
        ss -tunap 2>/dev/null | sort || echo "  (нет доступа)"
    else
        echo "  (ss нет)"
    fi
    echo "# INFO-END"
    echo

    echo "## Пакеты, связанные с телеметрией и сбором данных"
    if have dpkg; then
        dpkg -l 2>/dev/null | awk '/^ii/ {print $2}' \
            | grep -Ei 'whoopsie|apport|popularity|ubuntu-report|snapd' | sort \
            || echo "  (ничего из списка не установлено)"
    else
        echo "  (dpkg нет)"
    fi
}

if [ "$DRYRUN" -eq 1 ]; then
    echo "--- [dry-run] содержимое дампа ---"
    # Без трубы в head: head закрывает канал, dump получает SIGPIPE, и под
    # set -euo pipefail скрипт завершается кодом 141 вместо 0.
    DUMP_TEXT="$(dump)"
    # Текст уже в переменной, поэтому head читает из завершённой подстановки
    printf '%s\n' "$DUMP_TEXT" | head -40
    echo "  ... (дальше опущено в dry-run)"
    echo "--- [dry-run] файл $REPORT не записан ---"
    exit 0
fi

dump > "$REPORT"
LINES=$(wc -l < "$REPORT" | tr -d ' ')
echo "Дамп: $REPORT ($LINES строк)"

# --- Сравнение с прежним дампом ------------------------------------------
if [ -n "$BASE" ]; then
    DIFF="$OUT/system-audit-diff-$STAMP.txt"
    # Нормализуем дату и имя узла: иначе diff покажет расхождение там,
    # где изменилось только время снятия.
    norm() {
        grep -v '^# Дата:' "$1" | grep -v '^# Снят ' \
            | sed '/^# INFO-BEGIN$/,/^# INFO-END$/d'
    }
    norm "$BASE" > "$BASE.norm.tmp"
    norm "$REPORT" > "$REPORT.norm.tmp"
    if diff -u "$BASE.norm.tmp" "$REPORT.norm.tmp" > "$DIFF"; then
        CHANGED=0
    else
        CHANGED=1
    fi
    rm -f "$BASE.norm.tmp" "$REPORT.norm.tmp"
    # grep -c при нуле совпадений отвечает кодом 1, и под set -e это обрывает
    # скрипт на месте. awk всегда завершается нулём и печатает 0.
    N=$(awk '/^[+-]/ {n++} END {print n+0}' "$DIFF")
    echo "Diff: $DIFF (изменённых строк: $N)"
    if [ "$CHANGED" -eq 1 ]; then
        echo "ЕСТЬ ОТКЛОНЕНИЯ от исходного дампа — см. $DIFF"
        echo "Если изменения не планировались, это сработал механизм возврата."
        exit 4
    fi
    echo "Отклонений нет: состояние совпадает с исходным дампом."
fi

echo "Готово. Скопировать в reports/ станции."
exit 0
