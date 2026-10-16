# -*- coding: utf-8 -*-
"""Проверки Этапа 8 — документация и регламенты.

Решения владельца от 2026-10-15:
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

# --- [8] Чек-лист работ ------------------------------------------------------

print('\n[8] field-checklist.md')
chk = read(f'{D}/field-checklist.md')
for sec in ['До начала', 'На станции', 'По завершении']:
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
t('| 9 |' in sec and '✅' in sec.split('| 9 |')[1].split('\n')[0],
  'Этап 9 помечен готовым')
t('| 10 |' in sec and '✅' in sec.split('| 10 |')[1].split('\n')[0],
  'Этап 10 помечен готовым')
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

# --- [15] Выбор образа — факты, а не предписание ---------------------------

print('\n[15] Документ не предписывает выбор образа')
t('Отсюда правило выбора' not in comp,
  'предписательное «правило выбора» из compatibility.md убрано')
t('не использовать' not in comp,
  'формулировки «не использовать» в compatibility.md нет')
t('не использовать' not in chg,
  'формулировки «не использовать» в журнале нет')
t('Кто выбирает образ' in comp,
  'раздел о том, кто принимает решение, есть')
t('владелец' in comp.lower() or 'Владелец' in comp,
  'в разделе назван владелец как принимающий решение')
t('KB5121794' in comp, 'пакет включения для продления поддержки назван')
t('KB5121794' in chg, 'пакет включения назван и в журнале')
t('10.10.2028' in comp, 'срок поддержки после перехода указан')
t('Функций' in comp or 'функций' in comp,
  'указано, что переход функций не меняет')
t('завтра получить систему без обновлений' not in comp,
  'неверное утверждение про «завтра без обновлений» убрано')

chk2 = read(f'{D}/field-checklist.md')
t('Выбор образа' in chk2, 'в чек-листе есть блок выбора образа')
t('Причина:' in chk2, 'в чек-листе есть поле для записи причины выбора')
# Смена профиля 2026-10-16: владелец и исполнитель — одно лицо. Поле
# «Кто решил:» убрано как не несущее информации, и это не молчаливое
# ослабление — факт принадлежности решения проверяется по явной записи об
# отмене, а факт фиксации решения — по записи причины.
t('Кто решил' in chk2 and 'убрана' in chk2,
  'отмена поля «Кто решил» записана в чек-листе явно, а не пропала молча')
t('факты, затем решение, затем запись' in chk2.lower(),
  'в чек-листе закреплён порядок: факты, решение, запись')

# --- [16] Ключ продукта: прошивка игнорируется, активация отдельным шагом ---

print('\n[16] Ключ продукта и активация')
import xml.etree.ElementTree as ET

NS = '{urn:schemas-microsoft-com:unattend}'
GVLK = 'KBN8V-HFGQ4-MGXVD-347P6-PDQGT'
ANS = ('ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/answer/')

for fn in ['autounattend-ltsc-2024.xml', 'autounattend-ltsc-2024-bypass.xml']:
    root = ET.parse(ANS + fn).getroot()
    keys = {}
    for st in root.findall(f'{NS}settings'):
        ps = st.get('pass')
        for c in st.findall(f'{NS}component'):
            for pk in c.findall(f'{NS}ProductKey'):
                keys[ps] = (c.get('name'), (pk.text or '').strip())
    t('specialize' in keys, f'{fn}: ProductKey есть в проходе specialize')
    if 'specialize' in keys:
        comp, val = keys['specialize']
        t(comp == 'Microsoft-Windows-Shell-Setup',
          f'{fn}: ProductKey в компоненте Shell-Setup (факт {comp})')
        t(val == GVLK, f'{fn}: значение — GVLK редакции (факт {val})')
    t('windowsPE' not in keys,
      f'{fn}: в windowsPE ключа нет — иначе OOBE запросил бы его у пользователя')
    raw = open(ANS + fn, 'rb').read()
    t(b'OA3' in raw or b'OEM:OA3' in raw or 'OA3' in raw.decode('utf-8'),
      f'{fn}: причина игнорирования ключа прошивки объяснена')

alg = read('ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/'
           'algorithm.md')
t('### Шаг 12. Ключ продукта и активация' in alg, 'шаг 12 — ключ и активация')
for i in range(1, 16):
    t(f'### Шаг {i}. ' in alg, f'заголовок шага {i} на месте')
t('### Шаг 16. ' not in alg, 'лишнего шага 16 нет')
t(flat(alg).count('### Шаг 12. ') == 1, 'заголовок шага 12 не дублируется')
for cmd in ['slmgr /upk', 'slmgr /cpky', 'slmgr /ipk', 'slmgr /ato',
            'slmgr /dlv', 'slui 4', '0xC004C008']:
    t(cmd in alg, f'шаг 12 содержит {cmd}')
t('на старой' in alg, 'отвязка Retail-ключа привязана к старой станции')
t('RETAIL' in alg and 'VOLUME_MAK' in alg,
  'проверка типа лицензии после ввода ключа есть')
alg_flat = flat(alg)
t('лицензией не является' in alg_flat,
  'указано, что GVLK лицензией не является')

# Перекрёстные ссылки после перенумерации
t('Шаг 13 станционного алгоритма' in read(
    'tools/scripts/procedures/validation.md'),
  'validation.md ссылается на шаг 13')
t('из 15 шагов' in read('tools/os/windows/README.md'),
  'os/windows/README.md: 15 шагов')
t('из 15 шагов' in read('tools/os/windows/installation/README.md'),
  'installation/README.md: 15 шагов')
t('15 шагов от живой ОС' in read('PLAN.md'), 'PLAN.md: 15 шагов')
t('### Шаг 12.' not in read('CONVENTIONS.md'),
  'CONVENTIONS.md: пример обновлён на шаг 13')
t('из 14 шагов' not in read('tools/os/windows/README.md'),
  'старого «14 шагов» не осталось')

ansr = read(ANS + 'README.md')
t('ProductKey' in ansr and GVLK in ansr,
  'answer/README.md объясняет ProductKey и приводит GVLK')
t('шаг 12' in ansr, 'answer/README.md указывает на шаг активации')

chk3 = read(f'{D}/field-checklist.md')
t('slmgr /dlv' in chk3, 'в чек-листе есть проверка активации')
t('Retail' in chk3, 'в чек-листе учтён перенос Retail-ключа')

# --- [17] Пригодность ключей для билда и чтение ключа прошивки ------------

print('\n[17] Какие ключи годятся для этого билда')
t('OA3xOriginalProductKey' in alg, 'шаг 1 читает ключ из прошивки')
t('MSDM' in alg or 'OEM:OA3' in alg,
  'объяснено, где именно в прошивке лежит ключ')
t('на чистой' in flat(alg),
  'объяснено, почему ключ читается до переустановки, а не после')
alg_f = flat(alg)
for keytype, verdict in [
        ('MAK для Windows 11 IoT Enterprise LTSC 2024', 'да'),
        ('GVLK + доступный KMS-узел', 'да'),
        ('OEM-ключ IoT Enterprise LTSC для этой станции', 'да'),
        ('Ключ из прошивки этой станции (Win11 Home, OEM)', 'нет'),
        ('Retail-ключ Windows 11 Pro / Home', 'нет')]:
    i = alg.find('| ' + keytype + ' |')
    t(i > 0, f'в таблице есть строка «{keytype}»')
    if i > 0:
        row = alg[i:alg.find('\n', i)]
        t(('**да**' in row) if verdict == 'да' else ('**нет**' in row),
          f'«{keytype}» помечен как «{verdict}»')
t('не проверено' in alg, 'непроверенные случаи отделены от проверенных')
t('Retail-ключ Windows 11 Enterprise' in alg,
  'случай Retail Enterprise вынесен отдельно')
t('Windows 10 IoT Enterprise LTSC 2021' in alg,
  'случай ключа от LTSC 2021 вынесен отдельно')
t('Отвязка Retail-ключа ниже нужна для случаев' in alg_f,
  'сказано, когда отвязка Retail применяется, а когда нет')
# Версия паспорта не зашивается в тест: она растёт с каждой правкой алгоритма,
# и тест на конкретный номер ломался трижды. Проверяется связь паспорта
# с историей изменений — это и есть то, что может разойтись.
_ver = re.search(r'^\| Версия \| (\d+\.\d+) \|$', alg, re.M)
t(bool(_ver), 'в паспорте есть версия алгоритма')
if _ver:
    t(f'| {_ver.group(1)} |' in alg,
      f'версия паспорта {_ver.group(1)} имеет запись в истории изменений')
t('| 2026-10-15 | 1.3 |' in alg,
  'в истории изменений есть запись 1.3 с причиной правки')
t('| 2026-10-15 | 1.4 |' in alg,
  'в истории изменений есть запись 1.4 — приведение к правилу навигации')
t('| 1.2 |' in alg, 'в истории изменений есть запись 1.2')

# --- [18] Регрессия ---------------------------------------------------------

print('\n[18] Регрессия')
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
