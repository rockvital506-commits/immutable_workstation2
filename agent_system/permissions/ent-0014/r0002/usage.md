# ENT14r2 — owner-controlled local permission recognition

## Назначение, состав, источник, статус

Protocol для области разрешений agent_system. Full revision: authority.py,
permissions.schema.json, verify.py, usage.md, procedure.md. Точный status/scopes/
hashes/approval — единый registry. Источник — задание B, R4, явный выбор владельцем
варианта A и условное делегирование implementation после проверок. Это не источник
нового разрешения на конкретный выпуск/export/activation. Нет скрытых platform
instructions/частной архитектуры. Depends_on ENT14r1; supersedes r1 не отзывает и
не переключает его consumers. Старые r1 proposals и entity event types не меняются.

**Это R4/I1:** positive authority semantics и native guard существующего incomplete
candidate, не полный permission manager/exporter/readiness verifier. Ни один вызов
этой revision не возвращает performed/transition_allowed/release_allowed/
export_allowed/activation_allowed=true. Positive recognition означает только
exact intent в явно доверенно объявленном context. Effective transitions закрыты.
Общий допуск not_evaluated. Новые реальный grant store/current-head adapter/claims
и coverage verifier не созданы. Положительный actual compatible release не заявлен.

## API / local authority boundary

```python
establish_local_authority(context_bytes, expected_context,
                          trust_owner_controlled_context=True)
evaluate_permission(request_bytes, expected_request, subject_bytes,
                    expected_subject, event_blobs, *, authority,
                    expected_current_context)
check_current_candidate(request_bytes, expected_request, subject_bytes,
                        expected_subject, event_blobs, *, authority,
                        expected_current_context, proposal_bytes, expected_proposal,
                        candidate_bytes, expected_candidate, registry_blob,
                        entity_decisions, payloads, release_request_bytes=None)
```

Factory и evaluator использовать из одного trusted module instance. Context
объект содержит immutable bytes, не serializable transferable capability; другой
instance требует нового establishment. Прямой Python caller доверенный: этот
объект/ack не неподлежащее подделке sandbox boundary. Нельзя считать объект
аутентифицированным из-за имени класса. Исходные dictionaries/context JSON не
принимаются как authority object. Не принимать commands/modules/callbacks из data.

Explicit True (не1/string), external pin и closed schema обязательны. Они
**не** доказывают происхождение context: protected caller/operator обязан независимо
закрепить exact owner decisions и текущее ожидаемое context, не выводить allowlist
из тех же source bytes. Raw actor_role/flag в event не являются trust anchor и
закрытой schema не допускаются. Source-derived pin, предъявленный trusted caller
как external, pure функция отличить не может. Нельзя обещать provenance detector.

Источник согласия/полный текст/форма цитата или summary сохраняются оператором
отдельно в разрешённом private основании. r2 не получает/аутентифицирует сообщение
владельца и не реализует importer/storage этих оснований. approved_events —
явное attestation trusted context, не самостоятельное доказательство owner согласия.
«Продолжай разработку»/approve_revision/отсутствие запрета не owner grant.
Новый host/agent не наследует authority автоматически; bootstrap отдельный.
Не запрашивать секреты/ключи в чате и не экспортировать private context по умолчанию.

## Closed documents и точные связи

permissions.schema.json содержит локальные определения, без remote retrieval.
Strict UTF8/LF/noBOM/no duplicate keys/NaN/CR, один final LF; native int (не bool/
float) sizes/generation и canonical lowercase UUID.16MiB/document,10000events/
list entries,64MiB aggregate evaluator inputs. Native wrapper дополнительно
ограничивает общий набор своих documents/bytes до10000/64MiB до hashes.
Это input bounds, не RAM/CPU quota/atomic snapshot.

Context: profile owner-controlled-local-r0001, context_id/generation, exact sorted
known_events path/SHA/size и approved_events event UUID/SHA/size (subset известных).
Каждый предъявленный event должен быть в owner-approved set; unapproved event
не игнорируется. Map ровно known set; paths permission-events/UUID.json, ID/path
связаны. Остальные относительные paths без empty/dot/dotdot/backslash/colon/control,
но не являются безопасным destination: filesystem guards нужны отдельному actuator.
Context generation/current expected pin сравниваются, не объявляются свежими сами.

