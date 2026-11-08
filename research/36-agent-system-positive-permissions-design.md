# R4 — проект действительных разрешений release/export

## 1. Статус, основание, цель

**Исходный проект до реализации. Затем выбран A; актуальный срез — §10.**
Продолжение R4 подтверждено, но конкретный выпуск/экспорт/activation не разрешены.
Ни одной positive decision этот документ не создаёт. Это локальный design report,
не новая normative revision/индекс/активная связка. R4 пока не закрыт.

Источники: [аудит31 R4](31-agent-system-core-audit.md), [задание/история30](30-agent-system-discovery.md),
ENT1r1, ENT12r1 G03/G04/G07, ENT7r1, ENT14r1 и ENT13r1 (тексты/code прочитаны).
Registry на входе:68244bytes, SHA256
`36870624be4c8cc5436cb44ac6f97eb169b27db1b22910d8994fe8ae9d3219b5`,
18entities/27revisions/89norm artifacts/27approvals,116refs. R3 дал bounded
operator/self-review, не blanket owner review/coverage всех требований.

Цель: различать предложение/согласие/действительное точное разрешение/готовность
предмета/выполнение. Реализовать впоследствии positive и negative semantics,
а не поставить true рядом со старым incomplete candidate. Результативность R4
потребует исполняемых проверок, не только этого проекта и мысленных сценариев.

## 2. Что уже есть и где нельзя продолжить старый механизм молча

- ENT14r1 связывает **proposal**, candidate/registry/ledger и parent proposal;
  parent release_request — не grant. Он намеренно всегда закрыт для ENT13r1.
- ENT13r1/check.py допускает только incomplete_candidate и core_coverage=incomplete;
  замена readiness на ready не есть проверка coverage и должна отвергаться.
- ENT7r1 обрабатывает entity approve/restrict/revoke/lift; release/export events
  не поддерживает. ENT18r1 читает весь объявленный catalog/approvals. Добавление
  туда authorize_release сломает старый profile, а его фильтрация скроет unknown.
- Поэтому старые immutable versions/семантика не изменяются. Предпочтительное
  направление — новая revision ENT14 с собственным closed permission-event
  contract; entity ledger по-прежнему проверяется прежним стеком целиком.
  Если выявится необходимость новой версии общего event evaluator, её нужно
  отдельно описать/проверить и мигрировать consumers, не дописывать r1 in-place.
- Permission decisions — runtime данные, по умолчанию local вне Git, отдельно
  от catalog/approvals. Их полный объявленный набор передаётся явно; отсутствие
  stream/unknown kind/непроверенное происхождение не превращается в grant.
  Это не второй каталог normative entities: их единственный index остаётся registry.
  Runtime records не начинают автоматически экспортироваться как часть tools.

## 3. Ключевое решение: откуда известно, что owner действительно разрешил

Ни JSON field actor_role=owner, ни hash найденного JSON, ни flag trusted=true
внутри input не аутентифицируют владельца. Само решение нельзя использовать как
собственный trust anchor. Нужна authority **вне** входного source/event stream.

| Вариант | Плюсы | Минусы/риски/стоимость/влияние |
|---|---|---|
| **A. Owner-controlled local authority — рекомендуется для первого bounded профиля** | Явное решение владельца привязывается к exact bytes через независимо установленный protected context; stdlib/прежних deps достаточно; соответствует local вне Git | Нет cryptographic identity proof; нужны действительно доверенные operator/interpreter/namespace и отдельный bootstrap в новой среде; hostile same-uid/root вне обещания |
| B. Проверяемые подписи и ключевая политика | Проверяемое происхождение при переносе подписанных bytes | Нужно выбрать signer/verifier, доверенные ключи/отзыв/ротацию/восстановление и защиту ключей; новая инфраструктура/зависимости отдельно согласуются; подпись не доказывает coverage/freshness |
| C. Пока согласовать только trust contract | Не вводит преждевременное основание доверия | Effective positive execution остаётся blocked; ещё не реализованный R4 |

A — не TOFU: нельзя вывести trusted allowlist из того же недоверенного набора
или автоматически импортировать actor_role/statement как согласие. Известное
решение из диалога может быть источником human-reviewed записи; summary остаётся
summary, точный предмет/пределы предъявляются владельцу отдельно. «Продолжай R4»
не может стать allowlist для выпуска. Approval implementation тоже не такой grant.
Вне конкретного явно доверенного context результат unsupported/authority_not_established.
В новой среде authority не наследуется автоматически от истории.
Pure checker не может отличить одинаковые bytes «независимого pin» от pin,
вычисленного тем же caller из source: проверяемое происхождение context —
предпосылка protected client/operator, не свойство hash или произвольного аргумента
API. На тестах запрет source-derived bootstrap проверяется на client boundary;
не заявлять универсальный provenance detector внутри bytes-only функции.

## 4. Предмет и замкнутые связи (кандидат контракта)

### 4.1. Release subject

