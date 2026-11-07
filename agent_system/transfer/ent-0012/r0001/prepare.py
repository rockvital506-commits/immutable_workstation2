#!/usr/bin/env python3
"""Freeze declared transfer preparation, never export, release, activation or source IO."""
import hashlib
import json
from pathlib import Path
import runpy
import uuid

BASE = Path(__file__).resolve().parents[3]
PINS = {'validation/ent-0009/r0001/execute.py': {'sha256': '1a4340e4dfe4b01841702ffcb88a65caa0f8ccc05d6adce03c1e4b3d2e6ebdf9', 'size_bytes': 12955}, 'validation/ent-0009/r0001/verify.py': {'sha256': 'a082eeb938a62f4005d83f3664d027c403055c1f7851ff73a3a6517a09f41268', 'size_bytes': 11721}, 'validation/ent-0009/r0001/usage.md': {'sha256': '6c9ed888e4d5538a53521fa4406ce6df50e287718d2c5cc4545882432173425f', 'size_bytes': 11256}, 'protocols/ent-0011/r0001/work.md': {'sha256': '06923c52d5e7311556e8276cea473af71284f985476f970dced83d085a70cbb4', 'size_bytes': 22549}, 'protocols/ent-0011/r0001/scenarios.json': {'sha256': '441d2505e822cdbf37d534a17b4b89c32a54853ff4442d9e019104c0b3ea5f50', 'size_bytes': 12480}, 'protocols/ent-0011/r0001/verify.py': {'sha256': '3984ddb43a4ac7b45694608b891ac17e331bfc3fb8a624bc716bbd0ded834348', 'size_bytes': 6777}, 'protocols/ent-0012/r0001/governance.md': {'sha256': '2402346a739436871ba22b90306cf86c3836eb54f3ddb3801bbfa78398bbc0f9', 'size_bytes': 21236}, 'transfer/ent-0012/r0001/prompt.md': {'sha256': '8ce3983ed99058bfa1d1c559142fd884c60bb92b27331b58d2759e47b6e5866a', 'size_bytes': 4825}}
PROCEDURE = 'protocols/ent-0012/r0001/governance.md'
PROMPT = 'transfer/ent-0012/r0001/prompt.md'
COMPONENT = [PROCEDURE, PROMPT, 'transfer/ent-0012/r0001/prepare.py',
             'protocols/ent-0012/r0001/verify.py']


class PreparationBlocked(Exception):
    def __init__(self, code, unsupported=False):
        self.code, self.unsupported = code, unsupported
        super().__init__(code)


def _ref(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))


def prepare_run(plan_bytes, expected_plan):
    """Return immutable receipt bytes only; caller persists separately, without auto-export."""
    try:
        for path, expected in PINS.items():
            with (BASE/path).open('rb') as stream:
                raw = stream.read(expected['size_bytes']+1)
            if _ref(raw) != expected:
                raise PreparationBlocked('INSTALLED_PREPARATION_CHANGED', True)
        entry = runpy.run_path(str(BASE/'validation/ent-0009/r0001/execute.py'))
        try:
            parse, (validator, _), _, _, _ = entry['_load']()
            expected = dict(expected_plan) if type(expected_plan) is dict else expected_plan
            plan = entry['_plan'](plan_bytes, expected, parse, validator)
        except entry['PlanBlocked'] as error:
            raise PreparationBlocked(error.code, error.unsupported) from None
        if plan['context'] != dict(operation='export', area='agent_system.transfer'):
            raise PreparationBlocked('PREPARATION_CONTEXT_MISMATCH')
        subject = dict(catalog_id=plan['catalog_id'], entity_id='ENT-0012', revision='r0001')
        if subject not in plan['selection']:
            raise PreparationBlocked('PREPARATION_SELECTION_MISSING')
        artifacts = {a['path']: a for a in plan['artifacts']}
        component = []
        for path in COMPONENT:
            if path not in artifacts:
                raise PreparationBlocked('PREPARATION_INPUT_MISMATCH')
            expected = {k:artifacts[path][k] for k in ('sha256','size_bytes')}
            with (BASE/path).open('rb') as stream:
                installed = _ref(stream.read(expected['size_bytes']+1))
            if installed != expected or (path in PINS and installed != PINS[path]):
                raise PreparationBlocked('PREPARATION_INPUT_MISMATCH')
            component.append(dict(path=path, **installed))
        entries = [plan['registry'], *plan['artifacts'], *plan['decisions']]
        receipt = dict(schema_version='1', layer='transfer_preparation', status='prepared_only',
                       run_id=str(uuid.uuid4()), plan_id=plan['plan_id'], catalog_id=plan['catalog_id'],
                       plan=_ref(plan_bytes), preparation_component=dict(subject=subject,artifacts=component),
                       execution_profile=plan['execution_profile'], procedure=dict(path=PROCEDURE, **PINS[PROCEDURE]),
                       prompt=dict(path=PROMPT, **PINS[PROMPT]), context=dict(plan['context']),
                       declared_file_count=len(entries), declared_bytes=sum(a['size_bytes'] for a in entries),
                       overall_admission='not_evaluated', release_allowed=False, export_allowed=False,
                       activation_allowed=False, transition_allowed=False, export_performed=False,
                       activation_performed=False, current_binding_changed=False,
                       not_checked=['source_integrity', 'dependency_closure', 'known_restrictions',
                                    'mandatory_core_coverage', 'plan_authentication', 'release_permission',
                                    'export_permission', 'environment_compatibility', 'activation_permission'])
        return (json.dumps(receipt, ensure_ascii=False, indent=2)+'\n').encode('utf-8')
    except PreparationBlocked:
        raise
    except (ImportError, OSError):
        raise PreparationBlocked('PREPARATION_INSTALLATION_UNAVAILABLE', True) from None
    except (ValueError, TypeError, KeyError, RuntimeError, RecursionError):
        raise PreparationBlocked('PREPARATION_INPUT_OR_INSTALLATION_INVALID') from None
