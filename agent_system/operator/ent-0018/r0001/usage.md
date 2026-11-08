# ENT-0018 r0001 — bounded operator trial coordinator без допуска

## Полный состав, источник и статус

Protocol, scope agent_system.operator_trial. Полный immutable состав13files:
session.py, session.schema.json, evidence.py, verify.py, run.py, runner_verify.py,
replay.py, replay_verify.py, acceptance_verify.py, lab.py, usage.md, procedure.md,
prompt.md. Точные hashes/approval/status — только в едином registry; этот текст
не self-approval и не разрешение выпуска. Источники — задание B/восьмиблочный
маршрут владельца/условное делегирование после проверок и дизайн M1 D01–D18.
Partial implementation history — исследования30/32; версия не редактируется
in-place после exact регистрации. Старые normative r1/r2 не переписаны.

Depends_on ровно ENT9r2/ENT16r2/ENT13r1/ENT15r1/ENT17r1. Транзитивная fixed
installed dependency closure19revisions/57artifacts. С own13:20revisions/70artifacts,
но payload trial по-прежнему ENT13r1 **12/34**, coordinator/tools вне payload.
Новые releases/activation events этот protocol не создаёт. Никаких libraries
сверх stdlib и прежнего isolated hash-locked jsonschema/base dependencies.

## API и closed preflight

```python
installed_profile()
run_operator_trial(source_a_root, session_bytes, expected_session, documents,
                   *, source_b_root=None)
format_operator_result(result)
replay_operator_run(run_id, expected_index)
```

Session по session.schema.json — strict UTF-8/LF closed JSON с external SHA/native
size, task UUID, fixed purpose=local_core_trial/criteria/profile, exact candidate
pin, plan A/optional B refs и literal B/query context. Raw task text/commands/
URI retrieval/callbacks/reports не принимаются. Documents — ровно referenced
plan SHA→immutable bytes (при одинаковом A/B pin один document). Native int sizes,
не float/bool. Profile внутренний, из protected installed index/ledger, **не**
source-derived policy. Actual root strings/native Paths вне сериализованной session.

Bootstrap сверяет 57 fixed dependency pins, exact own composition/5roots,
protected approval и полную closure/known validate scope. Без registration
COORDINATOR_NOT_REGISTERED до source/claim; никакого draft bypass/auto-registration.
Hash-before-runpy не защищает от противника с записью trusted installation:
caller обязан обеспечить неизменяемый от source installed namespace/interpreter.

Plans — прежние ENT8r1/ENT9r2 limits/schema, exact catalog/selection/artifact refs,
context validate/agent_system.operator_trial. Нельзя переиспользовать E12
export/agent_system.transfer preparation как generic trial preflight. Source
registry/весь известный ledger закрепляются извне; unknown inventory останавливает,
но глобальная полнота/свежесть/аутентификация таким pin не доказывается.

## Порядок и byte handoff

Preflight → exclusive evidence claim → capture A → candidate subset → scoped
stage → guarded reader → exact handoff → optional отдельный capture B/derived
query → journal/human report → seal receipt. Public entry не принимает внешние
child packets; tools грузятся только из protected installation, не source/archive.

Report/plan/doc refs и exact source byte maps проверяются; full successful bundle
перепроверяется ENT10. Selected revision records должны совпадать с protected
profile: подмена source graph не исключает tool checks. Перед stage/read/query
проверяются known scoped blocks всего tool profile. ENT13 проверяет subset только
из A bytes; ENT15 не читает source заново. Reader ENT16r2 выдаёт первые captured
manifest/objects после всех late guards. Receipt/UUID/manifest/reader metadata,
candidate/registry/ledger/payload/objects/native counts/stored_bytes связываются.

Без B query=not_requested, A не считается current. При B делается отдельный
capture, даже если root/plan тот же. Derived plan строится из session literal
query и verified archive/B refs, не неизвестного filesystem manifest. Block/failed/
unsupported на любом requested downstream закрывает общий run; partial trial
не удаляется/не откатывается. Старые consumer pins остаются прежними.

Counters разделены: capture_invocations/completed_source_reports/validated_captures.
source_acquisition_calls отражает one-read_set контракт проверенных ENT9 envelopes;
если capture не вернулся или packet malformed, total=None/unknown, не ложный0/1.
Success no-B1, сB2; source calls не включают отдельные archive guard readbacks.
Это не атомарный snapshot/транзакция двух roots. Child run IDs связываются и не
переиспользуются для A/B. Unknown error/interruption не получает fabricated receipt.

## Private evidence и человекочитаемый итог

