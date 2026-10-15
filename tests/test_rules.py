# -*- coding: utf-8 -*-
"""Проверки сквозных правил CONVENTIONS.md, которые не покрыты repo-validate.sh.

Появился после вычитки сданных групп: у backup-vscode не было .sh-пары, и
правило дуальности (CONVENTIONS.md, раздел 5) нигде не контролировалось.
"""
import io, os, re, sys

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


# Исключения из правила дуальности: имя без расширения -> где зафиксировано
EXCEPTIONS = {
    'disk-image': ['PLAN.md', 'tools/backup/disk_image/README.md',
                   'tools/backup/initial_backup/README.md'],
}

print('[1] Правило дуальности скриптов (CONVENTIONS.md, раздел 5)')
scripts = {}
for root, dirs, fs in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
    for f in fs:
        if f.endswith(('.ps1', '.sh')):
            scripts.setdefault(os.path.join(root, f.rsplit('.', 1)[0]), set()).add(
                f.rsplit('.', 1)[1])
t(len(scripts) > 0, f'скрипты найдены ({len(scripts)} пар/одиночных)')
for path in sorted(scripts):
    ext = scripts[path]
    base = os.path.basename(path)
    if ext == {'ps1', 'sh'}:
        ok(f'{base}: есть .ps1 и .sh')
        continue
    if base in EXCEPTIONS:
        for doc in EXCEPTIONS[base]:
            t(os.path.isfile(doc) and base in io.open(doc, encoding='utf-8').read(),
              f'{base}: исключение зафиксировано в {doc}')
    else:
        bad(f'{path}: только {sorted(ext)} — нет пары и нет записи об исключении')

print('\n[2] Исключения объявлены честно')
conv = io.open('CONVENTIONS.md', encoding='utf-8').read()
t('двумя** файлами' in conv, 'в CONVENTIONS.md §5 сформулировано правило двух файлов')
for base, docs in EXCEPTIONS.items():
    for doc in docs:
        t(base in io.open(doc, encoding='utf-8').read(),
          f'{base} упомянут в {doc}')
ib = io.open('tools/backup/initial_backup/README.md', encoding='utf-8').read()
t('единственное' in ib, 'в initial_backup/README.md сказано, что исключение одно')

print('\n[3] Заголовки скриптов соответствуют CONVENTIONS.md §5')
# Проверяем только реально существующие файлы: disk-image.sh — исключение без
# .ps1-пары, поэтому disk-image.ps1 на диске нет.
sh_files = sorted(p + '.sh' for p in scripts if 'sh' in scripts[p])
ps_files = sorted(p + '.ps1' for p in scripts if 'ps1' in scripts[p])
t(len(sh_files) == len(scripts), f'у каждой сущности есть .sh ({len(sh_files)})')
for path in sh_files:
    s = io.open(path, encoding='utf-8').read()
    first = s.split('\n', 1)[0]
    t(first == '#!/usr/bin/env bash', f'{os.path.basename(path)}: shebang верный')
    t(re.search(r'^set -[a-z]*u[a-z]*o pipefail', s, re.M) is not None,
      f'{os.path.basename(path)}: включён режим pipefail')
t(len(ps_files) == len(scripts) - len(EXCEPTIONS),
  f'.ps1 нет только у зафиксированных исключений ({len(ps_files)})')
for path in ps_files:
    s = io.open(path, encoding='utf-8').read()
    t('#Requires' in s, f'{os.path.basename(path)}: есть #Requires')
    t('CmdletBinding' in s, f'{os.path.basename(path)}: есть [CmdletBinding()]')
    t('$ErrorActionPreference' in s,
      f'{os.path.basename(path)}: задан $ErrorActionPreference')

print('\n[4] backup-vscode: пара реальна, а не просто названа')
sh = 'tools/backup/initial_backup/scripts/backup-vscode.sh'
ps = 'tools/backup/initial_backup/scripts/backup-vscode.ps1'
t(os.path.isfile(sh), f'{sh} существует')
t(os.path.isfile(ps), f'{ps} существует')
if os.path.isfile(sh):
    s = io.open(sh, encoding='utf-8').read()
    t('--dry-run' in s, 'backup-vscode.sh: поддержан --dry-run')
    t('_manifest.sha256.csv' in s, 'backup-vscode.sh: строит манифест SHA256')
    t('.config/Code/User' in s, 'backup-vscode.sh: знает путь Linux')
    t('.vscode/extensions' in s, 'backup-vscode.sh: знает каталог расширений Linux')
    t('exit 3' in s, 'backup-vscode.sh: отдельный код возврата, когда ничего не найдено')
    t('Parная версия' in s or 'Парная версия' in s,
      'backup-vscode.sh: указана парная версия')
    p = io.open(ps, encoding='utf-8').read()
    t('%APPDATA%\\Code\\User' in p, 'backup-vscode.ps1: знает путь Windows')
    t('extensions-list.txt' in s and 'extensions-list.txt' in p,
      'имя списка расширений совпадает в обеих версиях')
    t('_manifest.sha256.csv' in p, 'имя манифеста совпадает в обеих версиях')

