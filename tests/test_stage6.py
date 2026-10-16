# -*- coding: utf-8 -*-
"""Проверки Этапа 6 — автоустановка и persistence.

Решения владельца от 2026-10-15:
  1. Для каждой задачи и каждой сборки — СВОЙ файл ответа; лежит в каталоге
     сборки, а не в общем ventoy/autoinstall/. В algorithm.md — точные
     указания: куда положить и какие строки ventoy.json править.
  2. Шаблон установки Linux Mint (preseed) НЕ нужен: Mint используется как
     Live с persistence.
  3. Локальная учётная запись: имя + пустой пароль.
  4. Обход требований (LabConfig) — отдельный файл, не ключ в общем.

Обоснование — research/16-autoinstall-persistence.md, CONVENTIONS.md §6.
"""
import csv, io, json, os, re, sys
from baseline import expected
import xml.etree.ElementTree as ET

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


ANS = 'ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/answer'
MAIN = f'{ANS}/autounattend-ltsc-2024.xml'
BYPASS = f'{ANS}/autounattend-ltsc-2024-bypass.xml'
ALG = ('ventoy-partition/builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/'
       'algorithm.md')
AI_README = 'ventoy-partition/ventoy/autoinstall/README.md'
VJSON = 'ventoy-partition/ventoy/ventoy.json'

with io.open('manifest.csv', encoding='utf-8') as f:
    body = [r for r in list(csv.reader(f))[1:] if r]

# --- [1] Состав ------------------------------------------------------------

print('\n[1] Состав Этапа 6')
for p in [MAIN, BYPASS, f'{ANS}/README.md', AI_README, VJSON, ALG]:
    t(os.path.isfile(p), f'на месте {p}')
t(not os.path.isfile('ventoy-partition/ventoy/autoinstall/autounattend.xml'),
  'в общем каталоге файла ответа нет (правило CONVENTIONS §6)')
t(not os.path.isfile('ventoy-partition/ventoy/autoinstall/diskpart-256gb.txt'),
  'ненужный diskpart-256gb.txt не создан (R1)')

# --- [2] XML: корректность, кодировка, проходы -----------------------------

print('\n[2] Файлы ответа: XML, кодировка, проходы')
for p in [MAIN, BYPASS]:
    rel = os.path.basename(p)
    raw = open(p, 'rb').read()
    t(raw.decode('utf-8') is not None, f'{rel}: UTF-8 декодируется')
    t(raw[:3] != b'\xef\xbb\xbf', f'{rel}: без BOM')
    t(b'\r\n' not in raw, f'{rel}: переводы строк LF')
    try:
        ET.parse(p)
        ok(f'{rel}: XML корректен')
    except Exception as e:
        bad(f'{rel}: XML корректен ({e})')
    s = io.open(p, encoding='utf-8').read()
    # N1: без прохода windowsPE Setup не кэширует файл и молча уходит в
    # ручной режим.
    t('pass="windowsPE"' in s, f'{rel}: есть проход windowsPE (N1)')
    t('pass="specialize"' in s, f'{rel}: есть проход specialize')
    t('pass="oobeSystem"' in s, f'{rel}: есть проход oobeSystem')
    t('SetupUILanguage' in s, f'{rel}: задан язык установщика')
    t('DiskConfiguration' in s, f'{rel}: разметка задана DiskConfiguration')
    t('ImageInstall' in s, f'{rel}: есть выбор образа')
    # N2: жёсткий DiskID 0 может поставить ОС на флешку Ventoy.
    t('$$VT_' in s, f'{rel}: диск задан переменной Ventoy (N2)')
    t('<DiskID>0</DiskID>' not in s, f'{rel}: нет литерального DiskID 0')
    # Разметка GPT из N10.
    for size in ['500', '260', '128']:
        t(f'<Size>{size}</Size>' in s, f'{rel}: раздел {size} МБ')
    t('DE94BBA4-06D1-4D40-A16A-BFD50179D6AC' in s,
      f'{rel}: GUID раздела WinRE')
    t('<Extend>true</Extend>' in s, f'{rel}: раздел Windows на остаток')
    # Решение владельца: имя + пустой пароль.
    t('<PlainText>true</PlainText>' in s, f'{rel}: пароль пустой (PlainText)')
    t('<LogonCount>1</LogonCount>' in s, f'{rel}: AutoLogon на один вход')
    t('HideOnlineAccountScreens' in s, f'{rel}: экраны онлайн-учётки скрыты')

