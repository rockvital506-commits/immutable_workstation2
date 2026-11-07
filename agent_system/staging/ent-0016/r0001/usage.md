# ENT-0016 r0001 — read-only проверка private trial по внешнему manifest pin

## Назначение, источник и независимость

Protocol, depends_on ENT-0015 r0001; normative этот текст,
[read.py](read.py), [verify.py](verify.py). Основание — задание B, проверка точного
неполного комплекта и условное делегирование владельца после проверок. Это summary,
не новая прямая цитата одобрения конкретных bytes. Частная архитектура/built-in
инструкции не извлекались. Реальных release/revoke/activate событий этап не создаёт.

Reader отдельно открывает существующий trial, проверяет его bytes и повторяет
архивную семантику. Он не вызывает stage_trial, не доверяет существованию
trial.json как completion marker и не принимает отчёт writer вместо чтения.
Независимость ограниченная: переиспользованы pinned directory/fingerprint/binding
helpers ENT15 и прежние ENT13/14/9/6 loaders, не независимая реализация всего стека.
Новых библиотек нет. Код берётся только из доверенной установки, не из trial.

**consistent_archived_trial — согласованность прочитанных архивных bytes**, не
доказательство исполнения ENT15, истинности source, полноты ledger или текущих
прав. current_permissions=not_evaluated; release/export/activation/transition=false,
overall_admission=not_evaluated. Новый результат не снимает blocked ENT14 и не
представляет incomplete candidate полноценным совместимым выпуском.

## API, доверие и фиксированная область

```python
read_trial(run_id, expected_manifest)
```

run_id — canonical lowercase UUID; expected_manifest — внешние sha256/size_bytes,
строго native integer 0–16 MiB и lowercase 64-hex digest. Ожидание задаётся caller
из доверенного основания, например отдельно сохранённого успешного receipt;
вычислить hash неизвестного trial.json — не аутентифицировать его. Receipt reader
не потребляет и не доказывает его авторство/факт исполнения writer.

Читается только installed BASE/local/trials/run_id/{trial.json,objects/sha256}.
Произвольные path/source/destination/import arguments отсутствуют. Нет discovery
всего local или live каталога решений. Нельзя направить run_id/manifest logical
paths на внешний файл. Перенос чужого дерева сюда, адаптация прав/uid и чтение
произвольных архивов этим не реализованы — это **private local reader**, не importer.

Поддержан Linux x86-64, без Windows/junction/иных архитектур/fallback. Предполагаются
доверенная не concurrently writable противником установка и private namespace без
hostile same uid/root. Три pins ENT15 проверяются до загрузки; прежние loaders
проверяют transitive pins/schema, retrieval иных URI запрещён. Собственный ENT16
учитывается отдельно обычным approval установки, без self-hash. Сохраняется
check→runpy TOCTOU ограничение; hashes не подписи и не owner authentication.

## Получение bytes без исполнения содержимого

1. До output/source доступа проверить UUID/внешний pin/platform. Открыть trusted
   BASE, затем существующие local/trials/run/objects через readonly directory fds,
   O_DIRECTORY/O_NOFOLLOW; create=False, без mkdir/chmod/исправления прав.
2. Проверить euid/permissions/st_dev через прежний directory helper. local не
   group/other writable; trials/run/objects private. В run ровно objects и trial.json.
3. Прочитать manifest под fd: O_RDONLY/O_NOFOLLOW/O_NONBLOCK, regular file,
   euid, mode600, nlink=1, same st_dev, expected size, bounded чтение и hash.
   Before/after fingerprint и name↔opened inode должны совпасть.
4. Strict UTF-8/LF JSON без BOM/duplicate keys/non-JSON constants, один конечный LF;
   закрытый manifest profile ENT15 r0001 и тот же run_id. Все gates false,
   readiness=incomplete_candidate. Native sizes/refs, sorted unique logical paths,
   ограничения количества/сумм. Manifest не исполняется и не выбирает код.
5. В objects inventory ровно множество referenced digests. Никаких extra/missing
   files; конфликтующие sizes для digest отвергаются. Открывать только validated
   digest basename, не logical path из payloads/decisions. Те же type/uid/mode/
   nlink/size/hash/fingerprint проверки. Capture каждого raw object в память.
6. ENT13 consistency получает **только captured bytes** candidate/registry/ledger/
   payload. Проверяются frozen records, approvals/closure/core/refs/gaps; затем
   ENT6 проверяет archived stage_trial и read_trial в literal agent_system.trial.
   Known archive block не игнорируется. Статический AST locator не исполняет Python.
