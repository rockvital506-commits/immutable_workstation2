#!/usr/bin/env bash
# tune-ssd-ram.sh — настройка под SSD и малый объём памяти
#
# Соответствует шагу 10 станционного алгоритма
# (ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/algorithm.md):
# снизить износ накопителя и уложиться в память.
#
# ГЛАВНОЕ ОГРАНИЧЕНИЕ ШАГА 10: файл подкачки НЕ ОТКЛЮЧАТЬ. При 8 ГБ
# распаянной памяти это прямой путь к падениям. Ставится фиксированный
# размер, чтобы система не пересоздавала файл.
#
# Каждое действие печатает обратную команду ДО изменения. Автоматического
# отката нет: при сбое выводится обратная команда, решает человек.
#
# Коды возврата:
#   0 — успех (или --dry-run)
#   1 — ошибка, в том числе неизвестный параметр
#   2 — нет нужных средств
#   4 — выполнено не всё: есть проваленные действия
set -euo pipefail

LOG_FILE="${TMPDIR:-/tmp}/${0##*/}.log"
# Лог — самоперезапуском через конвейер (CONVENTIONS.md §5).
if [ -z "${_LOGGED_SELF:-}" ]; then
    _LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"
    exit "${PIPESTATUS[0]}"
fi

usage() { sed -n '2,19p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit "${1:-0}"; }

DRYRUN=0
SWAPPINESS=10
MIN_FREE_PCT=10
VFS_CACHE_PRESSURE=50

while [ $# -gt 0 ]; do
    case "$1" in
        --swappiness)          SWAPPINESS="$2"; shift 2 ;;
        --vfs-cache-pressure)  VFS_CACHE_PRESSURE="$2"; shift 2 ;;
        --min-free-pct)        MIN_FREE_PCT="$2"; shift 2 ;;
        --dry-run)             DRYRUN=1; shift ;;
        -h|--help)             usage 0 ;;
        *) echo "Неизвестный параметр: $1" >&2; usage 1 ;;
    esac
done

for v in SWAPPINESS VFS_CACHE_PRESSURE MIN_FREE_PCT; do
    eval "val=\$$v"
    case "$val" in
        ''|*[!0-9]*) echo "ОШИБКА: $v должен быть числом, получено '$val'" >&2; exit 1 ;;
    esac
done
if [ "$SWAPPINESS" -gt 100 ] || [ "$VFS_CACHE_PRESSURE" -gt 1000 ]; then
    echo "ОШИБКА: swappiness 0..100, vfs_cache_pressure 0..1000" >&2
    exit 1
fi

FAILED=0
APPLIED=0

have() { command -v "$1" > /dev/null 2>&1; }
systemd_running() { [ -d /run/systemd/system ]; }

# Печатает обратную команду до изменения и применяет действие.
apply() {
    local what="$1" back="$2"
    shift 2
    echo "  $what"
    echo "    откат: $back"
    if [ "$DRYRUN" -eq 1 ]; then
        echo "    [dry-run] не изменено"
        APPLIED=$((APPLIED + 1))
        return 0
    fi
    if ! "$@" > /dev/null 2>&1; then
        echo "    ПРОВАЛ"
        echo "    ОТКАТ ВРУЧНУЮ: $back"
        FAILED=$((FAILED + 1))
        return 0
    fi
    APPLIED=$((APPLIED + 1))
    echo "    применено"
}

echo "============================================================"
echo "  tune-ssd-ram.sh  $(date '+%Y-%m-%d %H:%M:%S')"
echo "  SSD + малый объём памяти (шаг 10 алгоритма)"
echo "============================================================"

# --- 1. Износ накопителя: TRIM ---------------------------------------------
echo ""
echo "=== 1. TRIM ==="
if [ ! -r /proc/mounts ]; then
    echo "  /proc/mounts недоступен — пропуск"
elif awk '$2 == "/" {print $4}' /proc/mounts | tr ',' '\n' | grep -qx discard; then
    echo "  discard уже в опциях монтирования корня — ничего не меняем"
elif systemd_running && systemctl list-unit-files --no-legend fstrim.timer > /dev/null 2>&1; then
    # fstrim.timer штатно включён в большинстве дистрибутивов; включение
    # уже включённого не ошибка, но и не изменение.
    apply "fstrim.timer — периодический TRIM" \
          "systemctl disable fstrim.timer" \
          systemctl enable --now fstrim.timer
else
    echo "  нет ни discard, ни fstrim.timer"
    echo "    включите fstrim.timer или добавьте discard в /etc/fstab"
    echo "    откат: systemctl disable fstrim.timer / убрать discard из fstab"
    FAILED=$((FAILED + 1))
