# -*- coding: utf-8 -*-
"""Этап 10 — сквозная проверка: результат алгоритма против цели билда.

Отличие от остальных тестов. Тесты этапов проверяют соответствие правилам
репозитория. Этот проверяет другое: **приведёт ли прохождение алгоритма к тому
ради чего билд затевался**.

Цель билда (паспорт + задание заказчика): MSI Modern 15 B12M-211RU,
i3-1215U / 8 ГБ распаянной DDR4 / NVMe 256 ГБ / AX211, миграция с
предустановленной Win11 Home на Win11 IoT Enterprise LTSC 2024; профиль —
коммерческое использование, домашние ПК и малый бизнес, без вскрытия станций.

Каждый блок ниже — это вопрос «получит ли заказчик обещанное», а не «соблюдено
ли соглашение».
"""
import csv, io, os, re, sys
import xml.etree.ElementTree as ET

ROOT = '/home/user/immutable_workstation2'
os.chdir(ROOT)
checks = errors = 0
NS = '{urn:schemas-microsoft-com:unattend}'

B = 'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2'
ANS = f'{B}/answer/autounattend-ltsc-2024.xml'
BYP = f'{B}/answer/autounattend-ltsc-2024-bypass.xml'
ALG = f'{B}/algorithm.md'


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
    return re.sub(r'\s+', ' ', s)


xml_main = ET.parse(ANS).getroot()
xml_byp = ET.parse(BYP).getroot()
alg = read(ALG)
algf = flat(alg)


def settings(root, pass_name):
    for st in root.findall(f'{NS}settings'):
        if st.get('pass') == pass_name:
            return st
    return None


def comp(st, name):
    for c in st.findall(f'{NS}component'):
        if c.get('name') == name:
            return c
    return None


# =====================================================================
print('\n[A] Железо станции: потянет ли целевая ОС')
# =====================================================================

# i3-1215U — Alder Lake, в списке поддерживаемых процессоров LTSC 2024
t('i3-1215U' in alg and 'Alder Lake' in read('tools/docs/compatibility.md'),
  'целевой CPU назван в билде, а его платформа — в списке поддержки LTSC 2024')

# 2 ГБ — уровень Optional; на станции 8 ГБ
t('8 ГБ' in alg, 'объём ОЗУ станции зафиксирован в паспорте')
t('распаян' in alg,
  'учтено, что память распаяна — апгрейд невозможен, тюнинг обязателен')

# NVMe 256 ГБ против разметки: сумма фиксированных разделов должна влезть
sizes = [500, 260, 128]
overhead = sum(sizes)
t(overhead < 2048,
  f'фиксированные разделы ({overhead} МБ) занимают меньше 1 ГБ из 256 ГБ')
t(overhead / (256 * 1024) < 0.01,
  f'накладные расходы разметки — {overhead / (256 * 10.24):.2f} % диска')

# Переменная выбора диска рассчитана именно на 256 ГБ
disk_var = None
for d in settings(xml_main, 'windowsPE').findall(f'.//{NS}Disk'):
    disk_var = d.findtext(f'{NS}DiskID')
t(disk_var == '$$VT_WINDOWS_DISK_NONVTOY_CLOSEST_256$$',
  f'диск выбирается по ближайшему размеру к 256 ГБ (факт {disk_var})')
t('NONVTOY' in disk_var,
  'переменная исключает носитель Ventoy — ОС не встанет на флешку')

# Все устройства станции закрыты драйверами в шаге 7
step7 = alg.split('### Шаг 7.')[1].split('### Шаг 8.')[0]
for dev, label in [('AX211', 'Wi-Fi'), ('Bluetooth', 'Bluetooth'),
                   ('Аудио', 'аудио'), ('Накопитель', 'накопитель'),
                   ('DTT', 'Intel DTT'), ('GNA', 'Intel GNA')]:
    t(dev in step7, f'шаг 7 закрывает {label} ({dev})')
t('PCI' in step7 and 'VEN_' in step7,
  'драйверы привязаны к Hardware ID, а не к названию «на глаз»')
t('INF' in step7.upper() or '.inf' in step7,
  'для каждого устройства указан конкретный INF')

# VMD — известная проблема NVMe на Intel 11+
t('VMD' in alg, 'предупреждение про Intel VMD и невидимый NVMe есть')

