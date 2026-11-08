# ENT14r3 — private local assent/current-head/check-once controller

## Назначение, источник, состав и статус

Full revision protocol: state.py, state.schema.json, verify.py, usage.md,
procedure.md. Scopes/hashes/approval/status — единый registry, не этот текст.
Источник — задание B, R4, выбранный владельцем A и conditional implementation
делегирование после проверок. Частная архитектура/hidden platform instructions
не перенесены. Exact depends_on ENT14r2 + ENT15r1. supersedes r2 не отзывает и
не переключает r2/старых consumers. Изменённый API — отдельный явный local profile,
не прозрачная подмена прежних pure functions. r2 используется как точная dependency,
не копируется как второе нормативное ядро.

Это R4/I2a: private source assent records, immutable generation/hash-parent chain,
cooperative lock и exactly-once **check recording** в сохранённой цепочке. Не action
claim/export manager/готовность/activation. Все action/performed flags false.
Наличие owner statement/quote/summary в файле не доказывает происхождение/смысл
согласия: bootstrap trust остаётся у явно доверенного local operator (вариант A).

## API и workflow

```python
create_store(trust_owner_controlled_namespace=True)
AuthorityStore(store_id, expected_head,
               trust_owner_controlled_namespace=True)
store.summary()
store.context_packet()
store.import_assent(event_bytes, expected_event, assent_bytes, expected_assent,
                    subject_bytes, expected_subject, attest_exact_owner_assent=True)
store.check_once(request_bytes, expected_request, subject_bytes, expected_subject)
```

AuthorityStore — context manager; закрывает собственные FDs/lock. Explicit True
обязателен (не1/string). store_id canonical UUID; expected_head внешний SHA/native
size сохранённого receipt. Нет arbitrary root из входного data: fixed protected
installation/local/permission-authority/UUID. Установка/namespace/interpreter
owner-controlled, не concurrently writable недоверенным source. Новый protected
caller не получает bootstrap authority из history. При потере external head
нельзя автоматически принять найденную «последнюю» папку/поколение.

context_packet возвращает private bytes текущего verified context и полный
permission map для protected caller; не печатать/экспортировать автоматически.
summary содержит только IDs/pins/counts/static labels, не raw source/statement.
Его status consistent_private_authority_state не является permission/grant.

## Exact assent import и его граница доверия

Assent — closed pinned JSON: basis_id/source_id UUID, statement_form quote|summary,
полный statement (непустой,≤65536characters), exact event UUID/hash/size и literal
attestation exact_event_reviewed_by_local_operator. Basis identity уникальна в
store; source_id может ссылаться на общий разрешённый источник. Source IDs не
аутентификация личности/канала. Operator отдельно обязан иметь действительное
**конкретное** согласие на event bytes и допустимость хранения текста. Generic
«продолжай разработку», выбор A и approve_revision не такие release/export grants.

Import требует explicit attest_exact_owner_assent=True и внешние pins для
source/event/subject. Schema/refs/subject/event identity/permission stream/parent/
negative semantics проверяются перед persistence. Full source bytes сохраняются
в private CAS; quote/summary не превращаются в новую прямую цитату от хранения.
Ни NLP interpreter согласия, ни проверка источника внешнего сообщения не реализованы.
Trusted operator может ошибочно аттестовать ложное; coherent false claims могут
пройти consistency. Не использовать True/JSON actor label как доказательство owner.
Секреты автоматически не классифицируются; не собирать их ради формы и не
запрашивать ключи в чате. Для этого профиля source остаётся local вне Git/allowlist.

Duplicate event/basis identity, dangling revoke/parent, unknown kind, wrong pin/
subject/source schema не переписываются и не игнорируются. История cumulative:
новые generations сохраняют все прежние events/sources/checks и добавляют ровно
один import либо check. Удаления/lift/semantic correction/import replacement нет.
Известные deny/revoke сохраняются, новый grant не снимает deny. Не создавать
другой store ради забывания относящихся negatives: per-store history не доказывает
глобальную полноту или корректность нового bootstrap. Она требует своего основания.

## Current head и сохранение проверок

Каждый файл generations/00000000.json … — логический номер поколения, **не
временная метка**. Порядок contiguous от0, parent pin к exact предыдущим bytes,
store identity/number/schema/transition проверяются. Нет mutable latest alias,
нет приоритета по дате. Current head — конец сохранённой цепочки при совпадении
с externally expected head; несовпадение блокирует открытие/изменение.

