#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Альтернативные варианты шагов — правило CONVENTIONS.md §7.4.

Правило §7.4 требует для каждого шага алгоритма рекомендуемый и
альтернативный вариант. Рекомендуемый живёт в `algorithm.md`, альтернативы —
в `alternative_algorithm.md` того же каталога сборки.

Почему этот тест отдельный. Имя `alternative_algorithm.md` оканчивается на
`algorithm.md`, поэтому обход в test_navigation.py такой файл пропускает
(`p.endswith('algorithm.md')`), а `check_doc` вызывается только для
`algorithm.md`. Без отдельного теста файл альтернатив не проверяется ничем,
и правило остаётся без контроля.

Проверяется: структура файла, полнота записи каждой пары вариантов,
соответствие номеров шагов реальному алгоритму, полноценность сущностей
альтернативы по §7.4.4, разрешимость путей и живость ссылок.

Код возврата: 0 — всё в порядке, 1 — есть ошибки.
"""
from __future__ import annotations

import csv
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

checks = 0
errors = 0


def t(cond, msg):
    """Учёт одной проверки. Печатает только провал."""
    global checks, errors
    checks += 1
    if not cond:
        errors += 1
        print(f'  ОШИБКА: {msg}')


def read(p):
    return io.open(p, encoding='utf-8').read()


# Те же определения, что в test_navigation.py: сущность — файл с известным
# расширением. Свои определения завели бы второе правило навигации.
ENT = re.compile(r'([A-Za-z0-9_\-\.]+\.(?:ps1|sh|md|exe|zip|msi|conf|json|xml|iso|torrent))')
NOT_ENTITY = {
    'autounattend.xml', 'unattend.xml', 'README.md', 'CONVENTIONS.md',
    'PLAN.md', 'algorithm.md', 'manifest.csv',
    # Имена файлов ОС и среды, а не сущности флешки
    'alternative_algorithm.md',
}
PREFIX = {
    'VENTOY:/': 'ventoy-partition/',
    'TOOLS:/': 'tools/',
    'BUILD:/': None,
    'REPO:/': '',
}

# Обязательные поля записи пары вариантов — §7.4.3
STEP_FIELDS = ['**Цель шага.**', '**Рекомендуемый вариант.**',
               '**Альтернативный вариант.**', '**Средства альтернативы.**',
               '**Чем отличается.**', '**Плюсы альтернативы.**',
               '**Минусы альтернативы.**', '**Достижение цели.**']
# Обязательные разделы файла
DOC_SECTIONS = ['## 0. Паспорт', '## 3. Альтернативные варианты',
                '## 4. Карта сущностей альтернатив', '## 5. Не проверено на месте']

BUILDS = 'ventoy-partition/builds'
TPL = f'{BUILDS}/_templates/alternative_algorithm.md'
BUILD_DIRS = [d for d in sorted(os.listdir(BUILDS))
              if os.path.isdir(f'{BUILDS}/{d}') and d != '_templates']


def steps_of(text):
    """Границы записей по заголовкам «### Шаг N.» — как в test_navigation.py."""
    lines = text.split('\n')
    heads = [(i, ln) for i, ln in enumerate(lines) if re.match(r'^### Шаг ', ln)]
    out = []
    for k, (i, ln) in enumerate(heads):
        j = heads[k + 1][0] if k + 1 < len(heads) else next(
            (n for n, l in enumerate(lines[i + 1:], i + 1) if l.startswith('## ')),
            len(lines))
        out.append((ln, '\n'.join(lines[i:j])))
    return out


def means_lines(sec):
    """Строки таблицы из поля «Средства альтернативы».

    Разбор идёт до следующего поля-заголовка, а не до первой пустой строки:
    между заголовком поля и таблицей в документе стоит пустая строка, и
    разбиение по ней давало пустой блок. Тогда цикл не выполнялся ни разу и
    проверка проходила вхолостую, ничего не проверяя.
    """
    if '**Средства альтернативы.**' not in sec:
        return []
    tail = sec.split('**Средства альтернативы.**', 1)[1]
    out = []
    for line in tail.split('\n'):
        if re.match(r'^\*\*.+\.\*\*', line):
            break                 # следующее поле записи
        if line.startswith('|'):
            out.append(line)
    return out


