# -*- coding: utf-8 -*-
"""Проверки сквозных правил CONVENTIONS.md, которые не покрыты repo-validate.sh.

Появился после вычитки сданных групп: у backup-vscode не было .sh-пары, и
правило дуальности (CONVENTIONS.md, раздел 5) нигде не контролировалось.
"""
import io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # копия репозитория тестирует копию, не оригинал
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

print('\n[9] Раздел 11 «Протокол исполнения» (CONVENTIONS.md §11)')
t('## 11. Протокол исполнения' in conv, 'раздел 11 присутствует')
for i, name in [(1, 'три фазы'), (2, 'обязательный запрос'), (3, 'приоритет источников'),
                (4, 'триггеры запроса'), (5, 'сверка перед push')]:
    t(f'### 11.{i}.' in conv, f'подраздел 11.{i} ({name})')
low = conv.lower()
t('не более трёх итераций' in low or 'не более 3 итераций' in low,
  'предел итераций записан')
# Ссылки на разделы обязаны быть разрешимы: §11 трижды ссылался на
# «раздел 13», которого в файле не было. Проверка сравнивает номер ссылки
# с фактическими заголовками, а не со списком ожидаемых.
heads = {m.group(1) for m in re.finditer(r'(?m)^## (\d+)\.', conv)}
refs = set(re.findall(r'раздел[ае]? (\d+)', conv)) | set(re.findall(r'§(\d+)', conv))
bad_refs = sorted(r for r in refs if r not in heads)
t(not bad_refs, f'все ссылки на разделы разрешимы (битые: {bad_refs or "нет"})')
sub = {m.group(1) for m in re.finditer(r'(?m)^### (\d+\.\d+)\.', conv)}
bad_sub = sorted(r for r in set(re.findall(r'раздел[ае]? (\d+\.\d+)', conv))
                 | set(re.findall(r'§(\d+\.\d+)', conv)) if r not in sub)
t(not bad_sub, f'все ссылки на подразделы разрешимы (битые: {bad_sub or "нет"})')
t('AUDIT' in conv and 'CONSTRUCT' in conv and 'CHRONICLE' in conv,
  'все три фазы названы')
t('git fetch' in conv, 'сверка с remote названа командой')
t('reset --soft' in conv and 'не годится' in conv,
  'обосновано, почему reset --soft не подходит')
for trg in ('Т1', 'Т2'):
    t(trg in conv, f'триггер {trg} определён')

print('\n[10] Раздел 12 «Определение дефекта и пул дефектов» (CONVENTIONS.md §12)')
t('## 12. Определение дефекта и пул дефектов' in conv, 'раздел 12 присутствует')
for i, name in [(1, 'что такое дефект'), (2, 'что не дефект'), (3, 'протокол классификации'),
                (4, 'форма запроса'), (5, 'пул'), (6, 'порог'), (7, 'проверка пула'),
                (8, 'закрытие'), (9, 'один источник')]:
    t(f'### 12.{i}.' in conv, f'подраздел 12.{i} ({name})')
for col in ('id', 'signature', 'n', 'first_seen', 'last_seen', 'fix_target',
            'closes', 'verdict', 'source'):
    t(f'`{col}`' in conv, f'колонка {col} описана в §12.5')
for v in ('automated', 'open', 'wontfix'):
    t(f'`{v}`' in conv, f'вердикт {v} описан')
for ft in ('state', 'doc', 'decision'):
    t(f'`{ft}`' in conv, f'fix_target {ft} описан')
