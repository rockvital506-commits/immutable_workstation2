# ENT12r2 — inactive transfer composition API

Full revision profile: prepare.py/preparation.schema.json/procedure.md/prompt.md/
usage.md/verify.py. Exact dependencies: ENT12r1+ENT11r2+ENT14r3+ENT18r1. Registry
устанавливает status/approval/scopes/bytes. Supersedes не переключает r1 consumers.
Источник: owner B/P1ред2, conditional implementation delegation и R5 continuation.

prepare_inactive(root, request_bytes, expected_request, plan_bytes, expected_plan,
acknowledge_inactive_only=True) возвращает status/manifest_bytes (либоNone),
execution_report_bytes/documents. root — read-only source, не destination.
make_packet(registry_bytes, decisions) лишь строит declared caller-supplied plan,
не approval/authority/verifier. Полный known ledger передавать без фильтрации.
installed_packet(trust_installed_namespace=True) допускается только для заранее
protected installation; bootstrap source-derived pins не owner authentication.
prepare_inactive никогда не получает caller readiness/result callbacks.

Native capture через ENT9r2 используется один раз. Прочитанные payloads остаются
внутри операции; descriptor строится из того же capture. Возвращаются metadata/
plan/request/check reports/descriptor, **не raw normative payloads**. Никакого
physical kit/archive/export destination эта API не создаёт. Observed artifact
allowlist — exact declared closure, но не разрешённый action/export allowlist.
Пути только system prefixes; local/private project/build/history/Git не collect.
Это структурная граница, не secret/semantic-content detector для текстов, которые
сам owner поместил в system namespace. Цель подготовки тоже может быть private.

Seed ENT13r112versions/34artifacts native checked отдельно. Historical16capability/
9condition rows копируются без changes, checks defined_only не повышаются;
composition_coverage not_evaluated и все gap_to_check open_not_discharged. Не
объявлять старый seed current coverage нового composition. Runtime obligations
отдельны: R4 claim/R6 readiness/exporter/new environment/activation/high-water/
actual owner grants/behavior qualification. Prompt/procedure фиксированы до capture.

persist_preparation(result,trust_private_namespace=True) — ENT18 private CAS,
local/operator-runs/UUID,0700dirs/0600files, exclusive writes/readback/bindings.
Сохранение metadata не новое permission source/approval. verify_evidence(run_id,
index_pin) из ENT18 проверяет физические bytes/refs/inventory, не re-execution/
source authentication/semantic replay. Evidence receipts хранить отдельно; чужой
coherent result может быть consistency-valid без истинности происхождения.
При failed write partial остаётся, receipt success не выдаётся; no cleanup/repair/
auto retry/adoption. Исходные normative bytes не копируются в evidence store.

Documented native practice (только protected installed Linux x86-64):

```sh
/home/user/.venv/immutable-agent-system/bin/python agent_system/transfer/ent-0012/r0002/prepare.py --trust-installed-namespace
```

Path interpreter — локальный пример прежнего isolated hash-locked dependencies,
не portable requirement абсолютного пути. Flag отсутствует → exit2 до source/
state writes. Команда сохраняет private metadata и печатает лишь receipt/pins/
closed false flags. Не запускает exporter/permission import/activation manager.

Limits inherited:16MiB/document/64MiB source packet/10000files; full catalog/known
ledger/closure graph limits ENT6r3, metadata CAS128MiB/20064files ENT18. Предельные
values — bounds, не CPU/RAM quotas/atomic snapshot/crash durability guarantees.
Новый record не скрывает transient/unseen events. Installed code/interpreter/
namespace protected от foreign writable source; hostile same-uid/root вне обещаний.
No new dependencies. Reuse graph/reader/CAS — меньше duplicate policy/IO, но
full capture/replay costs и manual failure review остаются. Не benchmark ускорения.
Release/export/activation/compatible_release/performed/current_binding_changed
всегда false; preparation status не overall admission.
