#!/usr/bin/env python3
"""Create a new private local trial object store, never publish or activate."""
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import stat
import uuid

BASE=Path(__file__).resolve().parents[3]
PINS={'permissions/ent-0014/r0001/proposal.schema.json': {'sha256': '142a2a628ed5125229ac48a9e1d6768f62cf21ff138cc12a83fa1c220369ac39', 'size_bytes': 4320}, 'permissions/ent-0014/r0001/check.py': {'sha256': '18d47b251a0709ebd021a9473553c7faeb12b8e977d90ed41b20899dde9df1d2', 'size_bytes': 7333}, 'permissions/ent-0014/r0001/verify.py': {'sha256': 'd94ce36432537ce5e13f4d059fc6f0a0772c0e8fc6cbfb19734aa59e1937ed1e', 'size_bytes': 8170}, 'permissions/ent-0014/r0001/usage.md': {'sha256': '3ba366a47b00d576bfb1254dee15404b6e3c245437f3097be301907326eb2fd1', 'size_bytes': 15107}}
LIMIT=16*1024*1024
PROFILE='ent-0015-r0001-linux-x86_64-object-store'


class _Stop(Exception):
    def __init__(self,code):self.code=code


def reference(raw):
    return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def encode(value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT:raise _Stop('MANIFEST_LIMIT')
    return raw


def _load():
    for path,expected in PINS.items():
        with (BASE/path).open('rb') as stream:raw=stream.read(expected['size_bytes']+1)
        if reference(raw)!=expected:raise RuntimeError('Installed profile changed')
    entry=runpy.run_path(str(BASE/'permissions/ent-0014/r0001/check.py'))
    check,parse,_,binding=entry['_load']()
    return check,parse,binding


def _base_fd():
    return os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)


def _directory(parent,name,private,create=True):
    created=False
    if create:
        try:os.mkdir(name,0o700,dir_fd=parent);created=True
        except FileExistsError:pass
    fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=parent)
    try:
        s=os.fstat(fd)
        if (s.st_uid!=os.geteuid() or s.st_dev!=os.fstat(parent).st_dev
                or stat.S_IMODE(s.st_mode)&(0o077 if private else 0o022)):
            raise _Stop('UNSAFE_LOCAL_DIRECTORY')
        if created:os.fchmod(fd,0o700)
        return fd
    except BaseException:
        os.close(fd);raise


def _fingerprint(s):
    return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns,s.st_mode,s.st_uid,s.st_nlink)


def _read_file(directory,name,expected):
    fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
    try:
        before=os.fstat(fd)
        if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_uid!=os.geteuid()
                or stat.S_IMODE(before.st_mode)!=0o600 or before.st_dev!=os.fstat(directory).st_dev
                or before.st_size!=expected['size_bytes']):raise _Stop('OUTPUT_METADATA_CHANGED')
        pieces=[];remaining=expected['size_bytes']+1
        while remaining:
            chunk=os.read(fd,min(1024*1024,remaining))
            if not chunk:break
            pieces.append(chunk);remaining-=len(chunk)
        if reference(b''.join(pieces))!=expected or _fingerprint(os.fstat(fd))!=_fingerprint(before):
            raise _Stop('OUTPUT_BYTES_CHANGED')
    finally:os.close(fd)


def _write_file(directory,name,raw):
    fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
    try:
        os.fchmod(fd,0o600)
        view=memoryview(raw)
        while view:
            written=os.write(fd,view)
            if written<=0:raise _Stop('OUTPUT_SHORT_WRITE')
            view=view[written:]
        os.fsync(fd)
    finally:os.close(fd)
    _read_file(directory,name,reference(raw))


def _bound(parent,name,fd):
    named=os.stat(name,dir_fd=parent,follow_symlinks=False);opened=os.fstat(fd)
    if not stat.S_ISDIR(named.st_mode) or (named.st_dev,named.st_ino)!=(opened.st_dev,opened.st_ino):
        raise _Stop('OUTPUT_DIRECTORY_REBOUND')