# --- [3] Обход требований — отдельный файл --------------------------------

print('\n[3] LabConfig: отдельный файл (решение владельца)')
main = io.open(MAIN, encoding='utf-8').read()
byp = io.open(BYPASS, encoding='utf-8').read()
t('reg add' not in main, 'основной файл НЕ вносит LabConfig')
for k in ['BypassTPMCheck', 'BypassSecureBootCheck', 'BypassRAMCheck',
          'BypassStorageCheck', 'BypassCPUCheck']:
    t(f'/v {k} ' in byp, f'bypass-файл вносит {k}')
t(byp.count('RunSynchronousCommand wcm:action="add"') == 5,
  'bypass-файл: ровно 5 команд LabConfig')
t('$$VT_WINDOWS_DISK_NONVTOY_CLOSEST_256$$' in main,
  'основной файл: диск ближайший к 256 ГБ (NVMe станции)')
t('$$VT_WINDOWS_DISK_1ST_NONVTOY$$' in byp,
  'bypass-файл: первый не-Ventoy диск (железо произвольное)')

# --- [4] algorithm.md: точные указания ------------------------------------

print('\n[4] Шаг 6 алгоритма: куда положить и что править')
alg = io.open(ALG, encoding='utf-8').read()
step6 = alg.split('### Шаг 6.')[1].split('### Шаг 7.')[0]
# Markdown переносит длинные строки, в том числе внутри инлайн-кода, поэтому
# сопоставление идёт по тексту с нормализованными пробелами. Иначе проверка
# «Check plugin json configuration» падала на переносе между словами.
step6_flat = re.sub(r'\s+', ' ', step6)
t('answer/autounattend-ltsc-2024.xml' in step6, 'шаг 6: назван файл из answer/')
t('autounattend.xml' in step6_flat and
  ('переименов' in step6_flat.lower() or
   'Имя при копировании меняется' in step6_flat),
  'шаг 6: сказано про переименование в autounattend.xml')
t('НЕ В КОРЕНЬ ФЛЕШКИ' in step6, 'шаг 6: запрет класть в корень флешки (N3)')
t('builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2/autounattend.xml' in step6_flat,
  'шаг 6: точное значение template для ventoy.json')
t('НЕ ДОБАВЛЯТЬ' in step6_flat and 'autosel' in step6_flat,
  'шаг 6: запрет timeout и autosel (N5)')
t('Panther' in step6, 'шаг 6: диагностика через C:\\Windows\\Panther (N4)')
t('WillWipeDisk' in step6,
  'шаг 6: точка невозврата названа — начало установки')
t('Check plugin json configuration' in step6_flat,
  'шаг 6: проверка конфигурации через F5')

# --- [5] README autoinstall/ приведён к факту ------------------------------

print('\n[5] README autoinstall/ приведён к факту')
rd = io.open(AI_README, encoding='utf-8').read()
t('diskpart-256gb.txt' not in rd or 'не нужно' in rd,
  'README не обещает diskpart-256gb.txt как состав')
t('windowsPE' in rd, 'README: правило про проход windowsPE (R4)')
t('$$VT_' in rd, 'README: правило про переменные (R4)')
t('корень' in rd.lower(), 'README: правило про корень флешки (R5)')
t('autosel' in rd and 'timeout' in rd, 'README: семантика timeout/autosel (R3)')
t('builds/' in rd and 'CONVENTIONS.md' in rd,
  'README: отсылает файлы ответа в каталог сборки')
t('| > 0 |' in rd or 'не задан' in rd, 'README: таблица семантики ключей')

# --- [6] ventoy.json: режим ожидания выбора --------------------------------

print('\n[6] ventoy.json')
with io.open(VJSON, encoding='utf-8') as f:
    cfg = json.load(f)
t('auto_install' in cfg, 'блок auto_install есть')
t('persistence' in cfg, 'блок persistence есть')
for entry in cfg.get('auto_install', []):
    t('parent' in entry, 'auto_install: используется parent, а не image (K3)')
    t('image' not in entry, 'auto_install: ключа image нет')
    t('timeout' not in entry, 'auto_install: timeout не задан (N5)')
    t('autosel' not in entry, 'auto_install: autosel не задан (N5)')