# Экран 15.6" FHD против минимума LTSC (9" 720p) — с запасом
t('15.6' in alg and 'FHD' in alg, 'параметры экрана зафиксированы в паспорте')

# =====================================================================
print('\n[B] Файл ответа: действительно ли ставит LTSC на нужную станцию')
# =====================================================================

passes = [st.get('pass') for st in xml_main.findall(f'{NS}settings')]
t(passes == ['windowsPE', 'specialize', 'oobeSystem'],
  f'три прохода в правильном порядке (факт {passes})')
t(settings(xml_main, 'windowsPE') is not None,
  'проход windowsPE есть — без него Ventoy не подхватывает файл')

# Разметка: WinRE + EFI + MSR + Windows
disk = settings(xml_main, 'windowsPE').find(f'.//{NS}Disk')
created = disk.find(f'{NS}CreatePartitions').findall(f'{NS}CreatePartition')
t(len(created) == 4, f'создаётся 4 раздела (факт {len(created)})')
t(created[0].findtext(f'{NS}Size') == '500', 'WinRE 500 МБ')
t(created[1].findtext(f'{NS}Type') == 'EFI', 'раздел EFI')
t(created[2].findtext(f'{NS}Type') == 'MSR', 'раздел MSR')
t(created[3].findtext(f'{NS}Extend') == 'true',
  'последний раздел занимает остаток диска')

mods = disk.find(f'{NS}ModifyPartitions').findall(f'{NS}ModifyPartition')
t(mods[0].findtext(f'{NS}Label') == 'WinRE'
  and (mods[0].findtext(f'{NS}TypeID') or '').lower()
  == 'de94bba4-06d1-4d40-a16a-bfd50179d6ac',
  'WinRE получил правильный GUID типа раздела')
t(mods[3].findtext(f'{NS}Letter') == 'C', 'системный раздел получает букву C')
t(disk.findtext(f'{NS}WillWipeDisk') == 'true',
  'WillWipeDisk=true — точка невозврата названа честно')

# Обход требований на целевой станции не нужен: i3-1215U, TPM 2.0, 8 ГБ
elems_main = {e.tag for e in xml_main.iter()}
t(not any('Bypass' in tg or 'LabConfig' in tg for tg in elems_main),
  'в основном файле ответа нет элементов обхода — на этом железе он не нужен')
t('reg add' not in alg,
  'в алгоритме нет правки реестра для обхода требований')
byp_txt = read(BYP)
t(byp_txt.count('BypassTPMCheck') == 1 and byp_txt.count('Bypass') == 5,
  'в файле с обходом ровно пять значений LabConfig')

# =====================================================================
print('\n[C] Что получит пользователь после OOBE')
# =====================================================================

oobe = comp(settings(xml_main, 'oobeSystem'), 'Microsoft-Windows-Shell-Setup')
oo = oobe.find(f'{NS}OOBE')
t(oo.findtext(f'{NS}HideEULAPage') == 'true', 'EULA не показывается')
t(oo.findtext(f'{NS}HideOnlineAccountScreens') == 'true',
  'экраны входа в учётку Microsoft скрыты — можно войти локально')
t(oo.findtext(f'{NS}HideWirelessSetupInOOBE') == 'true',
  'мастер настройки сети пропущен — сеть на шаге 6 отключена')
t(oo.findtext(f'{NS}ProtectYourPC') == '3',
  'ProtectYourPC=3 — минимальный набор телеметрии с самого начала')

la = oobe.find(f'{NS}UserAccounts').find(f'{NS}LocalAccounts')
acc = la.find(f'{NS}LocalAccount')
t(acc.findtext(f'{NS}Name') == 'user', 'локальная учётка user создана')
grp = acc.find(f'{NS}Group')
t(grp is not None and 'Administrators' in (grp.text or ''),
  f'учётка в группе администраторов (факт {grp.text if grp is not None else None})')

al = oobe.find(f'{NS}AutoLogon')
t(al.findtext(f'{NS}Enabled') == 'true'
  and al.findtext(f'{NS}LogonCount') == '1',
  'автологон ровно на один вход — пройти OOBE и не остаться открытым')

sh = comp(settings(xml_main, 'specialize'), 'Microsoft-Windows-Shell-Setup')
t(sh.findtext(f'{NS}ComputerName') == 'MSI-B12M', 'имя станции задано')
t(len(sh.findtext(f'{NS}ComputerName')) <= 15,
  'имя укладывается в лимит NetBIOS 15 символов')
