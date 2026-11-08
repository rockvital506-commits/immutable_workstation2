# R5/I1 — inactive transfer preparation, closure и R6 gap basis

## 1. До кода: предмет и baseline

Продолжение согласовано владельцем после [39](39-agent-system-action-claim-model.md).
Baseline5cc4c54:18entities/29revisions/99norm/29approvals/128refs;
registry74250bytes SHA256 `de0f423fd23cd99e8daa3b00e9f750b2b743dc3e85f1cd5357c869bfb60b5964`.
R4/I2b runtime не закрыт. Export/compatible release/activation не разрешены.

Нужен не ещё один permission manager, а **подготовленный inactive composition**:
exact root/records/declared dependency closure, all known entity decisions,
materializable normative allowlist, procedure/prompt version pins, preserved
historical gap→check basis для R6. Пока это metadata descriptor и private evidence,
не скопированный готовый комплект/архив/полный release. Исходные private authority
journals/assents, binding history, private builds/project architecture не включаются.

## 2. Конструкция и цена

Новая полная версия профиля ENT12r2,6own files:
transfer/ent-0012/r0002/{prepare.py,preparation.schema.json,procedure.md,prompt.md,usage.md,verify.py}.
Exact dependencies ENT12r1 (governance), ENT11r2 (work), ENT14r3 (authority state),
ENT18r1 (existing evidence/native capture stack). supersedes12r1 без consumer switch.
Это один index и reuse правил, не копия governance/core/второй registry.

r1 prepared_only проверял только декларацию plan. r2 использует pinned ENT9r2
capture_plan → ENT5r3 source read → ENT6r3 full known graph/decisions in export
scope. Вычисленный closure должен точно совпасть с declared artifact plan,
отрицательные known events не фильтруются. Новая процедура/prompt фиксируются
до чтения source и все own6 bytes в selection сравниваются с installed component.
Foreign code не исполняется. Только поддержанный Linux x86-64 профиль tools;
сам текст правил не обещает совместимость tools с любой средой.

Seed ENT13r1 остаётся тем же incomplete descriptor. Его проверка выполняется
native checker по его **собственным**12versions/34artifacts в общем capture.
16capability+9condition rows/все gaps/check locators сохраняются как historical
basis, а не coverage нового composition. Никакие старые gaps не discharged по
одному появлению новых files/зелёным unit tests. Новые runtime obligations R4/
R6–R8 отдельно open. Нет универсального actual readiness verifier.

Alternatives: только r1 declaration (недостаточно); собственный graph/reader/DB
(дублирование/новые зависимости); reuse native single-capture+private EvidenceStore
(выбран). Плюсы: точный состав и проверяемые ограничения/история подготовки,
нет reread source ради descriptor. Цена: полный bounded capture/known ledger,
нет global completeness/atomic snapshot/semantic source auth/portable runtime
certification. Allowlist путей не secret/content classifier: owner должен хранить
в системном index только допустимые переносимые тексты. Ни один файл фактически
не экспортируется даже после successful preparation.

## 3. Критерии до реализации

| ID | Условие | Доказательство |
|---|---|---|
| T01 | Explicit inactive acknowledgment/external request+plan pins, closed schema | Reject до capture; native types/UUID/unknown fields |
| T02 | Exact procedure/prompt/seed/component6 installed bytes и selected12r2 | Wrong pin/omitted component/mutated source tests |
| T03 | Native capture используется один раз; source scripts не исполняются | Count acquisition; source code data only |
| T04 | Полный declared graph и exact materialized artifact set | Missing/extra file/duplicate roots/changed dep tests |
| T05 | Full known ledger, relevant restriction/revoke blocks preparation | Unknown/extra/missing event tests, no filtering |
| T06 | No local/history/private project path inputs | Prefix allowlist preflight; private extra source files не collect |
| T07 | Seed native incomplete проверен, все25rows unchanged/open | Wrong seed/basis tests; не coverage нового состава |
| T08 | All action/activation/performed flags false | Success/failure/API/CLI outputs |
| T09 | Private evidence reuses ENT18 CAS/readback, no payload copy | Actual disposable physical evidence verify; metadata-only docs |
| T10 | Limits/faults/unsupported fail closed; partial not cleanup/retry | Existing physical guards + targeted new boundary tests |
| T11 | Old128refs/records/bytes/consumers unchanged | Full pre/post suite/immutable registration proof |
| T12 | Actual installed-source documented practice after registration | No mocks; inactive descriptor/evidence/readback,0grants/0exports |

Source root и private receipt вне переносимого request. Collector для protected
installed namespace может построить **caller_supplied_not_authenticated** plan по
ограниченному наблюдению registry/full approval directory; это не независимая
owner authority/не permission bootstrap. Внешний pin supplied API обязателен.
Initial same-source pins не превращаются в authentication. Повторное чтение
native capture сравнивает наблюдённые expectations, не доказывает глобальную
freshness/невидимые transient events. Нельзя использовать collector для чужого
непроверенного namespace как established installation.