for entry in cfg.get('persistence', []):
    t('image' in entry and 'backend' in entry,
      'persistence: заданы image и backend')
    t(entry.get('backend', '').endswith('.dat'),
      'persistence: бэкенд — .dat, а не .img (N12)')
    t('casper-rw' in entry.get('backend', ''),
      'persistence: метка casper-rw для Mint (N11)')

# --- [7] preseed не создаётся (решение владельца) --------------------------

print('\n[7] Linux Mint: persistence, не установка')
import glob
t(not glob.glob('ventoy-partition/ventoy/autoinstall/*.seed') and
  not glob.glob('ventoy-partition/ventoy/autoinstall/*.cfg'),
  'preseed/kickstart не создан: Mint используется как Live')
t(os.path.isfile('ventoy-partition/ventoy/persistence/image_conf.json'),
  'persistence/image_conf.json на месте')
t(os.path.isfile('ventoy-partition/ventoy/persistence/'
                 'linuxmint-22.3-cinnamon_casper-rw_16GB.dat.md'),
  'заглушка persistence.dat на месте')
pers = io.open('ventoy-partition/ventoy/persistence/README.md',
               encoding='utf-8').read()
t('casper-rw' in pers, 'persistence/README: метка casper-rw')
t('CreatePersistentImg' in pers or 'sync' in pers,
  'persistence/README: есть команда создания или указание про sync')

# --- [8] manifest.csv -----------------------------------------------------

print('\n[8] manifest.csv')
by_name = {r[2]: r for r in body}
t('station_answer' in by_name, 'строка station_answer есть')
if 'station_answer' in by_name:
    t(by_name['station_answer'][0] == 'module', 'station_answer: type = module')
    t(by_name['station_answer'][1] ==
      'builds/MSI_B12M-211RU_Win11_LTSC_IoT_24H2',
      'station_answer: category — каталог сборки')
t(len(body) == expected('manifest_rows'),
  f"строк данных {expected('manifest_rows')} (факт {len(body)})")

# --- [9] Правило закреплено в CONVENTIONS ---------------------------------

print('\n[9] Правило файла ответа в CONVENTIONS.md')
conv = io.open('CONVENTIONS.md', encoding='utf-8').read()
t('Правило файла ответа' in conv, 'раздел правила существует')
t('свой файл ответа' in conv.lower() or 'свой файл ответа' in conv,
  'правило: для каждой сборки свой файл')
t('куда положить' in conv.lower() and 'ventoy.json' in conv,
  'правило: требует указаний по ventoy.json в algorithm.md')
t('windowsPE' in conv, 'правило: упоминает обязательный проход')

# --- [10] Относительные ссылки --------------------------------------------

print('\n[10] Относительные ссылки в файлах Этапа 6')
broken = 0
for md in [f'{ANS}/README.md', AI_README, ALG, 'CONVENTIONS.md',
           'research/16-autoinstall-persistence.md']:
    base = os.path.dirname(md)
    src = io.open(md, encoding='utf-8').read()
    src = re.sub(r'`[^`\n]*`', '', src)
    src = re.sub(r'```.*?```', '', src, flags=re.S)
    for m in re.finditer(r'\]\(([^)#]+)\)', src):
        link = m.group(1).split('#')[0]
        if not link or link.startswith(('http://', 'https://', 'mailto:')):
            continue
        if not os.path.exists(os.path.normpath(os.path.join(base, link))):
            bad(f'{md}: битая ссылка {link}')
            broken += 1
t(broken == 0, f'битых ссылок нет (найдено {broken})')

# --- [11] Регрессия -------------------------------------------------------

print('\n[11] Регрессия')
for p in ['tools/scripts/system-audit.sh',
          'tools/scripts/procedures/block-telemetry.md',
          'tools/os/windows/gpo_lock/LGPO/LGPO.exe.md',
          'research/15-automation-scripts.md',
          'tests/test_stage5.py']:
    t(os.path.isfile(p), f'на месте {p}')

print(f'\nИтог: проверок {checks}, ошибок {errors}')
sys.exit(1 if errors else 0)