t('n >= 2' in conv, 'порог автоматизации записан как n >= 2')
t('research/bestiary.csv' in conv, 'путь пула назван')
t('tests/test_bestiary.py' in conv, 'проверка пула названа')
t('возвратом дефекта' in conv, 'закрытие определено через возврат дефекта')
# 12.2 обязано перечислять ровно восемь случаев не-дефекта: список и есть
# определение, сокращение списка молча расширяет понятие дефекта.
sec = conv.split('### 12.2.')[1].split('### 12.3.')[0]
n_cases = len(re.findall(r'(?m)^\d+\. \*\*', sec))
t(n_cases == 8, f'в §12.2 ровно восемь случаев не-дефекта (факт {n_cases})')
# 12.1: оба условия должны быть названы, иначе определение неполно
sec1 = conv.split('### 12.1.')[1].split('### 12.2.')[0]
t('**А.**' in sec1 and '**Б.**' in sec1, 'в §12.1 названы оба условия А и Б')
t(sec1.count('|') >= 10, 'в §12.1 есть таблица источников обязательства')
t('с файлом и строкой' in sec1, 'источник требуется назвать с файлом и строкой')

print('\n[11] Раздел 12.9 и tests/baseline.csv согласованы')
t(os.path.isfile('tests/baseline.csv'), 'tests/baseline.csv существует')
t(os.path.isfile('tests/baseline.py'), 'tests/baseline.py существует')
bl = io.open('tests/baseline.py', encoding='utf-8').read()
t('раздел 12' in bl, 'baseline.py ссылается на раздел 12, а не на несуществующий')
sys.path.insert(0, HERE)
from baseline import expected, keys
t(len(keys()) >= 10, f'в baseline.csv не меньше десяти ключей (факт {len(keys())})')
t(expected('manifest_rows') == len(rows) - 1,
  f"baseline.csv manifest_rows совпадает с manifest.csv ({len(rows) - 1})")
print('\n[12] Класс B-10: харнесс не зашивает абсолютный путь')
# Пока 15 тестов держали ROOT литералом с путём рабочей копии, копия проверяла
# оригинал: возврат дефекта на копии (способ закрытия записи пула, раздел
# 12.8) был физически невыполним, а правка baseline.csv копии не меняла
# результат. Проверка держит два свойства: путей нет и корень выводится
# из __file__.
# Образец собирается из частей: записанный литералом, он встречался бы в
# этом самом файле и проверка ловила бы собственный текст и сообщение.
NEEDLE = '/' + os.path.join('home', 'user')


def scan_abs(base, exts):
    hits = []
    for f in sorted(os.listdir(base)):
        if not f.endswith(exts):
            continue
        txt = io.open(os.path.join(base, f), encoding='utf-8').read()
        for i, ln in enumerate(txt.split('\n'), 1):
            if NEEDLE in ln:
                hits.append(f'{f}:{i}')
    return hits


hard = scan_abs('tests', ('.py',))
t(not hard, f'в tests/*.py нет абсолютного пути к рабочей копии (найдено: {hard or "нет"})')
hardsh = scan_abs('scripts', ('.sh', '.ps1', '.py'))
t(not hardsh, f'в scripts/* нет абсолютного пути к рабочей копии (найдено: {hardsh or "нет"})')

for f in sorted(os.listdir('tests')):
    if not (f.startswith('test_') and f.endswith('.py')):
        continue
    txt = io.open(os.path.join('tests', f), encoding='utf-8').read()
    t('os.path.abspath(__file__)' in txt,
      f'{f}: корень выводится из __file__')
    t('os.chdir(ROOT)' in txt,
      f'{f}: тест переходит в свой корень, а не в каталог запуска')

runner_txt = io.open(os.path.join('tests', 'run-all.py'), encoding='utf-8').read()
t('cwd=os.path.dirname(HERE)' in runner_txt,
  'run-all.py передаёт подпроцессам корень репозитория, а не каталог запуска')
t('os.path.join(HERE, name)' in runner_txt,
  'run-all.py собирает путь к тесту от __file__')

# ROOT из окружения обязателен: без него копия в другом каталоге читает
# baseline.csv оригинала, и расходование выглядит как непрошедший возврат.
bl_txt = io.open(os.path.join('tests', 'baseline.py'), encoding='utf-8').read()
t("os.environ.get('ROOT')" in bl_txt,
  'baseline.py уважает ROOT из окружения')
