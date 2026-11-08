# M1/I4 — acceptance bounded operator trial

Статус: prequalification PASS; exact implementation зарегистрирована; реальный
installed lab с B и без B и отдельный semantic replay PASS. M1/R2 закрыт только
в согласованной bounded laboratory области, не вся переносимая система.
Основание: проект [32](32-agent-system-operator-trial-design.md), D01–D18/T01–T30,
подтверждённое продолжение и условное делегирование владельца после проверок.
Не одобрение release/export/activation. R3–R8 не выполнялись этим I4.

## Состав и метод

ENT18r1:13ownfiles; dependency19revisions/57artifacts; source20/70;
payload ENT13r1 без изменений12/34. Exact paths/hashes/summary approval фиксируются
только после prequalification. Native suite uses isolated approved interpreter
и прежний hash-lock ENT4r2; никаких новых packages. Реальная ENT18 до регистрации
отсутствует. Synthetic approval в temp fixture не owner decision и не practice.

Уровни: **physical** — native byte/filesystem path в disposable namespace;
**fault** — injection/patch child или syscall для конкретного stop contract;
**lower** — переиспользованные immutable lower-layer semantics; **lab** — один
installed entry с явно доверенным checkout. SubTests не отдельные full runs.
Патчи child packets не выдают себя за physical concurrency/real environment.

## T01–T30 traceability

Selectors — точные имена test methods (unittest class в соответствующем module):
F=operator/ent-0018/r0001/verify.py; R=runner_verify.py; P=replay_verify.py;
A=acceptance_verify.py (тот же каталог). E9=validation/ent-0009/r0002/verify.py;
E15=staging/ent-0015/r0001/verify.py; E16=staging/ent-0016/r0002/verify.py;
E17=validation/ent-0017/r0001/verify.py. Все пути относительно agent_system.

| ID | Сценарий и method selectors | Уровень / что НЕ доказывает |
|---|---|---|
| T01 | R.test_positive_without_b_and_private_evidence; E9.test_one_acquisition_per_surface | physical/lower; count envelope, не snapshot |
| T02 | R.test_positive_two_distinct_acquisitions; A.test_t30_documented_lab_entry_on_prospective_installation | physical;2observed read_set в prospective client, не authentication |
| T03 | R.test_changed_source_after_a_uses_captured_bytes | physical mutation; stage uses A, не freshness |
| T04 | F.test_external_session_pin_required; F.test_wrong_document_bytes; R.test_external_session_pin_and_b_pairing_stop_preflight | physical preflight; no claim/source |
| T05 | A.test_t05_extra_or_wrong_selection_rejected_before_claim; R.test_wrong_profile_composition_stop | physical preflight/exactselection |
| T06 | A.test_t06_installed_own_prompt_hash_mismatch; A.test_t06_changed_descriptor_metadata_stops_preflight; F.test_installed_pins_changed | physical bytes/metadata; hostile writable namespace не решён |
| T07 | A.test_t07_known_validate_block_a_no_capture; A.test_t07_unknown_event_a_no_stage | physical scoped block/unsupported, no downstream |
| T08 | A.test_t08_binding_fail_no_acquisition_reuse; E9.test_no_capture_for_failed_binding | fault/lower; packet absent, counters unknown |
| T09 | R.test_source_packet_forged_capture_rejected; R.test_source_packet_forged_document_rejected | fault boundary substitution, no fabricated source truth |
| T10 | A.test_t10_export_transfer_context_is_not_generic_trial; F.test_profile_mismatch_before_any_source_read | physical closed plan; E12 not generic preflight |
| T11 | R.test_stage_failure_not_reader_success; E15.test_partial_write_loop; E15.test_zero_write_stops; E15.test_fsync_failure_not_success | fault + lower actual private files, no rollback |
| T12 | R.test_reader_swapped_capture_handoff_rejected; E16.test_capture_refs_exact_manifest; P.test_reader_metadata_tamper_rejected | fault/lower/replay; exact object/manifest/metadata refs |
| T13 | A.test_t13_real_post_read_corruption_no_handoff; E16.test_late_binding_failure_withholds_capture | physical CAS mutation + lower fault |
| T14 | F.test_namespace_symlink_rejected; F.test_unsafe_namespace_not_repaired; E16.test_object_hardlink_rejected | physical/lower; selected filesystem guards, not all mount attacks |
| T15 | E9.test_capture_owned_maps; E16.test_independent_capture_maps; E16.test_capture_uses_first_reads_not_readback_outputs; E16.test_fd_cleanup_before_capture_delivery | lower handoff/ownership; independent exact byte maps |
| T16 | R.test_positive_without_b_and_private_evidence; P.test_success_no_b_semantics | physical; query not_requested, A not current |
| T17 | F.test_b_pairing; F.test_query_without_b | physical preflight |
| T18 | A.test_t18_wrong_b_document_stops_before_a; R.test_b_failure_cannot_fallback_a | physical preflight + fault B, no A fallback |
| T19 | A.test_t19_new_revoke_does_not_change_archive; R.test_actual_new_b_tool_query_block_not_permission | physical independent B block; archive/evidence old bytes unchanged |
| T20 | A.test_t20_exact_lift_not_latest_date; A.test_t20_lifting_one_of_two_leaves_other | physical plus existing E17 semantics; exact target, no latest-date heuristic |
| T21 | A.test_t21_archive_negative_cannot_disappear_in_b | physical; archived known negative retained, not global completeness |
| T22 | A.test_t22_old_view_with_two_acquisitions_not_freshness | physical; intentionally same old B passes consistency, freshness NOT_CHECKED |
| T23 | P.test_derived_query_context_tamper_rejected; E17.test_unknown_new_event_not_filtered | semantic tamper/lower; literal query/context, unknown unsupported |
| T24 | A.test_t24_claim_collision_does_not_read_source; A.test_t24_declared_caps_exact_no_dependency_change; F.test_byte_and_file_limits_poison_store; F.test_budget_includes_index; F.test_disk_full_retains_partial_and_poison | physical collision + reduced-cap/fault limits; no maximum RAM/CPU benchmark |
| T25 | F.test_readonly_tamper_extra_missing_and_permissions; F.test_partial_not_readable_as_sealed; P.test_extra_valid_cas_object_rejected_semantically | physical CAS vs semantic distinction |
| T26 | P.test_success_b_without_source_or_trial_or_live_ledger; P.test_counter_tamper_with_valid_cas_rejected; P.test_coherent_copy_is_not_execution_authentication | physical offline + semantic tamper; copy can pass, no execution proof |
| T27 | R.test_repeated_runs_no_overwrite; F.test_no_resume_or_overwrite; F.test_fd_cleanup_success_and_failure | physical repeat/no overwrite; fd cleanup |
| T28 | E9.test_r1_metadata_semantics_unchanged; E16.test_r1_metadata_parity_except_profile; full repository suite + old97refs comparison | lower/regression; unchanged immutable old artifact/approval bytes |
| T29 | P.test_human_report_closed_safe_and_reproducible; R.test_result_no_raw_bytes_or_absolute_roots; A.test_t30_cli_without_trust_is_safe_in_any_registration_state | physical/renderer; secrets classification not promised |
| T30 | A.test_t30_lab_requires_explicit_trust_not_source_discovery; A.test_t30_documented_lab_entry_on_prospective_installation; procedure.md lab.py command | prospective physical client, no loader/child injection; real registered practice — § результатов ниже |

