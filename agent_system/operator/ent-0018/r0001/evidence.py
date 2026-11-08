"""I3 private evidence foundation, not execution or semantic replay proof."""
import hashlib
import json
import os
from pathlib import Path
import runpy
import stat
import uuid

BASE=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
LIMIT=16*1024*1024
TOTAL=128*1024*1024
FILES=20064


class EvidenceBlocked(Exception):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def _encode(value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT:raise EvidenceBlocked('DOCUMENT_LIMIT')
    return raw


def _tools():
    # Reuse the one fixed trusted loader; never execute stored contents.
    session=runpy.run_path(str(HERE/'session.py'))
    try:session['_tools']()
    except session['SessionBlocked']:raise EvidenceBlocked('INSTALLED_PROFILE_UNAVAILABLE') from None
    stage=runpy.run_path(str(BASE/'staging/ent-0015/r0001/stage.py'))
    reader=runpy.run_path(str(BASE/'staging/ent-0016/r0002/read.py'))
    return stage,reader


def _uuid(value):
    if type(value) is not str or str(uuid.UUID(value))!=value:raise EvidenceBlocked('INVALID_RUN_ID')


def _pin(value):
    if (type(value) is not dict or set(value)!={'sha256','size_bytes'}
            or type(value['sha256']) is not str or len(value['sha256'])!=64
            or any(c not in '0123456789abcdef' for c in value['sha256'])
            or type(value['size_bytes']) is not int or not 0<=value['size_bytes']<=LIMIT):
        raise EvidenceBlocked('INVALID_BYTE_REFERENCE')


class EvidenceStore:
    """Single-use private CAS claim. Failure poisons it; never overwrite/resume/delete."""
    def __init__(self):
        self.run_id=str(uuid.uuid4());self.fds=[];self.objects={};self.bytes=0
        self.failed=False;self.sealed=False;self.closed=False;self.stage=None

    def __enter__(self):
        if self.closed or self.fds:raise EvidenceBlocked('EVIDENCE_ALREADY_CLAIMED')
        try:
            self.stage,self.reader=_tools()
            base=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);self.fds.append(base)
            local=self.stage['_directory'](base,'local',False);self.fds.append(local)
            runs=self.stage['_directory'](local,'operator-runs',True);self.fds.append(runs)
            os.mkdir(self.run_id,0o700,dir_fd=runs)  # exclusive claim; no EEXIST fallback
            run=self.stage['_directory'](runs,self.run_id,True,False);self.fds.append(run)
            store=self.stage['_directory'](run,'objects',True);self.fds.append(store)
            self.run,self.store=run,store
            return self
        except BaseException as error:
            self.failed=True;self._close()
            if isinstance(error,(OSError,ValueError,RuntimeError)) or (self.stage and isinstance(error,self.stage['_Stop'])):
                raise EvidenceBlocked('EVIDENCE_CLAIM_FAILED') from None
            raise

    def _close(self):
        try:
            for fd in reversed(self.fds):os.close(fd)
        finally:self.fds=[];self.closed=True

    def __exit__(self,*exc):self._close()

    def _ready(self):
        if self.failed or self.sealed or self.closed or not self.fds:raise EvidenceBlocked('EVIDENCE_NOT_WRITABLE')

    def _budget(self,size,files):
        if size>LIMIT or self.bytes+size>TOTAL or files>FILES:raise EvidenceBlocked('EVIDENCE_BUDGET')

    def _failure(self,error):
        self.failed=True
        if isinstance(error,EvidenceBlocked):raise error
        if isinstance(error,(OSError,ValueError,TypeError,RuntimeError,RecursionError)) or isinstance(error,(self.stage['_Stop'],self.reader['_Stop'])):
            raise EvidenceBlocked('EVIDENCE_WRITE_FAILED') from None
        raise error

    def put(self,raw):
        self._ready()
        try:
            if type(raw) is not bytes:raise EvidenceBlocked('INVALID_DOCUMENT_BYTES')
            if len(raw)>LIMIT:raise EvidenceBlocked('DOCUMENT_LIMIT')
            r=reference(raw);sha=r['sha256']
            if sha in self.objects:
                if self.objects[sha]!=r:raise EvidenceBlocked('OBJECT_REFERENCE_CONFLICT')
                found=self.reader['_read'](self.store,sha,r,self.stage)
                if found!=raw:raise EvidenceBlocked('OBJECT_REFERENCE_CONFLICT')
                return dict(r)
            self._budget(len(raw),len(self.objects)+2)  # new object plus final index
            self.stage['_write_file'](self.store,sha,raw)
            self.objects[sha]=r;self.bytes+=len(raw)
            return dict(r)
        except BaseException as error:self._failure(error)

    def seal(self,metadata):
        self._ready()
        try:
            if type(metadata) is not dict:raise EvidenceBlocked('INDEX_METADATA')
            index=dict(schema_version='1',profile='operator-evidence-r0001',run_id=self.run_id,
                       objects=[dict(r) for _,r in sorted(self.objects.items())],metadata=metadata)
            raw=_encode(index);self._budget(len(raw),len(self.objects)+1)
            self.stage['_write_file'](self.run,'index.json',raw)
            self._verify(reference(raw))
            os.fsync(self.store);os.fsync(self.run)
            self.bytes+=len(raw);self.sealed=True
            return dict(run_id=self.run_id,index=reference(raw))
        except BaseException as error:self._failure(error)

    def _verify(self,expected):
        return _verify_open(self.fds,self.run_id,expected,self.stage,self.reader)


