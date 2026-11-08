# M1: проект сквозного операторского trial и byte-handoff

> §§1–10 сохраняют проектный срез до реализации. Результат I1 — §11, результат I2 — §12; I3a — §13; I3b — §14; текущий I3c — §15.

## 1. Статус, основание и результат этого этапа

Дата: 2026-11-08. Baseline commit `93bcf1d`; исходное задание — исследование 30 §2,
аудит/очередь — [исследование 31](31-agent-system-core-audit.md), прежде всего §8.
Это **проект**, не реализованный coordinator, новая normative revision или выпуск.
Нормативные тексты/registry/approvals не меняются. Все proposed API/поля ниже
подлежат реализации и проверкам; наличие acceptance table не считается PASS.

Выбран bounded вариант B аудита: тонкий coordinator и минимальные revisions
двух интерфейсов. Без нового framework/библиотек, monkeypatch существующих модулей,
повторного source acquisition ради получения потерянных bytes и изменения r0001
in place. Само подтверждение разработки не разрешает export/activation.

**Результат M1 после будущей реализации:** один операторский запуск с проверяемой
передачей bytes и связанным evidence, понятным итогом и честным числом acquisition.
Payload пока исторический incomplete ENT13 r0001 (12/34). Это не утверждение,
что он содержит новый coordinator или весь современный tooling.

## 2. Роли и точка применения

- **Владелец:** полномочие задачи/ключевые ветвления, допустимые данные, основание
  доверия, отдельные release/export/activation решения в будущих этапах.
- **Оператор:** доверенная установка, внешние input pins, выбор source aliases и
  отдельно переданные реальные roots; запуск и чтение отчёта. Не вводит имя tool
  из source и не выдаёт пересчитанный unknown hash за approval.
- **Агент в trial:** получает явно предоставленное описание задачи/профиля/ссылок
  на правила и отчёт. Обозначает ограничения, объясняет отказ/следующий шаг;
  использует доступные разрешённые средства, не заявляет неподтверждённую активацию.
- **Coordinator:** фиксированный installed code выполняет закрытую цепочку и
  связывает bytes/refs. Не принимает произвольные callbacks, child reports или
  Python paths со входа как доказательство выполненного шага.

Способ предъявления правил на первом этапе — операторский user-controlled ввод/
ссылки в доступном контексте, не скрытая настройка платформы. Агент не считается
прочитавшим файлы только из-за их наличия. Если инструменты/файлы недоступны,
это фиксируется, а не имитируется исполнение. Реальная новая agent platform/
перманентная binding не выбраны. Проверка поведения W01–W09 остаётся отдельным R3;
M1 обеспечивает основание/trace, не NLP evaluator и не гарантированное соблюдение.

## 3. Границы первого профиля

Поддерживаемый lab profile: Linux x86-64, существующий file reader/byte checker,
private namespace установленной agent_system, отдельные source roots с внешними
ожиданиями. Без Windows/junction/foreign-root import/нового target adapter.
Installation доверенная и не concurrently writable противником. Файловые проверки
не защищают от hostile same uid/root, check→runpy TOCTOU не исчезает.

Source A — один явно pinned baseline; source B опционален и означает другой
declared-known snapshot, не доказанный current мир. Roots передаются вне portable
JSON, aliases A/B не содержат credentials/absolute paths. Coordinator source
не редактирует, новые decisions не регистрирует и не создаёт свежий view сам.

Payload — ENT13 r0001/roots ENT12r1+ENT10r1, immutable 12 revisions/34 artifacts.
Candidate descriptor — envelope, не 35-й payload artifact. Его четыре normative
файла должны быть проверены как source entity, не только получены по чужому pin.
Tool installation — отдельный точный profile, включает старые transitive версии
и новые proposed ENT9r2/ENT16r2/coordinator; не отождествляется с payload.

Первый M1 работает с тем же каталогом, содержащим точные версии этого tool profile
и descriptor. Source validation selection — exact profile roots, включая будущий
coordinator subject; artifacts — ровно его installed composition/depends_on closure,
не весь repo и не произвольные extra files. Такой строгий lab profile не обещает
обслуживать старый source catalog без новых tools: это отдельный будущий профиль.

