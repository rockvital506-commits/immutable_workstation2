# R4/I1 — local authority semantics и неизменный incomplete guard

## Предварительный baseline до кода

Владелец выбрал A: owner-controlled local authority. Это выбор профиля доверия,
не grant на release/export/activation. Основание — проект36/P01–P20. Источник
полномочий вне source; hash/JSON actor_role не подтверждает owner identity.

Цель I1: исполняемая семантика exact release/export grants/deny/revoke в явно
доверенном declared context плюс native guard фактического ENT13r1 через ENT14r1.
Pure authority recognition не actuation/readiness, не менеджер одноразовых claims.
Полный R4/положительный compatible-release end-to-end пока не заявляется.

Кандидат ENT14r2: authority.py, permissions.schema.json, verify.py, usage.md,
procedure.md. depends_on ENT14r1 (транзитивно старый стек), supersedes r1 без
переключения consumers. Нет новой entity/event schema r1 mutation, библиотеки
прежние isolated hash-locked jsonschema/base. Runtime permission events передаются
отдельным known map, не добавляются в catalog/approvals/Git автоматически.

До реализации фиксируются критерии:

| ID | Критерий | Метод |
|---|---|---|
| I01 | Closed strict UTF8/LF/duplicate-free JSON, native int refs, bounded sets | Own malformed/limit tests |
| I02 | Explicit trusted-owner context acknowledgement и external pin; не raw input flag | Context factory/client tests; identical caller provenance не различается pure API |
| I03 | Exact known stream/context/current expected pin/request/grant/subject | Missing/extra/wrong bytes/old-context tests |
| I04 | Positive authority recognition для exact release и export | Synthetic owner-reviewed context fixtures; не реальные owner grants |
| I05 | Approve/proposal/role без authority не дают recognition | Negative tests |
| I06 | Export parent/allowlist/destination/procedure/prompt exact | Cross-binding tests |
| I07 | Scoped deny accumulates; exact revoke не latest-wins | Two-block/revoked-grant tests |
| I08 | Unknown/ID collision/dangling targets fail closed, не фильтруются | Full stream tests |
| I09 | Current-head лишь externally pinned; no automatic freshness/claim/authentication | Explicit result limits и tests |
| I10 | Native ENT13r1 remains blocked даже при synthetic positive authority | Wrapper вызывает installed ENT14r1 без loader/child substitution |
| I11 | Старые116refs/records unchanged; no real grants/output writes | Regression/full suite/diff/hash checks |
| I12 | Success authority отдельно от action; все actuation/activation flags false | Tests и human procedure |

Known limitations: opaque subject refs не proof composition; coherent fabricated
context/evidence от trusted caller может пройти consistency. Protected caller/
namespace/interpreter обязательны, не hostile same-uid/root. Actuator/current
head/claim/readiness остаются R5/R6 integration, не моделируются как выполненные.

Результаты добавлять после baseline commit; критерии не менять по результату.

## Реализация и own проверки до registration

Baseline cb849d7.5ownfiles подготовлены;44/44methods PASS7.309s, включая native
release/export incomplete и actual entity-scope block без loader/child injection.
Первый запуск42methods:41PASS/1ERROR — test fixture пыталась concat str к bytes
при порче event. Исправлена fixture b+b' ', не production condition. Затем добавлены
safe pins/непечатный repr context и native entity scope regression. Все реальные
owner decisions synthetic только in-memory fixtures, не записывались в catalog.

Трасса P01–P20 из проекта36 (A=AuthorityTests, N=NativeGuardTests в verify.py):

