# R4/I2b — граница readiness и модель однократного action claim

## 1. Исходный статус и обязательная граница

Baseline4c8b0b1:18entities/29revisions/99norm/29approvals/128refs; registry74250bytes
SHA256 `de0f423fd23cd99e8daa3b00e9f750b2b743dc3e85f1cd5357c869bfb60b5964`.
[38](38-agent-system-local-authority-state.md) даёт persisted checks, не action
claims. [36](36-agent-system-positive-permissions-design.md) §4–6 требует отдельно
permission/current view/readiness/claim/action. «Продолжай» не actual grant.

Исследованный code: ENT14r2 check_current_candidate вызывает immutable ENT14r1
check_proposal, который всегда закрывает consistent ENT13r1. ENT13r1/check.py
принимает **только** incomplete profile/statuses; caller ready=true не readiness.
Положительного native verifier для compatible release ещё нет (R6/G05/G07).
Ставить release_allowed=true по одному r2 recognition нельзя. Проверенный source
assent controller не устраняет этот разрыв. Ни foreign callbacks, ни JSON ready
не будут production authority. Старые frozen revisions не меняются.

Этот checkpoint — **design+executable bounded model**, не новая normative revision,
не durable claim journal/actuator и не закрытие I2b/R4. Не создаётся новая папка
runtime/новый permission store/actual grant. Model живёт внутри test module, не
служит незарегистрированным production API. Никаких новых dependencies.

## 2. Выбранный минимальный контракт и альтернативы

1. Одноразовый request UUID r3 недостаточен: другой UUID повторно проверяет тот
   же grant. Reservation должен расходовать устойчивую identity действия, не
   identity анализа и не только changing context/head.
2. Планируемый immutable binding: authority namespace; action; exact subject;
   exact release grant; для export также exact export grant/export_id/descriptor,
   destination binding/procedure/prompt. History/source/current permission head,
   entity view и readiness evidence/verifier refs — basis reservation, не новый
   subject по умолчанию. IDs/hash здесь model symbols, не проверенные bytes.
3. Для export два cumulative uniqueness keys в одной authority области: grant
   identity и export_id. Это не позволяет обойти consumed grant новым request UUID/
   context/subject/destination либо новым grant с прежним export_id. Collision
   требует нового явно согласованного export, не overwrite/автоматический reset.
   Для release key — exact release grant. Export не расходует parent release
   grant как новое release действие: отдельные exports с новыми IDs и grants
   могут ссылаться на тот же parent. Release≠export≠activation.
4. Current namespace/head, full relevant permission stream/source binding, entity
   no-known-blocks, exact procedure и подтверждённая readiness — необходимые
   gates. Для export отдельно parent release permission и destination. Release
   не требует fictitious export parent/destination. Реальное выполнение release
   **не выводится** из parent permission; требования R5 к опубликованному bundle
   отдельны. Actual ready evidence/verifier и filesystem destination ещё отсутствуют.
5. Модель принимает эти gates как явно названные **аксиомы теста**, не production
   truth. Generic ready=true из data не реализует ни одну. Model result никогда
   не выставляет effective action flags. Current token equality не является
   global freshness/проверкой protected installation или cross-store completeness.

Варианты: optimistic check then copy (гонка/повтор — отклонён); transaction только
в permission store (не делает entity snapshot/приёмник атомарными); shared
protected operation window+durable reservation+terminal receipt (направление).
Stdlib SQLite мог бы атомарно менять одну DB, но не чужую ledger/filesystem;
не вводится ради ложного решения. Distributed transactions/crypto outside scope.
Плюсы выбранного контракта — явная linearization/консервативные failures/нет
авторизации из check receipt. Минусы — availability при lost receipt, несколько
trusted boundaries, будущая цена полного replay и обязательная runtime integration.
Эффективность модели — ловить противоречия **до** нового persistence code, не
benchmark и не доказательство эффективности actual exporter.

## 3. Переходы и failure policy (проверяемое предложение)

- absent → reserved: все gates и exact external current token совпали, обе
  uniqueness identity ещё свободны; будущая durable запись+readback до выдачи
  reservation receipt. В модели это один логический шаг, не OS atomicity.
- reserved → executing: повторные current/gates/binding проверки непосредственно
  перед actuator; start одноразовый. Stale/deny/revoke не разрешают new writes.
- reserved/executing → failed: stop, не rollback/delete/regrant. При pre-start
  отказе нет выполнения, но reservation уже заняла identity.
