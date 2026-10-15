# -*- coding: utf-8 -*-
"""Проверки Этапа 5 — скрипты автоматизации.

Решения заказчика от 2026-10-14/15:
  1. Четыре скрипта: system-audit, apply-blocking, validate-system,
     tune-ssd-ram — по паре .sh + .ps1 на каждый.
  2. Одновременно — пошаговые процедуры-инструкции; в алгоритме станции
     ссылки на них, как на скрипты.
  3. При сбое применения НЕ откатывать автоматически — указать на дамп и
     команду.
  4. Enforcement-задачу планировщика ставить (паттерн P5).
  5. LGPO.exe внести в manifest.csv в os/windows/gpo_lock/.
  6. apply-blocking управляем через отдельный файл профиля, а не правкой
     скрипта; GPO — отдельный шаг, скрипт их не трогает.

Обоснование — research/15-automation-scripts.md.

.sh-половины здесь ЗАПУСКАЮТСЯ, а не только читаются: коды возврата
проверяются фактическим исполнением. Ни один .ps1 не выполняется — PowerShell
в рабочей среде отсутствует.
"""
import csv, io, os, re, subprocess, sys, tempfile

ROOT = '/home/user/immutable_workstation2'
os.chdir(ROOT)
checks = errors = 0


def ok(m):
    global checks
    checks += 1
    print('  OK   ' + m)


def bad(m):
    global checks, errors
    checks += 1
    errors += 1
    print('  FAIL ' + m)


def t(cond, m):
    ok(m) if cond else bad(m)


SC = 'tools/scripts'
PR = 'tools/scripts/procedures'
NAMES = ['system-audit', 'apply-blocking', 'validate-system', 'tune-ssd-ram']

with io.open('manifest.csv', encoding='utf-8') as f:
    body = [r for r in list(csv.reader(f))[1:] if r]

# --- [1] Состав: четыре пары и процедуры -----------------------------------

print('\n[1] Состав Этапа 5')
for n in NAMES:
    t(os.path.isfile(f'{SC}/{n}.sh'), f'{n}.sh существует')
    t(os.path.isfile(f'{SC}/{n}.ps1'), f'{n}.ps1 существует')
t(os.path.isfile(f'{SC}/apply-blocking.conf'), 'apply-blocking.conf существует')
t(os.path.isfile(f'{SC}/README.md'), 'tools/scripts/README.md существует')
for p in ['basic-setup.md', 'block-telemetry.md', 'ssd-ram-tuning.md',
          'validation.md', 'README.md']:
    t(os.path.isfile(f'{PR}/{p}'), f'процедура {p} существует')

# --- [2] Общее правило: лог, коды, отсутствие автоотката -------------------

print('\n[2] Правило CONVENTIONS §5 и отказ от автоотката')
LOG_BLOCK = '_LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"'
for n in NAMES:
    sh = io.open(f'{SC}/{n}.sh', encoding='utf-8').read()
    ps = io.open(f'{SC}/{n}.ps1', encoding='utf-8').read()
    t(sh.startswith('#!/usr/bin/env bash'), f'{n}.sh: shebang')
    t('set -euo pipefail' in sh, f'{n}.sh: set -euo pipefail')
    t(LOG_BLOCK in sh, f'{n}.sh: лог самоперезапуском через tee')
    t('exec > >(tee' not in sh, f'{n}.sh: нет process substitution с tee')
    t('exit "${PIPESTATUS[0]}"' in sh, f'{n}.sh: код возврата через PIPESTATUS')
    t('Set-StrictMode -Version Latest' in ps, f'{n}.ps1: Set-StrictMode')
    t('Start-Transcript' in ps, f'{n}.ps1: лог через Start-Transcript')
    t('PowerShell.Exiting' in ps, f'{n}.ps1: транскрипт закрывается по событию')
    # Скрипт указывает на дамп и команду, но не откатывает сам.
    for src, ext in ((sh, 'sh'), (ps, 'ps1')):
        if n in ('system-audit', 'validate-system'):
            continue
        t('ОТКАТ ВРУЧНУЮ' in src or 'откат:' in src,
          f'{n}.{ext}: печатается обратная команда')
        t('Автоматический откат НЕ выполняется' in src or
          'не откатывает' in src.lower(),
          f'{n}.{ext}: отказ от автоматического отката зафиксирован')