Приватно сохраняются только metadata/evidence/request/plan/descriptors и hashes;
не raw normative payloads/owner source assents. Физическая проверка evidence —
consistency/readback, не повтор source acquisition и не proof execution truth.
Full source bytes не архивируются и не обещают последующий semantic replay.

## 4. Собственные проверки до регистрации

25methods PASS16.366s. Первые21methods:20PASS/1ERROR — fixture изменила BASE
EvidenceStore на temp, но оставила dependency loader искать protected code там
же. После разделения test storage base и actual installed tools следующий
24methods:23PASS/1ERROR — fixture ожидала metadata от публичного verify_evidence,
хотя он возвращает safe report, не raw index. Test исправлен на public report+
private test-only capture index, production evidence verifier не ослаблен.

Review до freeze выявил два production contract gaps: nested request.plan size
мог быть JSON float, равным int в Python; execution_report bytes не включались
в metadata CAS при наличии manifest.execution ref. Добавлены native size gate,
execution object и exact7-document reference closure при persistence, negative
extra raw payload/missing metadata tests. Это реальные изменения до freeze,
не заявка, что первоначальная реализация была уже корректной. Итог25/25PASS.

| Критерий | Точные methods PreparationTests в verify.py |
|---|---|
| T01 | test_exact_true_and_external_pins_before_tools; test_request_schema_unknown_ready_blank_purpose; test_native_request_size_and_duplicate_json_closed |
| T02 | test_request_plan_procedure_prompt_seed_pins; test_missing_own_component_preflight; test_source_mutation_and_symlink_fail |
| T03 | test_capture_once_same_capture_descriptor; test_positive_exact_inactive_closure_not_payload_kit |
| T04 | test_context_duplicate_roots_and_missing_own; test_extra_declared_public_artifact_not_silently_admitted; test_changed_profile_dependency_record_rejected |
| T05 | test_known_negative_relevant_to_export_not_filtered; test_unknown_extra_ledger_file_not_ignored; test_missing_ledger_file_blocks |
| T06 | test_private_project_path_rejected_before_capture; test_private_unplanned_source_is_not_collected |
| T07 | test_all_seed_rows_remain_historical_open |
| T08 | test_positive_exact_inactive_closure_not_payload_kit; test_bad_persist_ack_and_forged_action_flag |
| T09 | test_private_evidence_metadata_only_physical_readback; test_persist_rejects_extra_raw_payload_and_missing_metadata |
| T10 | test_document_and_plan_budget_preflight; test_platform_and_installed_pin_failure; test_evidence_write_fault_retains_partial_namespace |
| T11 | whole repository suite и old128refs freeze proof, отдельно ниже |
| T12 | actual CLI после регистрации, не disposable fixture approval |

Collector tests: test_installed_collector_ack_before_source и
 test_collector_observes_extra_ledger_and_rejects_symlink. Он сохраняет extra
observed decision refs для native проверки, не silently игнорирует файл вне
registry approvals. В тестах только synthetic approval собственной prospective
revision, реальные existing private journals не затрагивались.

## 5. Registration и actual installed-source practice

До регистрации полный45/45module suite PASS; pip check no broken requirements;
repo38/0warnings/0errors; manifest/self-hash/diff checks PASS. Frozen6ownfiles.
Implementation summary approval94df86c2-8803-4665-8425-3db650806134, не literal
owner approval exact bytes/actual release/export grant. Exact depends_on4 и
supersedes12r1, scopes прежние3, old consumers/M1closure20records70artifacts
не переключены. Catalog deployment61/61methods PASS после регистрации.

Registry18entities/30revisions/105norm/30approvals,135artifact/approval refs,
78201bytes SHA256 `452fde09d7952f15158550684572706412d57ea05dee88fcb84dd06c5f9f5914`.
Все прежние128refs/records/bytes сохранены. Actual documented CLI, protected
installed source, без callbacks/mocks/source code injection:

- root ENT12r2; **24selected revisions/90observed normative artifacts**;
- **30known entity decision files**, полный observed approval directory;
- seed проверен отдельно на original12versions/34artifacts;25historical rows
  сохранены/open, new composition coverage not_evaluated;
- private evidence run859a2ef9-220f-4265-91e7-706df2e45cc9;
- index1534bytes SHA256 `c4de5021ca456240878332429c00c31d41f96a82844b7480351119690e107586`;
- inactive manifest157170bytes SHA256 `ec2db149069c17e13f67462b55f03017ee92afc7987bc7f15ba63879ee1952ec`;
- native execution report1269bytes SHA256 `8f2fc1aab8356a0c39da7a847ee2b685e45c60f7805e6a18f0a2a90b782f5cf5`;
- seed validation2176bytes SHA256 `a9448a2d61570b3f3a6b539e6f3ce2a0a3f04051765a2e15cb3a9b1ecea32308`;
-7metadata objects/index,264419bytes aggregate; отдельный новый evidence module
  прочёл/проверил index+objects и воспроизвёл counts/closed flags без source reread;
- без explicit CLI flag — exit2/EXPLICIT_INSTALLED_NAMESPACE_REQUIRED.