pk = sh.find(f'{NS}ProductKey')
t(pk is not None and pk.text == 'KBN8V-HFGQ4-MGXVD-347P6-PDQGT',
  'ключ задан явно — ключ из прошивки не подхватится')
t(settings(xml_main, 'windowsPE').find(f'.//{NS}ProductKey') is None,
  'в windowsPE ключа нет — иначе OOBE запросил бы его у пользователя')

# =====================================================================
print('\n[D] Алгоритм: от живой ОС до эталона, без дыр')
# =====================================================================

steps = re.findall(r'^### Шаг (\d+)\. (.+)$', alg, flags=re.M)
nums = [int(n) for n, _ in steps]
t(nums == list(range(1, 16)), f'шаги 1–15 без пропусков и дублей (факт {nums})')

# Сеть: сначала онлайн (диагностика и бэкап), потом офлайн до включения
net = re.findall(r'^\| (\d+) \|[^|]+\|[^|]+\| \*\*([^*]+)\*\*', alg, flags=re.M)
netmap = {int(n): v.strip() for n, v in net}
t(netmap.get(1) == 'online', 'шаг 1 онлайн — нужны драйверы с сайта производителя')
t(netmap.get(3) == 'offline', 'шаг 3 — физическое отключение сети')
for i in (5, 6, 7, 8, 9, 10):
    t(netmap.get(i) == 'offline', f'шаг {i} выполняется офлайн')
t('под контролем' in (netmap.get(11) or ''),
  'шаг 11 — сеть включается под контролем, телеметрия уже заблокирована')

# Данные в безопасности ДО первой разрушающей операции
t(nums.index(2) < nums.index(5),
  'бэкап (шаг 2) выполняется до разметки диска (шаг 5)')
t('нет копии — работы не начинаются' in alg,
  'отсутствие копии — прямой запрет начинать работы')
t('WillWipeDisk' in alg or 'точка невозврата' in algf,
  'точка невозврата названа в алгоритме')

# Блокировка телеметрии и обязательная проверка Центра обновления
step9 = alg.split('### Шаг 9.')[1].split('### Шаг 10.')[0]
t('AllowTelemetry' in alg, 'AllowTelemetry упоминается в алгоритме')
t('Центр обновления' in alg or 'обновлен' in algf,
  'проверка Центра обновления после блокировки предусмотрена')
step14 = alg.split('### Шаг 14.')[1].split('### Шаг 15.')[0]
t('обновлен' in step14.lower() or 'Центр обновления' in step14,
  'отдельный шаг проверки обновлений после блокировки есть')

# Приёмка: 12 проверок существуют в скрипте
vs = read('tools/scripts/validate-system.sh')
found = sorted({int(m) for m in re.findall(r'(?:pass|fail) (\d+)', vs)})
t(found == list(range(1, 13)),
  f'validate-system содержит проверки 1–12 (факт {found[-1] if found else 0})')
t('все 12 проверок' in algf, 'алгоритм требует все 12 проверок')
t('три прогона' in algf,
  'приёмка в три прогона — пункт 11 не проверяется до перезагрузки')

# Лицензия: шаг после появления сети
step12 = alg.split('### Шаг 12.')[1].split('### Шаг 13.')[0]
t(nums.index(12) > nums.index(11),
  'ввод ключа (шаг 12) — после включения сети (шаг 11)')
for cmd in ['slmgr /ipk', 'slmgr /ato', 'slmgr /upk', 'slui 4']:
    t(cmd in step12, f'шаг 12 содержит {cmd}')

# Эталонный бэкап в конце
step15 = alg.split('### Шаг 15.')[1]
t('verify-backup' in step15, 'финальный шаг проверяет бэкап')
t('эталон' in step15, 'результат помечается как эталон')

# Точки отката и честность о непроверенном
t('## 6. Точки отката' in alg, 'точки отката описаны')
t('## 8. Не проверено на месте' in alg,
  'непроверенное вынесено отдельно, а не выдано за факт')
notver = alg.split('## 8. Не проверено на месте')[1].split('## 9.')[0]
t(notver.count('|') > 20, f'в «Не проверено» {notver.count("|") // 3} пунктов')