# --- [3] system-audit: фактический запуск ----------------------------------

print('\n[3] system-audit.sh — фактическое исполнение')


def run(script, *args, timeout=120):
    proc = subprocess.run(['bash', f'{SC}/{script}', *args],
                          capture_output=True, text=True, timeout=timeout)
    return proc.returncode, proc.stdout + proc.stderr


with tempfile.TemporaryDirectory() as td:
    rc, out = run('system-audit.sh', '--help')
    t(rc == 0, f'--help: код 0 (факт {rc})')
    t('set -euo pipefail' not in out, '--help не печатает строку set')

    rc, out = run('system-audit.sh', '-o', td)
    t(rc == 0, f'реальный прогон: код 0 (факт {rc})')
    dumps = [x for x in os.listdir(td) if x.startswith('system-audit-')]
    t(len(dumps) == 1, f'дамп создан (найдено {len(dumps)})')
    if dumps:
        txt = io.open(os.path.join(td, dumps[0]), encoding='utf-8').read()
        for sec in ['## Службы', '## Задачи планировщика', '## Автозапуск',
                    '## Модули ядра', '## Пакеты, связанные с телеметрией']:
            t(sec in txt, f'дамп содержит «{sec}»')
        t('# INFO-BEGIN' in txt and '# INFO-END' in txt,
          'информационный раздел помечен маркерами')
        rc2, out2 = run('system-audit.sh', '-o', td, '-d',
                        os.path.join(td, dumps[0]))
        t(rc2 == 0, f'--diff без изменений: код 0 (факт {rc2})')

    rc, _ = run('system-audit.sh', '-o', os.path.join(td, 'нет-такого'))
    t(rc == 3, f'недоступный каталог: код 3 (факт {rc})')
    rc, _ = run('system-audit.sh', '--bogus')
    t(rc == 1, f'неизвестный параметр: код 1 (факт {rc})')
    rc, out = run('system-audit.sh', '--dry-run', '-o', td)
    t(rc == 0, f'--dry-run: код 0 (факт {rc})')

# --- [4] apply-blocking: профиль и обязательный дамп -----------------------

print('\n[4] apply-blocking.sh — профиль и отказ без дампа')
CONF = f'{SC}/apply-blocking.conf'
conf = io.open(CONF, encoding='utf-8').read()
for k in ['P0', 'P1a', 'P1b', 'P2', 'T', 'P3', 'P5', 'VERIFY_WU',
          'EXCLUDE_SERVICES', 'P3_ENABLE', 'REPORT_DIR']:
    t(re.search(rf'(?m)^{k} =', conf) is not None, f'профиль: ключ {k}')
t(re.search(r'(?m)^P3 = 0', conf) is not None, 'P3 выключен по умолчанию')
t('icssvc' in conf and 'SharedAccess' in conf,
  'icssvc и SharedAccess исключены: точка доступа — рабочий инструмент')

rc, out = run('apply-blocking.sh', '--conf', CONF)
t(rc == 3, f'без дампа применение отклонено: код 3 (факт {rc})')
t('Без дампа исходные значения не зафиксированы' in out,
  'объяснено, почему без дампа нельзя')
rc, out = run('apply-blocking.sh', '--conf', CONF, '--dry-run')
t(rc == 0, f'--dry-run: код 0 (факт {rc})')
order = [out.find(f'=== {g} ===') for g in ['P0', 'P1a', 'P1b', 'P2', 'T', 'P3', 'P5']]
t(all(x > -1 for x in order) and order == sorted(order),
  'порядок групп P0 -> P1a -> P1b -> P2 -> T -> P3 -> P5 соблюдён')
