# M1/I3 — основа coordinator, незарегистрированный implementation draft

**Не нормативная внедрённая ENT18r1 и не законченный coordinator.** Каталог r0001
пока рабочий кандидат. Регистрация exact состава/approve_revision намеренно не
выполняется до реализации runner и относящихся проверок. Никаких grants.

> Актуальный статус — раздел I3c в конце. Foundation-разделы ниже
> сохраняют срез I3a и не отменяют его последующие уточнения.

## Реализованные границы

session.py/session.schema.json: внутренний validate_session проверяет внешний
session pin, strict JSON/LF/closed fields, фиксированные purpose/criteria/profile,
task UUID, candidate pin, plan A/optional B и literal query pairing. Raw task text
не принимается. Documents ровно referenced plans, без retrieval/extra entries;
нужны native integer sizes, bytes, обязательные external refs. Совпадающие A/B
plan refs допустимы (один document), но будущий runner всё равно обязан сделать
две отдельные acquisitions. Наличие B context не назначает A current.

Plans проверяются прежним ENT9r2 _plan/ENT8r1 schema и пределами, затем exact
catalog/selection/artifact metadata и validate/agent_system.operator_trial context.
Точный profile (catalog_id/selection/artifacts/candidate) — **доверенный внутренний
аргумент**, не вход session и не произвольная source-derived политика. Future
coordinator должен получить его из проверенного installed состава с собственными
артефактами; этот bootstrap ещё НЕ реализован. validate_session сам не читает
source/не claim evidence/не stage и не доказывает permissions или полноту ledger.

Loader закрепляет 57 dependency artifacts/19 revisions будущего dependency
closure ENT9r2/ENT16r2/ENT13r1/ENT15r1/ENT17r1; сверяет bounded bytes до runpy.
Это installed expectation map как в старых tools, не второй registry и не
доказательство authenticity. Сам draft/schema/evidence.py должны быть доверенно
установлены caller; пока нет registry approval этих файлов. Writable hostile
installation/самоподмена защищённого caller не покрываются.

## Private CAS foundation, не общий журнал исполнения

EvidenceStore — single-use private local/operator-runs/new UUID. Relative paths
служебные, пользовательских filenames/destinations нет. Directories открываются
через directory FDs/NOFOLLOW, claims и file writes exclusive, no overwrite/resume/
auto-delete/rollback. Private operator-runs/run/objects 0700, files0600; общий
legacy local ancestor допускает owner-only write/без group/other write и может
быть 0755. Уже unsafe ancestor не исправляется chmod. Same-device/owner/filetype/
single-link/fingerprint и bindings используют pinned ENT15/ENT16 helpers.

put(bytes) — SHA-keyed immutable object, dedup после повторной проверки точных
bytes; seal(metadata) — один index.json с отсортированными refs и private JSON
metadata. Limits: 16 MiB/document, 128 MiB aggregate unique objects **и index**,
20064 files включая index. Duplicates не расходуют budget второй раз. Нарушение
лимита/записи/readback/fsync/final binding poisons store; позднейшее seal/put
запрещено. Partial files сохраняются, no retry overwrite. Финальная ошибка может
оставить index на диске: существование файла НЕ является успешным receipt.

verify_evidence(run_id,expected_index) — readonly exact pinned index/object
inventory/metadata/hashes/bindings check. Не создаёт отсутствующие dirs/файлы,
не chmod/fsync/write. Внешний pin обязателен, без автообновления из unknown файла.
consistent_private_evidence — согласованность CAS, **не** semantic journal/child
replay и не доказательство исполнения. Даже metadata со словом success само по
себе не подтверждает работу агента. Raw objects/metadata не печатаются функцией.

Защита от hostile same-uid/root/privileged mount не заявлена; trusted namespace,
Linux/kernel/interpreter/installation обязательны. Наблюдения не атомарны,
временные исчезнувшие изменения могут быть не замечены; fsync не является полной
моделью crash recovery. RAM/CPU не квотируются; caps не обещают, что максимальные
A/B plus reports одновременно поместятся. Секреты автоматически не распознаются,
данные private и не коммитятся/экспортируются. Owner задаёт допустимые данные.

## Историческая граница I3a (уточнена разделом I3b ниже)

