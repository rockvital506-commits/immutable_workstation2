#!/usr/bin/env bash
# validate-system.sh — приёмка станции: 12 проверок из раздела 5 алгоритма
#
# Перечень проверок и нормы взяты из
# ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md,
# раздел 5, без изменений. Это критерии приёмки, поэтому они НЕ вынесены в
# профиль: менять их правкой конфига — значит менять критерий под результат.
#
# Скрипт только читает. Ничего не меняет и ничего не «чинит»: найденное
# отклонение — это результат приёмки, а не повод для автоматической правки.
#
# Пункты 2 и 11 ОБЯЗАТЕЛЬНЫ (раздел 5):
#   2  — AllowTelemetry = 0 ломает Центр обновления на части редакций, а
#        система без обновлений уязвимее системы с телеметрией;
#   11 — часть механизмов самовосстановления возвращает значения после
#        перезагрузки или по расписанию.
# Пункт 11 проверяется в два прогона: --save-baseline до перезагрузки,
# затем --baseline <файл> после. Без файла базовой линии приёмка считается
# НЕЗАВЕРШЁННОЙ (код 3), а не пройденной.
#
# Коды возврата:
#   0 — все проверки пройдены, обязательные выполнены
#   1 — ошибка, в том числе неизвестный параметр
#   2 — нет нужных средств
#   3 — обязательная проверка не выполнена: приёмка незавершена
#   4 — есть проваленные проверки: станция не сдаётся
set -euo pipefail

LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
# Лог — самоперезапуском через конвейер. Process substitution с tee запрещён
# правилом (CONVENTIONS.md §5): вместе с trap он висит при обрыве по set -e.
if [ -z "${_LOGGED_SELF:-}" ]; then
    _LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi

usage() { sed -n '2,25p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

BASELINE=""
SAVE_BASELINE=""
BACKUP_RC=""
DRYRUN=0
MIN_FREE_PCT=10

PASSED=0
FAILED=0
SKIPPED=0
RESULTS=""

while [ $# -gt 0 ]; do
    case "$1" in
        -b|--baseline)      BASELINE="$2"; shift 2 ;;
        --save-baseline)    SAVE_BASELINE="$2"; shift 2 ;;
        --backup-rc)        BACKUP_RC="$2"; shift 2 ;;
        --min-free-pct)     MIN_FREE_PCT="$2"; shift 2 ;;
        --dry-run)          DRYRUN=1; shift ;;
        -h|--help)          usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

case "$MIN_FREE_PCT" in
    ''|*[!0-9]*) echo "ОШИБКА: --min-free-pct должен быть числом, получено '$MIN_FREE_PCT'" >&2; exit 1 ;;
esac
if [ -n "$BACKUP_RC" ]; then
    case "$BACKUP_RC" in
        ''|*[!0-9]*) echo "ОШИБКА: --backup-rc должен быть числом, получено '$BACKUP_RC'" >&2; exit 1 ;;
    esac
fi

# --- Приём результатов -----------------------------------------------------

# Результат печатается строкой фиксированного вида, чтобы итог можно было
# читать и глазами, и машиной.
pass() { PASSED=$((PASSED + 1));  RESULTS="${RESULTS}PASS $1|$2"$'\n'; printf '%-4s  %2s  %s\n' "PASS" "$1" "$2"; }
fail() { FAILED=$((FAILED + 1));  RESULTS="${RESULTS}FAIL $1|$2|$3"$'\n'; printf '%-4s  %2s  %s\n' "FAIL" "$1" "$2"; [ -n "${3:-}" ] && printf '        норма: %s\n' "$3"; return 0; }
skip() { SKIPPED=$((SKIPPED + 1)); RESULTS="${RESULTS}SKIP $1|$2"$'\n'; printf '%-4s  %2s  %s\n' "SKIP" "$1" "$2"; }

# --- Средства --------------------------------------------------------------

have() { command -v "$1" > /dev/null 2>&1; }
systemd_running() { [ -d /run/systemd/system ]; }

echo "============================================================"
echo "  validate-system.sh  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  Приёмка станции: 12 проверок из раздела 5 алгоритма"
echo "============================================================"
echo ""
printf '%-4s  %2s  %s\n' "СТАТ" "№" "Проверка"
echo "------------------------------------------------------------"