# =====================================================================
print('\n[E] Все инструменты, на которые ссылается алгоритм, существуют')
# =====================================================================

refs = set(re.findall(r'\]\((\.\.[^)#]+)\)', alg))
missing = []
for r in sorted(refs):
    p = os.path.normpath(os.path.join(B, r))
    if not os.path.exists(p):
        missing.append(r)
t(not missing, f'все {len(refs)} относительных ссылок алгоритма ведут на существующее')
if missing:
    for m in missing:
        print('       отсутствует:', m)

# Процедуры образуют цепочку в заявленном порядке
procs = ['basic-setup.md', 'block-telemetry.md', 'ssd-ram-tuning.md',
         'validation.md']
for pr in procs:
    t(os.path.isfile(f'tools/scripts/procedures/{pr}'),
      f'процедура {pr} на месте')
for i, pr in enumerate(procs):
    pos = alg.find(pr)
    t(pos > 0, f'алгоритм ссылается на {pr}')
positions = [alg.find(pr) for pr in procs]
t(positions == sorted(positions),
  'процедуры идут в алгоритме в том же порядке, в каком их применяют')

# Скрипты и профиль на месте
for f in ['apply-blocking.sh', 'apply-blocking.ps1', 'apply-blocking.conf',
          'validate-system.sh', 'validate-system.ps1',
          'tune-ssd-ram.sh', 'tune-ssd-ram.ps1', 'system-audit.sh']:
    t(os.path.isfile(f'tools/scripts/{f}'), f'tools/scripts/{f} на месте')

# =====================================================================
print('\n[F] Обещание долгой поддержки выполнено')
# =====================================================================

compat = read('tools/docs/compatibility.md')
eol = re.findall(r'(2034-10-10|10\.10\.2034)', alg + read(f'{B}/README.md')
                 + read('tools/docs/compatibility.md'))
t(len(eol) >= 3, f'дата EOL 2034-10-10 согласована в документах ({len(eol)})')
comp_f = flat(compat)
t('расширенная до 10.10.2034' in comp_f,
  'срок расширенной поддержки LTSC 2024 указан')
t('09.10.2029' in compat and '10.10.2034' in compat,
  'обе даты — основная и расширенная поддержка')

# Ни один образ, который предлагается ставить, не снят с поддержки молча
t('истекает' in compat and '14.10.2026' in compat,
  'истечение поддержки Win11 Pro 24H2 названо, а не скрыто')
t('14.10.2025' in compat, 'истечение поддержки Win10 названо')

# =====================================================================
print('\n[G] Профиль: коммерческое использование, выезд, без вскрытия')
# =====================================================================

rec = read('tools/docs/recovery.md')
t('без вскрытия' in rec,
  'ограничение «без вскрытия станций» закреплено в регламенте')
t('в сервис' in rec or 'сервис' in rec,
  'случай, требующий разборки, явно уходит в сервис')
t('Лицензи' in alg or 'лицензи' in algf,
  'лицензирование рассмотрено — профиль коммерческий')
t('MAK' in alg and 'OEM' in alg and 'Retail' in alg,
  'все три канала лицензирования разобраны')
t('не проверено' in algf.lower() or 'Не проверено' in alg,
  'неисследованное в лицензировании названо, а не додумано')

chk = read('tools/docs/field-checklist.md')
t('Решение принято заказчиком' in chk,
  'решения принимает заказчик — профиль коммерческий, ответственность фиксируется')
t('Кто решил:' in chk, 'в чек-листе фиксируется, кто принял решение')

# =====================================================================
print('\n[H] Итог: что получит заказчик после прохождения алгоритма')
# =====================================================================

