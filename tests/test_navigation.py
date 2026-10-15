# -*- coding: utf-8 -*-
"""Проверка правила навигации по сущностям — CONVENTIONS.md раздел 10.

Правило введено 2026-10-15. Оно отвечает на вопрос, на который до его
появления не отвечала ни одна проверка: **сможет ли мастер по тексту документа
найти файл на флешке, не перебирая каталоги**.

Проверяются пять пунктов: префикс базы пути, ссылка на первое упоминание,
раздел «Средства» в каждом шаге, карта сущностей, разрешимость путей.
Отдельно проверяется шаблон сборки — если он не соответствует правилу,
следующий билд будет написан по-старому.
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


def read(p):
    return io.open(p, encoding='utf-8').read()


# Расширения сущностей: скрипты, процедуры, образы, архивы, конфиги
ENT = re.compile(r'([A-Za-z0-9_\-\.]+\.(?:ps1|sh|md|exe|zip|msi|conf|json|xml|iso|torrent))')
# Имена, которые сущностями репозитория не являются
NOT_ENTITY = {
    'autounattend.xml',   # имя, под которым файл ответа копируется на флешку
    'unattend.xml',       # C:\Windows\Panther\unattend.xml в установленной ОС
    'README.md',          # описывается правилом README, а не навигации
    'CONVENTIONS.md',     # правило, а не применяемая сущность
    'PLAN.md',
    'algorithm.md',
    'manifest.csv',
}
# Префиксы и их раскрытие в репозитории
PREFIX = {
    'VENTOY:/': 'ventoy-partition/',
    'TOOLS:/': 'tools/',
    'BUILD:/': None,          # подставляется каталог конкретной сборки
    'REPO:/': '',
}

def line_of(text, pos):
    """Строка, в которой стоит позиция. Обратным поиском: надёжнее, чем
    rsplit по переводу строки, когда позиция попадает на начало строки."""
    a = text.rfind('\n', 0, pos)
    b = text.find('\n', pos)
    return text[a + 1:b if b != -1 else len(text)]


CONV = read('CONVENTIONS.md')
TPL = 'ventoy-partition/builds/_templates/algorithm.md'
BUILD_DIRS = [d for d in sorted(os.listdir('ventoy-partition/builds'))
              if os.path.isdir(f'ventoy-partition/builds/{d}') and d != '_templates']

# ================================================================ [A]
print('\n[A] Правило зарегистрировано в реестре')
t('## 10. Навигация по сущностям' in CONV, 'в CONVENTIONS.md есть раздел 10')
for sub in ['10.1. Префикс базы пути', '10.2. Ссылка на первое упоминание',
            '10.3. Раздел «Средства» в каждом шаге', '10.4. Карта сущностей',
            '10.5. Что проверяется автоматически']:
    t(f'### {sub}' in CONV, f'есть подраздел {sub}')
for pre in ['VENTOY:/', 'TOOLS:/', 'BUILD:/', 'REPO:/', 'SYSTEM:']:
    t(pre in CONV, f'в правиле объявлен префикс {pre}')
t('lychee' in CONV and 'не добавляется' in CONV,
  'отказ от внешней утилиты зафиксирован в правиле')
t('research/20-navigation-paths.md' in CONV,
  'правило ссылается на обоснование')


# ================================================================ [B]
def steps_of(text):
    """Границы шагов по заголовкам ### Шаг N."""
    lines = text.split('\n')
    heads = [(i, ln) for i, ln in enumerate(lines) if re.match(r'^### Шаг ', ln)]
    out = []
    for k, (i, ln) in enumerate(heads):
        j = heads[k + 1][0] if k + 1 < len(heads) else next(
            (n for n, l in enumerate(lines[i + 1:], i + 1) if l.startswith('## ')),
            len(lines))
        out.append((ln, '\n'.join(lines[i:j])))
    return out