Старые r1 нужны существующим pinned зависимостям и остаются установленными.
Версии сосуществуют по разным paths/subject; supersedes не перенаправляет старые
pins и не отзывает старое согласование. Если позже переносимому payload приписываются
новые реализации, нужна новая candidate revision/coverage, не правка ENT13 r1.

## 4. Внешний session input и derived документы

Предлагаемый entry API (ещё не реализован):

```python
run_operator_trial(source_a_root, session_bytes, expected_session, documents,
                   *, source_b_root=None)
```

D01. Session — strict UTF-8/LF JSON closed profile с UUID, mode=local_trial,
explicit task/purpose и ограниченными критериями, exact candidate ref/subject,
validation plan A ref, optional validation plan B ref и optional literal query
context. Expected_session внешний sha256/native size. JSON documents plans
передаются через documents={sha256: bytes}: ровно referenced plan A и optional B,
без extra entries и без загружаемых URI/путей. Каждый document pin проверяется
до разбора; mappings копируются, bytes не изменяются.
Tool/profile/procedure/prompt версии закреплены отдельно, не latest.

D02. Plan A/B сохраняют ENT8r1 format, внешний pin каждого raw plan и полный
объявленный known ledger. Profile preflight проверяет exact selection/artifact
set/metadata, CID, limits и context validate/agent_system.operator_trial.
Extra arbitrary files/частная local history не попадают в plan artifacts.
Известные ограничения selected tools/descriptor проверяются вместе с payload;
только hash-installed code без относящихся известных decisions недостаточен.

D03. Source B/plan B/query либо объявлены согласованно, либо отсутствуют.
Отсутствие B не означает «A считается current» и не даёт query PASS. Некорректная
пара B/root/plan или wildcard query отвергается до source чтения.

D04. Manifest hash нового trial заранее неизвестен из-за нового UUID. Поэтому
comparison plan ENT17 строится как **derived document** после успешных stage/read,
из session context + captured B refs + verified manifest pin. Его pin вычисляется
внутри этой прослеживаемой цепочки, не выдаётся за отдельную подпись владельца.
Нельзя взять непроверенный filesystem manifest и самоподтвердить его hash.

Profile/session конкретная schema/procedure/prompt будут версиями будущего
coordinator. Этот отчёт не является скрытой v1 schema и не создаёт runtime files.

## 5. Минимальные изменения интерфейсов

### 5.1. ENT-0009 r0002: один worker, две поверхности

D05. Добавить `capture_plan(root, plan_bytes, expected_plan)`. Предлагаемый результат:

```python
{
    'report_bytes': bytes,
    'documents': {sha256: bytes},
    'capture': None  # or {'registry': bytes, 'artifacts': {path: bytes},
                     #     'decisions': {path: bytes}}
}
```

Общий private worker в r2 выполняет ровно один `read_set`, _acquired/binding/_bound
и формирует report из **этих же** captured maps. Старый public `execute_plan`
в r2 проецирует worker result в report_bytes/documents; capture_plan — полная
поверхность. Не делать capture_plan через вызов execute_plan и второе read_set;
не вызывать r1 через runtime patch/подмену callback, чтобы перехватить bytes.
R1 остаётся неизменным, regression сравнивает контракты/status/отказы, не UUID.

D06. Capture доступен **только** при report.status=passed_known_inputs и успешной
внутренней проверке всех refs/контекста/selection. При failed/blocked/unsupported —
capture=None, никакие partial maps не становятся пригодными для следующего шага.
Это намеренно не предоставляет полный raw bundle неуспешного binding: offline
semantic replay такого failed run без полного payload не обещается.

D07. Перед handoff coordinator сверяет raw plan ref, schema/envelope, evidence
refs и document hashes, exact maps/metadata, registry CID/closure/context. Затем
строит payload subset только по validated candidate components. Не достаточно
общего run_id или переданного извне dict с похожими полями.

ENT8r1 schema/reader5r3/checker6r3 можно сохранить, если их семантика не меняется.
Новый capture находится **вне** legacy report schema. ENT10r1 может проверить
прежнюю semantic report/bundle форму с полным сохранённым payload, но не новый
capture interface, producer r2 authenticity или внешнее исполнение. Нельзя
расширять это обещание без отдельной проверки. Profile string описывает прежний
reader/checker boundary; producer revision фиксируется отдельно.

