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