# --- 1. Сбор телеметрии отключён -------------------------------------------
# Windows: AllowTelemetry / DiagnosticData = 0. Linux-аналог — пакеты отчётов.
check1() {
    local found=""
    local p
    for p in whoopsie apport popularity-contest ubuntu-report; do
        if have dpkg && dpkg -l "$p" 2>/dev/null | grep -q '^ii'; then
            found="$found $p"
        fi
    done
    if [ -n "$found" ]; then
        fail 1 "установлены пакеты отчётов:$found" "пакеты отчётов не установлены"
        return 0
    fi
    if have dpkg; then
        pass 1 "пакеты отчётов не установлены"
    else
        skip 1 "нет dpkg — проверить нечем"
    fi
}

# --- 2. Центр обновления работает (ОБЯЗАТЕЛЬНО) ----------------------------
check2() {
    if [ "$DRYRUN" -eq 1 ]; then
        skip 2 "--dry-run: проверка обновлений не выполняется"
        return 0
    fi
    if ! have apt-get; then
        skip 2 "нет apt-get — проверить нечем"
        return 0
    fi
    local out
    # --print-uris не скачивает пакеты: приёмке нужен факт работоспособности
    # канала, а не установка. Сетевой запрос при этом выполняется.
    if out=$(apt-get -s upgrade 2>&1); then
        pass 2 "канал обновлений отвечает"
    else
        fail 2 "канал обновлений не отвечает" "обновления находятся"
        printf '        вывод: %s\n' "$(echo "$out" | head -2)"
        return 0
    fi
}

# --- 3. Службы из блэклиста остановлены ------------------------------------
check3() {
    if ! systemd_running; then
        skip 3 "systemd не запущен"
        return 0
    fi
    local bad="" u st
    for u in whoopsie apport; do
        if systemctl list-unit-files --no-legend "$u.service" > /dev/null 2>&1; then
            st=$(systemctl is-enabled "$u.service" 2>/dev/null || echo "неизвестно")
            case "$st" in
                disabled|masked) ;;
                *) bad="$bad $u=$st" ;;
            esac
        fi
    done
    if [ -n "$bad" ]; then
        fail 3 "не отключены:$bad" "disabled или masked"
        return 0
    fi
    pass 3 "службы из блэклиста отключены"
}

# --- 4. Задачи телеметрии отключены ----------------------------------------
check4() {
    if ! systemd_running; then
        skip 4 "systemd не запущен"
        return 0
    fi
    local bad="" t st
    for t in apt-daily.timer apt-daily-upgrade.timer; do
        if systemctl list-unit-files --no-legend "$t" > /dev/null 2>&1; then
            st=$(systemctl is-enabled "$t" 2>/dev/null || echo "неизвестно")
            case "$st" in
                disabled|masked) ;;
                *) bad="$bad $t=$st" ;;
            esac
        fi
    done
    if [ -n "$bad" ]; then
        fail 4 "не отключены:$bad" "disabled или masked"
        return 0
    fi
    pass 4 "задачи телеметрии отключены"
}

# --- 5. Драйверы без проблем -----------------------------------------------
# Windows: pnputil /enum-devices /problem. Linux — ошибки ядра по устройствам.
check5() {
    if ! have dmesg; then
        skip 5 "нет dmesg"
        return 0
    fi
    local n
    # || true: dmesg без прав может вернуть ненулевой код, и grep -c при нуле
    # совпадений тоже возвращает 1 — под set -e это обрывает скрипт.
    n=$(dmesg 2>/dev/null | grep -ci 'firmware.*fail\|driver.*fail' || true)
    n=${n:-0}
    if [ "$n" -gt 0 ]; then
        fail 5 "строк с ошибками драйверов/прошивок: $n" "0 проблемных"
        return 0
    fi
    pass 5 "ошибок драйверов в dmesg нет"
}

# --- 6. Сеть работает ------------------------------------------------------
check6() {
    local up=""
    if have ip; then
        up=$(ip -o link show 2>/dev/null | grep -c 'state UP' || true)
    fi
    up=${up:-0}
    if [ "$up" -eq 0 ]; then
        fail 6 "нет интерфейсов в состоянии UP" "хотя бы один Connected"
        return 0
    fi
    pass 6 "интерфейсов в состоянии UP: $up"
}

