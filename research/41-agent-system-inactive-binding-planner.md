# Inactive environment binding planner — G05/G07 prerequisites

## 1. Критерии до кода и граница

Baseline193173e:18entities/30revisions/105norm/30approvals/135refs.
[40](40-agent-system-inactive-transfer-preparation.md) — preparation, не actual
export/readiness. Owner продолжил разработку, не выбрал новую среду/activation.
ENT12r1 governance G06/G07 требует B1survey→B2inactive binding→B3checks→отдельное
B4exact permission/result и history, не activation от импорта/прошлой истории.

Первый construct — **планировщик и private immutable history неактивных связок**.
Не выдавать его за completed G05 adaptation manager/G07 activation actuator/R6.
Входные сведения о среде/адаптерах остаются declared claims с pinned evidence,
не доказательством истинности/сохранения смысла/actual host capability. Ни одного
реального target environment не обследуем/не активируем. Связка не изменяет
platform context/system configuration. Не читать hidden instructions/секреты.

Новая сущность ENT19r1, scope agent_system.connection/governance,6ownfiles:
connection/ent-0019/r0001/{binding.py,binding.schema.json,procedure.md,prompt.md,usage.md,verify.py}.
Exact depends_on ENT12r2+ENT18r1; их closure содержит прежние policies/authority.
Одно ядро/index, не копия governance/work/permission schemas.

## 2. Механизм и обоснование

Closed bytes/pins request/environment/adapter declarations/observation evidence,
exact R5 composition descriptor. Обязательные host capabilities не подменяются
adapter claims: host.* — исходные available/unavailable/unknown; adapters могут
дать только binding.* по declared prerequisites, fixed-point без циклов/self
bootstrap. Все предоставленные adapters проверяются, unknown/конфликты/duplicate
providers не игнорируются. Scope/current-existing-context pin binding отдельны.
Недостаток mandatory → blocked_declared_requirements; optional → limitation.
Даже satisfied означает **только declared condition resolution**, не compatible.

Новая binding запись — private ENT18 EvidenceStore, exclusive UUID, metadata/
inputs/assessment, immutable. Successor хранит exact predecessor run/index и
same environment_id/scope; прежние записи не переписываются. Forks draft lineage
явно разрешены для сравнения, не current/active selection. No mutable latest,
no authoritative current head/автоматический rollback. External chain pin нужен
для inspection; coherent old chain+old external pin не global freshness.
Все known lineage nodes проверяются с finite cap до новой записи. Не усыновлять
missing/corrupt predecessor или удалять partial после failure.

Activation proposal — только список недостающих gates для exact binding/context,
никогда grant/side effect; release/export decisions не activation authority.
Будущий actual manager/adapter/authority/check result потребует своей реализации
и qualification; Python bool ready/actor label не основание активации.

Альтернативы: ad-hoc environment notes (нет машинной exactness/history);
изменяемый active config (опасный scope/не готово); reuse immutable evidence+
declarative resolution (выбран). Плюсы: useful B2 drafts/unknown visibility/
exact successor lineage без изменения среды. Минусы: declarations не semantics,
no active state/atomic switch/current-head guarantee, bounded chain read cost.
Новых third-party packages нет; existing isolated jsonschema/base только.

| ID | До кода: критерий | Проверка |
|---|---|---|
| B01 | Exact pins/closed docs/native types/explicit inactive acknowledgment | Invalid/unknown/float/boolean/ID tests |
| B02 | Composition prepared_inactive, exact own component in declared closure | Wrong descriptor/flags/component/source bindings |
| B03 | Mandatory host unknown/unavailable не available, optional limitations | Positive/negative resolver tests |
| B04 | No adapter self/bootstrap cycles/conflicts/duplicate providers | Fixed-point/cycle/conflict/all declarations tests |
| B05 | Adapter data не code; semantic verification не inferred | No callback/import/command fields; no true effective flags |
| B06 | Exact environment/scope/existing context; recheck on change | Wrong current pin/environment/changed revision tests |
| B07 | Private immutable history/successors; old nodes retained | Physical CAS/readback/pinned predecessor tests |
| B08 | Forks не active/current selection; missing/tampered lineage stop | Bounded lineage/fork/missing tests |
| B09 | Activation proposal never action/grant/false performed | Proposal/outcomes/positive declared case checks |
| B10 | Unknown owner grant/platform/core readiness remain blocked | All activation flags false; don't reuse permission JSON |
| B11 | Old135refs/records/bytes/consumers unchanged | Full pre/post qualification/freeze proof |
| B12 | Actual documented demo only declared fixture, not R7/R8 | Private history with no host modification/activation |