## Коррекции до freeze

Первый acceptance run:11/12 PASS — test ошибочно ожидал failed для unknown ledger
kind, production верно дал unsupported. Исправлено ожидание, не production stop.
Затем17/17 PASS59.949s и18/18 PASS89.143s; добавлен явный T10 export-context
regression до финального freeze. Regex run.py переведён в raw literal, убран
invalid-escape warning. Runner fixture удаляет ENT18 только из disposable registry
перед synthetic append; unregistered test теперь не зависит от real registration.
Старые normative файлы/approval events не редактировались.

## Границы эффективности и решения

Shared acquisition/handoff вместо повторного чтения source подтверждается byte
ownership/count tests и prospective client2observedread_set. Дополнительный CAS/
hash/readback/semantic replay имеет цену; universal speedup не измерялся. Ограничены
stored unique bytes/files/documents, не весь RAM/CPU. Human report не печатает raw
maps/absolute paths, но automatic secret discovery не реализован. Only trusted
installed checkout lab; foreign roots требуют внешней expectation authority.
Сохранение coherent records не proof execution/current permission/freshness.

Implementation approval допустим только по ранее согласованному conditional
summary basis после всех prequalification checks. Native real T30 имеет bootstrap
зависимость от регистрации: до неё обязан остановиться, поэтому отдельно
postregistration. Если он не проходит — M1/R2 не закрывать, bytes не править
в-place, зафиксировать failure/новую ревизию. Даже положительная практика закрывает
только bounded M1, не R3–R8/полное поведение агента/выпуск/активацию.


## Фактические результаты и точная регистрация

До регистрации:40/40 repository modules PASS; отдельный19/19 acceptance run
78.649s, own35+26+17+19=97methods. Число97methods не путать со97старыми references.
Repo validation38checks/0warnings/0errors; pip check no broken requirements;
manifest/self-hash/diff checks PASS. Перед approval реальный documented CLI
с --trust-this-checkout вернул2/COORDINATOR_NOT_REGISTERED, как и требуется.

