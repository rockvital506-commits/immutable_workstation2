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

# Находка N54, класс B-01. test_stage10.py держал факт репозитория
# литералами: '47', '23 утилиты', '16 файлов `.ps1`'. Заголовок проверки
# обещал «числа в сводке совпадают с манифестом», а тело сравнивало сводку
# с числами, которые перестали быть фактом: строк в manifest.csv 46, утилит
# 22, файлов `.ps1` 14. Такая проверка не просто не ловила отставание
# tools/docs/summary.md — она его охраняла, потому что падала бы именно на
# исправленном документе.
# Проверка ниже структурная, а не по конкретному числу: она требует, чтобы
# в сравнении со сводкой не стояло quoted-литерала с цифрой. Значения,
# выведенные из ROWS, подставляются через f-строку и цифр в исходнике не
# содержат, поэтому исправленный код проходит, а возвращённый литерал — нет.
# Регулярка ищет отдельное число, а не цифру внутри слова: `'SHA256'` и
# расширение `.ps1` содержат цифры, но числами не являются. Первая версия
# проверки была наивной — `'[^']*\d[^']*'` — и давала два ложных
# срабатывания именно на них. Разделение проверено на обеих сторонах:
# литералы из 340ff66 ловятся, четыре контроля пропускаются.
_s10 = io.open(os.path.join('tests', 'test_stage10.py'), encoding='utf-8').read()
_num = re.compile(r'(?<![0-9A-Za-z_])\d+(?![0-9A-Za-z_.])')
_lit = []
for _i, _ln in enumerate(_s10.split('\n'), 1):
    if 'in smry' not in _ln:
        continue
    for _q in re.findall(r"'([^']*)'", _ln):
        if _num.search(_q):
            _lit.append(f'{_i}: {_q[:40]}')
t(not _lit,
  'в test_stage10.py нет числа литералом в сравнении со сводкой (§12.9)'
  + ('' if not _lit else f'; найдено {_lit}'))

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

print('\n[16] SHA256 в заглушке равен значению manifest.csv (§2, §4)')
# Класс B-13. Сумма хранилась в двух местах: в manifest.csv и в заглушке
# бинарника. Обновлялось первое, второе оставалось `PENDING` — разошлись
# восемь заглушек, включая VeraCrypt, у которой строка манифеста уже была
# `present`. Пять тестов групп tools/ требовали в заглушке буквального
# 'PENDING' и тем самым запрещали заглушке принять реальную сумму: правка
# манифеста роняла тест, и расхождение выглядело обязательным состоянием.
# Проверка сквозная — по всем строкам tool/iso, а не по подмножеству группы.
SHA_ROW = re.compile(r'\|\s*SHA256\s*\|\s*`?([0-9a-fA-F]{64}|PENDING)`?')
stubs = {}
for base in ('tools', os.path.join('ventoy-partition', 'ISO')):
    for root, dirs, fs in os.walk(base):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for f in fs:
            if f.endswith('.md'):
                stubs[f] = os.path.join(root, f)
mrows2 = list(_csv2.DictReader(io.open('manifest.csv', encoding='utf-8')))
checked = 0
for r in mrows2:
    if r['type'] not in ('tool', 'iso') or not r['file']:
        continue
    key = r['file'] + '.md'
    t(key in stubs, f"{r['name']}: заглушка {key} найдена")
    if key not in stubs:
        continue
    txt = io.open(stubs[key], encoding='utf-8').read()
    m = SHA_ROW.search(txt)
    t(m is not None, f"{r['name']}: в заглушке есть поле SHA256 со значением")
    if not m:
        continue
    checked += 1
    t(m.group(1).lower() == r['sha256'].lower(),
      f"{r['name']}: SHA256 в заглушке равен manifest.csv "
      f"(заглушка {m.group(1)[:12]}, манифест {r['sha256'][:12]})")
