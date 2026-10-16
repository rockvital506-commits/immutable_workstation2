# -*- coding: utf-8 -*-
"""Статическая проверка `.ps1` без PowerShell (задача A2, `research/24`).

PowerShell в рабочей среде отсутствует, поэтому ни один из 14 `.ps1` ни разу не
выполнялся. Этот тест закрывает часть пробела: он ловит то, что ломает **разбор**
файла интерпретатором, а не логику.

Что проверяется и почему именно это:

- BOM и CRLF. Windows PowerShell 5.1 читает файл без BOM как ANSI, поэтому
  кириллица в строках рассыпается; CRLF в репозитории с LF — расхождение,
  которое проявляется только на чужой машине.
- Табуляция в отступах. Ломает выравнивание here-string и не читается в diff.
- Парность `{}`, `()`, `[]`. Считается **после** вырезания строк и
  комментариев: грубый подсчёт по всему файлу балансирует и тогда, когда
  настоящая скобка потеряна, а внутри строки есть compensating символ.
- `#Requires -Version 5.1` ровно один раз и до первого исполняемого кода.
- `Set-StrictMode` и `$ErrorActionPreference` ровно по одному разу.
- Here-string: `@"` — последний символ строки, закрывающий маркер — в начале
  строки, пробел перед ним запрещён. Правила взяты из токенизатора PowerShell
  (`tokenizer.cs`, `ScanAfterHereStringHeader` и
  `ScanPossibleHereStringFooter`), а не из пересказа: содержимое ПОСЛЕ
  закрывающего маркера разрешено, поэтому `"@ | Set-Content …` корректно.
  Первая версия этого теста требовала, чтобы маркер был единственным на
  строке, и давала ложное срабатывание на `backup-chrome.ps1`.

Тест не утверждает, что скрипты работают. Он утверждает, что они разберутся.
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
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


# ---------------------------------------------------------------------------
# Вырезание строк и комментариев
# ---------------------------------------------------------------------------

def strip_ps(src):
    """Возвращает (код_без_строк_и_комментариев, список_ошибок_here_string).

    Состояния: обычный код, одинарная кавычка, двойная кавычка, here-string
    двух видов, строчный комментарий, блочный комментарий. Внутри двойной
    кавычки обратная кавычка экранирует следующий символ; внутри одинарной
    удвоение кавычки — это экранированная кавычка.
    """
    out = []
    hs_errors = []
    i, n = 0, len(src)
    state = 'code'
    line = 1
    while i < n:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < n else ''

        if ch == '\n':
            line += 1

        if state == 'code':
            if ch == '<' and nxt == '#':
                state = 'blockcom'
                i += 2
                continue
            if ch == '#':
                state = 'linecom'
                i += 1
                continue
            if ch == '@' and nxt in ('"', "'"):
                # here-string: открывающий маркер обязан быть последним в строке
                j = i + 2
                while j < n and src[j] in ' \t':
                    j += 1
                if j >= n or src[j] != '\n':
                    hs_errors.append(
                        f'строка {line}: here-string @{nxt} не последний символ строки')
                state = 'heredq' if nxt == '"' else 'heresq'
                out.append(' ')
                i = j
                continue
            if ch == "'":
                state = 'sq'
                out.append(' ')
                i += 1
                continue
            if ch == '"':
                state = 'dq'
                out.append(' ')
                i += 1
                continue
            out.append(ch)
            i += 1
            continue

        if state == 'linecom':
            if ch == '\n':
                state = 'code'
                out.append('\n')
            i += 1
            continue

        if state == 'blockcom':
            if ch == '#' and nxt == '>':
                state = 'code'
                i += 2
                continue
            if ch == '\n':
                out.append('\n')
            i += 1
            continue

        if state == 'sq':
            if ch == "'":
                if nxt == "'":      # '' внутри одинарной кавычки
                    i += 2
                    continue
                state = 'code'
            elif ch == '\n':
                out.append('\n')
            i += 1
            continue

        if state == 'dq':
            if ch == '`':           # экранирование обратной кавычкой
                i += 2
                continue
            if ch == '"':
                state = 'code'
            elif ch == '\n':
                out.append('\n')
            i += 1
            continue

        if state in ('heredq', 'heresq'):
            close = '"@' if state == 'heredq' else "'@"
            if ch == '\n':
                out.append('\n')
                # Правила закрывающего маркера — по токенизатору PowerShell
                # (tokenizer.cs, ScanPossibleHereStringFooter): маркер
                # распознаётся как «кавычка + @» в начале строки, а то, что
                # идёт после него, уже обычный код — поэтому `"@ | Set-Content`
                # корректно. Пробел ПЕРЕД маркером — отдельная ошибка
                # WhitespaceBeforeHereStringFooter.
                j = i + 1
                ws = 0
                while j < n and src[j] in ' \t':
                    ws += 1
                    j += 1
                if src.startswith(close, j):
                    if ws:
                        hs_errors.append(
                            f'строка {line + 1}: пробел перед закрывающим {close} '
                            f'(WhitespaceBeforeHereStringFooter)')
                    state = 'code'
                    i = j + len(close)
                    continue
            i += 1
            continue

    if state in ('heredq', 'heresq'):
        hs_errors.append('here-string не закрыт до конца файла')
    if state == 'blockcom':
        hs_errors.append('блочный комментарий <# не закрыт')
    if state in ('sq', 'dq'):
        hs_errors.append('строка в кавычках не закрыта до конца файла')
    return ''.join(out), hs_errors


PS_FILES = sorted(
    os.path.join(r, f)
    for r, d, fs in os.walk('.')
    if '.git' not in r
    for f in fs if f.endswith('.ps1'))

print('[1] Инвентаризация: тест видит все .ps1 репозитория')
t(len(PS_FILES) == 14, f'.ps1 найдено 14 (факт {len(PS_FILES)})')

print('\n[2] Кодировка: UTF-8 без BOM')
for p in PS_FILES:
    raw = open(p, 'rb').read()
    b = os.path.basename(p)
    try:
        raw.decode('utf-8')
        dec = True
    except UnicodeDecodeError:
        dec = False
    t(dec, f'{b}: декодируется как UTF-8')
    t(not raw.startswith(b'\xef\xbb\xbf'), f'{b}: нет BOM')
    t(b'\x00' not in raw, f'{b}: нет нулевых байтов (не UTF-16)')

print('\n[3] Переводы строк: LF, без CRLF и без одинокого CR')
for p in PS_FILES:
    raw = open(p, 'rb').read()
    b = os.path.basename(p)
    t(b'\r\n' not in raw, f'{b}: нет CRLF')
    t(b'\r' not in raw, f'{b}: нет одинокого CR')

print('\n[4] Отступы: без табуляции')
for p in PS_FILES:
    b = os.path.basename(p)
    lines = io.open(p, encoding='utf-8').read().split('\n')
    bad_lines = [i for i, l in enumerate(lines, 1) if l.startswith('\t')]
    t(not bad_lines,
      f'{b}: нет строк с табом в отступе'
      + (f' (строки {bad_lines[:5]})' if bad_lines else ''))
    ws = [i for i, l in enumerate(lines, 1) if l != l.rstrip() and l.strip()]
    t(not ws,
      f'{b}: нет висячих пробелов' + (f' (строки {ws[:5]})' if ws else ''))

print('\n[5] Парность скобок после вырезания строк и комментариев')
for p in PS_FILES:
    b = os.path.basename(p)
    src = io.open(p, encoding='utf-8').read()
    code, hs = strip_ps(src)
    t(not hs, f'{b}: here-string и комментарии корректны'
              + (f' — {hs[0]}' if hs else ''))
    for o, c, nm in (('{', '}', 'фигурных'), ('(', ')', 'круглых'),
                     ('[', ']', 'квадратных')):
        t(code.count(o) == code.count(c),
          f'{b}: баланс {nm} скобок ({code.count(o)}/{code.count(c)})')

print('\n[6] #Requires -Version 5.1 ровно один раз и до кода')
for p in PS_FILES:
    b = os.path.basename(p)
    src = io.open(p, encoding='utf-8').read()
    hits = [m for m in re.finditer(r'(?im)^#\s*requires\b.*$', src)]
    t(len(hits) == 1, f'{b}: #Requires ровно один (факт {len(hits)})')
    if not hits:
        continue
    t(re.search(r'-Version\s+5\.1', hits[0].group(0)) is not None,
      f'{b}: указана версия 5.1')
    before = src[:hits[0].start()]
    code_before = strip_ps(before)[0]
    stmt = [l for l in code_before.split('\n')
            if l.strip() and not l.strip().startswith(('.', '<'))]
    t(not stmt, f'{b}: #Requires стоит до первого исполняемого кода')

print('\n[7] Set-StrictMode и $ErrorActionPreference ровно по одному разу')
for p in PS_FILES:
    b = os.path.basename(p)
    src = io.open(p, encoding='utf-8').read()
    code = strip_ps(src)[0]
    sm = len(re.findall(r'Set-StrictMode', code))
    eap = len(re.findall(r'\$ErrorActionPreference\s*=', code))
    t(sm == 1, f'{b}: Set-StrictMode один раз (факт {sm})')
    t(eap == 1, f'{b}: $ErrorActionPreference задан один раз (факт {eap})')
    t(re.search(r'Set-StrictMode\s+-Version\s+(?:Latest|[23](?:\.0)?)', code)
      is not None, f'{b}: у Set-StrictMode указана версия')

print('\n[8] Пара .sh существует (правило дуальности, CONVENTIONS.md раздел 5)')
for p in PS_FILES:
    b = os.path.basename(p)
    t(os.path.isfile(os.path.splitext(p)[0] + '.sh'), f'{b}: есть пара .sh')

print('\n[9] Самопроверка сканера: он ловит нарушения, а не молчит всегда')
# Каждому образцу сопоставлено, что именно должно быть поймано. Если сканер
# начнёт пропускать эти случаи, проверки ниже упадут — значит [5] и [6]
# перестали что-либо гарантировать.
CASES = [
    ('незакрытая фигурная скобка',
     'if ($a) {\n  Write-Host "x"\n', '{', 'brace'),
    # Главный случай, ради которого скобки считаются после вырезания строк:
    # грубый подсчёт по всему файлу видит `{`=1 и `}`=1 и считает баланс
    # соблюдённым, тогда как настоящая фигурная скобка не закрыта, а `}`
    # лежит внутри строки.
    ('скобка потеряна, а compensating — внутри строки',
     'if ($a) {\n  $s = "}"\n', '{', 'brace'),
    ('here-string не закрыт',
     '$x = @"\nтекст\n', None, 'hs'),
    ('пробел перед закрывающим маркером',
     '$x = @"\nтекст\n  "@\n', None, 'hs'),
    ('открывающий маркер не последний в строке',
     '$x = @" лишнее\nтекст\n"@\n', None, 'hs'),
    ('блочный комментарий не закрыт',
     '<# комментарий\n$x = 1\n', None, 'hs'),
]
for name, src, brace, kind in CASES:
    code, hs = strip_ps(src)
    if kind == 'hs':
        t(bool(hs), f'сканер ловит: {name}')
    else:
        caught = code.count('{') != code.count('}')
        t(caught, f'сканер ловит: {name}')

# Обратные случаи: корректный код не должен давать ложных срабатываний.
CLEAN = [
    ('содержимое после закрывающего маркера — корректно',
     '$x = @"\nтекст\n"@ | Set-Content -LiteralPath $p\n'),
    ('скобки внутри строки не считаются',
     '$s = "текст { ( [ ) } ]"\nif ($a) { Write-Host $s }\n'),
    ('скобки внутри комментария не считаются',
     '# комментарий { ( [\nif ($a) { Write-Host 1 }\n'),
    ('блочный комментарий со скобками',
     '<# { ( [ #>\nif ($a) { Write-Host 1 }\n'),
    ('апостроф внутри двойной кавычки',
     "$s = \"it's fine\"\nif ($a) { Write-Host $s }\n"),
    ('удвоенная кавычка внутри одинарной',
     "$s = 'it''s fine'\nif ($a) { Write-Host $s }\n"),
    ('одинарный here-string',
     "$x = @'\n\"@ не маркер\n'@\n"),
]
for name, src in CLEAN:
    code, hs = strip_ps(src)
    t(not hs, f'нет ложного срабатывания: {name}')
    t(code.count('{') == code.count('}'),
      f'нет ложного срабатывания по скобкам: {name}')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)

