# ENT-0016 r0002 — guarded private trial capture

## Полный состав, источник и зависимости

Protocol agent_system.trial: read.py, verify.py, usage.md. Основание — задание B,
условное делегирование после проверок и M1 D08–D09; источник реализации — r0001.
Состояние согласования фиксирует единый registry. Depends_on ENT-0015 r0001
(runtime pinned helpers) и ENT-0016 r0001 (только compatibility parity verifier).
Supersedes r0001 не отменяет прежние решения и не перенаправляет старые consumers.
ENT17r1 продолжает загружать свои pinned r1 helpers. Новых dependencies нет.

## API и общий worker

```python
read_trial(run_id, expected_manifest)     # metadata dict
capture_trial(run_id, expected_manifest)  # {'result': metadata, 'capture': ...}
```

Expected_manifest — обязательный внешний {sha256,size_bytes}, native integer
0–16 MiB и lowercase SHA-256; run_id — canonical lowercase UUID. Не вычислять
ожидание из неизвестного файла как замену доверенного основания. Writer receipt
может закрепить bytes, но не аутентифицирует исполнение/полномочия.

Обе функции используют один _worker с прежним secure-read pipeline. Capture API
не вызывает r1 read_trial и не перечитывает paths после завершённой проверки.
После открытия fixed private local/trials/UUID/objects выполняются: inventory,
manifest pin/shape/profile/permissions, exact object refs/metadata, candidate
replay, archived stage_trial/read_trial scope checks, повторные inventories,
контрольные readbacks всех файлов и final directory bindings. FDs закрываются
до выдачи успешного capture. При успехе:

```python
{'result': {'status': 'consistent_archived_trial', ...},
 'capture': {'manifest_bytes': bytes, 'objects': {sha256: bytes}}}
```

Возвращаются **первые** captured inputs; readback outputs не становятся новым
snapshot. Objects — собственный dict с immutable byte values. В read_trial нет
raw maps. Metadata profile теперь ent-0016-r0002-private-trial-capture; on-disk
ENT15 manifest/profile не изменён. Это новая producer revision, не новый формат
архива. Успех означает согласованность архивных bytes, не факт исполнения writer.

Любой completed failed/blocked/unsupported run имеет capture=None — в том числе
после успешной acquisition, но failed semantic/scope/readback/binding проверки.
Unknown failure/interruption не переводятся в успех и могут не вернуть результат.
Нет stale fallback. Функция не пишет/chmod/удаляет/выполняет input code, не чинит
архив и не создаёт trial. Caller проверяет exact refs при handoff/storage.

## Trust, приватность и пределы

Прежние три installed artifact pins ENT15 проверяются до загрузки; остальные
helpers транзитивно pinned. Код только из trusted installation, не trial; kernel,
interpreter, proc и namespace должны быть доверенными. Hash-before-runpy не даёт
атомарной загрузки против writer установленного дерева. Same-uid/privileged attacker
и same-device hostile mount не покрыты. Только Linux x86-64; nonportable profile
не является универсальной совместимостью. FD bindings/inventories/readbacks не
создают атомарный snapshot и не обнаруживают все временные изменения.

Сохраняются 0700 private dirs/0600 regular single-link owner files, NOFOLLOW,
nonblocking open, same-device checks, stable file fingerprints/имена, exact pins.
16 MiB/document/object, до 10000 registry+payload+decision entries/64 MiB; candidate
объект отдельно, итого до 10001 objects/80 MiB. Полного RAM/CPU quota нет.
Raw maps удерживаются дольше; dict copy не копирует immutable byte buffers.

Capture/manifest/objects могут быть приватными: не печатать/публиковать/коммитить/
экспортировать автоматически. Без secret detector/автоматической классификации.
Private coordinator journal и handoff policy остаются отдельной задачей.
Current permissions/overall admission not_evaluated; release/export/activation/
transition false. Live ledger не открывается автоматически. Нет доказательства
freshness/global completeness/authenticity/поведения/среды/разрешений.

## Оптимизация, альтернативы, проверки

Один worker предпочтительнее read_trial+reread (другая гонка между проверкой и
handoff) и runtime patch r1 (неявный интерфейс/подмена границ). Плюсы: первые
проверенные bytes доступны без лишнего snapshot, прежний replay и consumer pins
сохраняются. Минусы: новая raw поверхность, in-memory retention, обязанность caller
защитить maps и проверить дальнейшую связь. Производительность на всех нагрузках
не подтверждена benchmark; уменьшать guards ради скорости нельзя.

verify.py: 41 metadata case и те же 41 capture mirror с exact/withholding checks,
12 дополнительных handoff cases: parity кроме profile, одинаковое число secure
reads на поверхность (включая обязательные guard readbacks), owned maps, no stale
reuse, late readback/binding failure, first-input retention, FD cleanup,
interruption/unknown error, no writes, exact refs, metadata без raw maps.
Синтетические проверки не являются практикой реального поведения агента или
полной coordinator acceptance matrix. Библиотеки — прежний isolated jsonschema
с обязательными dependencies по hash-lock; новые сторонние решения не добавлены.
