# R4/I2a — private assent journal, current head и одноразовая проверка

## Baseline до реализации

Выбор A уже сделан; новый grant из «продолжай» не выводится. Источники: проект36,
I1/ENT14r2, ENT15r1 file/FD primitives. Цель — работающий local controller:
private immutable source assent/event/subject records, append-only generation
chain, explicit external expected head, cooperative lock и проверяемый check-once.
Это первая часть I2, не actual одноразовая авторизация export: consumption request
для **проверки** отдельно от reservation/исполнения действия. Последние остаются
R4/I2b + R5/R6. Неполный ENT13 и все action flags остаются закрыты.

Кандидат ENT14r3: state.py/state.schema.json/verify.py/usage.md/procedure.md;
exact depends_on ENT14r2 + ENT15r1, supersedes r2 без смены consumers. Runtime
local/permission-authority/UUID вне Git. Не новый каталог entities/метаядро.

Альтернативы: (1) только r2 raw context — нет persistence/current controller;
(2) stdlib sqlite — готовые transactions, но новый storage adapter/journal/recovery
surface и отдельное обоснование pathname guards; (3) reuse ENT15 FD/readback и
append-only JSON/CAS — выбран для узкого local профиля, без новых packages.
Плюсы3: exact immutable chain/retention, reuse; минусы: полный bounded replay,
нет general DB recovery/rollback-resistant storage, цена растёт с историей.
Не обещать скорость/универсальную среду. Не создавать опасный экспорт ради теста.

| ID | Критерий до кода | Способ |
|---|---|---|
| S01 | Explicit namespace acknowledgement, Linux-only protected checkout | Gate до writes, native disposable FS |
| S02 | Private dirs0700/files0600, no-follow/single-link/owner/device/bindings | Real symlink/hardlink/permission/rename tests |
| S03 | Closed pinned source assent+event+subject, exact review acknowledgement | Wrong/missing ack/pin/subject/event tests, no writes on preflight reject |
| S04 | Statement/provenance retained privately; not cryptographic/NLP authentication | Exact stored source bytes + no raw text in safe summaries |
| S05 | Append-only contiguous generation/hash-parent chain and external expected head | Old-pin/rollback/branch/tamper tests |
| S06 | Imports cannot remove old known events/negative records or edit old sources | Cumulative history tests; no overwrite/revoke resurrection |
| S07 | Cooperative nonblocking exclusive lock; old head race rejected | Two store handles, no silent stale mutation |
| S08 | Check uses stored current context; same request UUID consumed once | Physical check replay/ID collision; NOT actual single-use action |
| S09 | Every check receipt/evaluation bound to previous context and exact inputs | Offline controller replay of r2 result; code only protected installation |
| S10 | Limits/short write/fsync/readback failure retains partial, no success receipt | Fault+physical tests, no auto recovery/delete/rollback |
| S11 | Old122refs/records unchanged; empty-store actual practice creates no grants | Full suite + checksum check + explicit trusted-namespace demo |
| S12 | No action permission, source auth/freshness/global completeness overclaim | All outputs action=false; high-water pin requirement explicit |

Source records: human-reviewed quote/summary + opaque source_id + exact event pin,
explicit local operator attestation. Это сохраняет основание, но не доказывает,
что текст действительно сказал owner/что он значит exact grant. Protected operator
обязан иметь относящееся реальное согласие. Generic «продолжай» не такое согласие.
В тестах только явно synthetic согласия; actual demo — empty authority/no grants.

Критерии фиксируются до кода. Полное R4/actual release/export/activation не заявлять.

## Собственные проверки и коррекции до freeze

Первый запуск34methods:4PASS/30ERROR. Причина production bootstrap — schema
validator evolved от r2 сохранял resolver старого root, поэтому #/$defs/head
искался в r2. Исправлено: отдельный validator/root/resource registry с forbidden
remote retrieval, не weakening schema. Повтор33/34PASS: guard directory-rebind
реально останавливал write, но его private _Stop выходил из _ready без public
StateBlocked translation. Добавлен exact helper-error translation/handle poison,
не отключён guard. Затем37/37,40/40 и итог42/42PASS29.636s.

Все source assents явно synthetic и только в disposable namespaces. Native
actual empty-store demo предстоит после conditional registration; его критерий
0events/0grants, один сохранённый GRANT_REFERENCE, closed action flags/reopen.
Не выдавать тестовые согласия за реальные owner события.