rc, _ = run('apply-blocking.sh', '--conf', os.path.join(SC, 'нет.conf'), '--dry-run')
t(rc == 1, f'нет профиля: код 1 (факт {rc})')

with tempfile.TemporaryDirectory() as td:
    bad1 = os.path.join(td, 'bad1.conf')
    io.open(bad1, 'w', encoding='utf-8').write(conf + '\nTYPO_KEY = 1\n')
    rc, out = run('apply-blocking.sh', '--conf', bad1, '--dry-run')
    t(rc == 1, f'неизвестный ключ профиля: код 1 (факт {rc})')
    t('TYPO_KEY' in out, 'неизвестный ключ назван в сообщении')

    bad2 = os.path.join(td, 'bad2.conf')
    io.open(bad2, 'w', encoding='utf-8').write(conf.replace('P0 = 1', 'P0 = 2'))
    rc, _ = run('apply-blocking.sh', '--conf', bad2, '--dry-run')
    t(rc == 1, f'P0 = 2: код 1 (факт {rc})')

    rc, _ = run('apply-blocking.sh', '--conf', CONF, '--audit',
                os.path.join(td, 'нет.txt'), '--dry-run')
    t(rc == 3, f'недоступный дамп: код 3 (факт {rc})')

# GPO и wrapper-подмена в скрипт не входят — это решения заказчика.
ab_sh = io.open(f'{SC}/apply-blocking.sh', encoding='utf-8').read()
ab_ps = io.open(f'{SC}/apply-blocking.ps1', encoding='utf-8').read()
t('LGPO' not in ab_sh, 'apply-blocking.sh не вызывает LGPO: GPO отдельный шаг')
t('не выполняет' in ab_ps or 'не входит' in ab_ps,
  'apply-blocking.ps1 фиксирует, что группа T не выполняется скриптом')
t('ImmutableStation-Enforcement' in ab_ps,
  'apply-blocking.ps1 ставит enforcement-задачу (P5)')

# --- [5] validate-system: 12 проверок и обязательные пункты ----------------

print('\n[5] validate-system.sh — приёмка')
vs = io.open(f'{SC}/validate-system.sh', encoding='utf-8').read()
for i in range(1, 13):
    t(f'check{i}()' in vs, f'проверка {i} определена')
t(vs.count('MANDATORY_MISSING') > 0, 'обязательные пункты отслеживаются')
t('exit 3' in vs and 'exit 4' in vs, 'различаются коды 3 и 4')
t('diff' not in vs.split('# --- 1.')[0],
  'до проверок нет постороннего кода сравнения')

rc, out = run('validate-system.sh', '--dry-run')
t(rc == 3, f'--dry-run: приёмка незавершена, код 3 (факт {rc})')
t('ОБЯЗАТЕЛЬНЫЙ пункт 2 НЕ ВЫПОЛНЕН' in out, 'пункт 2 назван обязательным')
t('ОБЯЗАТЕЛЬНЫЙ пункт 11 НЕ ВЫПОЛНЕН' in out, 'пункт 11 назван обязательным')
for i in range(1, 13):
    t(re.search(rf'(?m)^(PASS|FAIL|SKIP) +{i} ', out) is not None,
      f'проверка {i} выполнена')