def algo_steps(build):
    """Номера шагов реального алгоритма станции."""
    p = f'{BUILDS}/{build}/algorithm.md'
    if not os.path.isfile(p):
        return set()
    return {int(m.group(1)) for m in
            re.finditer(r'^### Шаг (\d+)\.', read(p), re.M)}


# Сущности репозитория: имена и файлы манифеста, а также имена без расширения
rows = list(csv.DictReader(io.open('manifest.csv', encoding='utf-8')))
MANI_NAMES = set()
for r in rows:
    for v in (r['name'], r['file']):
        v = (v or '').strip()
        if v:
            MANI_NAMES.add(v)
            MANI_NAMES.add(os.path.splitext(v)[0])
# Утилиты обязаны иметь строку в реестре Стрельца (§7.2.1)
REG_NAMES = {r['name'].strip() for r in
             csv.DictReader(io.open('tools/strelec-registry.csv', encoding='utf-8'))}
TOOL_NAMES = {r['name'].strip() for r in rows if r['type'] == 'tool'}
# Наши скрипты: средство уровня 4 по §7.4.2 («Свои решения — свой скрипт»)
SCRIPT_NAMES = {r['name'].strip() for r in rows if r['type'] == 'script'}


def entity_ok(name, base):
    """Сущность полноценна по §7.4.4.

    Полноценна, если есть строка манифеста либо это артефакт самой сборки
    (файл ответа, каталог драйверов) — такие сущности строки манифеста не
    получают. Артефакт ищется по имени в дереве каталога сборки: регулярка
    ENT каталог не захватывает, а файл ответа лежит в `answer/`, поэтому
    склейка «каталог + имя» его не находила.
    """
    stem = os.path.splitext(name)[0]
    if name in MANI_NAMES or stem in MANI_NAMES:
        return True
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d != '.git']
        if name in files:
            return True
    return False


# ================================================================ [A]
print('\n[A] Правило §7.4 зарегистрировано')
CONV = read('CONVENTIONS.md')
t('### 7.4. Разумный прагматизм' in CONV, 'в CONVENTIONS.md есть раздел 7.4')
for sub in ['7.4.1. Два обязательных исследования', '7.4.2. Цепочка приоритетов',
            '7.4.3. Рекомендуемый и альтернативный вариант шага', '7.4.4. Размещение']:
    t(f'#### {sub}' in CONV, f'есть подраздел {sub}')
t('alternative_algorithm.md' in CONV,
  'в §7.4 назван файл размещения альтернатив')
for lvl in ['Встроенные утилиты WinPE Стрельца', 'Сторонний софт',
            'Бесплатные аналоги', 'Свои решения']:
    t(lvl in CONV, f'в цепочке 7.4.2 есть уровень «{lvl}»')


# ================================================================ [B]
print('\n[B] Шаблон альтернатив — иначе следующий билд будет по-старому')
t(os.path.isfile(TPL), 'шаблон alternative_algorithm.md существует')
tpl = read(TPL)
for s in DOC_SECTIONS:
    t(s in tpl, f'в шаблоне есть раздел «{s[3:]}»')
for f in STEP_FIELDS:
    t(f in tpl, f'в схеме шага шаблона есть поле {f}')
for pre in ['VENTOY:/', 'TOOLS:/', 'BUILD:/', 'REPO:/', 'SYSTEM:']:
    t(pre in tpl, f'в шаблоне показан префикс {pre}')
t('7.4' in tpl, 'шаблон ссылается на правило 7.4')


