# -*- coding: utf-8 -*-
"""Проверка пула дефектов — CONVENTIONS.md раздел 12.

Зачем. До 2026-10-15 в репозитории было 48 задокументированных находок AUDIT
и ни одной записи о повторяющемся дефекте. Один и тот же класс («факт
зашит константой») падал 11 раз, потому что ничто не требовало после второго
падения ставить проверку. Пул вводит порог: n >= 2 влечёт проверку в tests/.

Этот файл проверяет сам пул, а не продукт. Продукт ловят проверки, названные
в колонке closes; здесь контролируется, что они названы, существуют и
зарегистрированы, иначе порог из раздела 12.6 остаётся словами.
"""
import csv, io, os, re, sys

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


COLS = ['id', 'signature', 'n', 'first_seen', 'last_seen',
        'fix_target', 'closes', 'verdict', 'source']
FIX = {'state', 'doc', 'decision'}
VERDICTS = {'automated', 'open', 'wontfix'}
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
BID = re.compile(r'^B-\d{2}$')
POOL = 'research/bestiary.csv'

print('[1] Файл пула и его заголовок')
t(os.path.isfile(POOL), f'{POOL} существует')
raw = io.open(POOL, encoding='utf-8').read()
head = raw.split('\n', 1)[0].strip()
t(head == ','.join(COLS), 'заголовок соответствует CONVENTIONS.md 12.5')
t(raw.endswith('\n'), 'файл заканчивается переводом строки')
t('\r' not in raw, 'нет CRLF: разделитель остаётся запятой')

rows = list(csv.DictReader(io.open(POOL, encoding='utf-8')))
t(len(rows) > 0, f'в пуле есть записи ({len(rows)})')

print('\n[2] Форма каждой записи')
seen = set()
for r in rows:
    rid = r['id']
    t(BID.match(rid) is not None, f'{rid}: идентификатор вида B-NN')
    t(rid not in seen, f'{rid}: идентификатор уникален')
    seen.add(rid)
    t(bool(r['signature'].strip()), f'{rid}: признак класса заполнен')
    t(r['signature'].count(',') == 0, f'{rid}: признак без запятой, csv не ломается')
    t(r['n'].isdigit() and int(r['n']) >= 1, f'{rid}: n целое и не меньше 1')
    for col in ('first_seen', 'last_seen'):
        t(DATE.match(r[col] or '') is not None, f'{rid}: {col} в форме ГГГГ-ММ-ДД')
    t(r['first_seen'] <= r['last_seen'],
      f'{rid}: first_seen не позже last_seen')
    t(r['fix_target'] in FIX, f'{rid}: fix_target из набора {sorted(FIX)}')
    t(r['verdict'] in VERDICTS, f'{rid}: verdict из набора {sorted(VERDICTS)}')
    t(bool(r['source'].strip()), f'{rid}: source заполнен')

print('\n[3] Порог автоматизации (CONVENTIONS.md 12.6)')
over = [r for r in rows if int(r['n']) >= 2]
under = [r for r in rows if int(r['n']) == 1]
t(len(over) > 0, f'есть классы с n >= 2 ({len(over)})')
for r in over:
    t(bool(r['closes'].strip()),
      f"{r['id']}: n={r['n']} >= 2, значит closes обязано быть заполнено")
    t(r['verdict'] == 'automated',
      f"{r['id']}: n={r['n']} >= 2, значит verdict = automated")
for r in under:
    t(r['closes'] == '',
      f"{r['id']}: n=1, проверка не требуется и closes пустое")
    t(r['verdict'] in ('open', 'wontfix'),
      f"{r['id']}: n=1 не может быть automated без проверки")

print('\n[4] Названные проверки существуют и зарегистрированы')
runner = io.open(os.path.join('tests', 'run-all.py'), encoding='utf-8').read()
named = set()
for r in rows:
    c = r['closes'].strip()
    if c:
        named.add((r['id'], c.split(' ')[0]))
for rid, fname in sorted(named):
    path = os.path.join('tests', fname)
    t(os.path.isfile(path), f'{rid}: {path} существует')
    t(fname in runner, f'{rid}: {fname} зарегистрирован в run-all.py')
t(len(named) >= 5, f'названо не меньше пяти различных проверок ({len(named)})')

print('\n[5] Мета-класс и полнота пула')
t(any(r['id'] == 'B-09' for r in rows),
  'мета-класс B-09 «дефект не учтён» в пуле есть')
meta = [r for r in rows if r['id'] == 'B-09'][0]
t(int(meta['n']) >= 40, f'B-09: n отражает находки AUDIT (факт {meta["n"]})')
t('closes' in COLS and meta['closes'] == 'test_bestiary.py',
  'B-09 закрывается проверкой самого пула')
# Разовый класс обязан остаться в пуле с датами: иначе повтор через полгода
# будет записан как новый, и порог n >= 2 не сработает никогда.
t(len(under) >= 1, f'разовые классы хранятся в пуле ({len(under)})')
for r in under:
    t(bool(r['first_seen']) and bool(r['last_seen']),
      f"{r['id']}: у разового класса обе даты заполнены")

print('\n[6] Пул согласован с правилом')
conv = io.open('CONVENTIONS.md', encoding='utf-8').read()
sec = conv.split('### 12.5.')[1].split('### 12.6.')[0]
for col in COLS:
    t(f'`{col}`' in sec, f'колонка {col} описана в 12.5')
t('research/bestiary.csv' in conv, 'в CONVENTIONS.md назван путь пула')
t('n >= 2' in conv, 'в CONVENTIONS.md записан порог n >= 2')
# Каждый automated-класс обязан указывать, чем закрыт: запись без проверки
# выглядит закрытой и перестаёт попадать в разбор.
for r in rows:
    if r['verdict'] == 'automated':
        t(bool(r['closes'].strip()), f"{r['id']}: automated без closes невозможен")

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