Fixed local/operator-runs/new UUID; private dirs0700/files0600, directory FDs,
NOFOLLOW/exclusive writes, no overwrite/resume/delete/auto-rollback. Legacy local
ancestor может быть0755 без group/other write; unsafe не chmod'ится автоматически.
Same-device/owner/regular-file/single-link/fingerprint/bindings и readback reuse
ENT15/16 helpers. Строгие limits16MiB/document,128MiB aggregate unique objects+
final index,20064files включая index. Dedup сверяет сохранённые bytes; budget не
расходуется дважды. Limit/write/fsync/readback/binding failure poisons store.
Partial files/index сохраняются; существующий index НЕ completion proof.

Journal связывает protected profile snapshot/records, session/plans/procedure/
prompt refs, raw successful source bundles/child docs, receipt/archive/query,
real child IDs и terminal claim. Human report воспроизводится по closed labels/
UUID/counts/step states/relative refs, false gates/not_checked/статический next step.
Raw maps/absolute roots/free diagnostics/task/decision texts не печатаются.
Секреты автоматически не классифицируются; caller проверяет допустимость данных.

Terminal claim ещё не seal: внешний receipt/index pin выдаётся после final
readback/bindings/fsync. Evidence failure — evidence_write_failed, не success;
unknown авария может оставить только partial без index. Ничего автоматически
не экспортируется/не коммитится. Crash durability/hostile same-uid/root/kernel/
privileged same-device mount/необнаруженные временные события не покрыты.

## Structural и semantic replay — разные результаты

verify_evidence — readonly pinned CAS index/inventory/refs/metadata/bindings,
consistent_private_evidence. Это не journal semantics/execution proof.
Internal capture сохраняет первые bytes, закрывает FDs, не reread'ит pathname
для передачи. Public structural checker не возвращает raw maps.

replay_operator_run отдельно проверяет full successful no-B/B journal: profile/
records/closure/procedure/prompt/session/human, ENT10 source bundles, ENT13 candidate,
scopes/receipt/reader/handoff, derived plan/ENT17, child IDs/counters/gates/refs и
unreferenced objects. Source/trial/live index/ledger не открываются; code из
архива не исполняется. Нужны protected immutable installed own revision/helpers и
external pinned receipt. consistent_recorded_operator_run_no_admission означает
согласованность записанных claims, **не** факт их внешнего исполнения.

Failed/blocked/unsupported sealed journal получает recorded_partial_run_no_full_replay
после structural/profile/session/report checks, full_replay=false; missing failed
capture не восстанавливается, полная failure semantics не заявлена. Coherent copied/
fabricated archive может пройти проверки; execution/source/caller authentication,
truth of observations, freshness/current permissions/global completeness/поведение/
target environment не доказаны. Replay не обновляет sealed journal/live permission.

## Один ограниченный lab client

lab.py/процедура: run_trusted_lab(trust_this_checkout=True,with_query=True|False).
Только явно trusted installed checkout как source; foreign roots/discovery не
поддерживаются этим client. Без explicit flag отказ; нет auto approval. Создаёт
closed plans/session из protected trusted namespace, вызывает один entry и отдельный
replay, возвращает safe human/receipt/replay summary. CLI пример в procedure.md.
Для недоверенного source использовать отдельно закреплённые ожидания/entry, не
lab pin derivation. Query export не выполняет export. T30 относится только к
этому bounded lab, не к новой agent platform/активации/совместимому выпуску.

## Обоснование, проверки и независимость состояний

Выбран thin coordinator/shared byte handoffs вместо manual recipes или workflow
framework. Плюсы: один источник bytes между слоями, явные stops/counts/refs,
reuse прежней semantics и CAS dedup. Минусы: raw privacy/memory retention,
новая persistence/code surface, hash/readback/replay overhead и trusted namespace.
Однократный lab и call counts подтверждают узкое улучшение traceability/reuse,
не универсальный performance benchmark. RAM/CPU не квотируются; максимальные A/B
плюс reports не обязаны одновременно помещаться в128MiB. Проверки ради скорости
не сокращаются, новые dependencies требуют отдельного решения.

Own tests:35foundation/26runner/17replay/19acceptance methods. SubTests не являются
дополнительными end-to-end сценариями; prospective approvals только в temp
fixtures, не реальные owner events. T01–T30 traceability/results — локальный
acceptance report, не второй нормативный core/registry и не release coverage.
Точная регистрация отдельно от implementation/tests/native practice/release/
activation. Overall/current permissions not_evaluated; release/export/activation/
transition false во всех результатах. Один запуск не снимает incomplete ENT13
coverage и не подтверждает фактическое соблюдение всех правил агентом.