def check_doc(path, build_dir=None, is_template=False):
    """Проверка одного algorithm.md по пунктам 10.1—10.5."""
    name = path.split('/')[-2] if not is_template else '_templates'
    text = read(path)
    base = os.path.dirname(path)
    steps = steps_of(text)

    print(f'\n[B] {name}: шаги и раздел «Средства»')
    t(len(steps) > 0, f'{name}: шаги найдены ({len(steps)})')
    no_means = [ln[4:44] for ln, sec in steps if '**Средства.**' not in sec]
    t(not no_means,
      f'{name}: раздел «Средства» есть в каждом шаге (нет в {len(no_means)})')
    for x in no_means:
        print('        без раздела:', x)
    # В шаге со средствами обязана быть таблица
    no_tbl = [ln[4:44] for ln, sec in steps
              if '**Средства.**' in sec and '|' not in sec.split('**Средства.**')[1][:600]]
    t(not no_tbl, f'{name}: в каждом разделе «Средства» есть таблица (нет в {len(no_tbl)})')

    print(f'\n[C] {name}: карта сущностей')
    t('### Карта сущностей' in text or (is_template and 'Карта сущностей' in text),
      f'{name}: раздел «Карта сущностей» есть')
    card = text.split('Карта сущностей')[1][:4000] if 'Карта сущностей' in text else ''
    for pre in ['VENTOY:/', 'TOOLS:/', 'SYSTEM:']:
        t(pre in card, f'{name}: в пояснении карты назван префикс {pre}')

    print(f'\n[D] {name}: ссылка на первое упоминание сущности')
    missing = []
    for ln, sec in steps:
        # Ссылки шага: и цели, и текст ссылок
        linked = set()
        for m in re.finditer(r'\[([^\]]*)\]\(([^)]+)\)', sec):
            linked.add(m.group(1))
            linked.add(m.group(2))
        linked_flat = ' '.join(linked)
        # Упоминания вне конструкций ссылок
        stripped = re.sub(r'\[[^\]]*\]\([^)]*\)', ' ', sec)
        # Внутри блока кода markdown-ссылка невозможна — такие упоминания
        # правило разрешает, если путь дан комментарием в том же блоке
        outside_code = re.sub(r'```.*?```', ' ', stripped, flags=re.S)
        for n in set(ENT.findall(outside_code)):
            if n in NOT_ENTITY:
                continue
            if n not in linked_flat:
                missing.append(f'{ln[4:36]}: {n}')
    t(not missing,
      f'{name}: каждая сущность вне блоков кода имеет ссылку (без ссылки {len(missing)})')
    for x in missing:
        print('        ', x)

    print(f'\n[E] {name}: пути с префиксом разрешимы')
    badpath = []
    for m in re.finditer(r'(VENTOY:/|TOOLS:/|BUILD:/|REPO:/)([^\s`|)]*)', text):
        pre, tail = m.group(1), m.group(2)
        # Строка пояснительной таблицы: префикс назван сам по себе, пути нет
        line = line_of(text, m.start())
        cells = [c.strip().strip('`') for c in line.split('|')]
        if line.startswith('|') and (pre in cells or pre.rstrip(':') in cells):
            continue
        # Плейсхолдер шаблона: путь намеренно не заполнен
        if '<' in tail or '>' in tail:
            continue
        if not tail or tail in ('…', '...'):
            badpath.append(f'{pre} без продолжения')
            continue
        root = PREFIX[pre]
        if root is None:
            root = f'ventoy-partition/builds/{build_dir}/' if build_dir else ''
        target = os.path.normpath(os.path.join(root, tail.rstrip('/')))
        if not os.path.exists(target):
            badpath.append(f'{pre}{tail} -> {target}')
    t(not badpath,
      f'{name}: все пути с префиксом разрешимы (не разрешается {len(badpath)})')
    for x in badpath:
        print('        ', x)

    print(f'\n[F] {name}: многоточий в путях нет')
    ell = []
    for m in re.finditer(r'[A-Za-z0-9_\-\\/]*(?:\.\.\.|…)[A-Za-z0-9_\-\\/\.]*', text):
        s = m.group(0)
        # Многоточие как перечисление («M1—M12», «и так далее») не путь
        line = line_of(text, m.start())
        if '«' in line and '»' in line:
            continue      # цитата строки интерфейса, не путь репозитория
        if re.search(r'[\\/](?:\.\.\.|…)[\\/]', s) or s.startswith(('builds', 'tools', 'ISO')):
            ell.append(s)
    t(not ell, f'{name}: путей с многоточием нет (найдено {len(ell)})')
    for x in ell:
        print('        ', x)

    print(f'\n[G] {name}: относительные ссылки живы')
    dead = []
    for m in re.finditer(r'\]\(([^)\s]+)\)', text):
        l = m.group(1)
        if l.startswith(('http', '#', 'mailto')):
            continue
        if '<' in l or '>' in l:      # плейсхолдер шаблона
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, l.split('#')[0]))):
            dead.append(l)
    t(not dead, f'{name}: битых относительных ссылок нет (битых {len(dead)})')
    for x in dead:
        print('        ', x)


check_doc(TPL, is_template=True)
for d in BUILD_DIRS:
    check_doc(f'ventoy-partition/builds/{d}/algorithm.md', build_dir=d)


# ================================================================ [H]
print('\n[H] Шаблон соответствует правилу — иначе следующий билд будет по-старому')
tpl = read(TPL)
t('**Средства.**' in tpl, 'в схеме шага шаблона есть раздел «Средства»')
t('Карта сущностей' in tpl, 'в шаблоне есть карта сущностей')
for pre in ['VENTOY:/', 'TOOLS:/', 'BUILD:/', 'REPO:/', 'SYSTEM:']:
    t(pre in tpl, f'в шаблоне показан префикс {pre}')