r = subprocess.run([sys.executable, '-c',
                    'import sys; sys.path.insert(0, %r); '
                    'import baseline; print(baseline.BASELINE)' % HERE],
                   capture_output=True, text=True,
                   env={**os.environ, 'ROOT': ROOT})
t(r.stdout.strip() == os.path.join(ROOT, 'tests', 'baseline.csv'),
  f'при ROOT из окружения baseline.csv берётся из него ({r.stdout.strip()})')

print('\n[13] Глубина category и держатели скриптов (CONVENTIONS.md §4)')
# Правило: утилита на втором уровне от корня раздела, исключение - группа os,
# где подкатегория windows делится на подразделы и утилита на третьем уровне.
# Второй и третий признаки из раздела 4 проверяются здесь: состав держателя
# скриптов и разрешение пути tools/<category>/<name>.
BINARY = ('.exe', '.msi', '.msu', '.dll', '.sys', '.zip', '.7z', '.rar', '.gz',
          '.xz', '.iso', '.wim', '.img', '.vhd', '.vhdx', '.efi', '.rom',
          '.bin', '.dat', '.cab', '.deb', '.rpm')
for r in rows[1:]:
    if r[0] != 'tool':
        continue
    name, cat = r[2], r[1]
    if cat.startswith('os/'):
        t(cat.count('/') == 2 and cat.startswith('os/windows/'),
          f'{name}: у группы os category из трёх частей ({cat})')
    else:
        t(cat.count('/') == 1,
          f'{name}: вне группы os category из двух частей ({cat})')
    t(os.path.isdir(os.path.join('tools', cat)),
      f'{name}: каталог подкатегории существует ({cat})')
    t(os.path.isdir(os.path.join('tools', cat, name)),
      f'{name}: каталог утилиты разрешается как tools/{cat}/{name}')

HOLDERS = ('scripts', 'procedures')
holders = 0
for root, dirs, files in os.walk('tools'):
    base = os.path.basename(root)
    if base not in HOLDERS:
        continue
    holders += 1
    rel = os.path.relpath(root, '.')
    t(any(f.endswith(('.sh', '.ps1', '.md')) for f in files),
      f'{rel}: в держателе есть скрипты или процедуры')
    wrong = [f for f in files
             if f.endswith(BINARY) or '.' in f and f.rsplit('.', 1)[1] in
             ('exe', 'msi', 'zip')]
    t(not wrong, f'{rel}: в держателе нет бинарников (найдено {wrong or "нет"})')
    nested = [d for d in dirs if d not in HOLDERS]
    t(not nested, f'{rel}: в держателе нет каталогов утилит (найдено {nested or "нет"})')
t(holders >= 5, f'держателей скриптов найдено не меньше пяти ({holders})')

# Утилита обязана быть каталогом, на который указывает ровно одна строка:
# иначе каталог либо лишний, либо строка указывает не туда.
tool_dirs = {}
for r in rows[1:]:
    if r[0] == 'tool':
        tool_dirs.setdefault(os.path.join('tools', r[1], r[2]).replace(os.sep, '/'), []).append(r[2])
t(all(len(v) == 1 for v in tool_dirs.values()),
  f'на каждый каталог утилиты указывает одна строка (каталогов {len(tool_dirs)})')

print('\n[14] Реестр Strelec согласован с manifest.csv (CONVENTIONS.md §7.2.1)')
# Реестр отвечает на вопрос "есть ли утилита в сборке", от которого зависит
# объём лицензионной сверки. Проверка держит форму и состав: утилита без
# строки в реестре осталась бы без режима сверки.
import csv as _csv
REG = 'tools/strelec-registry.csv'
t(os.path.isfile(REG), f'{REG} существует')
reg_rows = list(_csv.DictReader(io.open(REG, encoding='utf-8')))
REG_COLS = ['name', 'category', 'in_strelec', 'strelec_version',
            'own_copy_reason', 'audit_mode', 'status']