30registry revisions не выдаются за24materialized revisions: оставшиеся records
— known context, не неявно скопированные bytes/автовыбор latest. Это declared
entity dependency closure, не аудит всех возможных runtime dynamic imports.
Сохранены **только metadata**, не source payload bodies/архив готового комплекта.
Никаких0→positive owner permission events/imports/claims,0exports,0activations;
all action/performed/current_binding_changed flags false. Байтовая проверка
private evidence не повторяет source acquisition/исполнение и не доказывает
truth источника/behavior/readiness. Private evidence вне Git; его доступность
после восстановления среды не обещана.

## 6. R6: от каждого historical gap к требуемому уровню

Эта таблица — план qualification, **ни одна строка не discharged**. Точный
текущий subject/inputs надо фиксировать отдельно, а не расширять старый ENT13r1.

| ID | Следующая применимая проверка / недостающая реализация |
|---|---|
| G01 | Сквозной change→review→new revision→no implicit binding switch; owner decisions и failure outcomes, не лишь approval JSON |
| G02 | Exact source/record/runtime dependency audit и управляемое обновление inactive binding; no floating latest |
| G03 | Existing r2 recognition/r3 history/model39 не actual permission claim: проверить protected current entity/permission window и durable consumption |
| G04 | Безопасный destination/allowlisted captured bytes/partial outcome/readback/claim terminal receipt; preparation≠exporter |
| G05 | Универсальная capability adaptation manager/interface, unknown-capability stop и inactive adapter tests до full release; не заранее выбирать чужую среду |
| G06 | Прикладной readiness policy/verifier связывает exact coverage/evidence/known restrictions/permissions, не caller ready=true |
| G07 | Activation manager с explicit exact owner decision, preconditions/result/history; никакой активации от import/export/prompt |
| W01 | Actual agent source/research decisions и provenance review; structural scenario list не behavior |
| W02 | Реальное обнаружение coverage/unknown/contradictions и review на exact task |
| W03 | Отбор/reuse/reject паттернов с основанием/ограничениями в наблюдаемой работе |
| W04 | Цель/измеримые критерии до действий и validation результата, а не post-hoc описание |
| W05 | Review факта/recommendation/decision/practice на неоднозначных примерах |
| W06 | Actual consent boundary, not inferred grant из продолжения; owner/operator review level отдельно |
| W07 | Реальная остановка при ambiguity/FAIL/unsupported, полезный diagnostic и следующий шаг |
| W08 | Версионируемая очередь отложенного/условия возврата без silent forgetting |
| W09 | Exact evidence/results/errors/limits и self-review; R3 не independent owner/agent-behavior proof |
| C02 | Полная новая matrix16capabilities+9conditions с exact records/clauses/check evidence, не metadata count |
| C03 | У каждой capability text+application+applicable evidence level, не слово в README |
| C04 | Учет exact approved revisions и реальное предъявление/решение compatible-release subject; implementation delegation не release grant |
| C05 | Closure/full known negatives плюс необходимые policy/runtime dependencies, no private/history leak by automatic export |
| C06 | Native negative test: incomplete remains candidate/blocked, новый full profile не маскирует gaps |
| C07 | Уровни static/model/bounded execution/actual behavior, точные inputs/replay limits без overclaim |
| C08 | Механизм capability detection/adaptation/fail closed; actual выбранная новая среда обследуется отдельно R7, не universal compatibility claim |
| C09 | Раздельные implementation/release/export/activation decisions и replay-resistant actual action state |
| C10 | Core immutable/его изменение требует отдельного явного решения, downstream impact и новой версии |

G05/G07 здесь — capability IDs, не одноимённые секции governance G05/G07.
Механизмы adaptation/activation нужны до объявления full compatible release;
actual обследование/активация одной новой среды остаются отдельными R7/R8.
Нельзя требовать уже активировать неизвестную среду ради подготовки или считать
её автоматически совместимой. Главный следующий construct — закрывать эти
capability gaps применимыми interfaces/processes/evidence, а не повышать old status.

## 7. Финальная проверка и границы завершённого

Postregistration full45/45modules PASS;25own methods/61catalog deployment methods
PASS. pip check no broken requirements; repo38checks/0warnings/0errors;
manifest/self-hash/diff checks PASS. Все135refs/hash/native sizes проверены,
старые128refs/bytes/records unchanged относительно5cc4c54;6ownfiles совпадают
с freeze до approval, все T01–T12 method selectors проверены. Public234md/
86README/41research/45modules,553relative links/0broken. Private evidence/raw
source/runtime journals в Git не добавлены. Ранее найденные errors/corrections
зафиксированы, не заменены рассказом о первом беспроблемном запуске.

Завершён R5/I1 inactive preparation profile и actual metadata practice, **не весь
R5 и не собранный physical portable kit**. Уже согласованное продолжение не
авторизует действие. R4/I2b durable action state, R5 safe exporter, R6 actual
positive readiness/full compatible release и отдельные R7/R8 environment/activation
остаются открыты. Следующий construct — generic inactive adaptation/activation
mechanisms и применимая evidence qualification (capability G05/G07), затем
связать qualified coverage/current views/claims. Не активировать неизвестную
среду и не обходить incomplete guard ради продвижения номера этапа.