### 5.2. ENT-0016 r0002: capture после полного read-only контроля

D08. Добавить `capture_trial(run_id, expected_manifest)`:

```python
{
    'result': dict,  # metadata, no raw bytes here
    'capture': None  # or {'manifest_bytes': bytes, 'objects': {sha256: bytes}}
}
```

Общий worker r2 содержит прежний secure read/capture/replay/readback/binding
pipeline. read_trial возвращает metadata projection; capture_trial — metadata+
первые captured bytes только после всех проверок. Не вызывать сначала r1
read_trial, затем читать paths заново. Повторные guard readbacks внутри pipeline
не объявляются новыми input snapshots и не подменяют первые captured inputs.
Producer profile меняется на r2, on-disk ENT15 manifest profile остаётся прежним.

D09. Любой поздний readback/binding/permission/scope/inventory FAIL даёт capture=None.
Reader не пишет/chmod/удаляет и не выполняет input code. Raw maps существуют
только внутри trusted процесса; не сериализуются в stdout/human report.
Существующий ENT17r1 по-прежнему загружает свои pinned r1 helpers, но получает
проверенные ENT15-format bytes. Не перенаправлять его pins на r2 автоматически.

### 5.3. Coordinator как будущий отдельный protocol

D10. Предполагаемая новая сущность coordinator — ENT18r1, **ещё не зарегистрирована**.
Точные deps: новые ENT9r2/ENT16r2 и существующие ENT13r1/ENT15r1/ENT17r1; остальные
приходят по closure. Source profile roots/composition фиксируются после реализации,
не выдумываются сейчас hashes/approval IDs/counts. Свои code/procedure/prompt
версионируются/одобряются по обычному процессу.

Не включать registry hash в собственный normative artifact, чтобы не создать
self-hash cycle. Session/планы создаются отдельно после регистрации, фиксируют
каждый run index/known ledger. Code не может bootstrap доверие к собственному
approval: оно приходит от оператора/доверенной установки.

## 6. Состояния и порядок

| Состояние | Реальное действие/условие | При отказе |
|---|---|---|
| preflight | D01–D04, trusted profile, pins/schema, tools+own component refs/context | Нет source I/O/output claim, failed/unsupported |
| evidence_claimed | Новый private operator run UUID, фиксированные служебные paths | Не читать source при невозможности завести обязательное evidence |
| source_a_validated | ENT9r2 capture_plan: один root capability/read_set для A | capture=None; не stage |
| candidate_bound | Exact descriptor approval/composition, ENT13 candidate/payload и refs совпадают с A | Не создавать trial |
| trial_staged | ENT15 stage_trial над subset **A capture**, его known stage scope | Failed_partial сохраняется, не read как успешный trial |
| trial_read | ENT16r2 capture_trial по UUID/manifest pin из свежего successful stage receipt | Любой late failure закрывает capture, не compare |
| handoff_bound | Manifest ref/run/candidate/registry/ledger/payload совпадают с receipt и A; objects exact | Не скрывать swapped packet/evidence общей датой/run ID |
| source_b_validated | Только если запрошен B: отдельный capture_plan, собственный root capability | Не fallback на A как current |
| comparison_checked | Derived plan ENT17, objects **из reader capture**, current bytes **из B capture** | Block/failed/unsupported сохраняется в итог; не permission |
| evidence_sealed | Exact inventory/doc refs, итоговый журнал и human summary записаны и readback проверен | evidence_write_failed, не успешное закрытие |

D11. В успешном поддержанном run без B требуется **один** source acquisition;
с B — **два**, каждый под своим
одним root capability. Чтение trial — отдельное controlled I/O. Это не одна
атомарная транзакция двух roots и не исчезновение всех промежуточных изменений.
Корни A/B могут быть одинаковыми, но snapshots/refs остаются раздельными.
На отказе фиксировать фактические attempts/successful captures/not_run; не
подставлять число 2 только из-за наличия B в session и не выдавать попытку за успех.

D12. Default terminal statuses: trial_checked_no_query и
trial_checked_with_known_query_no_admission. Опциональный query not_requested
не переименовывается в passed. Остальные terminal states — failed, unsupported,
blocked_known_scope, failed_partial или evidence_write_failed; downstream шаги
not_run с причиной, не passed по умолчанию. Если B/query заблокирован после stage,
локальный trial остаётся, но общий requested run не становится успешным.