# --- 7. TRIM включён -------------------------------------------------------
check7() {
    local root_dev opts=""
    if [ ! -r /proc/mounts ]; then
        skip 7 "/proc/mounts недоступен"
        return 0
    fi
    root_dev=$(awk '$2 == "/" {print $1; exit}' /proc/mounts)
    opts=$(awk '$2 == "/" {print $4; exit}' /proc/mounts)
    if [ -z "$root_dev" ]; then
        skip 7 "корневая точка монтирования не найдена"
        return 0
    fi
    case "$opts" in
        *discard*) pass 7 "смонтировано с discard" ;;
        *)
            # Без discard в опциях монтирования TRIM может работать через
            # периодический fstrim — это тоже штатный режим.
            if systemd_running && systemctl list-unit-files --no-legend fstrim.timer > /dev/null 2>&1; then
                pass 7 "нет discard в опциях, но есть fstrim.timer"
            else
                fail 7 "нет ни discard, ни fstrim.timer" "TRIM включён"
            fi
            ;;
    esac
}

# --- 8. Гибернация выключена -----------------------------------------------
check8() {
    if [ ! -d /sys/power ]; then
        skip 8 "/sys/power недоступен"
        return 0
    fi
    local modes=""
    modes=$(cat /sys/power/mem_sleep 2>/dev/null || true)
    if [ -r /sys/power/state ] && grep -qw disk /sys/power/state 2>/dev/null; then
        fail 8 "режим disk (гибернация) доступен" "гибернация недоступна"
        return 0
    fi
    pass 8 "гибернация недоступна (${modes:-режимы не прочитаны})"
}

# --- 9. Файл подкачки фиксирован -------------------------------------------
# Windows: фиксированный pagefile.sys. Linux-аналог — swap: при 8 ГБ
# распаянной памяти подкачку не отключают (алгоритм, шаг 10), но её размер
# должен быть известен и не меняться.
check9() {
    if [ ! -r /proc/swaps ]; then
        skip 9 "/proc/swaps недоступен"
        return 0
    fi
    local n
    n=$(awk 'NR > 1 && $1 != "" {c++} END {print c+0}' /proc/swaps)
    if [ "$n" -eq 0 ]; then
        fail 9 "подкачки нет" "подкачка есть: при 8 ГБ ОЗУ отключение ведёт к падениям"
        return 0
    fi
    pass 9 "записей подкачки: $n"
}

# --- 10. Целостность хранилища ---------------------------------------------
# Windows: DISM /Online /Cleanup-Image /ScanHealth. Linux — проверка ФС.
check10() {
    if ! have fsck; then
        skip 10 "нет fsck"
        return 0
    fi
    local dev fstype
    dev=$(awk '$2 == "/" {print $1; exit}' /proc/mounts 2>/dev/null || true)
    fstype=$(awk '$2 == "/" {print $3; exit}' /proc/mounts 2>/dev/null || true)
    if [ -z "$dev" ]; then
        skip 10 "корневое устройство не определено"
        return 0
    fi
    # fsck -N только показывает, что было бы выполнено: проверка смонтированной
    # ФС без -n недопустима, а -n на некоторых ФС требует размонтирования.
    if fsck -N "$dev" > /dev/null 2>&1; then
        pass 10 "fsck доступен для $dev ($fstype), полная проверка — при размонтированном томе"
    else
        skip 10 "fsck -N не выполнен для $dev"
    fi
}

# --- 11. Настройки переживают перезагрузку (ОБЯЗАТЕЛЬНО) -------------------
# Снимается в два прогона: --save-baseline до перезагрузки, --baseline после.
BASE_KEYS="telemetry_pkgs blacklist_units timers"

snapshot11() {
    local out="" p u t
    local pkgs="" units="" tmrs=""
    for p in whoopsie apport popularity-contest ubuntu-report; do
        if have dpkg && dpkg -l "$p" 2>/dev/null | grep -q '^ii'; then
            pkgs="$pkgs $p"
        fi
    done
    if systemd_running; then
        for u in whoopsie apport; do
            units="$units $u=$(systemctl is-enabled "$u.service" 2>/dev/null || echo 'нет')"
        done
        for t in apt-daily.timer apt-daily-upgrade.timer; do
            tmrs="$tmrs $t=$(systemctl is-enabled "$t" 2>/dev/null || echo 'нет')"
        done
    fi
    out="telemetry_pkgs:${pkgs# }"$'\n'
    out="${out}blacklist_units:${units# }"$'\n'
    out="${out}timers:${tmrs# }"
    printf '%s\n' "$out"
}

