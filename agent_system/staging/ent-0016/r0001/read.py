#!/usr/bin/env python3
"""Read and replay a pinned private local trial; never infer current permission."""
import hashlib
import os
from pathlib import Path
import platform
import re
import runpy
import stat
import uuid

BASE=Path(__file__).resolve().parents[3]
PINS={'staging/ent-0015/r0001/stage.py': {'sha256': '2cf729cc03e65a4b28e5dbf1afac99de305c75b3422a08181b48c43392f3b9a0', 'size_bytes': 9215}, 'staging/ent-0015/r0001/verify.py': {'sha256': '46c3101cc2b6dd57b879e5e7aa1f9441943b74619ab6875f34bc5cc6d7a20a71', 'size_bytes': 13661}, 'staging/ent-0015/r0001/usage.md': {'sha256': '6e0bb1c173921c269d11da522e1ef290b6995e27cfc6857e16b849445151c14a', 'size_bytes': 14234}}
LIMIT=16*1024*1024
PROFILE='ent-0016-r0001-private-trial-reader'


class _Stop(Exception):
    def __init__(self,code):self.code=code


def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def _keys(value,names):
    if type(value) is not dict or set(value)!=set(names.split()):raise _Stop('MANIFEST_SHAPE')


def _ref(value):
    _keys(value,'sha256 size_bytes')
    if (type(value['sha256']) is not str or re.fullmatch('[0-9a-f]{64}',value['sha256']) is None
            or type(value['size_bytes']) is not int or not 0<=value['size_bytes']<=LIMIT):
        raise _Stop('INVALID_BYTE_REFERENCE')


def _load():
    for path,expected in PINS.items():
        with (BASE/path).open('rb') as stream:raw=stream.read(expected['size_bytes']+1)
        if reference(raw)!=expected:raise RuntimeError('Installed stage profile changed')
    entry=runpy.run_path(str(BASE/'staging/ent-0015/r0001/stage.py'))
    check,parse,binding=entry['_load']()
    return entry,check,parse,binding


def _base_fd():return os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)


def _read(directory,name,expected,entry):
    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_uid!=os.geteuid()
                or stat.S_IMODE(before.st_mode)!=0o600 or before.st_dev!=os.fstat(directory).st_dev
                or before.st_size!=expected['size_bytes']):raise _Stop('TRIAL_FILE_METADATA')
        parts=[];remaining=expected['size_bytes']+1
        while remaining:
            chunk=os.read(fd,min(remaining,1024*1024))
            if not chunk:break
            parts.append(chunk);remaining-=len(chunk)
        raw=b''.join(parts)
        named=os.stat(name,dir_fd=directory,follow_symlinks=False)
        if (reference(raw)!=expected or entry['_fingerprint'](before)!=entry['_fingerprint'](os.fstat(fd))
                or (named.st_dev,named.st_ino)!=(before.st_dev,before.st_ino)):
            raise _Stop('TRIAL_FILE_CHANGED')
        return raw
    finally:os.close(fd)


def _entries(rows):
    if type(rows) is not list or len(rows)>10000:raise _Stop('MANIFEST_ENTRY_SET')
    paths=[]
    for row in rows:
        _keys(row,'path sha256 size_bytes')
        if type(row['path']) is not str or not 1<=len(row['path'])<=4096:raise _Stop('MANIFEST_ENTRY_PATH')
        paths.append(row['path']);_ref({k:row[k] for k in ['sha256','size_bytes']})
    if paths!=sorted(set(paths)):raise _Stop('MANIFEST_ENTRY_SET')