print('\n[5] Поле file в manifest.csv (CONVENTIONS.md §4)')
t('**Пустое** для `type=module` и `type=script`' in conv,
  'в §4 описано, что у module/script поле file пустое')
t('SELF_ENTITIES' in conv, 'в §4 названа таблица SELF_ENTITIES как источник состава')
import csv
rows = list(csv.reader(io.open('manifest.csv', encoding='utf-8')))
for r in rows[1:]:
    if r[0] in ('module', 'script'):
        t(r[3] == '', f'{r[2]}: поле file пустое, как описано в §4')
    if r[0] == 'iso':
        t(r[3] != '', f'{r[2]}: у ISO поле file заполнено')

print('\n[6] set -euo pipefail и обоснованность исключения (CONVENTIONS.md §5)')
NO_ERR = {'scripts/repo-validate.sh'}
for path in sh_files:
    rel = os.path.relpath(path, '.')
    s = io.open(path, encoding='utf-8').read()
    if rel in NO_ERR:
        t('set -uo pipefail' in s and 'set -euo pipefail' not in s,
          f'{rel}: -e не включён, как и описано в §5')
        t('-e намеренно не включён' in s,
          f'{rel}: обоснование записано комментарием в файле')
    else:
        t('set -euo pipefail' in s, f'{rel}: включён set -euo pipefail')

print('\n[7] Лог в файл (CONVENTIONS.md §5)')
for path in sh_files:
    s = io.open(path, encoding='utf-8').read()
    rel = os.path.basename(path)
    t('LOG_FILE=' in s, f'{rel}: задан LOG_FILE')
    t('tee -a "$LOG_FILE"' in s, f'{rel}: вывод идёт через tee -a')
    # Process substitution с `wait` в trap виснет, если `set -e` обрывает
    # скрипт внутри функции, а tee ещё жив (проверено: код 124 вместо 1).
    # Поэтому лог ведётся самоперезапуском через конвейер, а код возврата
    # возвращается через PIPESTATUS.
    t('_LOGGED_SELF=1 exec bash "$0" "$@" 2>&1 | tee -a "$LOG_FILE"' in s,
      f'{rel}: лог ведётся самоперезапуском через tee')
    t('exit "${PIPESTATUS[0]}"' in s,
      f'{rel}: код возврата сохраняется через PIPESTATUS')
    t('exec > >(tee' not in s,
      f'{rel}: process substitution с tee не используется')
    t(s.index('LOG_FILE=') > s.index('set -'),
      f'{rel}: блок лога стоит после строки set')
for path in ps_files:
    s = io.open(path, encoding='utf-8').read()
    rel = os.path.basename(path)
    t('Start-Transcript' in s, f'{rel}: ведётся транскрипт')
    t('-Append' in s, f'{rel}: лог дописывается, а не перетирается')
    t('Set-StrictMode -Version Latest' in s,
      f'{rel}: строгий режим включён, иначе необъявленная переменная даёт $null')
    t('PowerShell.Exiting' in s,
      f'{rel}: транскрипт закрывается при exit внутри скрипта')

print('\n[8] SELF-HASH строк module/script свежий')
import importlib.util
spec = importlib.util.spec_from_file_location('cc', 'scripts/csv-check.py')
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)
for r in rows[1:]:
    if r[0] in ('module', 'script'):
        got = cc.self_hash(r[2], '.')
        t(got is not None, f'{r[2]}: файлы сущности на месте')
        if got:
            t(len(r[5]) == 64, f'{r[2]}: в манифесте полный SHA256, а не сокращение')
            t(r[5] == got[0], f'{r[2]}: sha256 совпадает с файлами')
            t(r[6] == str(got[1]), f'{r[2]}: size_bytes совпадает с файлами')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