D13. Во всех состояниях overall_admission/current_permissions=not_evaluated,
release/export/activation/transition_allowed=false. Staged/performed относится
только к конкретному local шагу; нельзя сбросить отрицательный child результат
из-за успеха соседнего. Source/caller/code execution authentication, freshness,
полнота ledger, поведение/target environment остаются явно непроверенными.

## 7. Evidence и перенос данных

D14. Coordinator пишет только fixed installed local/operator-runs/new UUID,
не source/trial inventory. Private directories 700/files 600, directory fds/
NOFOLLOW/exclusive claims, no overwrite/resume/автоудаление/автооткат. Базовые
helpers ENT15 можно переиспользовать с их same-uid/mount/atomicity ограничениями;
новый persistence path и отказ на disk full должны получить собственные тесты.

D15. В evidence — raw session/plans/procedure+prompt refs, reports/documents,
receipts/derived plan, ordered step records и общий итог с ref каждого child.
Full successful source validation bundle сохраняется в private digest store
по точному объявленному allowlist, чтобы replay не зависел от будущего source.
Это может включать tool artifacts вне trial payload; это **evidence**, не export
и не расширение payload. Дедупликация bytes, exact inventory, no arbitrary paths.
Планы могут содержать registry/known decisions; оператор отвечает за допустимость
данных, evidence не публикуется/не попадает в Git автоматически.

D16. Ошибочный capture не сохраняется как валидный bundle. Для failed binding
сохраняются доступные report/docs/refs и предел отсутствующих raw bytes, без
ложного обещания полной offline проверки. Частичный stage/evidence остаётся
для диагностики. Каждый step документ пишется один раз, final index не
перезаписывает старый. Реальные child run IDs не подменяются UUID coordinator.

D17. Human report содержит цель как profile label/task ref, фактический уровень, шаги/статусы, source
acquisition count, trial/evidence relative refs, что проверено/не проверено,
blocker/code и следующий шаг. Raw captured maps, absolute roots/traceback и
произвольный task/decision text не печатаются автоматически. Свободный summary
для публикации требует проверки оператором; универсальный secret detector не
заявляется. Общая структурная связность не
становится cryptographic proof внешнего исполнения.

D18. Повторное чтение успешного evidence в отдельном readonly режиме должно
проверять pinned final index/doc refs и доступный полный validation bundle;
partial run остаётся partial. Исторический replay не опрашивает live ledger
и не подтверждает сегодняшние права. Новая known проверка требует нового B plan/
run, не редактирования sealed старого журнала.

### 7.1. Resource envelope первого профиля

Исходные per-file/per-view caps прежних компонентов не расширяются. Session и
каждый raw plan до 16 MiB, максимум два initial plan documents; unknown/extra
input documents запрещены. A и B acquisition каждый до 64 MiB/10000 entries,
trial capture — прежний лимит ENT16; это разные allocations в памяти.

Для coordinator предлагается явный дополнительный предел **128 MiB всех
сохраняемых evidence bytes вместе** (unique objects + служебные документы),
отдельный документ до 16 MiB, до 20064 files. Проверять budget перед каждой
записью; превышение — отказ/partial с сохранением причины, не обрезание payload.
Это верхний предел профиля, не обещание, что любые одновременные максимумы A/B
поместятся вместе с reports. Disk free не доказательство будущего успеха записи.
CPU/RAM процесса глобально не квотируются: immutable raw maps/JSON structures
и повторный readback требуют памяти; privacy не оправдывает неограниченный buffer.
Численные caps включить в профиль/schema/tests при I3, не менять silently.

## 8. Acceptance matrix — план тестов, не результаты

