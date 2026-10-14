#!/usr/bin/env bash
# apply-blocking.sh — применение блокировок телеметрии и самовосстановления
#
# Порядок применения фиксирован (research/06-services-blocklist.md):
#   P0 -> P1a -> P1b -> P2 -> T -> P3 -> P5
# Инициаторы отключаются раньше исполнителей: иначе исполнитель поднимет
# своего инициатора обратно, и применение окажется видимым, но недействующим.
#
# Профиль — НЕ в этом файле, а в apply-blocking.conf рядом. Обе половины пары
# (.sh и .ps1) читают один файл, поэтому профиль станции не разъезжается.
#
# ВАЖНО. Скрипт не откатывает ничего автоматически. Откат без спроса может
# упасть по той же причине, по которой упало применение (так поступил
# Win11Debloat: PR #613 был реализован и отклонён). При сбое печатается путь к
# дампу и точная обратная команда для именно этого действия.
#
# Коды возврата:
#   0 — успех (или --dry-run)
#   1 — ошибка, в том числе неизвестный параметр или неизвестный ключ профиля
#   2 — нет нужных средств (не запущен systemd)
#   3 — обязательный дамп аудита не предоставлен или недоступен
#   4 — применено не всё: есть проваленные действия
set -euo pipefail

LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
# Лог ведётся самоперезапуском через конвейер. Process substitution с tee
# здесь запрещён правилом (CONVENTIONS.md §5): вместе с trap он висит, если
# set -e обрывает скрипт внутри функции, а tee ещё жив. Код возврата
# возвращается через PIPESTATUS.
if [ -z "${_LOGGED_SELF:-}" ]; then
    _LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi

usage() { sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

CONF=""
AUDIT=""
DRYRUN=0
NO_AUDIT=0
SELECTED_GROUPS=""
EXCLUDE_SERVICES=""
P3_ENABLE=""
REPORT_DIR=""
declare -A CFG=()
declare -A SEEN=()   # ключи, фактически встреченные в профиле. Отдельно от
                     # значений: P3_ENABLE = (пустое значение) — это валидная
                     # запись «ничего из P3 не включено», а не отсутствующий ключ.

# Ключи профиля. Неизвестный ключ — ошибка: опечатка не должна молча
# превращаться в «профиль не сработал».
KNOWN_KEYS="P0 P1a P1b P2 T P3 P5 VERIFY_WU EXCLUDE_SERVICES P3_ENABLE REPORT_DIR"

# --- Группы ----------------------------------------------------------------
# Перечни взяты из research/06-services-blocklist.md без изменений.
# В Linux-половине обрабатываются те позиции, у которых есть аналог в системе.

# P0 — критические инициаторы (Linux-аналоги: автообновление и «мусор сам»)
P0_UNITS="apt-daily.service apt-daily-upgrade.service"
# P1a — задачи-инициаторы
P1A_TIMERS="apt-daily.timer apt-daily-upgrade.timer"
# P1b — службы-инициаторы телеметрии
P1B_UNITS="whoopsie.service apport.service"
# P2 — исполнители. В Linux перечень из P2 не имеет аналогов: IFEO, службы
# Xbox и RemoteRegistry — объекты Windows. Группа остаётся в порядке
# применения, чтобы профиль был одинаковым для обеих платформ.
# P3 — ситуативные, включаются явно через P3_ENABLE
p3_units() {
    case "$1" in
        TabletInputService) echo "" ;;
        lfsvc)              echo "geoclue.service" ;;
        hyperv)             echo "libvirtd.service" ;;
        Spooler)            echo "cups.service cups-browsed.service" ;;
        WMPNetworkSvc)      echo "avahi-daemon.service" ;;
        nfc)                echo "neard.service" ;;
        phone)              echo "modemmanager.service" ;;
        *)                  echo "" ;;
    esac
}

FAILED=0
APPLIED=0

log()  { echo "$@"; }
head1() { log ""; log "=== $* ==="; }