def read_trial(run_id,expected_manifest):
    result=dict(schema_version='1',profile=PROFILE,layer='archived_private_trial',status='failed',
                overall_admission='not_evaluated',current_permissions='not_evaluated',
                transition_allowed=False,release_allowed=False,export_allowed=False,activation_allowed=False,
                diagnostics=[],not_checked=['manifest_authentication','execution_authentication','source_authentication',
                'current_decisions','global_event_completeness','coverage_claim_truth','agent_behavior',
                'target_environment','atomic_snapshot','hostile_same_uid_namespace','publication','activation'])
    fds=[];entry=None
    try:
        if platform.system()!='Linux' or platform.machine()!='x86_64':
            result['status']='unsupported';result['diagnostics']=[dict(code='UNSUPPORTED_PLATFORM')];return result
        if type(run_id) is not str or str(uuid.UUID(run_id))!=run_id:raise _Stop('INVALID_RUN_ID')
        _ref(expected_manifest);expected_manifest=dict(expected_manifest)
        try:entry,check,parse,binding=_load()
        except (OSError,ValueError,ImportError,RuntimeError,KeyError):
            result['status']='unsupported';result['diagnostics']=[dict(code='INSTALLED_PROFILE_UNAVAILABLE')];return result
        base=_base_fd();fds.append(base)
        local=entry['_directory'](base,'local',False,False);fds.append(local)
        trials=entry['_directory'](local,'trials',True,False);fds.append(trials)
        run=entry['_directory'](trials,run_id,True,False);fds.append(run)
        store=entry['_directory'](run,'objects',True,False);fds.append(store)
        before=[entry['_fingerprint'](os.fstat(fd)) for fd in [run,store]]
        if sorted(os.listdir(run))!=['objects','trial.json']:raise _Stop('TRIAL_RUN_INVENTORY')
        rawmanifest=_read(run,'trial.json',expected_manifest,entry)
        if (not rawmanifest.endswith(b'\n') or rawmanifest.endswith(b'\n\n') or b'\r' in rawmanifest):
            raise _Stop('MANIFEST_SERIALIZATION')
        manifest=parse(rawmanifest)
        _keys(manifest,'schema_version profile kind run_id candidate registry payloads decisions readiness release_allowed export_allowed activation_allowed transition_allowed overall_admission')
        if (manifest['schema_version']!='1' or manifest['profile']!=entry['PROFILE']
                or manifest['kind']!='incomplete_trial_snapshot' or manifest['run_id']!=run_id):
            raise _Stop('MANIFEST_PROFILE_OR_RUN')
        if (manifest['readiness']!='incomplete_candidate' or manifest['overall_admission']!='not_evaluated'
                or any(manifest[f] is not False for f in ['release_allowed','export_allowed','activation_allowed','transition_allowed'])):
            raise _Stop('MANIFEST_PERMISSION_CLAIM')
        _ref(manifest['candidate']);_ref(manifest['registry'])
        _entries(manifest['payloads']);_entries(manifest['decisions'])
        if (len(manifest['payloads'])+len(manifest['decisions'])+1>10000
                or sum(r['size_bytes'] for r in [manifest['registry'],*manifest['payloads'],*manifest['decisions']])>64*1024*1024):
            raise _Stop('TRIAL_SET_LIMIT')
        expected={}
        for row in [manifest['candidate'],manifest['registry'],*manifest['payloads'],*manifest['decisions']]:
            r={k:row[k] for k in ['sha256','size_bytes']};sha=r['sha256']
            if sha in expected and expected[sha]!=r:raise _Stop('OBJECT_REFERENCE_CONFLICT')
            expected[sha]=r
        if sorted(os.listdir(store))!=sorted(expected):raise _Stop('TRIAL_OBJECT_INVENTORY')
        objects={sha:_read(store,sha,ref,entry) for sha,ref in sorted(expected.items())}
        # All semantic replay consumes these captured bytes, not a second pathname read.
        candidate=objects[manifest['candidate']['sha256']];registry=objects[manifest['registry']['sha256']]
        payloads={r['path']:objects[r['sha256']] for r in manifest['payloads']}
        decisions={r['path']:objects[r['sha256']] for r in manifest['decisions']}
        child=check(candidate,manifest['candidate'],registry,decisions,payloads)
        if child['status']!='consistent_incomplete_candidate':
            result['status']=child['status'];result['diagnostics']=child['diagnostics'];return result
        parsed=parse(candidate)
        for operation in ['stage_trial','read_trial']:
            scoped=binding(registry,decisions,payloads,parsed['roots'],operation=operation,area='agent_system.trial')
            if scoped['status']!='passed_known_inputs':
                result['status']=scoped['status'];result['diagnostics']=([dict(code='ARCHIVED_KNOWN_SCOPE_BLOCK')] if scoped['status']=='blocked_known_scope' else scoped['diagnostics']);return result
        if (sorted(os.listdir(run))!=['objects','trial.json'] or sorted(os.listdir(store))!=sorted(expected)
                or [entry['_fingerprint'](os.fstat(fd)) for fd in [run,store]]!=before):
            raise _Stop('TRIAL_OBSERVATION_CHANGED')
        # Repeat manifest pin check and directory bindings, without changing the captured inputs.
        _read(run,'trial.json',expected_manifest,entry)
        for sha,expected_ref in sorted(expected.items()):_read(store,sha,expected_ref,entry)
        if sorted(os.listdir(run))!=['objects','trial.json'] or sorted(os.listdir(store))!=sorted(expected):
            raise _Stop('TRIAL_OBSERVATION_CHANGED')
        for parent,name,fd in [(base,'local',local),(local,'trials',trials),(trials,run_id,run),(run,'objects',store)]:
            entry['_bound'](parent,name,fd)
        result.update(status='consistent_archived_trial',manifest=expected_manifest,
                      candidate=manifest['candidate'],registry=manifest['registry'],
                      payload_count=len(payloads),decision_count=len(decisions),objects_count=len(objects),
                      captured_bytes=sum(map(len,objects.values())))
    except _Stop as error:result['diagnostics']=[dict(code=error.code)]
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,RecursionError,AttributeError):
        result['diagnostics']=[dict(code='TRIAL_OR_IO_INVALID')]
    except Exception as error:
        if entry is None or not isinstance(error,entry['_Stop']):raise
        result['diagnostics']=[dict(code=error.code)]
    finally:
        for fd in reversed(fds):os.close(fd)
    return result