| ID | Проверка будущей реализации | Ожидание |
|---|---|---|
| T01 | ENT9 capture positive | Report/doc refs и returned bytes совпадают с одним acquisition |
| T02 | Count read_set вызовов | Один для A, отдельный один для B; нет скрытого повторного чтения |
| T03 | Source меняется после capture A | Stage использует A bytes, не новый pathname read |
| T04 | Wrong external session/plan pin | Stop до source I/O/output claim |
| T05 | Missing/extra profile artifacts или wrong selection | Preflight stop, no arbitrary file capture |
| T06 | Wrong descriptor/installed component metadata | Не stage под другим candidate/tool profile |
| T07 | Scoped block/unknown event на A | capture=None, downstream not_run |
| T08 | Binding failed при успешном acquisition | Нельзя использовать partial captured maps; честный предел replay |
| T09 | Swapped report/documents/capture A | Handoff mismatch, не успех по совпадению UUID |
| T10 | Wrong plan context E12 | Не обходить guard старого prepare_run и не выдать transfer receipt |
| T11 | Stage partial/write/fsync failure | Остаток сохранён, общий run не passed |
| T12 | Reader captured bytes vs stage/A refs | Exact match, descriptor остаётся envelope |
| T13 | Late reader corruption/binding/permissions fail | capture=None, no compare |
| T14 | Object/logical-path traversal, symlink/FIFO/hardlink | Прежние физические отказы, без unsafe fallback |
| T15 | Returned maps mutable alias | Копии mappings, bytes immutable; извне packet не принимается как child proof |
| T16 | B отсутствует | query not_requested, A не объявлен current |
| T17 | B объявлен без root/plan/context | Preflight отказ |
| T18 | B capture fail или wrong refs | Не fallback A, общий run failed/blocked |
| T19 | New known revoke | Archive не меняется, query blocked, permission false |
| T20 | Exact lift/второй оставшийся block | Прежняя ENT7 семантика, не latest/date |
| T21 | Archived negative пропущен в B | Отказ ENT17 retention |
| T22 | Старый B предъявлен как новый | Может быть consistent; freshness not_checked, не grant |
| T23 | Derived comparison plan | Только session context/verified refs, не произвольный ввод из trial |
| T24 | Evidence collision/unsafe directory/disk full | No overwrite/chmod чужого; failure/partial, не sealed success |
| T25 | Extra/missing/tampered evidence document | Readonly replay отвергает mismatch |
| T26 | Source недоступен после success | Replay использует private saved bundle, без source reread |
| T27 | Повтор той же task/UUID | Новый run/отказ collision, не resume с перезаписью |
| T28 | Старые версии/API/общий regression suite | R1 bytes/поведение сохранены; изменённый producer r2 обозначен отдельно |
| T29 | Печать результата | Нет raw bytes/absolute roots/секретов; actual counts и limits видимы |
| T30 | Реальный bounded lab опыт | One operator entry + evidence replay, без `/tmp` recipes как обязательного интерфейса |

Unit/fault fixtures, physical filesystem checks, интеграционный опыт и human
оценка отделяются. Эту таблицу нельзя засчитать как 30 исполненных тестов.

## 9. Порядок реализации и stop boundaries

I1. ENT9r2 capture worker/API + собственные/общие regression проверки; регистрация
только после PASS/подтверждения результата. I2. ENT16r2 worker/capture с теми же
условиями. I3. Coordinator protocol/profile/schema/procedure/versioned prompt и
persistence, с точными pins обеих новых revisions и прежних deps. I4. Интеграция
T01–T29, один ограниченный практический run/replay T30 и корректировка найденного.
Собственные проверки не заменяют полный repo suite или относящуюся практику.

Рекомендация B сохраняет общий стек/минимизирует новые abstraction layers; цена —
новые revisions, explicit byte-map поверхность, private evidence storage и
дополнительные negative tests. Альтернативы manual recipes не закрывают M1,
полный framework увеличивает риск/зависимости без доказанной необходимости.
Benchmark преимущества не выполнен; лимиты памяти/диска требуют проверки на
реализации, input byte caps не равны глобальной resource quota.

Если при реализации потребуются новые сторонние зависимости, сокращение core,
другая agent platform или опасный переход — предъявить key branch владельцу.
Сейчас I1 не требует такого выбора: один approved Linux technical profile,
stdlib+прежний jsonschema stack, никакого export/activation. При несовместимости
legacy report semantics остановить этот участок и версионировать относящийся
контракт, а не молча сохранить старый profile/валидатор.

## 10. Проверка проекта и выход к следующему действию

На этом этапе проверяются source signatures/return contracts, immutable baseline,
полнота D01–D18/T01–T30/I1–I4 и согласованность с аудитом/ядром. Это review проекта,
не исполнение новых API и не прохождение acceptance matrix. Источник правил —
существующие normative версии; report не второй core/registry/activation profile.