Отдельные immutable bytes описывают точный состав: identity/purpose, selected
versions/dependency closure/records/artifact path+SHA+native size, core/coverage
report refs, критерии/процедура/prompt нужной версии и известные ограничения.
Subject pin внешний, не вычисленный и тут же объявленный доверенным из source.
Нельзя authorize произвольный subset/другой descriptor тем же названием.

Coverage report должен иметь проверяемые exact inputs/evidence и относящийся
trusted verifier/policy. Caller boolean ready=true, произвольный JSON report
или copy self-assessment не заменяют проверку. Пока соответствующий механизм
не выполнен (R6), фактическая readiness текущего subject не подтверждается.
ENT13r1 остаётся incomplete12versions/34artifacts и не получает grant как полный.
Даже coherent fabricated evidence не обязано отличаться от истинного при чистом
replay: policy/verifier проверяет заявленную область, не реальность произвольных
наблюдений. Для нужного уровня проверки требуется относящееся доверенное
основание; crypto signature не делает ложное наблюдение истинным.

### 4.2. Release decision

Предлагаемые closed fields: version/kind/decision_id, action=release и literal
area, exact subject ref, exact basis-view refs, explicit limits, statement/provenance.
Поля provenance сохраняют происхождение/форму цитата либо summary, но не служат
машинным доказательством authority. Авторитет устанавливается выбранным §3 способом.
Историческая approve_revision не переименовывается в эту decision.

### 4.3. Export decision

Отдельная identity/action=export, exact release decision pin и тот же subject,
exact allowlist paths/bytes, pinned procedure/prompt и destination binding.
Release grant сам по себе не разрешает копирование. Subset/лишний файл/другая
цель/выходной формат/процедура требуют своего явно разрешённого subject/export.
Root для записи передаётся вне source; pathname/hash строки не доказывает
тождество/безопасность приёмника. Реальную проверку binding/FD/claims выполняет
будущий exporter/adaptor R5, которого этот проект не создаёт.

Один export разрешает одну конкретную операцию. Повтор — новый run/claim в
доверенном state; поле одноразовости в JSON само её не обеспечивает. Без
подходящего stateful механизма нельзя объявлять replay protection реализованной.
Активировать получившуюся среду этим grant нельзя.

### 4.4. Нет самоссылки и плавающего latest

Basis view фиксируется **до** decision, grant не входит в собственный hash.
Новый evaluation view явно содержит сам grant и последующие known negatives.
Старый basis не выдаётся за current. Добавление unrelated revision в registry
не должно автоматически подменять/расширять subject: exact old records/bytes
проверяются и сохраняются. Semantic correction — новая запись/новый subject,
а не редактирование старого approval/гранта. UUID+hash, не дата/latest, связывают записи.

## 5. Конфликты, отрицательные решения и состояние

1. У каждого перехода два необходимых условия: действительное exact permission
   и подтверждённая применимая readiness/no-known-blocks. Ни одно не выводится
   из другого; отсутствие запрета не есть согласие.
2. Entity restrict/revoke проверяются старым entity ledger для точных subject/
   tools/scope; permission deny/revoke — своим полным объявленным stream.
3. Permission revoke ссылается на exact grant UUID+hash; действие — запрет
   будущих переходов по нему. Исторически выполненный факт не удаляется.
4. Deny в применимой области имеет приоритет над положительным grant; независимые
   запреты накапливаются. Новый grant/дата не снимают deny. Conflicting identity,
   duplicate IDs с разными bytes, dangling target и unknown kind → stop.
5. Первый профиль не поддерживает «поднять любой запрет» или исправить grant
   свободным текстом. Entity lift не является permission regrant; permission
   revoke не отменяется задним числом. Если нужен controlled reauthorization
   после deny, его точный процесс проектируется явно, не latest-wins.
6. Permission check — не atomic action. Для actuation R5 нужен protected current
   head/generation, recheck и exclusive single-use claim непосредственно у записи.
   Pure bytes evaluator подтверждает только предъявленный context; не должен
   обещать globally freshest ledger, rollback resistance или atomic export.
7. Повтор старого view не доказывает current permission. Если обязательное текущее
   состояние/authority/claim не установлены, action блокируется. Доверенная
   current-head политика не может браться из самого недоверенного old snapshot.
8. Частичный export/failure сохраняется; success receipt/performed не фабрикуются.
   Автоматическое удаление/откат/публикация/activation не добавляются.

## 6. Результаты проверки: независимые уровни

Контракт будущего результата должен различать:

- document/schema/reference validity;
- authority_valid для exact decision в конкретном trust context;
- readiness verified/not_checked/blocked;
- scoped permission eligibility **только для exact action/subject/context**;
- execution performed=false до фактического actuator/проверенного receipt;
- activation_allowed=false, overall_admission=not_evaluated.

Positive authority test не является positive compatible-release test. Synthetic
complete subject/внешний readiness stub допустимы для unit semantics только с
явной маркировкой; они не закрывают actual coverage/R6. Проверки положительного
пути должны отдельно показывать, какое реальное условие исполнено и какое
смоделировано. Текущий actual incomplete candidate остаётся blocked даже при
достоверном явном owner intent. Обещать готовый positive end-to-end выпуск сейчас нельзя.

## 7. Предварительная acceptance matrix до реализации