def _verify_open(fds,run_id,expected,stage,reader,*,with_capture=False):
    _pin(expected)
    base,local,runs,run,store=fds
    for parent,fd,private in [(base,local,False),(local,runs,True),(runs,run,True),(run,store,True)]:
        observed=os.fstat(fd)
        if (observed.st_uid!=os.geteuid() or observed.st_dev!=os.fstat(parent).st_dev
                or (stat.S_IMODE(observed.st_mode)!=0o700 if private else bool(stat.S_IMODE(observed.st_mode)&0o022))):
            raise EvidenceBlocked('EVIDENCE_DIRECTORY_METADATA')
    raw=reader['_read'](run,'index.json',expected,stage)
    # Parse through the same strict installed JSON parser as the legacy contract.
    parse=stage['_load']()[1]
    if not raw.endswith(b'\n') or raw.endswith(b'\n\n') or b'\r' in raw:raise EvidenceBlocked('INDEX_SERIALIZATION')
    index=parse(raw)
    if (type(index) is not dict or set(index)!={'schema_version','profile','run_id','objects','metadata'}
            or index['schema_version']!='1' or index['profile']!='operator-evidence-r0001'
            or index['run_id']!=run_id or type(index['metadata']) is not dict
            or type(index['objects']) is not list or len(index['objects'])+1>FILES):raise EvidenceBlocked('INDEX_SHAPE')
    rows=index['objects']
    for row in rows:_pin(row)
    if [r['sha256'] for r in rows]!=sorted({r['sha256'] for r in rows}):raise EvidenceBlocked('INDEX_OBJECT_SET')
    if sum(r['size_bytes'] for r in rows)+len(raw)>TOTAL:raise EvidenceBlocked('EVIDENCE_BUDGET')
    names=[r['sha256'] for r in rows]
    if sorted(os.listdir(run))!=['index.json','objects'] or sorted(os.listdir(store))!=names:raise EvidenceBlocked('EVIDENCE_INVENTORY')
    objects={}
    for row in rows:
        captured=reader['_read'](store,row['sha256'],row,stage)
        if with_capture:objects[row['sha256']]=captured
    reader['_read'](run,'index.json',expected,stage)
    if sorted(os.listdir(run))!=['index.json','objects'] or sorted(os.listdir(store))!=names:raise EvidenceBlocked('EVIDENCE_INVENTORY')
    for parent,name,fd in [(base,'local',local),(local,'operator-runs',runs),(runs,run_id,run),(run,'objects',store)]:stage['_bound'](parent,name,fd)
    return (index,objects) if with_capture else index


def _read_evidence(run_id,expected_index,*,with_capture=False):
    """Read-only structural CAS verification; NOT journal/child semantic replay."""
    fds=[];stage=None
    try:
        _uuid(run_id);_pin(expected_index)
        stage,reader=_tools()
        base=os.open(BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);fds.append(base)
        for name,private in [('local',False),('operator-runs',True),(run_id,True),('objects',True)]:
            fds.append(stage['_directory'](fds[-1],name,private,False))
        verified=_verify_open(fds,run_id,dict(expected_index),stage,reader,with_capture=with_capture)
        if with_capture:return verified
        index=verified
        return dict(status='consistent_private_evidence',run_id=run_id,index=dict(expected_index),
                    objects_count=len(index['objects']),overall_admission='not_evaluated',transition_allowed=False,
                    not_checked=['execution_authentication','journal_semantics','child_semantic_replay','current_permissions','freshness','global_completeness'])
    except EvidenceBlocked:raise
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,RecursionError,AttributeError):
        raise EvidenceBlocked('EVIDENCE_INVALID') from None
    except Exception as error:
        if stage is None or not isinstance(error,(stage['_Stop'],reader['_Stop'])):raise
        raise EvidenceBlocked('EVIDENCE_INVALID') from None
    finally:
        for fd in reversed(fds):os.close(fd)


def verify_evidence(run_id,expected_index):
    """Public structural-only checker; no raw maps, execution or journal proof."""
    return _read_evidence(run_id,expected_index)