Следующее действие — **I1: реализовать ENT9r2 с capture_plan и одним worker**.
ENT16r2/coordinator пока не существуют; R2/M1 целиком не закрыт. Новый payload/
compatible release/positive grants/R3 поведение/первая новая среда не предъявлены.


## 11. Реализация I1 после подтверждения продолжения

ENT9r2 реализован и зарегистрирован; полный текст/API/ограничения —
[usage](../agent_system/validation/ent-0009/r0002/usage.md).
Общий _worker, metadata projection и capture_plan не вызывают r1 и не читают
source повторно. Capture maps выдаются только после binding/_bound и final
Schema/serialization; late errors не возвращают пригодные partial maps.
Legacy report profile/схемы сохранены, producer r2 фиксируется отдельно.

74 own tests: 30 metadata сценариев, их 30 capture mirror и 14 handoff случаев.
Есть r1 semantic parity кроме run_id, single read_set, независимость dict,
source change после binding, final failure, unsupported/no stale reuse и
successful offline ENT10 replay. Это не 74 различных сценария и не исполнение
всей T01–T30 coordinator matrix. R1 нормативные bytes не изменены.

Практика до регистрации: 17 revisions/51 artifacts/23 decisions, 75 captured
inputs; после регистрации с producer в selection: 18 revisions/54 artifacts/
24 decisions, 79 captured inputs, 800516 bytes. В обоих случаях один наблюдённый
read_set, passed_known_inputs и consistent_recorded_bundle, admission не оценён.
Это собственный каталог в trusted checkout, не чужая новая среда/поведение агента.
Evidence/private run refs и checks — исследование 30 §52.

Новая depends_on ENT9r1 нужна только verifier для compatibility parity; worker
использует тот же ENT8r1/21-pin reader/checker closure. Старые pinned consumers
не перенаправляются, payload ENT13r1 остаётся 12/34. Следующий шаг — I2/ENT16r2,
затем I3 coordinator/I4 integration. M1/R2 и выпуск/экспорт/активация не закрыты.


## 12. Реализация I2 — guarded trial capture

ENT16r2 реализован/зарегистрирован; полный контракт —
[usage](../agent_system/staging/ent-0016/r0002/usage.md).
read_trial и capture_trial проецируют общий worker; raw manifest/objects выдаются
после поздних guard readbacks, bindings и закрытия FDs. Используются первые
captured bytes, не readback outputs. Failure/blocked/unsupported — capture=None.
Новый metadata profile r2; on-disk ENT15 profile/старые ENT17r1 pins неизменны.
Прямой depends_on ENT16r1 — только parity verifier, не вызов r1 из worker.

94 own tests: 41 metadata, их 41 capture mirror и 12 handoff, не 94 уникальных
сценария. Pre-registration regression — 36/36 PASS. Manual integration harness
выполнил ENT9r2 A → ENT15 stage → ENT16r2 capture → отдельный ENT9r2 B → ENT17r1.
До и после регистрации reader consistent_archived_trial, comparison
compared_known_views_no_admission. Две отдельные source acquisitions того же
явно declared registry; это не freshness proof и не A fallback as current.
Evidence/точные counts/решение — исследование 30 §53.

93 старых normative/approval файла сохранены, payload ENT13r1 всё ещё 12/34.
**I2 завершён; следующий шаг I3/coordinator**, затем I4/full integration cases.
Ручной harness не заменяет будущие session preflight/state machine/private
journal/resource-manager/handoff checks; полная T01–T30 matrix не исполнена.
M1/R2 целиком, R3–R8 и разрешения release/export/activation не закрыты.


## 13. I3a — реализованная основа, не завершённый coordinator

[Рабочий кандидат](../agent_system/operator/ent-0018/r0001/usage.md) содержит
session/schema validator и private evidence CAS. Это implementation draft вне
registry/approvals, не новая нормативная ENT18r1 и не общий run entry. Подэтап
выделен, чтобы проверить input/persistence boundary до соединения всех actions.