До code фиксируем критерии. Actual practice после conditional registration;
не использовать synthetic approvals или demo declarations как owner grant.

До code уточнён путь: **adapters/ent-0019/r0001/** вместо connection/....
Причина — immutable ENT12r2 намеренно допускает system adapters prefix, но не
произвольный connection prefix. Не расширяем frozen allowlist in-place и не
собираем скрытую зависимость. ENT19 явно добавляется root нового R5 run; старый
prepared composition24/90 не повышается молча до включающего ENT19.

## 3. Own checks и corrections до freeze

26methods PASS13.810s до последнего добавления явного false compatible-release
flag; этот flag также проверяется whole suite. Первый24methods:10PASS/14ERROR —
production native-integer guard ошибочно применился к строковым catalog revision
r0001 внутри composition. Guard ограничен numeric environment/adapter revision;
size_bytes проверяется везде. Следующий24:22PASS/1FAIL/1ERROR. Negative adapter
rule test менял alias observed-artifact metadata одновременно с rule, выявив
missing binding own component→observed set. Добавлен subset gate, не weakening
negative test. Второй error — fixture вызывала original evidence loader после
переноса BASE на temp; использован уже загруженный protected stage reference.
Затем24PASS, добавлены exact scope и coherent forged-assessment replay tests:
26PASS. Не выдавать первоначальный код за уже прошедший qualification.

| ID | Точные BindingTests methods verify.py |
|---|---|
| B01 | test_false_ack_before_loader_and_wrong_pin; test_native_float_revisions_and_ref_sizes_rejected; test_unknown_fields_commands_and_verified_claim_rejected |
| B02 | test_missing_component_and_action_claims_in_composition_block; test_adapter_cannot_provide_host_or_reference_noncomposition_rule |
| B03 | test_positive_declared_resolution_is_inactive_not_ready; test_unknown_unavailable_mandatory_host_not_available; test_available_requires_pinned_observation |
| B04 | test_cycles_and_self_providers_do_not_bootstrap; test_fixed_point_order_independent; test_conflict_blocks_even_unneeded_adapter; test_duplicate_provider_adapter_host_requirement_rejected |
| B05 | test_unknown_fields_commands_and_verified_claim_rejected; test_adapter_cannot_provide_host_or_reference_noncomposition_rule |
| B06 | test_expected_context_is_separate; test_changed_environment_requires_revision_advance; test_wrong_family_or_scope_predecessor_rejected; test_wrong_scope_successor_rejected |
| B07 | test_physical_private_history_and_immutable_parent; test_coherently_forged_assessment_recomputed_on_inspection |
| B08 | test_forks_are_inactive_not_current; test_missing_corrupt_predecessor_stops_before_writes; test_lineage_cap_before_new_node |
| B09 | test_activation_proposal_never_grant_or_action; test_assessment_tamper_and_save_ack_block |
| B10 | test_activation_proposal_never_grant_or_action; test_positive_declared_resolution_is_inactive_not_ready |
| B11 | whole suite/old135refs/freeze proof отдельно ниже |
| B12 | actual declared demo после registration; test_limits_and_demo_ack preflight |

Physical fault case test_write_failure_retains_partial_no_receipt; private
lineage test проверяет0700/0600 и unchanged ancestor bytes. Coherent rewrite
case пересчитывает CAS/index pins в disposable temp, но protected resolver
всё равно отвергает изменённый результат. Это вычислительный replay деклараций,
не authentication наблюдений/host behavior/semantic adaptation. Old contexts
используются только как historical inputs, не как текущий platform context.

## 4. Registration и actual declared demo

До registration full46/46modules PASS; pip/repo38checks0warnings0errors/
manifest/self-hash/diff PASS. Summary approval8e2ed5aa-58cc-4743-b08d-0348d1edb4ad
только conditional implementation, не exact activation decision/реальная новая
среда.6own artifacts frozen. Старые135refs/records/bytes сохранены. Registry
19entities/31revisions/111norm/31approvals,142artifact/approval refs,81383bytes
SHA256 `fe8683b40e359d1074c166ef7cec0e18b770f8b4c3d4aa2673ab7d93bf148883`.
Catalog deployment63/63methods PASS; legacy M1closure20records70artifacts unchanged.

Actual documented binding.py --demo-inactive, без injected callbacks/code/mock:

- новое R5 explicit roots12r2+19r1:25revisions/96norm artifacts/31known decisions,
  исходный historical coverage25rows не discharged;
- private source preparation run0c110658-3fca-4846-932e-90cc8dfb0367,
  index1534bytes SHA256 `ecb53c82666ebe28756736fce1018a337d325e908e56d39225e5cab412848a87`;
- source manifest161685bytes SHA256 `e1468abb04c6529223341b8052536e913d996e2c025acbc62a13b1349709c983`;
- parent inactive binding5acc12c0-7f09-4e82-95d2-9392e406f0f3,7objects,
  index1180bytes SHA256 `5403b79cab0bd5a4c943b21f188bd60eb228f0d685fdaa513a43c3525c3b0b19`;
- child inactive bindingf0800ba1-d70d-470c-9663-67cf7bd823ff,6objects,
  index1060bytes SHA256 `4e3cd2a6ff3509d0334e56515c4a11bcfebf174f921d7dede514422bd9ccb801`;
- parent declared_conditions_satisfied с optional limitation; changed demo survey
  revision2→host unknown→child blocked_declared_requirements. Обе связки inactive;
- source/evidence counts/readback и **отдельное новое module instance**
  inspect_history:2nodes/consistent_inactive_lineage, declared resolver replay PASS;
- activation_proposal activation_not_authorized,5missing gates, все action flags
  false. Без --demo-inactive exit2/EXPLICIT_DEMO_ACK_REQUIRED до namespace IO.

Это actual execution/private storage **для объявленного demo**, не survey
capabilities реального host и не actual адаптация агента/смена context. Строка
observation_level=declared_demo и evidence явно указывают, что host observation
не производилось. Ни одного actual owner grant/permission import/activation/
export/active pointer. Private inputs/история вне Git и autoexport; доступность
этих private stores после восстановления среды не обещана.

## 5. Что ещё не qualified и следующий переход

G05 получил рабочий declared planner/immutable draft history, не semantic adapter
execution/verification. G07 — proposal scaffolding/обязательные gates и история,
не actual activation authority/actuator/result manager. Core coverage нельзя
повысить по слову implemented planner. R6 complete/readiness/compatible-release
и R4/I2b durable actions остаются открыты.

Следующая qualification должна отдельно определить trusted observation/adapter
interface, проверяемое сохранение смысла, applicable checks и exact activation
permission/result. Новая actual среда R7/реальное B4 не выбираются автоматом.
Требуется не ещё один bool ready/actor label, а действительное основание и
применимый verifier/actuator. История не текущая конфигурация. Scope архитектуры
частного проекта/hidden instructions/secret material в протокол не переносится.

## 6. Финальная квалификация среза

Полный postregistration46/46modules PASS;26own methods/63catalog deployment
methods PASS. pip check no broken requirements; repo38checks/0warnings/0errors;
manifest/self-hash/diff checks PASS. Все142refs/hash/native sizes, старые135refs/
bytes/records unchanged относительно193173e,6ownfiles frozen до approval,
method selectors B01–B12 проверены. Public238md/86README/42research/46modules,
561relative links/0broken. Private inputs/lineage/evidence не добавляются в Git.

Результат — рабочий declared inactive planner/history с computational replay и
реальной FS practice на **demo declarations**, не квалифицированная actual
semantic adaptation/activation/compatible release. Никаких automatic binding
switches/exports/rollback/actual new environment. Восстановленные workspace
данные отдельно сохранены, прежние stashes не применялись/не удалялись.