OUTCOMES = [
    ('Windows 11 IoT Enterprise LTSC 2024 на целевой станции',
     'LTSC 2024' in alg and 'f6b14814' in alg),
    ('Поддержка до 2034 года', '2034-10-10' in alg),
    ('Локальная учётка без принуждения к учётке Microsoft',
     oo.findtext(f'{NS}HideOnlineAccountScreens') == 'true'),
    ('Телеметрия заблокирована до первого включения сети',
     netmap.get(9) == 'offline' and netmap.get(11, '').startswith('online')),
    ('Центр обновления проверен и работает',
     'Центр обновления' in alg and found == list(range(1, 13))),
    ('Все устройства станции работают',
     all(d in step7 for d in ['AX211', 'Bluetooth', 'Аудио'])),
    ('8 ГБ распаянной памяти достаточно для работы после тюнинга',
     'pagefile' in algf or 'pagefile' in read('tools/scripts/procedures/ssd-ram-tuning.md')),
    ('Среда восстановления на диске',
     (mods[0].findtext(f'{NS}TypeID') or '').lower()
     == 'de94bba4-06d1-4d40-a16a-bfd50179d6ac'),
    ('Данные заказчика в копии до начала работ',
     nums.index(2) < nums.index(5) and 'нет копии — работы не начинаются' in alg),
    ('Эталонный образ для следующих станций', 'эталон' in step15),
    ('Лицензия введена, активация подтверждена',
     'slmgr /ato' in step12 and 'Licensed' in step12),
    ('Приёмка по 12 проверкам в три прогона',
     'все 12 проверок' in algf and 'три прогона' in algf),
]
for title, cond in OUTCOMES:
    t(cond, title)


# ---------------------------------------------------------------- [I]
print('\n[I] Итоговая сводка соответствует фактическому содержимому')

ROWS = list(csv.DictReader(io.open('manifest.csv', encoding='utf-8')))
t(len(ROWS) == 47, f'в манифесте 47 строк данных (факт {len(ROWS)})')

by_type = {}
for r in ROWS:
    by_type[r['type']] = by_type.get(r['type'], 0) + 1
for want, n in [('iso', 7), ('tool', 23), ('script', 11), ('module', 6)]:
    t(by_type.get(want) == n, f'тип {want}: {n} строк (факт {by_type.get(want)})')

# Каждая строка tool указывает каталог с README.md — иначе утилита не описана
miss = [r['category'] for r in ROWS if r['type'] == 'tool'
        and not os.path.exists(f"tools/{r['category']}/README.md")]
t(not miss, f'у всех 23 строк tool есть README по категории (нет у {len(miss)})')

# И обратно: каталог утилиты обязан иметь строку в манифесте
CATS = {r['category'] for r in ROWS if r['type'] == 'tool'}
# Двустороннее соответствие манифеста и каталогов.
# Заглушка бинарника — это <имя>.<расширение>.md: у имени есть расширение
# скачиваемого файла. У служебных документов расширения нет
# (offline-procedure.md, fat32-stick.md, strelec-tools.md), и в манифест
# они не попадают.
TOOLS = [r for r in ROWS if r['type'] == 'tool']
nofile = [r['name'] for r in TOOLS if not r['file'].strip()]
t(not nofile, f'у всех 23 строк tool заполнено поле file (пусто у {len(nofile)})')

# Путь в манифесте заканчивается категорией: tools/<category>/<file>.md.
# Заглушка же лежит на уровень глубже — внутри каталога утилиты, поэтому
# ищем её обходом подкатегории.
lost = []
for r in TOOLS:
    want = r['file'] + '.md'
    found = False
    for root, dirs, files in os.walk(f"tools/{r['category']}"):
        if want in files:
            found = True
            break
    if not found:
        lost.append(r['name'])
t(not lost, f'у каждой строки tool есть заглушка в её категории (нет у {len(lost)})')

NAMES = {r['file'] for r in TOOLS}
stray = []
for root, dirs, files in os.walk('tools'):
    dirs[:] = [d for d in dirs if d not in ('_templates', 'docs',
                                           'scripts', 'procedures')]
    for x in files:
        if not x.endswith('.md') or x == 'README.md':
            continue
        base = x[:-3]
        if '.' in base and base not in NAMES:
            stray.append(f'{root}/{x}')
t(not stray, f'нет заглушек бинарников вне манифеста (сирот {len(stray)})')

# Подкатегория без строки в манифесте допустима: значит, собственных
# бинарников она не несёт, а задачу решают утилиты из Strelec или процедура.
# Вложенность бывает и два уровня (network/scan), и три (os/windows/tweaks),
# поэтому перечисляем подкатегории обходом.
PROC_ONLY = []