run_operator_trial, trusted own-profile bootstrap, state machine/child journals,
полная candidate/handoff проверка, общий human report, procedure/versioned prompt,
semantic evidence replay по ENT10/17 и единый практический operator entry. Ни
source acquisition, stage, query, release/export/activation этот draft не запускает.
Полная T01–T30 matrix не исполнена; R2/M1 и I3 целиком не закрыты.

## Альтернативы, оптимизация и проверка

Выбрана небольшая основа над прежними pinned helpers вместо нового storage/
workflow framework. Плюсы: ограничения до write/source execution, без повторения
архивной семантики/дополнительных libraries, CAS dedup. Минусы: raw memory/privacy,
новый private persistence path, повторный hash/readback, необходимость отдельно
доказать orchestration/семантику. Эффективность пока подтверждена узко тестами
caps/dedup/no writes и storage lab, не benchmark coordinator.

verify.py/tests wrapper проверяют session errors/closed profile, mappings,
plan pins/context/limits, dedup/quotas, collisions/unsafe namespace, disk-full/
fsync/late binding/permissions failures, no resume/overwrite, readonly corruption/
FIFO/symlink/hardlink/inventory refusals, FD cleanup. Синтетические варианты внутри
subTests не считаются независимыми end-to-end scenarios. Окружение — прежний
hash-locked jsonschema с обязательными dependencies, без новых библиотек.

## I3b update — runner реализован как fail-closed candidate

Этот раздел уточняет исторический foundation срез выше: run.py/runner_verify.py
теперь существуют. Реализован run_operator_trial(source_a_root,session_bytes,
expected_session,documents,*,source_b_root=None) и installed_profile(). **В текущем
реальном registry ENT18 нет, поэтому public entry останавливается кодом
COORDINATOR_NOT_REGISTERED до claim/source I/O. Никакого draft bypass флага нет.**

Bootstrap использует только protected installed index/ledger, проверенные 57
fixed dependency pins, exact own r1 artifact set/пять dependency roots и known
validate scope. Own artifacts включаются в точный source profile, даже когда они
не входят в старый trial payload. Проверяются native refs и полная closure,
без self-hash cycle/второго registry/source-derived approval. Пока список own
artifacts — 7 draft files; procedure/prompt и semantic replay ещё предстоит
реализовать/включить в будущий exact composition до регистрации.

Runner: preflight → private claim → capture A → candidate subset → stage → reader
→ exact handoff → optional отдельный capture B/derived literal comparison → journal
object → CAS seal/receipt. Не принимает child reports/callbacks от пользователя.
Exact source packet maps/docs/report/plan сверяются, успешный bundle перепроверяется
ENT10; selected revision records должны совпадать с protected installed profile.
Это не позволяет silently исключить tools из closure через подмену source graph.
Перед stage/read/query проверяются известные scoped blocks всего tool profile,
не только payload. Candidate payload остаётся ENT13r1 12 revisions/34 files.

Handoff сверяет fresh stage receipt, UUID/manifest, reader metadata/candidate/
registry/ledger/payload refs, полный exact object set/bytes и counts. B не заменяется
на A. Query/reader/stage отказ закрывает requested run, не стирает существующий
trial. Полные child documents/raw successful source bundles сохраняются только
private CAS. Failed binding не выдаёт отсутствующий payload как replayable.
Journal хранит настоящие child run IDs и отдельную terminal claim; seal подтверждён
только внешним receipt после final guards. Index не включён в свой hash-cycle.

Return — безопасные codes/status/counts/relative refs без raw maps/absolute roots.
Это структурированный operator result, не завершённый отдельный human report.
Counters разделены: capture_invocations/completed_source_reports/validated_captures.
source_acquisition_calls для completed validated envelopes отражает one-read_set
контракт ENT9r2; если capture не вернулся/packet malformed — None (unknown), не
выдуманный 0/1. После unknown error/interruption completed receipt не фабрикуется;
partial evidence/trial сохраняются. Evidence failure — evidence_write_failed,
не sealed success. Release/export/activation/transition=false во всех результатах.

26 runner test methods на disposable prospective installation/source fixtures.
Synthetic approval ENT18 находится только в temp tree, не реальном ledger. Есть
physical stage/read/evidence, no-B/B positive, реальный known tool stage/query block,
source change после capture, forged packets/docs/records, late reader/permission/
seal failures, B failure/no fallback, неизвестный counter при exception, unknown
error без sealed receipt, повторные UUID и private result. Отдельные fault tests
меняют child outputs, не выдаются за полное событие/поведение production среды.
Тест public gate на реальном незарегистрированном каталоге ожидает отказ.