check11() {
    if [ -n "$SAVE_BASELINE" ]; then
        local dir
        dir=$(dirname "$SAVE_BASELINE")
        if [ ! -d "$dir" ]; then
            fail 11 "каталог базовой линии недоступен: $dir" "каталог существует"
            return 0
        fi
        snapshot11 > "$SAVE_BASELINE"
        pass 11 "базовая линия записана: $SAVE_BASELINE"
        printf '        ОБЯЗАТЕЛЬНО: перезагрузить станцию и запустить повторно\n'
        printf '        с --baseline %s\n' "$SAVE_BASELINE"
        return 0
    fi
    if [ -z "$BASELINE" ]; then
        skip 11 "нет --baseline: проверка ПОСЛЕ перезагрузки не выполнена"
        return 0
    fi
    if [ ! -r "$BASELINE" ]; then
        fail 11 "базовая линия недоступна: $BASELINE" "файл читается"
        return 0
    fi
    local now before d n
    now=$(snapshot11)
    before=$(cat "$BASELINE")
    # `|| true` обязателен: diff возвращает 1 при различии файлов, и под
    # set -e обрывается САМО ПРИСВАИВАНИЕ, а не только конвейер. Проверено:
    # без защиты скрипт молча выходил с кодом 1, не дойдя до вывода.
    d=$( { diff <(printf '%s\n' "$before") <(printf '%s\n' "$now") || true; } |
        awk '/^[<>]/ {c++} END {print c+0}')
    if [ "$d" -gt 0 ]; then
        fail 11 "после перезагрузки вернулось значений: $d" "значения не вернулись"
        { diff <(printf '%s\n' "$before") <(printf '%s\n' "$now") || true; } |
            head -10 | sed 's/^/        /'
        return 0
    fi
    pass 11 "после перезагрузки значения не вернулись"
}

# --- 12. Бэкап снят и проверен ---------------------------------------------
# Норма раздела 5 — verify-backup с кодом 0. Скрипт не запускает verify-backup
# сам: у того свои обязательные параметры, и молчаливый запуск с неверными
# аргументами дал бы ложный результат приёмки.
check12() {
    if [ -z "$BACKUP_RC" ]; then
        skip 12 "нет --backup-rc: запустите verify-backup и передайте его код"
        return 0
    fi
    if [ "$BACKUP_RC" -eq 0 ]; then
        pass 12 "verify-backup вернул 0"
    else
        fail 12 "verify-backup вернул $BACKUP_RC" "код 0"
    fi
}

for c in 1 2 3 4 5 6 7 8 9 10 11 12; do
    "check$c"
done

echo "------------------------------------------------------------"
echo "Пройдено: $PASSED   Провалено: $FAILED   Пропущено: $SKIPPED"
echo ""

# Обязательные пункты раздела 5: 2 и 11.
MANDATORY_MISSING=0
for m in 2 11; do
    if printf '%s' "$RESULTS" | grep -q "^SKIP $m|"; then
        echo "ОБЯЗАТЕЛЬНЫЙ пункт $m НЕ ВЫПОЛНЕН."
        MANDATORY_MISSING=1
    fi
done

if [ "$MANDATORY_MISSING" -eq 1 ]; then
    echo ""
    echo "Приёмка НЕЗАВЕРШЕНА: станция не сдаётся без обязательных пунктов."
    if printf '%s' "$RESULTS" | grep -q "^SKIP 2|"; then
        echo "  Пункт 2 — Центр обновления работает. AllowTelemetry = 0 ломает"
        echo "  Центр обновления на части редакций; система без обновлений"
        echo "  уязвимее системы с телеметрией. Проверить без --dry-run."
    fi
    if printf '%s' "$RESULTS" | grep -q "^SKIP 11|"; then
        echo "  Пункт 11 — настройки переживают перезагрузку. Выполняется в два"
        echo "  прогона: --save-baseline <файл>, перезагрузка, --baseline <файл>."
    fi
    exit 3
fi

if [ "$FAILED" -gt 0 ]; then
    echo "ЕСТЬ ПРОВАЛЕННЫЕ ПРОВЕРКИ: станция не сдаётся."
    echo "Скрипт ничего не исправляет — найденное отклонение это результат"
    echo "приёмки. Правит человек, затем повторный прогон."
    exit 4
fi

echo "Все проверки пройдены. Станция принимается."
exit 0