- reserved/executing → outcome_unknown при crash/lost outcome: identity занята,
  не auto-expire/unlock-by-time/retry/adopt. Ошибка после durable reserve может
  оставить reservation без доставленного receipt. Ручное reconciliation policy
  проектируется отдельно и не получает права на повтор старого export.
- executing → succeeded: только проверенный trusted actuator receipt exact
  binding/output manifest/readback. Model input receipt_verified — **аксиома**, не
  проект production bool API. Unknown/failed не становятся success по повторной
  просьбе. Successful recorded outcome не permission на повтор.
- При revoke после start: остановить будущие writes в следующем controlled
  boundary, сохранить partial. Отмену уже произошедшего физического действия
  гарантировать нельзя. Модель проверяет stop outcome, не промежуточные байты.

Reservation до side effect консервативно расходует identity даже при отсутствии
known writes. Это не новая правообразующая политика повторного grant: она лишь
не добавляет retry к старому «одна конкретная операция». Возобновление/repair/
снятие deny требуют отдельного процесса/основания. Новое явное owner решение
не снимает старый deny автоматически.

## 4. Критерии до кода

| ID | Критерий | Доказательство и граница |
|---|---|---|
| A01 | Gates независимы, все required exact True | Exhaustive boolean truth table; truthy inputs не True |
| A02 | Смена current token после reserve не даёт start | Finite transition test; не глобальная freshness |
| A03 | New request UUID/view/subject не снимают old consumption | Model identity collision tests |
| A04 | export_id и grant каждый уникален независимо | Alias/collision tests внутри namespace |
| A05 | Namespace/subject/procedure/destination binding не заменяются | Exact frozen binding test; не FD proof |
| A06 | Terminal outcomes absorbing; crash/lost reserve не retry | Model unknown/failure/repeat/start/finish tests |
| A07 | Перемежения двух callers не дают двух reserves/starts | Exhaustive bounded serial interleavings; не kernel concurrency |
| A08 | Separate export grants могут иметь общий release parent | Semantic model test; не two actual exports |
| A09 | r3 positive checks с новыми UUID действительно не расходуют export | Disposable physical store, synthetic assents, native r2 evaluator |
| A10 | Старый native incomplete guard не обходится | Реальный installed native code, synthetic owner context; без readiness injection |
| A11 | Все128refs/registry/старые records unchanged | Bytes/hash/git baseline + whole repository suite |
| A12 | Model не normative activation/actual grant/performed | Closed false public flags; report scope/runner integration |

После model проверки: trace методов/количества interleavings/реальные результаты,
открытые runtime obligations. R5/R6 потребуют своего pre-code design/qualification;
не подменять это фиктивным ready path в новой ENT14.

## 5. Исполненный checkpoint и trace

До model code commit88e2838 зафиксировал A01–A12. Изолированная прежняя
hash-locked среда восстановлена; никаких новых packages. Новый test module
содержит только model+tests, не importable production manager из agent_system.
19methods PASS4.3s (включая реальные disposable r3 файлы и native r2 guard).
Первый запуск18PASS/1FAIL: ошибочный expected oracle11states, не нарушение
uniqueness. Он пропускал различие failed/outcome_unknown до/после start. Oracle
исправлен по структуре1absent+2callers×7states=15, не ослаблены transitions или
инварианты. Итог depth7,11commands/2callers,15unique states,803explored edges.
Это exhaustive **в пределах указанного finite serial model**, не arbitrary
parallel threads/processes/сбой питания/доказательство атомарности filesystem.

| ID | Метод tests/test_agent_action_claim_model.py |
|---|---|
| A01 | test_required_gate_truth_table —512rows; test_truthy_is_not_verified_gate |
| A02 | test_preflight_stale_does_not_consume; test_stale_or_new_negative_between_reserve_and_start |
| A03 | test_new_request_context_subject_cannot_replay_export; test_same_request_id_not_available_for_other_binding |
| A04 | test_export_id_and_grant_each_independently_unique |
| A05 | test_each_binding_field_is_exact_at_start; test_namespace_scoping_not_global_completeness |
| A06 | test_terminal_outcomes_are_absorbing_and_consumed; test_lost_reserve_receipt_or_crash_does_not_regrant; test_start_is_once_success_requires_modeled_receipt |
| A07 | test_exhaustive_bounded_two_caller_serial_interleavings |
| A08 | test_release_and_two_exports_have_distinct_claim_keys |
| A09 | test_physical_r3_checks_do_not_consume_export |
| A10 | test_native_incomplete_guard_still_closed_without_readiness_injection |
| A11 | repository full suite и unchanged baseline proof, отдельно ниже |
| A12 | test_model_outputs_never_actual_permission_or_execution; test_unknown_action_and_blank_binding_symbols_rejected |