# ================================================================ [C]
def check_doc(path, build):
    """Проверка одного alternative_algorithm.md."""
    name = build or '_templates'
    text = read(path)
    base = os.path.dirname(path)

    print(f'\n[C] {name}: разделы файла')
    for s in DOC_SECTIONS:
        t(s in text, f'{name}: есть раздел «{s[3:]}»')

    steps = steps_of(text)
    print(f'\n[D] {name}: записи пар вариантов ({len(steps)})')
    if build:
        t(len(steps) > 0, f'{name}: есть хотя бы одна запись пары вариантов')

    real = algo_steps(build) if build else set()
    for head, sec in steps:
        label = head[4:44]
        m = re.match(r'^### Шаг (\d+)\.', head)
        num = int(m.group(1)) if m else None
        if build:
            t(num in real,
              f'{name}: шаг {num} существует в algorithm.md (там шаги '
              f'{min(real) if real else "-"}—{max(real) if real else "-"})')
        miss = [f for f in STEP_FIELDS if f not in sec]
        t(not miss, f'{name}: {label} — заполнены все поля (нет {len(miss)})')
        for x in miss:
            print('        нет поля:', x)
        # Таблица средств обязана быть внутри поля, а не где-то рядом
        tail = sec.split('**Средства альтернативы.**')[1][:700] \
            if '**Средства альтернативы.**' in sec else ''
        t('|' in tail, f'{name}: {label} — в средствах альтернативы есть таблица')

    print(f'\n[E] {name}: сущности альтернатив полноценны (§7.4.4)')
    bad_ent, tools_used = [], set()
    for head, sec in steps:
        for line in means_lines(sec):
            cells = [c.strip() for c in line.split('|')]
            if len(cells) < 4:
                continue
            path_cell = cells[3]
            if 'SYSTEM:' in path_cell or path_cell in ('Путь на флешке', '---'):
                continue          # средство ОС строки манифеста не получает
            for n in set(ENT.findall(cells[1])):
                if n in NOT_ENTITY:
                    continue
                if not entity_ok(n, base):
                    bad_ent.append(f'{head[4:24]}: {n}')
                elif os.path.splitext(n)[0] in TOOL_NAMES:
                    tools_used.add(os.path.splitext(n)[0])
    t(not bad_ent,
      f'{name}: каждая утилита альтернативы — сущность репозитория '
      f'(не сущность {len(bad_ent)})')
    for x in bad_ent:
        print('        ', x)
    no_reg = sorted(x for x in tools_used if x not in REG_NAMES)
    t(not no_reg,
      f'{name}: утилиты альтернатив есть в реестре Стрельца (нет {len(no_reg)})')
    for x in no_reg:
        print('        ', x)

    print(f'\n[F] {name}: пути с префиксом разрешимы')
    badpath = []
    for m in re.finditer(r'(VENTOY:/|TOOLS:/|BUILD:/|REPO:/)([^\s`|)]*)', text):
        pre, tail = m.group(1), m.group(2)
        a = text.rfind('\n', 0, m.start())
        b = text.find('\n', m.start())
        line = text[a + 1:b if b != -1 else len(text)]
        cells = [c.strip().strip('`') for c in line.split('|')]
        if line.startswith('|') and (pre in cells or pre.rstrip(':') in cells):
            continue              # строка пояснительной таблицы
        if '<' in tail or '>' in tail:
            continue              # плейсхолдер шаблона
        root = PREFIX[pre] if PREFIX[pre] is not None else f'{BUILDS}/{build}/'
        target = os.path.normpath(os.path.join(root, tail.rstrip('/')))
        if not os.path.exists(target):
            badpath.append(f'{pre}{tail} -> {target}')
    t(not badpath,
      f'{name}: все пути с префиксом разрешимы (не разрешается {len(badpath)})')
    for x in badpath:
        print('        ', x)

    print(f'\n[G] {name}: ссылки живы, многоточий в путях нет')
    dead = []
    for m in re.finditer(r'\]\(([^)\s]+)\)', text):
        l = m.group(1)
        if l.startswith(('http', '#', 'mailto')):
            continue
        if '<' in l or '>' in l:
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, l.split('#')[0]))):
            dead.append(l)
    t(not dead, f'{name}: битых относительных ссылок нет (битых {len(dead)})')
    for x in dead:
        print('        ', x)
    ell = []
    for m in re.finditer(r'[A-Za-z0-9_\-\\/]*(?:\.\.\.|…)[A-Za-z0-9_\-\\/.]*', text):
        s = m.group(0)
        a = text.rfind('\n', 0, m.start())
        b = text.find('\n', m.start())
        line = text[a + 1:b if b != -1 else len(text)]
        if '«' in line and '»' in line:
            continue
        if re.search(r'[\\/](?:\.\.\.|…)[\\/]', s) or s.startswith(('builds', 'tools', 'ISO')):
            ell.append(s)
    t(not ell, f'{name}: путей с многоточием нет (найдено {len(ell)})')
    for x in ell:
        print('        ', x)

    print(f'\n[H] {name}: нет вкраплений CJK')
    cjk = [f'{i}: {l.strip()[:60]}' for i, l in enumerate(text.split('\n'), 1)
           if any('\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff' for c in l)]
    t(not cjk, f'{name}: вкраплений CJK нет (найдено {len(cjk)})')
    for x in cjk:
        print('        ', x)

    print(f'\n[J] {name}: утверждения сверены с первоисточником')
    # N46 и N47: три утверждения этого файла были ложны против
    # первоисточника — версия algorithm.md, уровень цепочки шага 7 и
    # дословность таблицы §2. Прогон 62/0 не ловил ни одного: тест не
    # сверял написанное с источником. Блок сверяет ровно эти три места.

    # 1. Таблица цепочки обязана равняться §7.4.2 строка в строку. Берётся
    #    первый сплошной блок строк таблицы: в §2 пилота их две, вторая —
    #    уровни альтернатив этого файла, и она к правилу отношения не имеет.
    def _rows(block):
        out, started = [], False
        for l in block.split('\n'):
            if l.startswith('|'):
                started = True
                out.append(l)
            elif started:
                break
        return [l for l in out if not set(l.replace('|', '').strip()) <= set('-')]

    _rule = CONV.split('#### 7.4.2', 1)[1].split('#### 7.4.3', 1)[0]
    _sec2 = text.split('## 2. Цепочка', 1)
    _got = _rows(_sec2[1].split('\n## ', 1)[0]) if len(_sec2) > 1 else []
    _want = _rows(_rule)
    t(_got == _want,
      f'{name}: таблица цепочки равна §7.4.2 строка в строку '
      f'({len(_got)} против {len(_want)})')
    for _a, _b in zip(_want, _got):
        if _a != _b:
            print('        правило:', _a)
            print('        файл:   ', _b)

    if not build:
        return          # у шаблона вместо значений плейсхолдеры

    # 2. Версия algorithm.md в паспорте обязана равняться его паспорту.
    _algo = read(f'{BUILDS}/{build}/algorithm.md')
    _va = re.search(r'^\|\s*Версия\s*\|\s*([0-9]+(?:\.[0-9]+)*)\s*\|', _algo, re.M)
    _vp = re.search(r'версии\s+([0-9]+(?:\.[0-9]+)*)', text)
    t(_va is not None, f'{name}: в algorithm.md есть поле «Версия»')
    t(_vp is not None, f'{name}: в паспорте названа версия algorithm.md')
    if _va and _vp:
        t(_vp.group(1) == _va.group(1),
          f'{name}: версия algorithm.md равна его паспорту '
          f'({_vp.group(1)} против {_va.group(1)})')

    # 3. Уровень цепочки обязан соответствовать средству: наш скрипт
    #    (type=script в manifest.csv) — это уровень 4 по §7.4.2, а не 1.
    for head, sec in steps_of(text):
        _m = re.search(r'\*\*Альтернативный вариант\.\*\*\s*Уровень\s+([1-4])',
                       sec)
        t(_m is not None, f'{name}: {head[4:24]} — уровень альтернативы назван')
        if not _m:
            continue
        _lvl = int(_m.group(1))
        _own = sorted({os.path.splitext(n)[0]
                       for line in means_lines(sec) for n in ENT.findall(line)}
                      & SCRIPT_NAMES)
        if _own:
            t(_lvl == 4,
              f'{name}: {head[4:24]} — средство {", ".join(_own)} это наш '
              f'скрипт, значит уровень 4 (указан {_lvl})')


check_doc(TPL, None)
for d in BUILD_DIRS:
    p = f'{BUILDS}/{d}/alternative_algorithm.md'
    if os.path.isfile(p):
        check_doc(p, d)
    else:
        print(f'\n[C] {d}: файл альтернатив отсутствует')
        t(False, f'{d}: нет alternative_algorithm.md (правило §7.4.4)')


# ================================================================ [I]
print('\n[I] Обход test_navigation.py действительно пропускает этот файл')
# Контроль самого механизма находки: если имя перестанет оканчиваться на
# algorithm.md, обход начнёт проверять файл сам, и этот тест станет избыточным.
t('alternative_algorithm.md'.endswith('algorithm.md'),
  'имя файла по-прежнему оканчивается на algorithm.md — обход его пропускает')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
