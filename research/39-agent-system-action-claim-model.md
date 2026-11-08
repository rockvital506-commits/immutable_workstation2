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