I3 целиком не закрыт: нет semantic journal replay, versioned procedure/prompt,
полного human report и I4 matrix/practice. verify_evidence по-прежнему только CAS
consistency; наличие runner этого обещания не расширяет. ENT18 не зарегистрирована,
новые approvals/releases/активация не созданы. Следующий шаг — semantic replay и
operator procedure/prompt с относящимися проверками, не обход registration gate.

## I3c update — offline semantic replay, procedure/prompt и human report

Актуальный срез — I3c. Добавлены replay.py/replay_verify.py,
[procedure r0001](procedure.md), [prompt r0001](prompt.md) и format_operator_result.
OWN draft composition теперь11files; expected source closure20revisions/68artifacts
существует пока **только в prospective fixtures**, не в реальном approved registry.
Foundation/I3b разделы выше — исторические срезы, не текущий список отсутствующего.

Journal теперь связывает pinned protected-profile snapshot (records/refs), raw
session, procedure/prompt refs и воспроизводимый UTF-8 human report. Human renderer
выводит только closed labels/canonical UUID/counts/step states, relative operator
ref, false gates, not_checked и статический следующий шаг. Raw maps/root paths/
свободные diagnostics/task/decision тексты не копируются. Это не secret detector;
opaque IDs/публикация результатов всё равно требуют caller policy. Seal отделён
от terminal claim: подтверждается только отдельным receipt/external index pin.

Evidence internal readonly capture возвращает первые object bytes после полного
CAS контроля и fd cleanup. Public verify_evidence **по-прежнему только structural**.
Новый replay_operator_run(run_id,expected_index) отдельно проверяет:
- exact journal/profile/session/criteria/procedure/prompt и human-report binding;
- source bundles/plan/report/docs/maps, selected closure/records и ENT10 replay;
- candidate result через ENT13, scoped tool checks для stage/read/query;
- receipt/reader/manifest/candidate/registry/ledger/object-set/count handoff;
- literal derived comparison plan и ENT17 result, реальные связанные child IDs;
- terminal counters/status/false gates и отсутствие unreferenced CAS objects.

Никакой code из архива не исполняется. Загружаются только fixed immutable trusted
installed helpers/own files; source/trial/live index/ledger не читаются. Bootstrap
регистрации для **нового запуска** не обходится. Historical replay сравнивает own
archive code refs с protected immutable r1; после регистрации in-place edits
недопустимы, для другого состава нужен новый versioned профиль. Пока draft может
меняться, старый draft journal не обещается совместимым с новым replay code.

Full replay поддержан только для successful no-B/B journals:
consistent_recorded_operator_run_no_admission. Failed/blocked/unsupported sealed
journals получают recorded_partial_run_no_full_replay, full_replay=false после
structural/profile/session/report проверки. Они не объявляются семантически
доказанными ошибками/успехами; missing failed capture не восстанавливается.
Не sealed/evidence_write_failed run не имеет пригодного replay receipt.

Согласованная фабрикация/копия архива может пройти проверки: authentication,
истинность наблюдений/факт внешнего исполнения, freshness/current permissions/
полнота/поведение/совместимость не доказаны. Replay не публикует и не активирует.
Все release/export/activation/transition gates false, даже при полном consistency.

17 replay test methods (15 первоначально +2human/protocol cases), prospective temp
fixtures only; это не17 новых owner-approved сценариев. Проверены no-B/B, no
source/trial/live-ledger/writes, coherent rehash/reseal attacks на counters/IDs/
steps/candidate/reader/query/profile/protocol/human и extra CAS object, failed
journal partial status, wrong external pin и coherent copied archive NOT authentication.
При review также усилен runner handoff: reader candidate/registry/layer, native
counts и stored_bytes receipt связываются явно; два source child IDs не переиспользуются.

I3 implementation candidate подготовлен, **не зарегистрирован**. Следующий этап
I4: полная traceability T01–T30/относящиеся проверки и bounded lab, затем оценка
выполнения условий exact registration. Нельзя автоматически считать 35+26+17
методов полной matrix, переносом/совместимым выпуском/активацией или выполненным T30.
