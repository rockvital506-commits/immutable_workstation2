# ENT19r1 — declared inactive binding planner/history

Full six-file profile: binding.py/schema/procedure/prompt/usage/verify. Exact
ENT12r2+ENT18r1 dependencies, registry status/approval/bytes. No duplicate core.
Input fields are declared facts/evidence, not measured capabilities or semantics.

assess_binding(request_bytes,expected_request,documents,expected_existing_context,
acknowledge_inactive_only=True) reads only supplied bytes plus protected installed
tools. documents exact SHA→bytes map: environment/composition/adapter declarations/
non-null observation evidence, no extras. source scripts never run. Composition
must explicitly contain exact installed ENT19 component. Existing-context pin is
supplied separately; equal bytes are not proof of freshness/owner identity.

Returns request/assessment/documents (private data, not autoexport). Status
is declared_conditions_satisfied or blocked_declared_requirements, never ready.
Host unknown/unavailable stays unresolved. Adapter provides binding.* only; all
prerequisites must resolve, cycles don't self-bootstrap, conflicts/duplicates
are visible. No formal proof of preserving rule meaning. Request requirements
are deployment requirements, **not a replacement/relaxation of mandatory core**.

save_binding(result,predecessor=None,trust_private_namespace=True) recomputes the
assessment, preserves original input bytes privately using ENT18 EvidenceStore,
local/operator-runs/UUID. New immutable binding_id matches evidence UUID. A
successor is a new record linked by predecessor run/index; no current/active
pointer, no overwrite, inactive forks permitted. Changed environment bytes in a
family require advancing logical revision. Need new independent high-water for
rollback resistance: old coherent chain+old pin can pass. No global completeness.

inspect_history(receipt) checks structural CAS/pins/history, not execution truth.
activation_proposal(receipt,expected_existing_context) returns missing gates only,
never consumes grant or modifies host/config/context. Release/export authority
cannot be reused for activation. Actual permission/actuator/result path remains
unimplemented, all flags false even with a satisfied declared assessment.

Limits:16MiB/doc,64MiB input packet,1000documents/128capabilities/adapters/requirements,
32lineage nodes/128MiB aggregate; inherited ENT18 CAS128MiB/20064files per node.
Not CPU/RAM quotas, atomic global history or crash durability proof. Private
0700/0600/exclusive/readback/binding guards reused, failures retain partial and
return no success receipt, no repair/delete/retry/adoption. Trusted installed
interpreter/namespace protected from inputs, hostile same-uid/root out of scope.
Inspection of older nodes is consistency/history, not current facts or an active
context. Pinned observation text is not authentication or actual execution.

R7 environment not yet selected. Only synthetic declared demo/physical temp tests
here. This is useful B2 planning/history and B4 proposal scaffolding, **not full
G05 adaptation capability/G07 activation manager/R6 admission**. Next qualification
must implement/apply actual observation/adapter semantics/checks/authority/actuator
interfaces. No packages beyond existing isolated locked jsonschema/base.

Documented declared demo (approved isolated interpreter path — local example):

```sh
/home/user/.venv/immutable-agent-system/bin/python agent_system/adapters/ent-0019/r0001/binding.py --demo-inactive
```

Builds new R5 composition explicitly selecting ENT19, persists R5 metadata and two
inactive demo lineage nodes (declared satisfied → changed survey unknown/blocked).
No actual host survey/selected new environment/activation. Prints safe receipts,
counts/status/false flags, not raw observation/context. Without flag exit2 before
namespace IO. API run_declared_demo(acknowledge_demo_only=True) identical scope.

Every retained assessment is recomputed by protected declared resolver at history
inspection, with its original inputs/context (not today's environment). A coherent
CAS rewrite of a result alone is rejected. This computational replay still does
not authenticate input observations/semantics, and is not activation/execution
replay. Disposable tests may adversarially rewrite their own temp fixtures only.