def stage_trial(candidate_bytes,expected_candidate,registry_blob,decisions,payloads):
    result=dict(schema_version='1',profile=PROFILE,layer='private_trial_staging',status='failed',
                stage_created=False,staged=False,overall_admission='not_evaluated',
                transition_allowed=False,release_allowed=False,export_allowed=False,activation_allowed=False,
                diagnostics=[],not_checked=['source_authentication','global_event_completeness',
                'source_acquisition_boundary','coverage_claim_truth','agent_behavior','target_environment',
                'hostile_same_uid_namespace','atomic_snapshot','crash_durability','publication','activation'])
    fds=[]
    try:
        if platform.system()!='Linux' or platform.machine()!='x86_64':
            result['status']='unsupported';result['diagnostics']=[dict(code='UNSUPPORTED_PLATFORM')];return result
        if (type(candidate_bytes) is not bytes or len(candidate_bytes)>LIMIT or type(expected_candidate) is not dict
                or set(expected_candidate)!={'sha256','size_bytes'} or type(expected_candidate['size_bytes']) is not int
                or type(expected_candidate['sha256']) is not str or reference(candidate_bytes)!=expected_candidate):raise _Stop('CANDIDATE_REFERENCE_MISMATCH')
        if type(decisions) is not dict or type(payloads) is not dict:raise _Stop('INPUT_TYPE')
        decisions,payloads=dict(decisions),dict(payloads)
        try:check,parse,binding=_load()
        except (OSError,ValueError,ImportError,RuntimeError,KeyError):
            result['status']='unsupported';result['diagnostics']=[dict(code='INSTALLED_PROFILE_UNAVAILABLE')];return result
        child=check(candidate_bytes,expected_candidate,registry_blob,decisions,payloads)
        if child['status']!='consistent_incomplete_candidate':
            result['status']=child['status'];result['diagnostics']=child['diagnostics'];return result
        candidate=parse(candidate_bytes)
        scoped=binding(registry_blob,decisions,payloads,candidate['roots'],operation='stage_trial',area='agent_system.trial')
        if scoped['status']!='passed_known_inputs':
            result['status']=scoped['status'];result['diagnostics']=([dict(code='KNOWN_SCOPE_BLOCK')] if scoped['status']=='blocked_known_scope' else scoped['diagnostics']);return result
        run_id=str(uuid.uuid4())
        if str(uuid.UUID(run_id))!=run_id:raise _Stop('INVALID_GENERATED_ID')
        objects={}
        def put(raw):
            digest=reference(raw)
            if digest['sha256'] in objects and objects[digest['sha256']]!=raw:raise _Stop('OBJECT_DIGEST_COLLISION')
            objects[digest['sha256']]=raw
            return digest
        manifest=dict(schema_version='1',profile=PROFILE,kind='incomplete_trial_snapshot',run_id=run_id,
                      candidate=put(candidate_bytes),registry=put(registry_blob),
                      payloads=[dict(path=p,**put(b)) for p,b in sorted(payloads.items())],
                      decisions=[dict(path=p,**put(b)) for p,b in sorted(decisions.items())],
                      readiness='incomplete_candidate',release_allowed=False,export_allowed=False,
                      activation_allowed=False,transition_allowed=False,overall_admission='not_evaluated')
        rawmanifest=encode(manifest)
        base=_base_fd();fds.append(base)
        local=_directory(base,'local',False);fds.append(local)
        trials=_directory(local,'trials',True);fds.append(trials)
        # Exclusive claim: no resume/retry into an existing run, no overwrite or rollback.
        os.mkdir(run_id,0o700,dir_fd=trials)
        result.update(stage_created=True,local_ref='local/trials/'+run_id)
        run=_directory(trials,run_id,True,False);fds.append(run)
        store=_directory(run,'objects',True);fds.append(store)
        for name,raw in sorted(objects.items()):_write_file(store,name,raw)
        if sorted(os.listdir(store))!=sorted(objects):raise _Stop('OUTPUT_INVENTORY_CHANGED')
        for name,raw in sorted(objects.items()):_read_file(store,name,reference(raw))
        _write_file(run,'trial.json',rawmanifest)
        if sorted(os.listdir(run))!=['objects','trial.json']:raise _Stop('OUTPUT_INVENTORY_CHANGED')
        _read_file(run,'trial.json',reference(rawmanifest))
        for parent,name,opened in [(base,'local',local),(local,'trials',trials),(trials,run_id,run),(run,'objects',store)]:
            _bound(parent,name,opened)
        for fd in [store,run,trials,local]:os.fsync(fd)
        result.update(status='staged_trial_only',staged=True,manifest=reference(rawmanifest),
                      objects_count=len(objects),stored_bytes=sum(map(len,objects.values())))
    except _Stop as error:
        result['diagnostics']=[dict(code=error.code)]
        if result['stage_created']:result['status']='failed_partial'
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,RecursionError,AttributeError):
        result['status']='failed_partial' if result['stage_created'] else 'failed'
        result['diagnostics']=[dict(code='STAGING_IO_OR_INPUT_INVALID')]
    finally:
        for fd in reversed(fds):os.close(fd)
    return result
