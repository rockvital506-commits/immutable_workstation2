# -*- coding: utf-8 -*-
"""Проверки Этапа 8 — документация и регламенты.

Решения заказчика от 2026-10-15:
  1. Каталог документации живёт на флешке: tools/docs/ (раздел Tools),
     а не только в git.
  2. Таблица совместимости — по всем семи образам флешки.
  3. CHANGELOG-flash.md ведётся по вехам, восстановленным из истории git.
  4. Версия Ventoy в README: 1.1.17 «на момент создания» остаётся,
     добавляется явный минимум 1.1.14 и рекомендуемая 1.1.18.

Расхождения, найденные AUDIT (research/17-documentation.md): R1 docs/ не
создан при закрытом пункте PLAN; R2 статусы этапов в README устарели; R3
дерево структуры обещало docs/; R4 repo-validate не проверял docs/; R5
версия Ventoy устарела.
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


def read(p):
    return io.open(p, encoding='utf-8').read()


def flat(s):
    """Markdown переносит длинные строки, в том числе внутри инлайн-кода."""
    return re.sub(r'\s+', ' ', s)


DOCS = ['README.md', 'recovery.md', 'reinstall.md', 'field-checklist.md',
        'compatibility.md', 'CHANGELOG-flash.md']
D = 'tools/docs'

# --- [1] Каталог существует и не пуст -------------------------------------

print('\n[1] Каталог tools/docs/')
for f in DOCS:
    p = f'{D}/{f}'
    t(os.path.isfile(p), f'есть {p}')
    if os.path.isfile(p):
        sz = os.path.getsize(p)
        t(sz > 500, f'{p} не пуст ({sz} байт)')

# --- [2] Индекс ссылается на все документы --------------------------------

print('\n[2] Индекс tools/docs/README.md')
idx = read(f'{D}/README.md')
for f in DOCS[1:]:
    t(f']({f})' in idx, f'индекс ссылается на {f}')
t('Что здесь не дублируется' in idx, 'индекс объясняет, что не дублируется')

# --- [3] Битые ссылки -------------------------------------------------------

print('\n[3] Относительные ссылки в tools/docs/')
broken = 0
for f in DOCS:
    md = f'{D}/{f}'
    src = re.sub(r'`[^`\n]*`', '', read(md))
    src = re.sub(r'```.*?```', '', src, flags=re.S)
    for m in re.finditer(r'\]\(([^)#]+)\)', src):
        link = m.group(1).split('#')[0]
        if not link or link.startswith(('http://', 'https://', 'mailto:')):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(D, link))):
            bad(f'{md}: битая ссылка {link}')
            broken += 1
t(broken == 0, f'битых ссылок нет (найдено {broken})')

# --- [4] Таблица совместимости: все семь образов ----------------------------

print('\n[4] Таблица совместимости')
comp = read(f'{D}/compatibility.md')
IMAGES = ['Win11 IoT Enterprise LTSC 2024', 'Win10 IoT Enterprise LTSC 2021',
          'Win11 Pro 24H2', 'Win10 Pro 22H2', 'Strelec WinPE 2026.02.05',
          'Linux Mint 22.3', 'Clonezilla Live 3.3.3-37']
for img in IMAGES:
    t(img in comp, f'в таблице есть {img}')
t(comp.count('| Образ |') == 1, 'сводная таблица одна')

# --- [5] Таблица совместимости: данные --------------------------------------

print('\n[5] Данные таблицы совместимости')
t('Preferred' in comp and 'Optional' in comp,
  'два уровня требований LTSC 2024 — Preferred и Optional')
t('не обязателен' in comp, 'TPM в уровне Optional помечен необязательным')
t('i3-1215U' in comp, 'целевой процессор назван')
t('Alder Lake' in comp, 'платформа целевого процессора названа')
t('196 МБ' in comp, 'требование Clonezilla по памяти приведено')
t('14.10.2026' in comp, 'истечение поддержки Win11 Pro 24H2 указано')
t('14.10.2025' in comp, 'истечение поддержки Win10 указано')
t('09.10.2029' in comp, 'срок основной поддержки LTSC 2024 указан')
t('12.01.2027' in comp, 'срок поддержки Win10 LTSC 2021 указан')
t('x64' in comp, 'разрядность образов указана')
t('ARM' in comp, 'ограничение по ARM сформулировано')
t('Secure Boot' in comp, 'Secure Boot упомянут')
t('Не проверено' in comp, 'раздел «Не проверено» есть')
t('Конфликт источников' in comp,
  'конфликт источников по TPM зафиксирован, а не проигнорирован')

# --- [6] Регламент восстановления ------------------------------------------

print('\n[6] recovery.md')
rec = read(f'{D}/recovery.md')
t('без вскрытия' in rec, 'ограничение профиля «без вскрытия» названо')
t('Спросить про данные' in rec, 'первый шаг — вопрос про данные')
t('Не записывать на диск' in rec,
  'запрет записи на восстанавливаемый диск есть')
for sec in ['Аппаратура', 'Данные', 'Загрузчик', 'Неизвестен пароль',
            'Когда восстановление невозможно', 'После восстановления']:
    t(sec in rec, f'раздел «{sec}» есть')
t('BitLocker' in rec, 'ограничение по шифрованию названо')
t('SMART' in rec, 'проверка состояния диска до интенсивных операций')
t('reinstall.md' in rec, 'связь с регламентом переустановки есть')
t('procedures/' in rec, 'связь с процедурами есть')

# --- [7] Регламент переустановки -------------------------------------------

print('\n[7] reinstall.md')
rei = read(f'{D}/reinstall.md')
t('1.1.14' in rei, 'минимальная версия Ventoy указана')
t('1.1.18' in rei, 'рекомендуемая версия Ventoy указана')
t('1.1.11' in rei, 'версия появления переменной диска указана')
t('UEFI CA 2023' in rei, 'запись ключа при первой загрузке описана')
t('VTOYEFI' in rei, 'служебный раздел назван')
t('autounattend.xml' in rei, 'имя файла ответа указано')
t('в корень флешки' in rei, 'запрет корня флешки есть')
t('timeout' in rei and 'autosel' in rei,
  'запрет timeout и autosel сформулирован')
t('WillWipeDisk' in rei, 'точка невозврата названа')
t('Panther' in rei, 'диагностика через Panther указана')
for proc in ['basic-setup.md', 'block-telemetry.md', 'ssd-ram-tuning.md',
             'validation.md']:
    t(proc in rei, f'процедура {proc} в порядке после установки')
t('algorithm.md' in rei, 'ссылка на алгоритм целевой станции есть')

# --- [8] Чек-лист выезда ----------------------------------------------------

print('\n[8] field-checklist.md')
chk = read(f'{D}/field-checklist.md')
for sec in ['До выезда', 'На станции', 'По возвращении']:
    t(sec in chk, f'блок «{sec}» есть')
t('- [ ]' in chk, 'чек-лист размечен полями для отметки')
t(chk.count('- [ ]') >= 25,
  f'полей для отметки достаточно ({chk.count("- [ ]")})')
t('1.1.14' in chk, 'проверка версии Ventoy в чек-листе есть')
t('manifest.csv' in chk, 'сверка SHA256 с манифестом есть')
t('CHANGELOG-flash.md' in chk, 'внесение записи в журнал по возвращении')
t('Три правила' in chk, 'блок часто нарушаемых правил есть')

# --- [9] Журнал изменений ---------------------------------------------------

print('\n[9] CHANGELOG-flash.md')
chg = read(f'{D}/CHANGELOG-flash.md')
t('по вехам' in chg, 'правило ведения журнала сформулировано')
for stage in ['Этап 6', 'Этап 5', 'Этап 7', 'Этап 4.8', 'Этап 4.7',
              'Этап 4.6', 'Этап 4.5', 'Этап 4.4', 'Этап 4.3']:
    t(stage in chg, f'веха «{stage}» есть')
t('2026-10-07' in chg, 'каркасные этапы объединены одной вехой')
t('Что следует для выезда' in chg,
  'в вехах есть практический вывод для выезда')
t('не проверялось' in chg,
  'журнал честно отделяет изменения в репозитории от состояния флешки')
t(chg.count('## 2026-') >= 9,
  f'записей с датами достаточно ({chg.count("## 2026-")})')

# --- [10] R2: статусы этапов в README приведены к факту ---------------------

print('\n[10] Статусы этапов в README.md')
rd = read('README.md')
# Разделитель строк Markdown-таблицы тоже состоит из «---», поэтому резать
# по нему нельзя — срежется сразу после шапки таблицы.
sec = re.split(r'^---\s*$', rd.split('## 5. Статус этапов')[1],
               flags=re.M)[0]
DONE = ['| 1 |', '| 2 |', '| 3 |', '| 3c |', '| 3d |', '| 4 |', '| 5 |',
        '| 6 |', '| 7 |', '| 8 |']
for row in DONE:
    t(row in sec and sec.split(row)[1].split('\n')[0].count('✅') == 1,
      f'строка {row.strip("| ")} помечена готовой')
t('| 9 |' in sec and '⬜' in sec.split('| 9 |')[1].split('\n')[0],
  'Этап 9 ещё не помечен готовым')
t('| 10 |' in sec and '⬜' in sec.split('| 10 |')[1].split('\n')[0],
  'Этап 10 ещё не помечен готовым')
t('tools/docs/' in rd, 'README указывает фактическое размещение документации')
t('\n└── docs/' not in rd, 'отдельного каталога docs/ в дереве больше нет')

# --- [11] R4: валидация проверяет документацию ------------------------------

print('\n[11] Валидация проверяет документацию')
sh = read('scripts/repo-validate.sh')
ps = read('scripts/repo-validate.ps1')
for f in DOCS:
    t(f'tools/docs/{f}' in sh, f'repo-validate.sh проверяет tools/docs/{f}')
    t(f'tools/docs/{f}' in ps, f'repo-validate.ps1 проверяет tools/docs/{f}')

# --- [12] R5: версия Ventoy -------------------------------------------------

print('\n[12] Версия Ventoy в README.md')
t('1.1.17' in rd, 'версия на момент создания сохранена')
t('1.1.14' in rd, 'минимальная версия указана явно')
t('1.1.18' in rd, 'рекомендуемая версия указана')

# --- [13] Расхождение в tools/README.md закрыто ----------------------------

print('\n[13] Карта групп в tools/README.md')
tr = read('tools/README.md')
t('docs-offline' not in tr,
  'несозданная группа docs-offline/ из карты убрана')
t('`docs/`' in tr, 'фактическая группа docs/ в карту внесена')
t('⬜ Этап 5' not in tr, 'группа scripts/ больше не помечена незакрытой')
t('⬜ Этап 6' not in tr, 'группа deployment/ больше не помечена незакрытой')

# --- [14] Имена источников и доменов — только латиницей --------------------

print('\n[14] Смешанные написания в документации')
MIX = re.compile(r'[\u0410-\u044f\u0401\u0451][A-Za-z]|[A-Za-z][\u0410-\u044f\u0401\u0451]')
mixed = 0
for f in DOCS:
    src = read(f'{D}/{f}')
    src = re.sub(r'```.*?```', '', src, flags=re.S)
    src = re.sub(r'`[^`\n]*`', '', src)
    src = re.sub(r'\u00ab[^\u00bb\n]*\u00bb', '', src)
    for m in MIX.finditer(src):
        bad(f'{f}: смешанное написание {m.group(0)!r}')
        mixed += 1
t(mixed == 0, f'смешанных написаний нет (найдено {mixed})')

# --- [15] Регрессия ---------------------------------------------------------

print('\n[15] Регрессия')
for p in ['research/17-documentation.md',
          'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/'
          'answer/README.md',
          'tests/test_stage6.py',
          'scripts/repo-validate.sh']:
    t(os.path.isfile(p), f'на месте {p}')
ans = read('ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/'
           'answer/README.md')
t('1.1.11' in ans and '1.1.14' in ans,
  'минимальная версия Ventoy осталась в answer/README.md')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