Subject — pinned **description**: candidate/registry/entity_decisions/artifacts,
coverage_description/procedure/prompt refs. Exact composition/coverage по одним
этим opaque refs evaluator не проверяет. Subject bytes закрыты, refs связаны;
actual composition требует native wrapper/будущего verifier. Пустой artifacts
набор недопустим. Entity stream отделён от permission stream, но для actuation
нельзя опускать ни один. Не фильтровать known negatives/unknown events.

Events: authorize_release/authorize_export/deny_permission/revoke_permission.
Action одна release или export, literal scope соответствует agent_system.release
или agent_system.transfer. Release event не содержит parent/export/target.
Export event содержит exact release parent UUID+hash+size, того же subject;
paths ровно полный subject artifact allowlist, destination/procedure/prompt pins
и export_id. Request export bytes должны соответствовать всему export descriptor.
Destination pin только описание, не root identity/safe filesystem capability.

Deny cumulative по exact subject/action; release deny блокирует зависимый export,
export deny сам release не блокирует. Revoke targets exact authorize UUID/hash/
size/subject/action. Revoked release блокирует его export; revoke export не
отзывает release. Другой явно owner-approved grant не resurrect старый; deny
всё равно имеет приоритет. Нет latest/date priority, wildcard/lift/regrant-over-deny/
semantic correction. Unresolved targets/colliding IDs/unknown shapes fail closed.
Не заявляется удаление исторически выполненного факта при revoke.

Event не ссылается на содержащий его context: basis — сам exact subject с refs
entity basis. Context с event refs строится после событий, без self-hash cycle.
Request фиксирует current declared context/generation/subject/selected grant и
export descriptor. Любая смена требует новых request bytes/pin, не редактирования
старой истории. Runtime decisions не подмешиваются в catalog/approvals: старый
ENT7 остаётся fail-closed на неподдержанные типы, нет silent event filtering.

## Результаты и native incomplete profile

permission_granted_in_declared_context, authority_valid=true, recognized release/
export — согласованность точного intent и scoped known permission stream внутри
предъявленной authority. blocked_known_permission — известный deny/revoke.
failed/unsupported — binding/schema/profile failure. Report содержит pins context/
request/subject/grant, static checks/diagnostic codes, без raw objects/free text.
Отрицательный native result может сохранить authority recognition: это не
разрешает action и показывает, какое независимое условие не выполнено.

check_current_candidate связывает subject с actual proposal/candidate/registry/
полным entity ledger/payload и установленными ENT12r1 governance/prompt refs.
Для текущего ENT13r1 coverage_description — exact candidate descriptor с coverage
rows, **не** доказательство truth этих rows. Вызывается installed ENT14r1 без
внешнего child report или injected verifier. Он проверяет old candidate/scoped
entity restrictions; возвращает blocked_incomplete_candidate/readiness=incomplete
либо иной реальный отказ. Re-label ready=true не добавляет поддержку ready profile.

Pure evaluator не читает source/trial/ledger namespace, не пишет data и не
исполняет код из входов. Загружаются только protected installed old tools/schema
по fixed pins; own code trust обеспечивается установкой/caller. Hash-before-load
не защищает concurrently hostile writable installation. Same-uid/root/kernel/
truth of observations/current global completeness не доказываются.

## Не реализовано и почему это нельзя обходить recognition-флагом

Повтор одинакового old context/request может вновь пройти **consistency**.
expected_current_context должен приходить из независимо управляемого current
state; передать туда старый pin — не freshness proof. One export_id не является
single-use claim. До R5 stateful claim/current-head/guarded destination и R6
coverage readiness никаких actual transitions. Нельзя использовать recognized
flags вместо always-false action flags или выдавать fabricated coverage за ready.
Никаких timestamp filenames/latest, auto rollback/delete/export/activation.

## Обоснование, стоимость и проверки

Thin bytes-only layer поверх неизменного ENT14r1 вместо crypto framework или
переписывания entity event evaluator. Плюсы: явная external authority boundary,
positive/negative semantics, точные independent conditions и reuse native guard.
Цена: дополнительные schema/hash parsing/пять immutable files, operator judgement
и сохранение private source оснований вне этой функции. Риски self-attestation,
rollback/TOCTOU и coherent fabricated context остаются; strong authentication
или universal speedup не заявлены. Dependencies прежние isolated jsonschema/base.

verify.py:44methods, synthetic owner-reviewed contexts только fixtures;
часть NativeGuardTests использует actual installed candidate/registry/payload/ledger
и настоящий old checker без loader/child substitution. Это не actual owner grants,
не ready compatible composition, не single-use/export/activation integration.
Применение/открытые ограничения — procedure.md; runtime records private вне Git.