with tempfile.TemporaryDirectory() as td:
    bl = os.path.join(td, 'baseline.txt')
    # --dry-run пропускает обязательный пункт 2, поэтому приёмка незавершена
    # и код 3 честный. Базовая линия при этом записывается — именно она и есть
    # цель этого вызова.
    rc, out = run('validate-system.sh', '--dry-run', '--save-baseline', bl)
    t(rc == 3, f'--save-baseline в --dry-run: код 3, пункт 2 не выполнен (факт {rc})')
    t('PASS  11' in out, '--save-baseline: пункт 11 пройден')
    t(os.path.isfile(bl), 'файл базовой линии записан')
    # Без --dry-run пункт 2 выполняется по-настоящему, и приёмка доходит до
    # оценки провалов: в песочнице провалены 8 и 9, поэтому код 4.
    bl2 = os.path.join(td, 'baseline-real.txt')
    rc, out = run('validate-system.sh', '--save-baseline', bl2)
    t(rc in (0, 4), f'--save-baseline без --dry-run: код 0 или 4 (факт {rc})')
    t('PASS   2' in out, 'без --dry-run пункт 2 выполнен по-настоящему')
    rc, out = run('validate-system.sh', '--dry-run', '--baseline', bl)
    t('PASS  11' in out, '--baseline без изменений: пункт 11 пройден')
    changed = os.path.join(td, 'changed.txt')
    txt = io.open(bl, encoding='utf-8').read()
    io.open(changed, 'w', encoding='utf-8').write(
        txt.replace('blacklist_units:', 'blacklist_units: whoopsie=enabled ')
        if txt.strip() else 'x=1\n')
    if txt.strip():
        rc, out = run('validate-system.sh', '--dry-run', '--baseline', changed)
        t('FAIL  11' in out, '--baseline с изменением: пункт 11 провален')
    rc, _ = run('validate-system.sh', '--baseline', os.path.join(td, 'нет.txt'))
    t('FAIL  11' in _, 'недоступная базовая линия: пункт 11 провален')
    rc, out = run('validate-system.sh', '--dry-run', '--save-baseline',
                  os.path.join(td, 'нет-каталога', 'b.txt'))
    t('FAIL  11' in out, 'недоступный каталог базовой линии: пункт 11 провален')

rc, out = run('validate-system.sh', '--dry-run', '--backup-rc', '7')
t('FAIL  12' in out, '--backup-rc 7: пункт 12 провален')
rc, _ = run('validate-system.sh', '--backup-rc', 'x')
t(rc == 1, f'--backup-rc не числом: код 1 (факт {rc})')
rc, _ = run('validate-system.sh', '--min-free-pct', 'abc')
t(rc == 1, f'--min-free-pct не числом: код 1 (факт {rc})')
rc, _ = run('validate-system.sh', '--bogus')
t(rc == 1, f'неизвестный параметр: код 1 (факт {rc})')

# --- [6] tune-ssd-ram: подкачка не отключается -----------------------------

print('\n[6] tune-ssd-ram.sh — SSD и память')
ts = io.open(f'{SC}/tune-ssd-ram.sh', encoding='utf-8').read()
t('НЕ отключать' in ts or 'НЕ отключаем' in ts or 'НЕ отключается' in ts,
  'правило «файл подкачки не отключать» зафиксировано')
t('swapoff' not in ts, 'скрипт не отключает подкачку')
t('rm -rf' not in ts and 'Remove-Item' not in ts,
  'скрипт не удаляет кэш и временные файлы')

rc, out = run('tune-ssd-ram.sh', '--dry-run')
t(rc == 0, f'--dry-run: код 0 (факт {rc})')
t('Ничего не изменено' in out, '--dry-run сообщает, что ничего не изменено')
t('discard' in out or 'TRIM' in out, 'раздел TRIM выполнен')
for a in ['--swappiness', 'abc', '--bogus']:
    pass
rc, _ = run('tune-ssd-ram.sh', '--swappiness', 'abc', '--dry-run')
t(rc == 1, f'--swappiness не числом: код 1 (факт {rc})')
rc, _ = run('tune-ssd-ram.sh', '--swappiness', '200', '--dry-run')
t(rc == 1, f'--swappiness 200: код 1 (факт {rc})')
rc, _ = run('tune-ssd-ram.sh', '--bogus')
t(rc == 1, f'неизвестный параметр: код 1 (факт {rc})')

# --- [7] Процедуры: содержание и ссылки ------------------------------------

print('\n[7] Процедуры-инструкции')
proc_text = {}
for p in ['basic-setup.md', 'block-telemetry.md', 'ssd-ram-tuning.md',
          'validation.md', 'README.md']:
    proc_text[p] = io.open(f'{PR}/{p}', encoding='utf-8').read()
t('WinUtil' in proc_text['basic-setup.md']
  and 'Win11Debloat' in proc_text['basic-setup.md'],
  'basic-setup: WinUtil и Win11Debloat')