| ID | Method / evidence уровень и граница |
|---|---|
| P01 | A.test_positive_release_recognition_not_readiness — synthetic context/opaque subject, не coverage |
| P02 | A.test_no_authority_from_role_or_raw_context; A.test_input_actor_role_not_an_authority_field |
| P03 | A.test_context_ack_required_not_boolean_coercion; A.test_context_pin_required — client/API precondition; identical trusted-caller provenance не доказывается |
| P04 | A.test_external_request_and_subject_pins; A.test_known_event_mutation_missing_extra |
| P05 | A.test_proposal_or_approve_not_permission_event |
| P06 | A.test_no_implicit_export_from_release |
| P07 | A.test_positive_export_with_exact_release_parent — synthetic semantics, не actual export |
| P08 | A.test_export_parent_wrong_subject; A.test_export_request_destination_procedure_prompt_and_id_binding; A.test_export_allowlist_no_subset_extra_reorder; N.test_real_profile_wrong_pinned_procedure |
| P09 | N.test_native_release_authority_but_incomplete_no_injection; N.test_native_export_authority_but_incomplete_no_injection — настоящий installed old checker, authority synthetic |
| P10 | N.test_ready_boolean_not_supported — rebind mutated description и native old validator; не coherent-fabrication detector |
| P11 | N.test_actual_entity_scope_block_not_bypassed_by_positive_authority; A.test_deny_release_blocks_export |
| P12 | A.test_revoke_exact_grant_not_latest; A.test_revoked_release_blocks_child_export |
| P13 | A.test_two_denies_not_overridden_by_later_grant — synthetic accumulated blocks, снятие одного не снимает другой |
| P14 | A.test_unknown_unrelated_event_not_filtered; A.test_dangling_revoke_even_unrequested_event; A.test_duplicate_event_id_or_wrong_path; A.test_known_event_mutation_missing_extra |
| P15 | I1 strict snapshot binding: нет automatic switch; generic cross-view preservation не реализовано |
| P16 | N.test_candidate_mutation_even_with_reapproved_synthetic_context; A.test_external_request_and_subject_pins |
| P17 | A.test_old_context_rejected_by_external_current_pin; A.test_same_old_context_is_not_freshness_or_claim — frozen-old view может пройти consistency, не freshness |
| P18 | A.test_same_old_context_is_not_freshness_or_claim — повтор принимается pure recognition; stateful claim/actuator **не реализованы**, performed всегда false |
| P19 | A.test_no_authority_from_role_or_raw_context; A.test_proposal_or_approve_not_permission_event — новую среду не обследовали; activation всегда false |
| P20 | Проверка116oldrefs + full suite далее; r1 события не расширены и runtime permission events не добавлены в old ledger |

Subject refs в pure evaluator opaque; native profile строго связывает полный
snapshot. Изменение registry/entity known set требует нового bound description и
отдельного exact согласия: совместимость stable subject с новым evaluation view
без излишней reauthorization — будущая cross-view integration, не готовая P15.
Stateful importer/source of owner assent/current-head/claims/coverage verifier и
actual export ещё впереди. r2 не решает происхождение context аргументом True.


## Conditional implementation registration

До регистрации42/42repository modules и44/44own methods PASS; pip check no broken
requirements; repo38/0warnings/0errors; manifest/self-hash/diff checks PASS.
Прежние116refs/bytes/records сохранены.5ownfiles frozen до approval.
Approval89660162-2b9a-4abe-83aa-df98e5561e4e: summary условного implementation
основания после выбора A, **не** новое согласие owner на grant и не цитата об
exact bytes. Честно фиксирует partial I1/не реализованные trust provenance/state/
readiness/actuator и always-false action flags. Catalog deployment57/57 PASS.

Registry:18entities/28revisions/94norm artifacts/28approvals,71078bytes,
SHA256 `c95f60dd1b022041ede0084e75b448863e079facef68061300a6c8eb0d15b797`.
122normative/approval refs. Сохраняются старые scopes
agent_system.permissions/agent_system.release/agent_system.transfer. Runtime
permission events отсутствуют в catalog/approvals; новая запись — только
approve_revision реализации. Старые consumers не переведены на r2; M1 source20/70,
ENT13 payload12/34/incomplete. Никаких реальных owner release/export grants.

Результативность ограниченно подтверждена positive/negative semantics и native
incomplete/entity-scope guards, reuse старого checker вместо внешнего framework.
Синтетическая authority attestation не доказывает owner identity/происхождение
контекста; actor/flag/hash в source не становятся правом. Coherent false claims
от trusted caller могут пройти consistency; это предпосылка, не устранённый риск.

Следующий I2: реальный operator-controlled источник/импорт exact согласия и
current-head/state contract, сохранение known negatives/отказа и безопасные
single-use claims; отдельно cross-view binding/P15, R5 actuator и R6 readiness.
Не спрашивать повторно выбор A, но не выводить реальный grant из этого выбора.
Новая authority context/bootstrap в другой среде требует своего основания.

## Финальная проверка после registration

Повторный полный suite42/42modules PASS,57catalog deployment methods/44own methods
PASS; pip check no broken requirements, repo-validate38/0warnings/0errors,
manifest/self-hash/diff checks PASS. Public226md/86README/38research/42modules,
534relative links/0broken. Все122refs проверены; старые116refs/байты/records
не менялись,5own artifacts совпадают с freeze до approval.

Реальный documented ENT18 no-B regression после регистрации: trial_checked_no_query,
1source capture/full semantic replay PASS. UUID a4a9b84a-1814-45f6-b590-64a9efc14c41,
index14160bytes, SHA256
`edfe132b8fe0c7bbdd3c13140204bfd578b2487c8f9a6adb2099282ff71ba15c`.
Это только regression старого byte-trial; не positive owner grant/ready release.
Private evidence local вне Git; доступность после восстановления не обещана.
I1 реализован/проверен; R4 целиком не закрыт и actual переходов не было.