Approval `77e27297-3504-42b5-bee6-5db1cd4ac8ac`: summary условного основания, не
новая цитата владельца о конкретных bytes. Честно фиксирует, что registered native
T30 на момент решения ещё впереди; synthetic client prequalification не подменяет
его. После регистрации53/53 catalog deployment methods PASS.13ownfiles frozen;
последующие правки только ненормативного отчёта/navigation/deployment regression.
Старые97artifact/approval refs/байты и все прежние revision records сохранены.

Registry:18entities/26revisions/85normative artifacts/26approvals;65612bytes,
SHA256 `5aca488cb10853f5c3fdca9e0b0ee8d23800286b9b5455ce27936caaaa76a417`.
Payload ENT13 по-прежнему12/34. Никаких новых negative/release/export/activation
events. Два actual запуска — ровно documented CLI из procedure.md, второй
с --without-query; без loader/child packet injection и без /tmp recipe в интерфейсе.

| Проверка | С B/query | Без B/query |
|---|---|---|
| operator_run_id | 1904b3ce-3d85-4328-826f-11cfd90e2229 | 22db629f-01ef-40d1-a2f8-14aa87856fe7 |
| task_id | ae2fa1da-99bf-48c2-851b-885a6e92aaec | 720f3747-5fb1-4bc8-ac18-1bab9d36f1c3 |
| status | trial_checked_with_known_query_no_admission | trial_checked_no_query |
| capture_invocations/completed_source_reports/validated_captures/source_acquisition_calls | 2/2/2/2 | 1/1/1/1 |
| private CAS objects / unique bytes | 116 / 1230482 | 111 / 1184833 |
| receipt index bytes | 14528 | 13916 |
| full semantic replay / source_bundles | true / 2 | true / 1 |

External receipt/index pins (для отдельного readonly replay):

- B: `037d343ef2d5fada2d21abf913ff5baf5cdb1015f5e7e8830591e4e648482672`,14528bytes.
- no-B: `2c45e854f941d3bf888b9ef60ed0755b8faa707087de2985d8f2e4e1e3c2c870`,13916bytes.

### query — сохранённые входные pins

- session: `982cd6730d8245d460ef412c80c2c924158e200756ac7307a6e3deb62ef1862b`,707bytes.
- A plan: `dc7731473ff69219bf8d0af9d14ce4b3a82c5461ffb13847f7c19bb3447f7f1a`,18323bytes.
- B plan: `7bdf952c38e46c48a4beb54f80e49f3bb15d60b8e32278889b521bff1ef2d809`,18323bytes.
### no-query — сохранённые входные pins

- session: `9ff98d4e8a58139b6df7eaf5debbf2672bcc377e3ce3a897f5568b45202c7919`,536bytes.
- A plan: `c7ed411a2bddbf7759c0ec70c54ef9fda34f6309d929bf6b8cbcff6b4bf1b9b5`,18323bytes.


Оба CAS отдельно проверены verify_evidence → consistent_private_evidence; затем
повторный отдельный replay_operator_run → consistent_recorded_operator_run_no_admission,
full_replay=true. Read-only profile observer при этих повторных replay зафиксировал
0source read_set/0live catalog-ledger `_installed` calls. Это узкое наблюдение
функций, не OS-wide IO audit.2/1source_acquisition_calls actual CLI — counters
проверенных ENT9 envelopes, не независимый syscall tracer; independent2read_set
наблюдались в prospective client test. Различие evidence уровней сохранено.
Private CAS/trials остаются local вне Git; UUID/pins не обещают вечной доступности
при переносе workspace. Никакие raw maps/decision texts в отчёт не скопированы.

Source/installation совпадают только в explicit trusted checkout lab. Foreign
environment/discovery/adapters/behavior/permission не проверялись. known query
export не выполняет экспорт. Release/export/activation/transition=false;
overall/current_permissions=not_evaluated, incomplete candidate неизменен.

Следующий маршрут: R3 — практическое применение методологии на согласованной
содержательной задаче, затем R4 positive permission model, R5 portable composition,
R6 coverage/отдельное решение о compatible release, R7 обследование одной среды
и inactive binding, R8 отдельная activation. Этот lab ни один из них не подменяет.

## Финальная проверка после registration/practice

Повторный полный tests/run-all.py через approved isolated interpreter:40/40modules
PASS, включая53catalog deployment tests и35+26+17+19ownmethods. pip check — no
broken requirements; repo-validate38checks/0warnings/0errors; csv-check/self-hash
и git diff --check PASS. Public inventory218md/86README/34research/40modules,
511relative links/0broken. Повторно сверены13frozen own artifacts и97старых
references/bytes плюс неизменность всех прежних revision records. Local evidence
не добавляется в Git. Никакого отдельного release/export/activation допуска.