t('NoAutoRebootWithLoggedOnUsers' in proc_text['basic-setup.md'],
  'basic-setup: зафиксирован порядок из-за ключа, который WinUtil удаляет')
t('LGPO' in proc_text['block-telemetry.md'],
  'block-telemetry: LGPO отдельным шагом')
t('P0 → P1a → P1b → P2 → T → P3 → P5' in proc_text['block-telemetry.md'],
  'block-telemetry: порядок групп зафиксирован')
t('pagefile' in proc_text['ssd-ram-tuning.md'].lower(),
  'ssd-ram-tuning: фиксированный pagefile')
t('не отключать' in proc_text['ssd-ram-tuning.md'].lower(),
  'ssd-ram-tuning: правило про подкачку')
t('три прогона' in proc_text['validation.md'],
  'validation: приёмка в три прогона')
t('-ScanHealth' in proc_text['validation.md'],
  'validation: DISM /ScanHealth по явному флагу')
for p, txt in proc_text.items():
    t('Не проверено на месте' in txt, f'{p}: раздел «Не проверено на месте»')

# --- [8] Ссылки из алгоритма станции --------------------------------------

print('\n[8] Ссылки из шагов 8/9/10/12 алгоритма')
ALG = ('ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/'
       'algorithm.md')
alg = io.open(ALG, encoding='utf-8').read()
for f in ['basic-setup.md', 'block-telemetry.md', 'ssd-ram-tuning.md',
          'validation.md']:
    t(f'procedures/{f}' in alg, f'алгоритм ссылается на {f}')
for f in ['apply-blocking.ps1', 'apply-blocking.conf', 'tune-ssd-ram.ps1',
          'validate-system.ps1']:
    t(f in alg, f'алгоритм ссылается на {f}')

# Все относительные ссылки в новых файлах должны существовать.
print('\n[9] Относительные ссылки в файлах Этапа 5')
targets = [f'{SC}/README.md', ALG] + [f'{PR}/{p}' for p in proc_text]
broken = 0
for md in targets:
    base = os.path.dirname(md)
    src = io.open(md, encoding='utf-8').read()
    src = re.sub(r'`[^`\n]*`', '', src)
    src = re.sub(r'```.*?```', '', src, flags=re.S)
    for m in re.finditer(r'\]\(([^)#]+)\)', src):
        link = m.group(1).strip()
        if link.startswith(('http', 'mailto:')):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, link))):
            bad(f'{md}: битая ссылка {link}')
            broken += 1
t(broken == 0, f'битых ссылок нет (найдено {broken})')

# --- [10] manifest.csv ----------------------------------------------------

print('\n[10] manifest.csv')
by_name = {r[2]: r for r in body}
for n in NAMES:
    t(n in by_name, f'строка {n} есть')
    if n in by_name:
        t(by_name[n][0] == 'script', f'{n}: type = script')
        t(by_name[n][1] == 'scripts', f'{n}: category = scripts')
t('LGPO' in by_name, 'строка LGPO есть (решение заказчика)')
if 'LGPO' in by_name:
    t(by_name['LGPO'][0] == 'tool', 'LGPO: type = tool')
    t(by_name['LGPO'][1] == 'os/windows/gpo_lock',
      f"LGPO: category = os/windows/gpo_lock (факт {by_name['LGPO'][1]})")
t(len(body) == 46, f'строк данных 46 (факт {len(body)})')

# --- [11] Регрессия: предыдущие этапы целы --------------------------------

print('\n[11] Регрессия')
for p in ['tools/firmware/bios/scripts/bios-inventory.sh',
          'tools/drivers/export/scripts/integrate-drivers.sh',
          'scripts/repo-validate.sh',
          'research/15-automation-scripts.md',
          'research/06-services-blocklist.md',
          'tests/test_stage48.py']:
    t(os.path.isfile(p), f'на месте {p}')
t(os.path.isfile('tools/scripts/system-audit.sh'),
  'system-audit.sh не потерян при правках')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