in_excluded() {
    local u="$1" e
    for e in $EXCLUDE_SERVICES; do
        [ "$u" = "$e.service" ] && return 0
        [ "$u" = "$e.timer" ] && return 0
        [ "$u" = "$e" ] && return 0
    done
    return 1
}

# Каждое действие печатает обратную команду ДО изменения. Если команда упадёт,
# обратная команда уже на экране и в логе — искать её не придётся.
disable_unit() {
    local unit="$1" kind="$2" now back
    if ! systemctl list-unit-files --no-legend "$unit" > /dev/null 2>&1; then
        log "  [пропуск] $unit — нет в системе"
        return 0
    fi
    now=$(systemctl is-enabled "$unit" 2>/dev/null || echo "неизвестно")
    case "$kind" in
        service) back="systemctl enable $unit && systemctl start $unit" ;;
        timer)   back="systemctl enable --now $unit" ;;
    esac
    log "  $unit: сейчас '$now' -> disabled"
    log "    откат: $back"
    if [ "$DRYRUN" -eq 1 ]; then
        log "    [dry-run] не изменено"
        APPLIED=$((APPLIED + 1))
        return 0
    fi
    if ! systemctl disable --now "$unit" > /dev/null 2>&1; then
        log "    ПРОВАЛ: не удалось отключить $unit"
        log "    ОТКАТ ВРУЧНУЮ: $back"
        log "    Дамп исходного состояния: ${AUDIT:-<не предоставлен>}"
        FAILED=$((FAILED + 1))
        return 0
    fi
    APPLIED=$((APPLIED + 1))
    log "    применено"
}

mask_unit() {
    local unit="$1" now
    if ! systemctl list-unit-files --no-legend "$unit" > /dev/null 2>&1; then
        log "  [пропуск] $unit — нет в системе"
        return 0
    fi
    now=$(systemctl is-enabled "$unit" 2>/dev/null || echo "неизвестно")
    log "  $unit: сейчас '$now' -> masked"
    log "    откат: systemctl unmask $unit"
    if [ "$DRYRUN" -eq 1 ]; then
        log "    [dry-run] не изменено"
        APPLIED=$((APPLIED + 1))
        return 0
    fi
    if ! systemctl mask "$unit" > /dev/null 2>&1; then
        log "    ПРОВАЛ: не удалось замаскировать $unit"
        log "    ОТКАТ ВРУЧНУЮ: systemctl unmask $unit"
        log "    Дамп исходного состояния: ${AUDIT:-<не предоставлен>}"
        FAILED=$((FAILED + 1))
        return 0
    fi
    APPLIED=$((APPLIED + 1))
    log "    применено"
}

# --- Профиль ---------------------------------------------------------------

read_conf() {
    local file="$1" line key val
    [ -r "$file" ] || { log "ОШИБКА: профиль недоступен: $file"; exit 1; }
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%%$'\r'}"
        case "$line" in ''|'#'*) continue ;; esac
        case "$line" in
            *=*) ;;
            *) log "ОШИБКА: строка профиля без '=': $line"; exit 1 ;;
        esac
        key="${line%%=*}"
        val="${line#*=}"
        key="$(echo "$key" | tr -d ' \t')"
        val="$(echo "$val" | sed 's/^[ \t]*//; s/[ \t]*$//; s/[ \t]*,[ \t]*/,/g')"
        local known=0 k
        for k in $KNOWN_KEYS; do [ "$key" = "$k" ] && known=1 && break; done
        if [ "$known" -ne 1 ]; then
            log "ОШИБКА: неизвестный ключ профиля: '$key'"
            log "Допустимые: $KNOWN_KEYS"
            exit 1
        fi
        case "$key" in
            EXCLUDE_SERVICES|P3_ENABLE|REPORT_DIR) ;;
            *)
                case "$val" in
                    0|1) ;;
                    *) log "ОШИБКА: $key должен быть 0 или 1, получено '$val'"; exit 1 ;;
                esac
                ;;
        esac
        CFG[$key]="$val"
        SEEN[$key]=1
    done < "$file"
    local k
    for k in $KNOWN_KEYS; do
        if [ -z "${SEEN[$k]-}" ]; then
            log "ОШИБКА: в профиле нет обязательного ключа: $k"
            exit 1
        fi
    done
}