Closed session фиксирует purpose/criteria/task UUID, pins candidate/plans и
optional literal query/B pairing. Exact profile — только trusted внутренний
аргумент, не пользовательское поле; future installed own-profile bootstrap ещё
не реализован. Pinned dependency closure 19 revisions/57 artifacts, stdlib плюс
прежний isolated jsonschema. Source I/O и action pipeline validator не вызывает.

Evidence CAS реализует exclusive private claim/no overwrite/resume/delete,
16 MiB/document/128 MiB aggregate с final index/20064 files, dedup и poison на
отказе. Readonly checker проверяет exact inventory/refs/metadata/bindings, **не**
semantic journal/child replay или факт исполнения. Проверки/практика — исследование
30 §54. Это частичная реализация D01–D04/D14 и storage части D18, не полный PASS
этих требований или T01–T30. Registry/97 прежних refs не изменены.

Следующая часть I3 — trusted own-profile bootstrap, runner/state machine,
candidate/handoff binding, child journal, human report, procedure/versioned prompt
и semantic replay. Затем интеграция I4 и только после относящихся PASS — решение
о регистрации exact ENT18 состава по условному делегированию. I3/M1 не закрыты.


## 14. I3b — fail-closed runner candidate

run.py реализует entry и protected installed-profile bootstrap. В реальном
каталоге ENT18 по-прежнему отсутствует: public entry возвращает preflight error
COORDINATOR_NOT_REGISTERED до claim/source. Prospective approval для тестирования
есть только в disposable install/source trees, не является решением владельца.

Реализованы source packet+ENT10 semantic binding, exact installed revision records,
candidate subset, scoped tool checks перед stage/read/query, exact trial handoff,
optional B без fallback, derived plan, child IDs/private journal/CAS seal. Return
не содержит raw maps/absolute roots. Source counters разделены; exception/invalid
packet даёт acquisition_calls=None, не ложную точность. Unknown error не получает
успешный receipt; partial artifacts не удаляются. Подробности — usage и §55
основного обследования. Ни all-gates false, ни structural CAS не являются permission.

26 runner test methods дополняют 35 foundation методов. Real stage/query negative
события созданы только в fixtures. Не полная T01–T30 matrix и не T30 native public
success: реальный gate пока закономерно закрыт. I3c — semantic journal replay,
procedure/versioned prompt и human report; затем I4/относящаяся практика и только
после проверки exact состава — условная регистрация. I3/R2/M1 целиком не закрыты.


## 15. I3c — replay/procedure/prompt/human candidate

Добавлены pinned offline journal replay, versioned procedure/prompt и безопасный
renderer. Journal включает profile snapshot/protocol refs/session/human binding;
source bundles перепроверяются ENT10, candidate — ENT13, handoff/derived query —
ENT17 и точными links/counts. Full success replay без source/trial/live ledger;
failed journals остаются partial, а coherent copy не даёт execution authenticity.
Public structural CAS checker и новый semantic API различаются. Source/read/helper
коды из evidence не исполняются. Детали/границы — usage и исследование30 §56.

17 replay methods дополняют35foundation/26runner. Кандидат содержит11ownfiles,
prospective source closure20revisions/68artifacts; эти числа не описывают реальный
approved registry (по-прежнему17entities/25revisions). Никакой ENT18 approval или
новый compatible payload этим checkpoint не создан. Public gate остаётся закрыт.

Следующий I4: T01–T30 traceability/негативные и ресурсные проверки/ограниченная
практика/коррекция и оценка готовности conditional registration. Полного T30
реального зарегистрированного entry ещё нет. M1/R2, R3–R8 и release/export/
activation не закрыты реализацией replay. Старые97 normative/approval refs сохранены.


## 16. I4 — implementation acceptance и отдельная native verification

[Матрица T01–T30](33-agent-system-operator-trial-acceptance.md) различает уровни
physical/fault/reused lower semantics/prospective client/реальный registered CLI.
13ownfiles frozen; conditional summary approval после40/40prequalification.
Native lab с явным trusted-checkout acknowledgment с B и без B — PASS,2/1source
acquisitions, private CAS и отдельный full semantic replay. M1/R2 bounded область
закрыта; payload12/34 и no-admission gates не расширены. R3–R8 остаются отдельно.
Результат не execution authentication/current permissions/global completeness/
новая среда/activation. Старые97references и immutable revision records сохранены.
