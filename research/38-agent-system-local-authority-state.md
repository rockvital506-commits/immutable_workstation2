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