A09: **физические** temp files0700/0600, synthetic release/export assents,
два разных requests одного export_id/grant признаны r2, checks_count2, reopen
PASS; обаaction_claim_created=false/export_allowed=false. Проверка показывает
практически, почему нельзя повысить check UUID в actual action single-use.
Это не два совершённых экспорта. A10 вызывает installed old guard без injected
readiness: release/export обе blocked_incomplete_candidate при synthetic exact
permission recognized. ENT13 coverage не менялась. Actual положительного owner
события не создавалось; новый private actual namespace не запускался.

Test stop_after_start_records_failure_without_undo_claim моделирует уведомление
контроллера о stop и terminal failure. Он **не** наблюдает реальный revoke во время
copy и не проверяет промежуточные bytes. Между writes/current checks/partial receipt
остаётся обязанностью R5 actuator. Модель не выдаёт verified_receipt наружу как
машинный способ доказать успех; такой future API ещё надо спроектировать.

## 6. Открытые runtime obligations и следующий конструктивный шаг

1. Durable claims должны участвовать в том же protected serialized permission
   window, а не в independently committed DB beside r3: иначе crash создаёт split
   brain. r3 head schema закрыта/immutable — future revision, не sidecar overwrite.
2. Protected entity current view и permission head — отдельные trust boundaries.
   Требуется явная координация cooperating writers/operation window и внешние
   pins/high-water; hash/read-twice не доказывают отсутствие transient updates.
   Стабильный protected installation — предпосылка A, не hostile same-uid promise.
3. Binding destination/procedure/prompt проверяется будущим actual FS adapter,
   а не совпадением opaque symbols. Разрешённый export allowlist не включает raw
   private authority statements/journal/секреты/частную архитектуру автоматически.
4. Отсутствующий положительный coverage/readiness verifier нельзя заменить
   моделью. R5 сначала готовит явно **неактивный** переносимый комплект/closure/
   versioned prompt с зафиксированной процедурой; R6 квалифицирует все обязательные
   coverage gaps и отдельный compatible-release предмет. Только затем можно
   квалифицировать actual положительный claim+actuator на таком предмете и exact
   owner grant. Негативная и модельная ветви R4 проверяемы сейчас, но не закрывают
   positive actual path. Порядок этих зависимостей не разрешает сам выпуск.
5. Lost receipt/manual recovery/bootstrap новой среды и independent high-water
   не реализованы. None/unknown/clock timeout не освобождает consumed identity.
   Новое явное действие владельца, R7 адаптация и R8 activation — отдельно.

Таким образом дальше не создаём ещё один «всегда blocked permission manager»,
который маскировал бы отсутствие readiness. Следующий предмет — R5 inactive
transfer preparation/closure и Gap→check map для R6; I2b runtime integration
остаётся явно открытым. Это уточнение технических dependencies, не отмена R4
и не новый scope/owner grant. Registry/approvals/старые consumers не меняются.


Первый full run:43/44modules PASS, test_rules FAIL2/891checks. Новый test module
использовал pathlib ROOT, но repository test-root convention требует стандартный
HERE/os.path.dirname(ROOT)+os.chdir(ROOT). Исправлен сам модуль (независимость
от cwd); правило/проверка не ослаблены. Остальные43modules, в том числе19model/
physical/native methods, прошли уже в этом запуске. Полный rerun обязателен ниже.

## 7. Финальная квалификация этого среза

Повторный **полный** tests/run-all.py44/44modules PASS (включая19новых methods).
repo-validate38checks/0warnings/0errors; test_rules891/0; pip check no broken
requirements; manifest/self-hash/diff checks PASS. Registry и все128artifact/
approval refs/records побайтово unchanged относительно4c8b0b1. Проверены hashes/
native sizes и все method selectors A01–A12. Public230md/86README/40research/
44modules,546relative links/0broken. Нет conditional implementation approval:
новой normative implementation/активации этот model checkpoint не содержит.

Результат: проверенная design model и воспроизведённая native граница, **не**
завершённый I2b action manager и не завершение R4. Текст продолжения не основание
реального release/export. Старые consumers, исходные normative bytes, исходные
approval events и private authority journals не менялись. Новых actual owner
assents/permission events/positive release/export/activation нет.