t(checked == sum(1 for r in mrows2
                 if r['type'] in ('tool', 'iso') and r['file']),
  f'проверены все строки tool/iso с файлом ({checked})')

print('\n[17] Реестр Strelec: in_strelec подтверждён чтением состава (§7.2.1)')
# Класс B-16. Сверка состава трижды делалась поиском подстроки вместо чтения
# раздела: N14 дал три ложных «в сборке есть» по утилитам из раздела «Чего в
# Strelec нет», N40 и N43 повторили тот же механизм на причинах PENDING.
# Поиск подстроки не различает разделов, а strelec-tools.md перечисляет
# утилиты и в составе, и в списке отсутствующих. Проверка режет документ по
# заголовку «Чего в Strelec нет и что берём из Tools» и читает части отдельно.
# Имя утилиты основанием не служит: MemTest86Plus в документе записан как
# «Memtest86+», поэтому для in_strelec=yes сверяется версия из strelec_version.
_st = io.open(os.path.join('tools', 'diagnostics', 'strelec-tools.md'),
              encoding='utf-8').read().split('\n')
_cut = None
for _i, _l in enumerate(_st):
    if _l.startswith('## Чего в Strelec нет'):
        _cut = _i
        break
t(_cut is not None, 'в strelec-tools.md найден раздел «Чего в Strelec нет»')
_comp = '\n'.join(_st[:_cut]) if _cut else ''
_abs = '\n'.join(_st[_cut:]) if _cut else ''
t(len(_comp) > 0 and len(_abs) > 0,
  f'документ разрезан на состав ({len(_comp)} зн.) и отсутствующие '
  f'({len(_abs)} зн.)')
_VER = re.compile(r'^\d+(?:\.\d+)*$')
_reg = list(_csv2.DictReader(
    io.open(os.path.join('tools', 'strelec-registry.csv'), encoding='utf-8')))
_yes = _no = 0
for r in _reg:
    if r['in_strelec'] == 'yes':
        _yes += 1
        _v = r['strelec_version'].strip()
        if _VER.match(_v):
            t(_v in _comp,
              f"{r['name']}: in_strelec=yes подтверждён версией {_v} в составе")
        else:
            t('не указана' in _v,
              f"{r['name']}: версия в сборке заявлена как неизвестная")
    else:
        _no += 1
        t(r['name'] not in _comp,
          f"{r['name']}: in_strelec=no, в составе сборки имени нет")
t(_yes >= 1 and _no >= 1, f'разобраны обе группы реестра (yes {_yes}, no {_no})')

print('\n[18] Живые счётчики в связном тексте равны пересчёту (§12.5)')
# Класс B-15. Значение живёт в research/bestiary.csv и пересказывается в
# связном тексте: research/24-next-steps.md §1 и research/README.md. Пересказ
# не обновлялся вместе с источником: N44 нашёл в §1 три отставших числа, тот
# же механизм повторился в research/README.md:51 и в индексе §8 того же файла.
# Отличие от B-12 и B-13: пересказ находится не в baseline.csv и не в заглушке
# бинарника, а в тексте плана, и до этой проверки его никто не читал.
_b = list(_csv2.DictReader(
    io.open(os.path.join('research', 'bestiary.csv'), encoding='utf-8')))
_ncls = len(_b)
_last = max(r['id'] for r in _b)
_n24 = io.open(os.path.join('research', '24-next-steps.md'),
               encoding='utf-8').read()
_nrd = io.open(os.path.join('research', 'README.md'), encoding='utf-8').read()
_b09 = [r for r in _b if r['id'] == 'B-09']
t(len(_b09) == 1 and int(_b09[0]['n']) == expected('audit_findings'),
  f"baseline.csv audit_findings равен B-09.n ({expected('audit_findings')})")
_m = re.search(r'\|\s*Находок AUDIT\s*\|\s*(\d+)\s*\|', _n24)
t(_m is not None and int(_m.group(1)) == expected('audit_findings'),
  f"research/24 §1 «Находок AUDIT» равен baseline.csv "
  f"({_m.group(1) if _m else 'строки нет'} против {expected('audit_findings')})")