cfg() { echo "${CFG[$1]-}"; }

# --- Параметры -------------------------------------------------------------

while [ $# -gt 0 ]; do
    case "$1" in
        -c|--conf)     CONF="$2"; shift 2 ;;
        -a|--audit)    AUDIT="$2"; shift 2 ;;
        -g|--groups)   SELECTED_GROUPS="$2"; shift 2 ;;
        --report-dir)  REPORT_DIR="$2"; shift 2 ;;
        --dry-run)     DRYRUN=1; shift ;;
        --no-audit)    NO_AUDIT=1; shift ;;
        -h|--help)     usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

[ -n "$CONF" ] || CONF="$(dirname "${BASH_SOURCE[0]}")/apply-blocking.conf"

head1 "apply-blocking.sh $(date '+%Y-%m-%d %H:%M:%S')"
log "Профиль: $CONF"
read_conf "$CONF"
[ -n "$REPORT_DIR" ] || REPORT_DIR="$(cfg REPORT_DIR)"

for k in $KNOWN_KEYS; do
    log "  $k = $(cfg "$k")"
done

if [ -z "$SELECTED_GROUPS" ]; then
    SELECTED_GROUPS="P0 P1a P1b P2 T P3 P5"
fi
log "Группы к применению: $SELECTED_GROUPS"

# --- Обязательный дамп -----------------------------------------------------
# Исходные значения фиксируются дампом на первом шаге; без него откат
# невозможен (research/06). Поэтому отсутствие дампа — отказ, а не
# предупреждение.
if [ "$DRYRUN" -eq 0 ] && [ -z "$AUDIT" ] && [ "$NO_AUDIT" -ne 1 ]; then
    log ""
    log "ОШИБКА: не предоставлен дамп аудита."
    log "Сначала:  bash system-audit.sh -o <каталог>"
    log "Потом:    bash apply-blocking.sh --audit <путь к дампу>"
    log "Без дампа исходные значения не зафиксированы и откат невозможен."
    log "Осознанно обойти: --no-audit (не рекомендуется)."
    exit 3
fi
if [ -n "$AUDIT" ] && [ ! -f "$AUDIT" ]; then
    log "ОШИБКА: дамп недоступен: $AUDIT"
    exit 3
fi
[ -n "$AUDIT" ] && log "Дамп исходного состояния: $AUDIT"

# --- Средства --------------------------------------------------------------

systemd_running() { [ -d /run/systemd/system ]; }

if [ "$DRYRUN" -eq 0 ] && ! systemd_running; then
    log ""
    log "ОШИБКА: systemd не запущен — управлять службами нечем."
    log "В Live-сессии без systemd скрипт применять нечего; запустите"
    log "--dry-run, чтобы увидеть, что было бы сделано."
    exit 2
fi

# --- Применение ------------------------------------------------------------

want() {
    local g="$1"
    case " $SELECTED_GROUPS " in *" $g "*) ;; *) return 1 ;; esac
    [ "$(cfg "$g")" = "1" ]
}