t(list(reg_rows[0].keys()) == REG_COLS, 'заголовок реестра соответствует §7.2.1')
mani_tools = {r[2] for r in rows[1:] if r[0] == 'tool'}
reg_names = {r['name'] for r in reg_rows}
t(reg_names == mani_tools,
  f'реестр покрывает все утилиты манифеста (расхождение {reg_names ^ mani_tools or "нет"})')
for r in reg_rows:
    t(r['in_strelec'] in ('yes', 'no'),
      f"{r['name']}: in_strelec из набора yes/no")
    t(r['audit_mode'] in ('build_version', 'full'),
      f"{r['name']}: audit_mode из набора build_version/full")
    want = 'build_version' if r['in_strelec'] == 'yes' else 'full'
    t(r['audit_mode'] == want,
      f"{r['name']}: режим сверки соответствует признаку присутствия")
    t(bool(r['own_copy_reason'].strip()),
      f"{r['name']}: основание своей копии записано")
    t(bool(r['status'].strip()), f"{r['name']}: состояние записано")
t(os.path.isfile('tools/diagnostics/strelec-tools.md'),
  'источник состава сборки на месте')
src = io.open('tools/diagnostics/strelec-tools.md', encoding='utf-8').read()
t('не сверен с самим образом' in src,
  'в источнике состава сохранена оговорка о том, что он не сверен с ISO')

print('\n[15] Счётчики baseline.csv совпадают с manifest.csv (§12.9)')
# Класс B-01 лечился выносом констант из тестов в baseline.csv. Лечением
# была перенесена только половина: значение стало храниться в одном месте,
# но сравнивалось с фактом один раз — при внесении. Ключ manifest_sha_filled
# простоял с числом 18 от создания файла, пока в манифесте стало 27 строк
# с реальной суммой; расхождение не ловилось ни одним тестом, потому что
# [11] сверял с manifest.csv только manifest_rows.
# Проверка закрывает ровно этот зазор: каждый ключ baseline.csv, который
# выводится из manifest.csv, пересчитывается здесь и сравнивается с файлом.
import csv as _csv2
mrows = list(_csv2.DictReader(io.open('manifest.csv', encoding='utf-8')))
mtype = [r['type'] for r in mrows]


def _filled(r):
    return bool(r['sha256'].strip()) and r['sha256'] != 'PENDING'


DERIVED = {
    'manifest_rows': lambda: len(mrows),
    'manifest_iso': lambda: mtype.count('iso'),
    'manifest_tool': lambda: mtype.count('tool'),
    'manifest_script': lambda: mtype.count('script'),
    'manifest_module': lambda: mtype.count('module'),
    'manifest_sha_filled': lambda: sum(1 for r in mrows if _filled(r)),
    'manifest_planned': lambda: sum(1 for r in mrows
                                    if r['status'] == 'planned'),
    'manifest_present': lambda: sum(1 for r in mrows
                                    if r['status'] == 'present'),
    'manifest_pending_sha': lambda: sum(1 for r in mrows
                                        if r['sha256'] == 'PENDING'),
    'manifest_planned_zero_size': lambda: sum(
        1 for r in mrows
        if r['status'] == 'planned' and r['size_bytes'].strip() in ('', '0')),
}
bl_all = _csv2.DictReader(io.open('tests/baseline.csv', encoding='utf-8'))
bl_map = {r['key'].strip(): int(r['value']) for r in bl_all}
for key in sorted(DERIVED):
    t(key in bl_map, f'ключ {key} объявлен в baseline.csv')
    if key in bl_map:
        fact = DERIVED[key]()
        t(bl_map[key] == fact,
          f'{key} совпадает с manifest.csv (факт {fact}, в файле {bl_map[key]})')
t(sum(1 for r in mrows if r['status'] == 'planned')
  + sum(1 for r in mrows if r['status'] == 'present') == len(mrows),
  'статус каждой строки манифеста — planned или present, третьего нет')
t(bl_map['manifest_pending_sha']
  == bl_map['manifest_rows'] - bl_map['manifest_sha_filled'],
  'sha_filled и pending_sha в сумме дают все строки')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