_m = re.search(r'\|\s*Классов дефектов в пуле\s*\|\s*(\d+),\s*`B-01`…`(B-\d+)`',
               _n24)
t(_m is not None and int(_m.group(1)) == _ncls and _m.group(2) == _last,
  f'research/24 §1 «Классов дефектов» равен bestiary.csv '
  f'({_ncls} классов, последний {_last})')
_m = re.search(r'(\d+)\s+классов\s+`B-01`…`(B-\d+)`', _nrd)
t(_m is not None and int(_m.group(1)) == _ncls and _m.group(2) == _last,
  f'research/README.md «классов B-01…» равен bestiary.csv '
  f'({_ncls} классов, последний {_last})')

# Расширение 2026-10-21, находка N50. До этой правки блок читал только
# значения из bestiary.csv и поэтому пропустил тот же механизм на
# счётчиках, выведенных из manifest.csv: при закрытии A5 строка Prime95
# впервые получила сумму, и обновлён был только tests/baseline.csv.
# Пересказ в research/24 §1 и в tools/docs/flash-verify.md остался на 28
# при факте 29 — восемь живых вхождений в двух файлах. Заголовок блока
# обещал «живые счётчики в связном тексте», а тело сверяло только пул:
# название шире тела, и это само по себе рассинхрон.
_fv = io.open(os.path.join('tools', 'docs', 'flash-verify.md'),
              encoding='utf-8').read()
_n_sha = sum(1 for r in mrows if _filled(r))
_n_pend = sum(1 for r in mrows if r['sha256'] == 'PENDING')
_n_tool_sha = sum(1 for r in mrows if r['type'] == 'tool' and _filled(r))
_n_tool = sum(1 for r in mrows if r['type'] == 'tool')
_n_zero = sum(1 for r in mrows if r['status'] == 'planned'
              and r['size_bytes'].strip() in ('', '0'))
_n_file_sha = sum(1 for r in mrows if r['file'] and _filled(r))
_n_file_pend = sum(1 for r in mrows if r['file'] and not _filled(r))

