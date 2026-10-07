# initial_backup — первоначальный бэкап станции

Модуль снимает четыре копии, без которых любые разрушающие действия
недопустимы: образ диска, драйверы, профиль Chrome, настройки VS Code.

## Задача модуля

До начала работ станция должна быть восстановима **полностью**: и побайтово
(образ диска), и по компонентам (драйверы), и по данным пользователя (профили).

Критерий готовности: каждая копия создана, имеет манифест SHA256 и проходит
`verify-backup`.

## Состав

```
initial_backup/
├── README.md                     этот файл
└── scripts/
    ├── export-drivers.ps1        экспорт INF-драйверов (online и WinPE /Image)
    ├── export-drivers.sh         каталогизация Driver Store из Linux (только чтение)
    ├── backup-chrome.ps1         копия профиля Chrome + манифест
    ├── backup-chrome.sh          то же из Live-Linux по примонтированному разделу
    ├── backup-vscode.ps1         настройки и расширения VS Code
    └── verify-backup.ps1 / .sh   сверка копии с манифестом
```

Образ диска снимается отдельным модулем: `tools/backup/disk_image/scripts/disk-image.sh`.

## Порядок работы

| # | Действие | Среда | Сеть | Результат |
|---|----------|-------|------|-----------|
| 1 | `disk-image.sh --device /dev/nvme0n1 --destination /home/partimg --name <станция>_before` | Clonezilla Live | offline | Образ диска + дамп GPT/MBR |
| 2 | `export-drivers.ps1 -Destination <флешка>\builds\<станция>\drivers` | Рабочая ОС | offline | INF-пакеты + манифест |
| 3 | Закрыть Chrome → `backup-chrome.ps1 -Destination <флешка>\builds\<станция>\backup\profiles` | Рабочая ОС | offline | `chrome_<дата>/` + манифест |
| 4 | Закрыть VS Code → `backup-vscode.ps1 -Destination <...>\backup\profiles` | Рабочая ОС | offline | `vscode_<дата>/` + манифест + список расширений |
| 5 | `verify-backup.ps1 -Path <каждая копия>` | Рабочая ОС | offline | Код 0 по каждой копии |

Если сеть на шаге 1 недоступна, образ пишется на раздел `Tools` флешки или на
второй внешний носитель.

## Требования

- Права: администратор (Windows) / root (Linux).
- DISM для экспорта драйверов; в WinPE — **только** с ключом `/Image`,
  потому что `/Online` даёт ошибку 50.
- Свободное место: не менее размера занятых данных на диске.
- Для Chrome и VS Code — приложения **закрыты**; иначе базы SQLite копируются
  несогласованно, и скрипт отказывается работать без `-Force`.

## Коды возврата

| Код | Значение |
|-----|----------|
| 0 | Успех |
| 1 | Общая ошибка |
| 2 | Нет прав или required утилит |
| 3 | Источник/каталог не найден |
| 4 | Приложение запущено (только `backup-chrome.ps1`) |

## Риски

> Бэкап не защищает от ошибок, если он не проверен. Шаг 5 обязателен:
> непроверенная копия равна отсутствию копии.

> `Default\Login Data` в Chrome зашифрован DPAPI в контексте учётной записи —
> на другой машине пароли из копии не расшифруются. Перенос паролей только
> штатным экспортом `chrome://settings/passwords`.

> BitLocker: снимайте образ при приостановленном шифровании, иначе Clonezilla
> пойдёт через `dd` и образ будет размером со весь том.

## Исключение из правила дуальности

`disk-image.sh` не имеет `.ps1`-пары: `ocs-sr` существует только в Clonezilla
Live, то есть в Linux. Замену PowerShell-ом делать нечем, поэтому модуль
сознательно односторонний — отклонение зафиксировано здесь, а не замолчано.

## Проверка модуля

```bash
# dry-run всех скриптов
bash ../disk_image/scripts/disk-image.sh -d /dev/nvme0n1 -D /tmp/img -n test --dry-run
bash export-drivers.sh --device /dev/nvme0n1p3 --destination /tmp/drv --dry-run
bash backup-chrome.sh --source <профиль> --destination /tmp/prof --dry-run

# реальная проверка целостности
bash verify-backup.sh --path <каталог копии>
```
