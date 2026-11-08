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