_m = re.search(r'\|\s*Строк с реальной SHA256\s*\|\s*(\d+)\s*\|', _n24)
t(_m is not None and int(_m.group(1)) == _n_sha,
  f'research/24 §1 «Строк с реальной SHA256» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_sha})")
_m = re.search(r'\|\s*Строк с `sha256=PENDING`\s*\|\s*(\d+)\s*\|', _n24)
t(_m is not None and int(_m.group(1)) == _n_pend,
  f'research/24 §1 «Строк с sha256=PENDING» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_pend})")
_m = re.search(r'\|\s*Утилит с ожидаемой суммой\s*\|\s*(\d+) из (\d+)\s*\|', _n24)
t(_m is not None and int(_m.group(1)) == _n_tool_sha
  and int(_m.group(2)) == _n_tool,
  f'research/24 §1 «Утилит с ожидаемой суммой» равен manifest.csv '
  f"({_m.group(0) if _m else 'строки нет'} против {_n_tool_sha} из {_n_tool})")
_m = re.search(r'\|\s*`planned` с `size_bytes=0`\s*\|\s*(\d+)\s*\|', _n24)
t(_m is not None and int(_m.group(1)) == _n_zero,
  f'research/24 §1 «planned с size_bytes=0» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_zero})")

# tools/docs/flash-verify.md — второй пересказ того же факта
_m = re.search(r'Строки с заполненной ожидаемой суммой — (\d+)\.', _fv)
t(_m is not None and int(_m.group(1)) == _n_sha,
  f'flash-verify.md «строк с ожидаемой суммой» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_sha})")
_m = re.search(r'\|\s*Итого сверяемых\s*\|\s*\*\*(\d+)\*\*', _fv)
t(_m is not None and int(_m.group(1)) == _n_sha,
  f'flash-verify.md «Итого сверяемых» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_sha})")
_m = re.search(r'поле `file` заполнено, сумма есть\s*\|\s*\*\*(\d+)\*\*'
               r'\s*\(1 `iso` \+ (\d+) `tool`\)', _fv)
t(_m is not None and int(_m.group(1)) == _n_file_sha
  and int(_m.group(2)) == _n_tool_sha,
  f'flash-verify.md «file заполнен и сумма есть» равен manifest.csv '
  f"({_m.group(0) if _m else 'строки нет'} против {_n_file_sha} "
  f'и {_n_tool_sha} tool)')
_m = re.search(r'\|\s*`file` заполнено, сумма `PENDING`\s*\|\s*\*\*(\d+)\*\*', _fv)
t(_m is not None and int(_m.group(1)) == _n_file_pend,
  f'flash-verify.md «file заполнено, сумма PENDING» равен manifest.csv '
  f"({_m.group(1) if _m else 'строки нет'} против {_n_file_pend})")

# Расширение 2026-10-21, находка N52. Таблица §1 держит одиннадцать строк
# живых счётчиков, а блок читал семь. Четыре оставались непокрытыми, и урок
# N52 здесь прямой: «Сумма есть, размера нет» держит не только число, но и
# разбивку «6 утилит + 1 образ» и перечень имён. Такие связанные значения
# расходятся с источником и тогда, когда само число верно, — N52 выросла
# именно на непокрытой строке §2.2. Строки разбираются по ячейкам, а не
# регуляркой по метке: в метках есть бэктики и скобки.
def _row24(label):
    for _ln in _n24.split('\n'):
        if _ln.startswith('| ' + label + ' |'):
            return [c.strip() for c in _ln.strip().strip('|').split('|')]
    return None

def _names24(cell):
    return sorted(re.findall(r'`([^`]+)`', cell or ''))

_n_all = len(mrows)
_n_pres = sum(1 for r in mrows if r['status'] == 'present')
_n_plan = sum(1 for r in mrows if r['status'] == 'planned')
_pres_ok = lambda r: (_filled(r) and r['size_bytes'].strip() not in ('', '0'))
_f_tool_pres = sorted(r['name'] for r in mrows
                      if r['type'] == 'tool' and r['status'] == 'present'
                      and _pres_ok(r))
_f_nosize = sorted(r['name'] for r in mrows
                   if _filled(r) and r['size_bytes'].strip() in ('', '0'))
_f_nosize_tool = [n for n in _f_nosize
                  if any(r['name'] == n and r['type'] == 'tool' for r in mrows)]
_f_nosize_iso = [n for n in _f_nosize
                 if any(r['name'] == n and r['type'] == 'iso' for r in mrows)]

_c = _row24('Строк в `manifest.csv`')
_m = re.search(r'^(\d+)$', (_c or [''])[1] if _c else '')
t(_m is not None and int(_m.group(1)) == _n_all,
  f'research/24 §1 «Строк в manifest.csv» равен manifest.csv '
  f'({_m.group(1) if _m else "строки нет"} против {_n_all})')

_c = _row24('`present` / `planned`')
_m = re.search(r'^(\d+)\s*/\s*(\d+)$', (_c or [''])[1] if _c else '')
t(_m is not None and int(_m.group(1)) == _n_pres
  and int(_m.group(2)) == _n_plan,
  f'research/24 §1 «present / planned» равен manifest.csv '
  f'({_m.group(0) if _m else "строки нет"} против {_n_pres} / {_n_plan})')

_c = _row24('Утилит в `present` (сумма + размер)')
_m = re.search(r'^(\d+)$', (_c or [''])[1] if _c else '')
t(_m is not None and int(_m.group(1)) == len(_f_tool_pres),
  f'research/24 §1 «Утилит в present» равен manifest.csv '
  f'({_m.group(1) if _m else "строки нет"} против {len(_f_tool_pres)})')
t(_c is not None and _names24(_c[2] if len(_c) > 2 else '') == _f_tool_pres,
  f'research/24 §1 перечень утилит в present равен manifest.csv '
  f'({len(_f_tool_pres)} имён)'
  + ('' if _c and _names24(_c[2] if len(_c) > 2 else '') == _f_tool_pres
     else f'; факт {_f_tool_pres}'))

_c = _row24('Сумма есть, размера нет')
_m = re.search(r'^(\d+)$', (_c or [''])[1] if _c else '')
t(_m is not None and int(_m.group(1)) == len(_f_nosize),
  f'research/24 §1 «Сумма есть, размера нет» равен manifest.csv '
  f'({_m.group(1) if _m else "строки нет"} против {len(_f_nosize)})')
_mb = re.search(r'(\d+)\s+утилит\s*\(.*?\)\s*\+\s*(\d+)\s+образ',
                (_c or [''])[2] if _c and len(_c) > 2 else '')
t(_mb is not None and int(_mb.group(1)) == len(_f_nosize_tool)
  and int(_mb.group(2)) == len(_f_nosize_iso),
  f'research/24 §1 разбивка «N утилит + M образ» равна manifest.csv '
  f'({_mb.group(0) if _mb else "нет"} против {len(_f_nosize_tool)} утилит '
  f'+ {len(_f_nosize_iso)} образ)')
t(_c is not None and _names24(_c[2] if len(_c) > 2 else '') == _f_nosize,
  f'research/24 §1 перечень «сумма есть, размера нет» равен manifest.csv '
  f'({len(_f_nosize)} имён)'
  + ('' if _c and _names24(_c[2] if len(_c) > 2 else '') == _f_nosize
     else f'; факт {_f_nosize}'))

# Порог ниже — защита от холостого прохода: если регулярки перестанут
# совпадать из-за правки формулировки, проверки выше упрутся в `None`
# и упадут, но этот порог называет причину прямо.
_n_cnt = len(re.findall(r'\|\s*(?:Строк с реальной SHA256|'
                        r'Строк с `sha256=PENDING`|'
                        r'Утилит с ожидаемой суммой|'
                        r'`planned` с `size_bytes=0`)\s*\|', _n24))
_n_cnt += sum(1 for _lb in ('Строк в `manifest.csv`', '`present` / `planned`',
                            'Утилит в `present` (сумма + размер)',
                            'Сумма есть, размера нет')
              if _row24(_lb) is not None)
t(_n_cnt == 8,
  f'в §1 найдены все восемь строк счётчиков, а не часть ({_n_cnt} из 8)')

# Решение владельца 2026-10-21 по N51, вариант A. Строка «Прогоны» в §1
# пересказывала числа, которые выводит сам прогон, и устаревала четыре раза:
# 186/0, 456/0, 767/0 и 800/0 против факта 809/0. Проверить её изнутри
# набора нельзя — проверка в test_rules.py меняет число проверок
# test_rules.py, то есть сверяемое значение. §12.9 вынести такие значения в
# baseline.csv запрещает прямо: «значения, которые тест вычисляет сам и
# сравнивает между собой» туда не кладутся. Поэтому лечением стал отказ от
# второго источника: числа из строки убраны, а проверка ниже не даёт им
# вернуться. Первая проверка требует наличия строки, чтобы её удаление не
# выглядело исполнением правила.
_pg = re.search(r'^\|\s*Прогоны\s*\|(.*)$', _n24, re.M)
t(_pg is not None, 'строка «Прогоны» в §1 research/24 присутствует')
if _pg:
    _vol = re.findall(r'\d+\s*/\s*\d+', _pg.group(1))
    t(not _vol,
      'строка «Прогоны» не содержит летучих чисел вида N/M '
      f'(решение владельца 2026-10-21 по N51); найдено: {_vol}')

# Находка N52. Правка N50 заменила в §2.2 «18 строк без суммы» на 17, но
# оставила связанное «Остальные 12 — утилиты» и список из двенадцати имён в
# том же предложении. Число 12 было верным до A5: строка Prime95 получила
# сумму, и утилит без суммы осталось одиннадцать. Предложение стало
# арифметически несходным — 6 + 12 против заявленных 17.
# Ценность проверки в том, что первые два утверждения не требуют внешнего
# источника: несоответствие видно из самого текста. Третье сверяет состав
# списка с manifest.csv, чтобы список не отстал от факта молча.
_m_tot = re.search(r'Осталось (\d+) строк без суммы\. Из них (\d+) — ISO', _n24)
_m_ut = re.search(r'Остальные (\d+) — утилиты', _n24)
_m_lst = re.search(r'Все (\d+):((?:(?!Двенадцатой|Тринадцатой).)*?)\.\s',
                   _n24, re.S)
t(_m_tot is not None and _m_ut is not None and _m_lst is not None,
  'в §2.2 найдены все три части утверждения о строках без суммы')
if _m_tot and _m_ut and _m_lst:
    _tot, _iso = int(_m_tot.group(1)), int(_m_tot.group(2))
    _utl = int(_m_ut.group(1))
    _dcl = int(_m_lst.group(1))
    _nms = re.findall(r'`([^`]+)`', _m_lst.group(2))
    t(_iso + _utl == _tot,
      f'§2.2 сходится арифметически: {_iso} ISO + {_utl} утилит = {_tot} '
      f'(заявлено {_tot})')
    t(_dcl == len(_nms),
      f'§2.2 «Все {_dcl}» равно числу имён в списке ({len(_nms)})')
    _fact_ut = sorted(r['name'] for r in mrows
                      if r['sha256'] == 'PENDING' and r['type'] == 'tool')
    t(sorted(_nms) == _fact_ut,
      f'§2.2 список утилит без суммы равен manifest.csv ({len(_fact_ut)} имён)'
      + ('' if sorted(_nms) == _fact_ut else
         f'; лишние {sorted(set(_nms) - set(_fact_ut))}, '
         f'пропущены {sorted(set(_fact_ut) - set(_nms))}'))
    t(_utl == len(_fact_ut),
      f'§2.2 число утилит без суммы равно manifest.csv '
      f'({_utl} против {len(_fact_ut)})')

# Находка N53, класс B-15. tools/docs/summary.md объявляет в шапке: «Все
# числа взяты подсчётом по файлам репозитория и строкам manifest.csv на
# дату сверки. Если файл изменён — пересчитайте, не переписывайте от руки».
# Документ живой по собственному объявлению, но его числа не сверял ни один
# прогон: test_stage10.py сводку читал, однако сравнивал её с литералами, а
# не с манифестом (находка N54). Одиннадцать значений отстали — 47 строк
# при 46, 23 утилиты при 22, 30 planned при 25, 155 файлов .md при 163,
# 21 исследование при 27, 16 тестов при 19, 16 файлов .ps1 при 14, и в
# tools/docs/README.md 28 строк с суммой при 29 и 18 PENDING при 17.
_smry = io.open(os.path.join('tools', 'docs', 'summary.md'),
                encoding='utf-8').read()
_drd = io.open(os.path.join('tools', 'docs', 'README.md'),
               encoding='utf-8').read()
_drd_f = re.sub(r'\s+', ' ', _drd)

# Счётчики файлов считаются здесь же: по §12.9 самовычисляемое значение в
# baseline.csv не кладётся. Обход excludes .git и __pycache__, иначе счёт
# расходится с git ls-files на артефактах прогона.
_cnt = {'ps1': 0, 'md': 0, 'readme': 0, 'research': 0, 'tests': 0}
for _r, _d, _fs in os.walk('.'):
    _d[:] = [x for x in _d if x not in {'.git', '__pycache__'}]
    for _f in _fs:
        _p = os.path.join(_r, _f)[2:]
        if _f.endswith('.ps1'):
            _cnt['ps1'] += 1
        if _f.endswith('.md'):
            _cnt['md'] += 1
            if os.path.basename(_f) == 'README.md':
                _cnt['readme'] += 1
            if _p.startswith('research/'):
                _cnt['research'] += 1
        if _p.startswith('tests/test_') and _f.endswith('.py'):
            _cnt['tests'] += 1


def _snum(pattern, text, label, fact):
    _mm = re.search(pattern, text)
    t(_mm is not None and int(_mm.group(1)) == fact,
      f'summary.md «{label}» равен пересчёту '
      f'({_mm.group(1) if _mm else "строки нет"} против {fact})')


_snum(r'\((\d+) строк данных\)', _smry, 'строк данных', len(mrows))
_snum(r'### Утилиты \((\d+)\)', _smry, 'Утилиты', _n_tool)
_snum(r'\*\*Всего (\d+) утилиты', _smry, 'Всего утилиты', _n_tool)
_snum(r'все (\d+) файлов со статусом `planned`', _smry,
      'planned-файлов', _n_plan)
_snum(r'\*\*Скачать (\d+) файлов\*\*', _smry, 'Скачать файлов', _n_plan)
_snum(r'сверить все (\d+) сумм', _smry, 'сумм к сверке', _n_sha)
_snum(r'\| Файлов `\.md` \| (\d+) \|', _smry, 'Файлов .md', _cnt['md'])
_snum(r'\| Файлов `README\.md` \| (\d+) \|', _smry,
      'Файлов README.md', _cnt['readme'])
_snum(r'\| Исследований в `research/` \| (\d+) \|', _smry,
      'Исследований в research/', _cnt['research'])
_snum(r'\| Тестов в `tests/` \| (\d+) \|', _smry, 'Тестов в tests/',
      _cnt['tests'])
_snum(r'\| Все (\d+) файлов `\.ps1` \|', _smry, 'файлов .ps1', _cnt['ps1'])

# Таблица §2 сверяется по типам: у каждой строки три числа, и расхождение
# в любом из них — тот же механизм. Именно здесь сводка держала
# tool 23/0/23 при факте 22/4/18 и script 11/0/11 при факте 11/11/0.
for _ty in ('iso', 'tool', 'script', 'module'):
    _sub = [r for r in mrows if r['type'] == _ty]
    _fp = sum(1 for r in _sub if r['status'] == 'present')
    _fl = sum(1 for r in _sub if r['status'] == 'planned')
    _mt = re.search(r'\| `' + _ty + r'` \| (\d+) \| (\d+) \| (\d+) \|', _smry)
    t(_mt is not None and int(_mt.group(1)) == len(_sub)
      and int(_mt.group(2)) == _fp and int(_mt.group(3)) == _fl,
      f'summary.md строка `{_ty}` равна manifest.csv '
      f'({_mt.group(0) if _mt else "строки нет"} '
      f'против {_ty} {len(_sub)} / {_fp} / {_fl})')

_mi = re.search(r'\| \*\*Итого\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\* '
                r'\| \*\*(\d+)\*\* \|', _smry)
t(_mi is not None and int(_mi.group(1)) == len(mrows)
  and int(_mi.group(2)) == _n_pres and int(_mi.group(3)) == _n_plan,
  f'summary.md строка «Итого» равна manifest.csv '
  f'({_mi.group(0) if _mi else "строки нет"} '
  f'против {len(mrows)} / {_n_pres} / {_n_plan})')

# tools/docs/README.md — второй пересказ тех же двух чисел
_md = re.search(r'покрыты (\d+) строк с суммой и почему (\d+) строк', _drd_f)
t(_md is not None and int(_md.group(1)) == _n_sha
  and int(_md.group(2)) == _n_pend,
  f'tools/docs/README.md «строк с суммой / PENDING» равен manifest.csv '
  f'({_md.group(0) if _md else "строки нет"} против {_n_sha} / {_n_pend})')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