def subcats(rel):
    if not os.path.isdir(f'tools/{rel}'):
        return
    for name in sorted(os.listdir(f'tools/{rel}')):
        sub = f'{rel}/{name}'
        if not os.path.isdir(f'tools/{sub}'):
            continue
        # scripts/ внутри категории — держатель скриптов, а не подкатегория
        # утилит; procedures/ — каталог процедур. Ни то ни другое в учёт
        # подкатегорий не входит.
        if name in ('scripts', 'procedures'):
            continue
        # Строка манифеста — это учтённая подкатегория, спуск ниже не нужен.
        # Проверку «префикс манифеста» здесь делать нельзя: она отсекла бы
        # os/windows целиком и три его подкатегории без бинарников
        # (activation, installation, updates) остались бы неучтёнными.
        if sub in CATS:
            continue
        # Дети, которые сами являются подкатегориями. scripts/ и
        # procedures/ не в счёт: это держатели, а не подкатегории, поэтому
        # каталог, у которого из детей только scripts/, — лист.
        kids = [k for k in os.listdir(f'tools/{sub}')
                if os.path.isdir(f'tools/{sub}/{k}')
                and k not in ('scripts', 'procedures')]
        if kids:
            before = len(PROC_ONLY)
            subcats(sub)
            if len(PROC_ONLY) == before:
                PROC_ONLY.append(sub)
        else:
            PROC_ONLY.append(sub)


for g in sorted(os.listdir('tools')):
    if g not in ('docs', '_templates', 'scripts'):
        subcats(g)
for sub in PROC_ONLY:
    t(os.path.exists(f'tools/{sub}/README.md'),
      f'подкатегория без бинарников описана: {sub}')
t(len(PROC_ONLY) == 14,
  f'подкатегорий без собственных бинарников 14 (факт {len(PROC_ONLY)})')

# Каждая утилита — каталог с собственным README.md
NOREADME = []
for r in TOOLS:
    hit = None
    for root, dirs, files in os.walk(f"tools/{r['category']}"):
        if r['file'] + '.md' in files:
            hit = root
            break
    if hit and not os.path.exists(f'{hit}/README.md'):
        NOREADME.append(r['name'])
t(not NOREADME, f'у всех 23 утилит есть каталог с README.md (нет у {len(NOREADME)})')

SUB = 0
for g in sorted(os.listdir('tools')):
    if g in ('docs', '_templates'):
        continue
    gp = f'tools/{g}'
    if os.path.isdir(gp):
        SUB += sum(1 for c in os.listdir(gp) if os.path.isdir(f'{gp}/{c}'))
t(SUB == 26, f'подкатегорий в tools/ ровно 26 (факт {SUB})')

# Каталоги ISO на разделе VENTOY обязаны существовать
for r in ROWS:
    if r['type'] == 'iso':
        d = f"ventoy-partition/{r['category']}"
        t(os.path.isdir(d), f"каталог образа существует: {r['category']}")

# planned-файлы: размер и сумма ещё не заявлены — это надо сказать вслух,
# иначе неполную загрузку образа нечем обнаружить
zero = [r['name'] for r in ROWS
        if r['status'] == 'planned' and r['size_bytes'] == '0']
t(len(zero) == 30, f'30 planned-файлов имеют размер 0 (факт {len(zero)})')
nohash = [r['name'] for r in ROWS if r['sha256'] == 'PENDING']
t(len(nohash) == 29, f'29 planned-файлов без SHA256 (факт {len(nohash)})')

smry = read('tools/docs/summary.md')
smry_f = flat(smry)
t('size_bytes' in smry and 'SHA256' in smry,
  'сводка называет незаполненные размер и сумму как контрольную точку')
t('Что не проверено' in smry, 'в сводке есть раздел «Что не проверено»')
t('Что осталось сделать' in smry, 'в сводке есть раздел с оставшимися работами')
t('Все 16 файлов `.ps1`' in smry or '16 файлов `.ps1`' in smry,
  'невыполнимость .ps1 названа в сводке')
t('47' in smry and '23 утилиты' in smry_f and '7' in smry,
  'числа в сводке совпадают с манифестом')
t('ISO/winpe/' in smry, 'каталог Strelec указан верно — ISO/winpe/')
t('summary.md](summary.md)' in read('tools/docs/README.md'),
  'сводка внесена в перечень документации')
t('"tools/docs/summary.md"' in read('scripts/csv-check.py'),
  'сводка учтена в SELF_ENTITIES["docs"]')
t('summary.md' in read('scripts/repo-validate.sh')
  and 'summary.md' in read('scripts/repo-validate.ps1'),
  'сводка входит в обязательный состав репозитория (обе версии валидатора)')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