t('CONVENTIONS.md' in tpl and '10' in tpl,
  'шаблон ссылается на раздел 10 правила')

# ================================================================ [I]
print('\n[I] Соответствие по всему репозиторию')
# Каждая сущность манифеста должна быть достижима по ссылкам из документации
rows = list(csv.DictReader(io.open('manifest.csv', encoding='utf-8')))
names = {r['file'] for r in rows if r['type'] in ('iso', 'tool') and r['file'].strip()}
linked_all = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in files:
        if f.endswith('.md'):
            linked_all.append(io.open(os.path.join(root, f), encoding='utf-8').read())
blob = '\n'.join(linked_all)
unreached = sorted(n for n in names if n not in blob)
t(not unreached,
  f'каждая утилита и образ манифеста названы в документации (не названы {len(unreached)})')
for x in unreached:
    print('        ', x)

# Ни один документ не даёт путь к сущности флешки без префикса в таблицах «Средства»
naked = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d != '.git']
    for f in files:
        if not f.endswith('.md'):
            continue
        p = os.path.join(root, f)
        txt = read(p)
        # Только сама таблица «Средства»: от отметки до первой пустой строки.
        # Иначе в выборку попадают соседние таблицы — состав драйверов,
        # таблица проверок валидатора, примеры внутри CONVENTIONS.md.
        for sec in re.findall(r'\*\*Средства\.\*\*(.*)', txt):
            for line in sec.split('\n'):
                if not line.strip():
                    break
                if not line.startswith('|'):
                    continue
                cells = [c.strip() for c in line.split('|')[1:-1]]
                if len(cells) < 3:
                    continue
                last = cells[-1].strip('` ')
                if not last or last.startswith(('VENTOY:/', 'TOOLS:/', 'BUILD:/',
                                                'REPO:/', 'SYSTEM:')):
                    continue
                if last in ('Путь на флешке', '---', '') or set(last) <= {'-'}:
                    continue
                naked.append(f'{p}: {last}')
t(not naked,
  f'в таблицах «Средства» все пути с префиксом (без префикса {len(naked)})')
for x in naked[:10]:
    print('        ', x)


# ================================================================ [J]
print('\n[J] Объявление базы пути в рабочих документах (раздел 10.1)')
DECL_RE = re.compile(r'(?m)^> \*\*База пути\.\*\*')
BARE_RE = re.compile(r'`((?:tools|ventoy-partition|scripts|tests)/[^`]*)`')
no_decl = []
unresolved = []
checked_docs = 0
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git', 'research')]
    for f in files:
        if not f.endswith('.md'):
            continue
        p = os.path.join(root, f)[2:]
        # algorithm.md и шаблоны проверяются блоками B—H: там префиксы обязательны
        if p.endswith('algorithm.md') or '/_templates/' in p or p == 'CONVENTIONS.md':
            continue
        txt = read(p)
        # Зачёркнутый текст — запись о том, что создавать не стали: такой путь
        # намеренно не существует, и это зафиксированное решение, а не дефект
        txt = re.sub(r'~~[^~]*~~', ' ', txt)
        bare = BARE_RE.findall(txt)
        if not bare:
            continue
        checked_docs += 1
        if not DECL_RE.search(txt):
            no_decl.append(p)
            continue
        # Фиксация отказа: «не нужен», «не создан», «вместо», «дублировал бы».
        # Это записанное решение не создавать каталог, а не битая ссылка.
        NEG = re.compile(r'не нужн|не создава|не создан|вместо|отказ|закрыт|'
                         r'второй экземпляр|дублир')
        # База объявления: корень репозитория или каталог этого модуля
        base = os.path.dirname(p) if 'от каталога' in txt.split('База пути')[1][:120] else ''
        for raw in bare:
            line = line_of(txt, txt.find(raw))
            if NEG.search(line):
                continue
            tgt = raw.split('`')[0].strip().rstrip('/.,;:')
            if '<' in tgt or ' ' in tgt or not tgt:
                continue          # плейсхолдер или команда с аргументами
            if any(c in tgt for c in '*{}'):
                continue          # glob: описание набора файлов, а не путь
            if os.path.exists(tgt):
                continue
            if base and os.path.exists(os.path.join(base, tgt)):
                continue
            unresolved.append(f'{p}: {tgt}')
t(not no_decl,
  f'во всех рабочих документах с путями объявлена база (без объявления {len(no_decl)})')
for x in no_decl[:10]:
    print('        ', x)
t(not unresolved,
  f'пути по объявленной базе разрешимы (не разрешается {len(unresolved)})')
for x in unresolved[:10]:
    print('        ', x)
t(checked_docs > 30,
  f'проверка охватила рабочие документы (охвачено {checked_docs})')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