| ID | Сценарий | Ожидаемый результат |
|---|---|---|
| P01 | Exact trusted release intent / закрытый subject | authority_valid в заданном context; readiness проверяется отдельно |
| P02 | Такая же decision только с actor_role=owner, без external authority | blocked/unsupported, не grant |
| P03 | Pin вычислен из source и им же создана trust allowlist | Не допустимый bootstrap; без независимого trust не выполнять |
| P04 | Один byte/size/subject/selected revision изменён | Reference/binding failure |
| P05 | Нет release grant, есть только proposal/approve_revision | Нет release permission |
| P06 | Release grant есть, export grant нет | Экспорт запрещён |
| P07 | Exact export decision и release decision совпадают по subject | Scope/authority допустимы, нужны readiness/current state/claim |
| P08 | Другой parent subject/allowlist/destination/procedure | Export blocked |
| P09 | Incomplete actual ENT13, даже с trusted intent | Compatible release blocked |
| P10 | Naked ready=true / report без требуемого trust/evidence | Blocked; coherent falsification не обещается обнаружить pure replay |
| P11 | Entity scope block / permission deny | Затронутый переход blocked |
| P12 | Exact grant revoked / новая дата или иной grant рядом | Revoked grant не возрождается, deny не исчезает |
| P13 | Два независимых запрета, устранён только один | Другой продолжает блокировать |
| P14 | ID collision/dangling revoke/unknown event/negative пропущен относительно внешнего known-set pin | Fail closed, не фильтровать; unseen global events не обнаруживаются |
| P15 | Новый unrelated registry record, old subject неизменен | Никакой автоматической смены subject/полномочия |
| P16 | Изменились pinned subject records/coverage bytes | Новая проверка/decision, старую не переписать |
| P17 | Old view предъявлен как current | Pure consistency не freshness; action без protected current context blocked |
| P18 | Повтор export UUID/claim / write failure | Single-use claim требует stateful механизма; partial ≠ performed |
| P19 | Новая среда/actor без bootstrap / просьба activation | Authority не наследуется; activation запрещена |
| P20 | Legacy ENT7/14/18 и старые116refs | Immutable bytes/закрытые старые scopes сохраняются; новых events в old ledger нет |

Это ожидаемые решения, **не выполненные tests**. До кода уточнить API/closed fields,
limits/dependency closure и уровень каждого доказательства, зафиксировать baseline.
После реализации: own positive/negative methods, integration/фактический blocked
actual candidate, full suite, old116refs/records, private/secret checks, conditional
implementation assessment. Реальный release/export остаётся отдельным решением.

## 8. Ближайшая развилка и влияние

Рекомендуется A для bounded local profile, не универсальная криптографическая
аутентификация. B нужен, если владелец требует проверяемое происхождение через
недоверенную границу переноса; его нельзя обещать за счёт одного hash. Ключи/
секреты не запрашиваются в чате и не добавляются в Git ни при одном выборе.

До выбора не создавать normative r2, новый trust store или реальные разрешения.
Не менять ENT13 coverage/readiness, старые consumers/candidates/активные связки.
R5/R6 должны интегрировать current state/readiness/actuation, R7/R8 — отдельную
среду/activation. Условия этого проекта не выдают допуска к этим блокам.

## 9. Проверки этого design checkpoint

Прочитаны относящиеся тексты и код, P01–P20 проверены на полноту/уникальность
идентификаторов, но не исполнялись как positive semantics tests. test_repo299/0,
test_rules885/0, test_navigation68/0; repo-validate38/0warnings/0errors;
manifest/self-hash/diff checks PASS. Все116normative/approval refs/bytes и registry
побайтово совпадают с b0a5129. Public223md/86README/37research/41modules,
529relative links/0broken. Полный41module suite на этом documentation-only
checkpoint не перезапускался; последний полный PASS — R3, не positive R4.
Реальные grants/trust store/crypto keys/новые нормативные версии не создавались.


## 10. Выбран A, выполнен ограниченный I1

[Реализация37](37-agent-system-local-permission-implementation.md): выбран
owner-controlled local authority, ENT14r2. Positive intent recognition/deny/revoke
и native incomplete guard реализованы,44own methods/42module prequalification
PASS. Conditional summary registration не является реальным owner grant.
Все action flags/performed остаются false; effective positive transitions не
реализованы. P15 cross-view generalization, P18 stateful claims, источник/trusted
importer/current-head и readiness/actuator integration не объявляются готовыми.
R4 целиком не закрыт. Реальный неполный ENT13r1 не выпущен/не экспортирован.


## 11. I2a — local state, не одноразовая actual action

[Отчёт38](38-agent-system-local-authority-state.md): ENT14r3, private source
journal/cumulative generations/externally pinned head/cooperative lock/check-once.
Сохраняется смысл typed operator attestation, не authentication/NLP source proof.
Повтор request UUID блокируется; новый UUID может ещё проверить тот же grant,
actual grant/export_id не расходуется. Это не выполненный P18 actuation claim.
Empty-authority actual demo0grants/1отказ/reopen PASS; R4 целиком не закрыт.