Context синтезируется только из всех retained source/event refs и generation,
сверяется с сохранёнными bytes. Protected r2 evaluator проверяет полный stream.
Check использует предыдущий current context; request.context/generation/subject
должны точно совпасть. Он сохраняет request/subject/result bytes и consumed UUID,
затем новый head/context. Повтор UUID, даже с другими bytes, отвергается. Новые
requests требуют нового context/pin. Malformed/stale request отвергается до записи;
valid check с отрицательным result сохраняется как отрицательная проверка.

При reopen все transitions повторно проверяются. Imported subject/event/assent
binding восстанавливается; recorded result пересчитывается protected ENT14r2
по **предыдущему** контексту, не исполняя archived code. Source bytes/hash chain
не являются execution authentication. Inspection не обновляет старые факты.

check_id_consumed=true означает лишь однократную запись **этой проверки**.
action_claim_created=false всегда. Новый UUID может снова проверить тот же grant:
export_id/само разрешение не расходуются. Нельзя использовать эту операцию как
exactly-once export/authorization reservation или receipt совершённого действия.
Store не заменяет native check_current_candidate/readiness verifier; pure intent
не проверяет composition/coverage. Actual incomplete ENT13 остаётся blocked в
его native profile; этот controller вообще не выдаёт effective action flags.

## Физический профиль, limits, failure

Только Linux x86-64/stdlib fcntl + прежний isolated hash-locked jsonschema/base.
Никаких новых packages. Девять installed dependency/schema pins до загрузки;
own code trust обеспечивается protected installation/caller, не self-hash.
Hash/load TOCTOU не защищает противника с записью в installation.

Фиксированный base и local ancestors: euid, no group/other write; private
namespace/store/objects/generations dirs0700. Files0600, regular/single-link/
owner/same-device; NOFOLLOW/NONBLOCK/directory FDs, inode bindings/readback.
Existing unsafe mode не ремонтируется. Не promise hostile same-uid/root/kernel/
privileged same-device mount protection. Для локальных guards reused ENT15
_directory/_bound/_write_file/_fingerprint, source adapters не исполняются.

Fixed lock file проверяется по bytes/metadata/binding; nonblocking exclusive
flock защищает только cooperating callers/processes. Busy → stop, не wait loop/
не удаление lock. Kernel освобождает lock при закрытии последних FDs; это не
recovery данных. Namespace bindings/modes проверяются до/после mutations.

Limits:16MiB/document,128MiB суммарных unique CAS objects+всех heads+lock,
20064files (objects+heads+lock),256generations/128imported events. Bounded directory
enumeration; бюджеты проверяются и при replay. Дополнительные16MiB/64MiB
limits самого r2 evaluator по его declared input packet тоже сохраняются. JSON decode/history replay всё
равно не RAM/CPU quota. При достижении cap — stop, не rotate/drop old negatives.

Запись: preflight → exclusive CAS writes+fsync+readback → generation file EXCL →
fsync dirs → full verify/bindings → external receipt. Dedup проверяет existing
bytes; нет overwrite. Short/zero write/fsync/readback/binding/limit failure не
возвращает success receipt; handle poisons, закрыть. Partial сохраняется: extra
objects/incomplete generations блокируют reopen. Ничего не удаляется/не откатывается/
не усыновляется автоматически. Failure после записи head может оставить committed
state без receipt: старый pin больше не совпадёт; требуется отдельный manual review/
recovery policy, не автоматический retry/adoption. Crash/power-loss durability
или recovery manager не доказаны одними fsync.

Полный coherent rollback store **и** external pin может вновь пройти consistency;
внешний trusted high-water надо сохранять независимо. Код не реализует аппаратный
monotonic counter/защиту внешнего high-water. Не выдавать persisted current head
за глобальную freshness или полноту всех owner stores. Семантика source statements,
реальный мир/выполнение/новая среда остаются not_checked.

## Обоснование, нюансы и проверки

Reuse одного thin JSON/CAS controller поверх ENT14r2/ENT15 вместо нового DB/crypto
framework. Плюсы: private provenance сохранено, current state и checks связаны,
ошибка/negative не исчезают; delta data dedup. Цена — полный bounded history replay,
операторская ответственность за source/high-water и manual recovery при partial;
локальный finite store не general DB/permission service. Эффективность narrow
reuse/traceability, не benchmark ускорения/универсального поведения.

verify.py:42methods, реальные disposable filesystem/cross-process lock cases и
явно synthetic assents. Coherent rollback/old-pin passing case показывает границу,
не скрывается. Test cleanup/adversarial deletes только disposable fixtures, не
операторские данные. Actual documented empty-store lab создаёт0assents/0grants,
записывает один отказ GRANT_REFERENCE и reopen проверяет цепочку. Это не positive
owner release/export и не permission source authenticity. Другие ветви R4/I2b,
R5 actuator/R6 readiness/R7 environment/R8 activation остаются отдельно.