apply_group() {
    local g="$1"
    if ! want "$g"; then
        log "  [выключено профилем или не выбрано]"
        return 0
    fi
    case "$g" in
        P0)
            local u
            for u in $P0_UNITS; do
                in_excluded "$u" && { log "  $u — в EXCLUDE_SERVICES, пропуск"; continue; }
                disable_unit "$u" service
            done
            ;;
        P1a)
            local t
            for t in $P1A_TIMERS; do
                in_excluded "$t" && { log "  $t — в EXCLUDE_SERVICES, пропуск"; continue; }
                disable_unit "$t" timer
            done
            ;;
        P1b)
            local u
            for u in $P1B_UNITS; do
                in_excluded "$u" && { log "  $u — в EXCLUDE_SERVICES, пропуск"; continue; }
                mask_unit "$u"
            done
            ;;
        P2)
            log "  Перечень P2 (IFEO-заглушки, службы Xbox, RemoteRegistry,"
            log "  RetailDemo) — объекты Windows. В Linux аналогов нет,"
            log "  применяется половиной .ps1."
            ;;
        T)
            log "  Точечные запреты (wrapper'ы DISM/powercfg/fsutil/vssadmin/"
            log "  bcdedit) реализуются на стороне Windows — apply-blocking.ps1."
            ;;
        P3)
            local list item units u
            list="$(cfg P3_ENABLE)"
            if [ -z "$list" ]; then
                log "  P3_ENABLE пуст: ни одна ситуативная позиция не"
                log "  применяется. Это штатное состояние: каждая позиция P3"
                log "  ломает рабочую функцию и включается под профиль."
                return 0
            fi
            IFS=',' read -ra items <<< "$list"
            for item in "${items[@]}"; do
                units="$(p3_units "$item")"
                if [ -z "$units" ]; then
                    log "  $item — аналога в Linux нет (позиция Windows)"
                    continue
                fi
                for u in $units; do
                    in_excluded "$u" && { log "  $u — в EXCLUDE_SERVICES, пропуск"; continue; }
                    disable_unit "$u" service
                done
            done
            ;;
        P5)
            log "  Enforcement-задача ставится на стороне Windows —"
            log "  apply-blocking.ps1. В Linux аналога нет."
            ;;
    esac
}

for g in P0 P1a P1b P2 T P3 P5; do
    case " $SELECTED_GROUPS " in *" $g "*) ;; *) continue ;; esac
    head1 "$g"
    apply_group "$g"
done

# --- Итог ------------------------------------------------------------------

head1 "Итог"
log "Действий выполнено: $APPLIED"
log "Провалено: $FAILED"

if [ -n "$REPORT_DIR" ] && [ "$DRYRUN" -eq 0 ]; then
    if [ -d "$REPORT_DIR" ]; then
        REPORT="$REPORT_DIR/apply-blocking-$(date '+%Y%m%d-%H%M%S').txt"
        {
            echo "# Отчёт о применении блокировок"
            echo "# Дата: $(date '+%Y-%m-%d %H:%M:%S')"
            echo "# Профиль: $CONF"
            echo "# Дамп исходного состояния: ${AUDIT:-<не предоставлен>}"
            echo "# Группы: $SELECTED_GROUPS"
            echo "# Действий выполнено: $APPLIED, провалено: $FAILED"
            echo "# Откат выполняется по дампу: таблица «применили / откатили»"
            echo "# в research/06-services-blocklist.md"
        } > "$REPORT"
        log "Отчёт: $REPORT"
    else
        log "ОШИБКА: каталог отчётов недоступен: $REPORT_DIR"
        exit 1
    fi
fi

if [ "$FAILED" -gt 0 ]; then
    log ""
    log "ПРИМЕНЕНО НЕ ВСЁ. Автоматический откат НЕ выполняется:"
    log "откат без спроса может упасть по той же причине, по которой"
    log "упало применение. Решает человек."
    log "  Дамп исходного состояния: ${AUDIT:-<не предоставлен>}"
    log "  Сравнить с текущим: bash system-audit.sh --diff ${AUDIT:-<путь>}"
    log "  Обратные команды — в выводе выше, по одной на проваленное действие."
    exit 4
fi

if [ "$DRYRUN" -eq 1 ]; then
    log ""
    log "Ничего не изменено (--dry-run)."
    exit 0
fi

log ""
log "Готово. ОБЯЗАТЕЛЬНЫЙ следующий шаг — повторный аудит и сравнение:"
log "  bash system-audit.sh -o <каталог> --diff $AUDIT"
exit 0