| Критерий | Точная опора StateTests в verify.py / уровень |
|---|---|
| S01 | test_ack_before_writes; test_platform_and_installed_pin_gate_before_namespace — actual preflight |
| S02 | test_create_reopen_empty_private; test_file_symlink_hardlink_fifo_metadata; test_unsafe_base_and_late_private_modes; test_store_directory_rebound_before_write — physical guards |
| S03 | test_missing_exact_attestation_no_writes; test_false_source_pin_no_persistence; test_assent_event_subject_binding_and_blank_statement; test_assent_basis_identity_cannot_be_reused_for_other_event |
| S04 | test_source_bytes_retained_and_no_raw_statement_summary; test_statement_form_and_unknown_source_fields_closed — byte retention, не origin/NLP proof |
| S05 | test_stale_external_head_rejected; test_rollback_missing_new_head_detected_by_external_pin; test_recorded_parent_link_native_generation_and_inventory |
| S06 | test_negative_records_cumulative_and_not_removed; test_known_negative_cannot_be_removed_from_new_generation; test_exact_revoke_blocks_old_grant |
| S07 | test_lock_nonblocking_and_fd_cleanup; test_cross_process_lock_not_just_python_object — kernel lock/cooperative processes |
| S08 | test_positive_check_once_replay_rejected; test_check_id_collision_different_bytes_rejected; test_fresh_check_id_does_not_mean_export_grant_was_consumed — одноразовая запись проверки, не действие |
| S09 | test_recorded_check_result_not_just_cas_hashes; test_old_request_context_rejected_under_current_head; test_failed_check_persisted_not_action_claim |
| S10 | test_zero_write_failure_no_receipt_or_auto_cleanup; test_fsync_failure_not_success_retains_partial; test_physical_corruption_after_write_readback_stops_commit; test_partial_write_loop_success; test_reduced_budget_and_generation_limits — fault+physical, не power-loss audit |
| S11 | test_empty_lab_creates_no_owner_decisions — prospective disposable entry; actual registration/practice и old122refs/full suite отдельно далее |
| S12 | test_old_pin_can_accept_coherently_restored_whole_old_store — intentionally passes old pin/whole-store rollback; все safe summaries/action flags false |

Оценка узкая: owner-controlled controller/source retention/finite consistency и
check replay prevention. Store не предотвращает false trusted attestation,
coherent rollback с потерей внешнего high-water, пропуски outside known store
или повтор actual export под новым request_id. R4 целиком не закрыт.


## Conditional registration и actual empty-authority practice

До регистрации43/43repository modules и42/42own methods PASS; pip check no broken
requirements; repo38/0warnings/0errors; manifest/self-hash/diff checks PASS.
Старые122refs/records/bytes сохранены,5ownfiles frozen до approval. Summary
approval40d34fbe-c255-4330-b9de-c56bacaeb4bd: implementation I2a, не прямая цитата
owner об exact bytes, не разрешение на grant/action. Честно фиксирует pending
actual demo и отсутствующие action claims/readiness/actuator/global trust proof.
После регистрации59/59catalog deployment methods PASS.

Registry:18entities/29revisions/99norm artifacts/29approvals,74250bytes,
SHA256 `de0f423fd23cd99e8daa3b00e9f750b2b743dc3e85f1cd5357c869bfb60b5964`.
128artifact/approval refs. Старые scopes сохранены, никакие consumers/bindings
не переключены. Новый catalog event — только approve_revision реализации.

Реальный documented state.py --trust-owner-controlled-namespace, без loader/
child injection и без обязательного /tmp recipe:

- store_id6d86883f-6d6a-4c73-98ca-9a62cd2b8ea4;
- generation1;0events/0assents/0grants;1check recorded, check_id_consumed=true;
- result failed/GRANT_REFERENCE/authority_valid=false; action_claim_created=false;
- head986bytes SHA256 `05b42492a1314b4216b04c76d97b8b15b3655fd8cc2319e87b8f59f2eb14a7bc`;
- context228bytes SHA256 `76f00bfdec8c8bb838a40e51c3597d5dac3864086ff350b346b054f522ae2e43`;
- reopen тем же entry и отдельный вызов нового module instance/API с external
  receipt PASS; source/trial worlds не подключались, owner statements не импортированы;
- без explicit flag CLI вернул2/EXPLICIT_OWNER_NAMESPACE_REQUIRED до новых writes.

Приватный journal local вне Git. Это actual storage/negative-path/replay practice,
не actual positive owner grant, не real-world authority authentication, не
single-use export и не readiness. Все action/performed/activation flags false.
Доступность private store после восстановления workspace не обещана; receipt pins
не являются экспортом его raw contents/истории. Full R4/I2b/R5/R6 не закрыты.

## Финальная проверка после регистрации и практики

Повторный полный tests/run-all.py:43/43modules PASS,59catalog deployment methods/
42own state methods PASS. pip check no broken requirements; repo-validate38checks/
0warnings/0errors; manifest/self-hash/diff checks PASS. Все128artifact/approval
refs проверены; прежние122refs/байты/records сохранены,5own artifacts совпадают
с freeze до approval. Public229md/86README/39research/43modules,
541relative links/0broken. Private store/raw contents не добавляются в Git.

Actual generation0 parent receipt:393bytes SHA256
`8d0c5cf5e0ba7fda4b13d1a77a4fbb0da4d94f02e752b0e832516c5df367cf98`.
Сохранённый check UUID94adbb2e-2a93-46ea-a945-4c3bef716453;
request598bytes SHA256 `2a41565530eec62714ecf09f737fe3e39ff53ddfc19532fda7ec1e1e64c65cfe`;
subject892bytes SHA256 `fe89d73cb081b51366482503d99357ca277cbc5d92143d4f59c25f74f9680a9b`;
recorded result792bytes SHA256 `9425c29d6e0e608218352e1a7902f2e117893807c6ae07646cb68fc952e2f4c8`.
Это учебное dummy subject/unknown grant для actual negative controller demo,
не release description действительного комплекта. Физически8files; raw source
assent/event отсутствуют. Отдельный reopen подтвердил head1/0events/1check.

Следующий I2b: связать источник/authority namespace, актуальное entity view и
ready verifier с однократной **авторизацией действия**, резервированием/terminal
outcome, не подменять её check UUID. Lost-head/manual recovery и bootstrap новой
среды требуют отдельной политики/основания. Actual grants не выводить из этого
implementation/продолжения; current incomplete candidate не обходить. Полный
R4/actual release/export/R5–R8 этим срезом не закрыты.