fi

# --- 2. Память: агрессивность подкачки -------------------------------------
# При малом объёме памяти высокое vm.swappiness ведёт к постоянному вытеснению
# и росту записи на SSD. Низкое — к преждевременным OOM. Это компромисс, а не
# «чем меньше тем лучше», поэтому значение параметризовано.
echo ""
echo "=== 2. Подкачка и кэш ядра ==="
if [ -r /proc/sys/vm/swappiness ]; then
    cur=$(cat /proc/sys/vm/swappiness 2>/dev/null || echo "?")
    apply "vm.swappiness: $cur -> $SWAPPINESS" \
          "sysctl -w vm.swappiness=$cur" \
          sysctl -w "vm.swappiness=$SWAPPINESS"
else
    echo "  /proc/sys/vm/swappiness недоступен — пропуск"
fi
if [ -r /proc/sys/vm/vfs_cache_pressure ]; then
    cur=$(cat /proc/sys/vm/vfs_cache_pressure 2>/dev/null || echo "?")
    apply "vm.vfs_cache_pressure: $cur -> $VFS_CACHE_PRESSURE" \
          "sysctl -w vm.vfs_cache_pressure=$cur" \
          sysctl -w "vm.vfs_cache_pressure=$VFS_CACHE_PRESSURE"
else
    echo "  /proc/sys/vm/vfs_cache_pressure недоступен — пропуск"
fi

# Подкачку НЕ отключаем (шаг 10). Проверяем, что она есть.
echo ""
echo "  Подкачка НЕ отключается: при малом объёме распаянной памяти"
echo "  это прямой путь к падениям (шаг 10 алгоритма)."
if [ -r /proc/swaps ]; then
    n=$(awk 'NR > 1 && $1 != "" {c++} END {print c+0}' /proc/swaps)
    if [ "$n" -eq 0 ]; then
        echo "    ВНИМАНИЕ: подкачки нет. Настроенный файл/раздел подкачки"
        echo "    обязателен, иначе система будет падать при нехватке памяти."
        if [ "$DRYRUN" -eq 0 ]; then
            FAILED=$((FAILED + 1))
        fi
    else
        echo "    записей подкачки: $n"
    fi
fi

# --- 3. Свободное место ----------------------------------------------------
echo ""
echo "=== 3. Свободное место ==="
if have df; then
    line=$(df -P / 2>/dev/null | awk 'NR == 2 {print $2, $4}')
    total=$(echo "$line" | awk '{print $1}')
    free=$(echo "$line" | awk '{print $2}')
    if [ -n "${total:-}" ] && [ "${total:-0}" -gt 0 ]; then
        pct=$((free * 100 / total))
        echo "  корень: свободно $pct% (норма не менее $MIN_FREE_PCT%)"
        if [ "$pct" -lt "$MIN_FREE_PCT" ]; then
            echo "    МАЛО МЕСТА: очистите кэш и временные файлы"
            FAILED=$((FAILED + 1))
        fi
    else
        echo "  не удалось определить свободное место"
    fi
else
    echo "  нет df — пропуск"
fi

# --- 4. Кэш и временные файлы ----------------------------------------------
echo ""
echo "=== 4. Кэш и временные файлы ==="
# Кэш браузера и временные файлы ограничиваются по размеру, а не удаляются
# без спроса: в кэше могут быть данные текущего сеанса владельца.
echo "  Кэш браузера и временные файлы скрипт НЕ удаляет: в них могут"
echo "  быть данные текущего сеанса. Ограничение размера — настройка"
echo "  приложения, выполняется по процедуре-инструкции."
if [ -d "${TMPDIR:-/tmp}" ]; then
    sz=$( { du -sm "${TMPDIR:-/tmp}" 2>/dev/null || true; } | awk '{print $1}')
    echo "  ${TMPDIR:-/tmp}: ${sz:-?} МБ"
fi

# --- Итог ------------------------------------------------------------------
echo ""
echo "============================================================"
echo "Действий выполнено: $APPLIED   Провалено: $FAILED"

if [ "$DRYRUN" -eq 1 ]; then
    echo ""
    echo "Ничего не изменено (--dry-run)."
    exit 0
fi

if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "ВЫПОЛНЕНО НЕ ВСЁ. Автоматический откат НЕ выполняется:"
    echo "обратные команды — в выводе выше, по одной на действие."
    exit 4
fi

echo ""
echo "Готово. Проверка: validate-system (пункты 7, 8, 9)."
exit 0