7. Сопоставить before/after directory fingerprints/inventories, повторно прочитать
   manifest/объекты по тем же pins (это наблюдение, не замена captured inputs),
   вновь проверить inventories и directory bindings. Закрыть все fds.

Нет os.write/mkdir/chmod/fsync/rename/unlink в reader path. Обычные чтения могут
изменять atime средствами ОС; read-only не обещает нулевых метаданных на уровне
носителя. Нормальная загрузка зависимостей принадлежит доверенной установке,
не trial. Ошибки не исправляются, extra files не удаляются, отсутствующий run
не создаётся и сборка не перезапускается автоматически.

Type/permissions/symlink/FIFO/hardlink/changed bytes/inventory/binding дают failed;
unsupported platform/tools — unsupported; известный архивный запрет —
blocked_known_scope с ARCHIVED_KNOWN_SCOPE_BLOCK. Диагностика только codes,
без произвольного содержимого/абсолютных путей. При любом результате права false.
Успех возвращает manifest/candidate/registry refs и counts, не payload bytes,
не пересобранное дерево и не команды исполнения/активации.

## Лимиты и пределы наблюдения

Manifest до 16 MiB, каждый object до 16 MiB; registry+payloads+decisions до
64 MiB/10000 entries; candidate дополнительно до 16 MiB. Unique objects максимум
10001, до 80 MiB captured object bytes, manifest отдельно. Это не глобальная
CPU/RAM quota: parser/semantic checks и повторное чтение требуют ресурсов.
Size/type проверяется до чтения, FIFO открыт nonblocking и отвергается как nonregular.

Destination/source mount adaptation нет. Разные st_dev отвергаются, но это не
openat2 NO_XDEV и не доказательство отсутствия privileged same-device bind mounts.
Один directory capability и повторные наблюдения не дают atomic snapshot,
отсутствие всех кратких изменений или неизменность после возврата. Повторный readback
ловит сохраняющуюся порчу после первичного capture, но не историю всех изменений.
Нельзя объявлять эту модель защитой от concurrent hostile same uid/root.

## Архивный ledger и текущие разрешения

Используется **ровно ledger, записанный в manifest**, с archived registry.
Scope относится только к нему и selected candidate payload. Reader не читает
сегодняшние catalog/registry.json и catalog/approvals, не обещает отсутствие новых
restrict/revoke и не считает архивный approval актуальным разрешением.

Дальнейшее затронутое действие требует нового отдельного run с актуально объявленными
известными решениями/внешними ожиданиями; нужна самостоятельная модель сравнения
архивного состава с новым ledger. Её здесь нет. Ни старый pin, ни новый агент,
ни consistent_archived_trial не разрешают release/export/activation автоматически.

Последовательно сфабрикованный manifest/снимок может пройти consistency: это
намеренно проверяется отдельным тестом. execution_authentication/manifest_authentication,
source authentication/global completeness/coverage claim truth/поведение/новая
среда/current_decisions остаются not_checked. Неполный состав не меняет статус
готовности от числа зелёных tests или наличия этого reader.

## Тестирование и оценка решения

В подготовленной изолированной среде:

```sh
python agent_system/staging/ent-0016/r0001/verify.py
python tests/run-all.py
```

Fixtures используют реальный temporary object store ENT15; негативные изменения
файлов/ссылок/прав физические, без подмены file type/stat. Synthetic restriction
остаётся только в fixture. Тесты независимого чтения не подтверждают безопасность
импорта произвольных foreign trees или практическую работу агента в новой среде.

Выбран fixed private root + внешний pin + capture/replay вместо доверия receipt
или выполнения файлов. Плюсы: отдельная byte acquisition, отсутствие path materialization,
ограниченный input surface, переиспользование точных helpers. Цена: повторное чтение,
память под captured bytes и зависимость от общего trusted стека; реализации не
независимы для аудита общего дефекта. Это обоснование ограниченной результативности/
эффективности, не benchmark превосходства. Альтернатива произвольного root/import
отложена; тихое обновление archived ledger на live отвергнуто как смешение смыслов.

Снимок не редактировать для устранения ошибок: сохранить диагностику и построить
новый trial/run по согласованному процессу. Изменение самого ENT16 проходит immutable
versioning/согласование/проверки; старые данные и версии не отзываются автоматически.
