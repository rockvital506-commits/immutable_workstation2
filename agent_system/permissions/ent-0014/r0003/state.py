"""Private local assent/controller journal. No release/export/activation actuator."""
import hashlib
import json
import os
from pathlib import Path
import platform
import runpy
import stat
import uuid

INSTALL=Path(__file__).resolve().parents[3]
LOCAL_BASE=INSTALL
LIMIT=16*1024*1024
TOTAL=128*1024*1024
FILES=20064
GENERATIONS=256
EVENTS=128
LOCK=b'local-owner-journal-lock-r0001\n'
PINS={'permissions/ent-0014/r0002/authority.py': {'sha256': '02965181c4cee21ae022df069fdc08dfad4718e47fe2494e87e3a523859505d3', 'size_bytes': 15528}, 'permissions/ent-0014/r0002/permissions.schema.json': {'sha256': 'fad42d9a79676dd2458a2412493328a55064dc66505d5696751a5643e6fa0941', 'size_bytes': 7335}, 'permissions/ent-0014/r0002/verify.py': {'sha256': 'e00d39a00e29217aaf008842e644fbfac3b7e7e158617bb07e31fb86715b14ab', 'size_bytes': 18918}, 'permissions/ent-0014/r0002/usage.md': {'sha256': 'd6d0df0887849a6ea51dc76beff3fddd650e5408b038c28eb8320c0383fac29b', 'size_bytes': 12562}, 'permissions/ent-0014/r0002/procedure.md': {'sha256': 'f9fd0753480732468fd16373dd0237c0435ccedc523dff57a429e2b5096ef256', 'size_bytes': 4294}, 'staging/ent-0015/r0001/stage.py': {'sha256': '2cf729cc03e65a4b28e5dbf1afac99de305c75b3422a08181b48c43392f3b9a0', 'size_bytes': 9215}, 'staging/ent-0015/r0001/verify.py': {'sha256': '46c3101cc2b6dd57b879e5e7aa1f9441943b74619ab6875f34bc5cc6d7a20a71', 'size_bytes': 13661}, 'staging/ent-0015/r0001/usage.md': {'sha256': '6e0bb1c173921c269d11da522e1ef290b6995e27cfc6857e16b849445151c14a', 'size_bytes': 14234}, 'permissions/ent-0014/r0003/state.schema.json': {'sha256': '21f2ec5fdd3743f2224bd034297bb2067ab4e1d3f4191228f2b4ff63ec8f247c', 'size_bytes': 4731}}


class StateBlocked(Exception):
    def __init__(self,code):self.code=code;super().__init__(code)


def _stop(code):raise StateBlocked(code)
def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))
def encode(value):return (json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()


def _uuid(value):
    try:
        if type(value) is not str or str(uuid.UUID(value))!=value:_stop('INVALID_ID')
    except (ValueError,AttributeError):_stop('INVALID_ID')


def _ref(value):
    if (type(value) is not dict or set(value)!={'sha256','size_bytes'} or type(value['size_bytes']) is not int
            or not 0<=value['size_bytes']<=LIMIT or type(value['sha256']) is not str
            or len(value['sha256'])!=64 or any(c not in '0123456789abcdef' for c in value['sha256'])):_stop('INVALID_PIN')


def _pin(raw,expected):
    _ref(expected)
    if type(raw) is not bytes or len(raw)>LIMIT or reference(raw)!=expected:_stop('REFERENCE_MISMATCH')


def _installed(path):
    expected=PINS[path]
    with (INSTALL/path).open('rb') as f:raw=f.read(expected['size_bytes']+1)
    _pin(raw,expected);return raw


def _tools():
    if platform.system()!='Linux' or platform.machine()!='x86_64':_stop('UNSUPPORTED_PLATFORM')
    import fcntl
    for p in PINS:_installed(p)
    a=runpy.run_path(str(INSTALL/'permissions/ent-0014/r0002/authority.py'))
    s=runpy.run_path(str(INSTALL/'staging/ent-0015/r0001/stage.py'))
    s['_load']();validator=a['_schema']()
    schema=a['_json'](_installed('permissions/ent-0014/r0003/state.schema.json'))
    type(validator).check_schema(schema)
    from referencing import Registry
    def deny(_):raise ValueError('Schema retrieval forbidden')
    state_validator=type(validator)(schema,format_checker=validator.format_checker,registry=Registry(retrieve=deny))
    return a,s,fcntl,validator,state_validator


def _plain(r):return {k:r[k] for k in ['sha256','size_bytes']}


def _names(fd,limit=FILES):
    names=[]
    with os.scandir(fd) as entries:
        for entry in entries:
            if len(names)>=limit:_stop('INVENTORY_LIMIT')
            names.append(entry.name)
    return sorted(names)


def _context(head):
    return dict(schema_version='1',kind='local_owner_context',profile='owner-controlled-local-r0001',
                context_id=head['store_id'],generation=head['generation'],
                known_events=sorted([dict(path='permission-events/'+v['event']['event_id']+'.json',**_plain(v['event'])) for v in head['sources']],key=lambda v:v['path']),
                approved_events=[dict(v['event']) for v in head['sources']])


class AuthorityStore:
    def __init__(self,store_id,expected_head,*,trust_owner_controlled_namespace=False,_create=False):
        if trust_owner_controlled_namespace is not True:_stop('EXPLICIT_OWNER_NAMESPACE_REQUIRED')
        _uuid(store_id)
        if not _create:_ref(expected_head)
        self.store_id=store_id;self.expected=expected_head;self.creating=_create
        self.fds=[];self.closed=False;self.failed=False;self.a=None;self.s=None

    def __enter__(self):
        if self.closed or self.fds:_stop('HANDLE_ALREADY_USED')
        try:
            self.a,self.s,self.fcntl,self.av,self.sv=_tools()
            base=os.open(LOCAL_BASE,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC);self.fds.append(base)
            self._base_bound(base)
            local=self.s['_directory'](base,'local',False,self.creating);self.fds.append(local)
            namespace=self.s['_directory'](local,'permission-authority',True,self.creating);self.fds.append(namespace)
            if self.creating:os.mkdir(self.store_id,0o700,dir_fd=namespace)
            store=self.s['_directory'](namespace,self.store_id,True,False);self.fds.append(store)
            objects=self.s['_directory'](store,'objects',True,self.creating);self.fds.append(objects)
            gens=self.s['_directory'](store,'generations',True,self.creating);self.fds.append(gens)
            self.store,self.objects_fd,self.gens=store,objects,gens
            if self.creating:self.s['_write_file'](store,'lock',LOCK)
            lock=os.open('lock',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=store);self.fds.append(lock);self.lock=lock
            self._lock_bound()
            try:self.fcntl.flock(lock,self.fcntl.LOCK_EX|self.fcntl.LOCK_NB)
            except BlockingIOError:_stop('AUTHORITY_STATE_BUSY')
            self._bounds()
            if self.creating:
                self.head=None;self.objects={};self.head_bytes=[]
                self._commit('initialize',[],[],{})
                for fd in self.fds[:4]:os.fsync(fd)
            else:self._verify(self.expected)
            return self
        except BaseException as error:
            self.failed=True;self.close();self._error(error)

    def close(self):
        try:
            for fd in reversed(self.fds):os.close(fd)
        finally:self.fds=[];self.closed=True

    def __exit__(self,*args):self.close()

    def _error(self,error):
        if isinstance(error,StateBlocked):raise error
        if self.a and isinstance(error,self.a['PermissionBlocked']):raise StateBlocked('AUTHORITY_'+error.code) from None
        if (self.s and isinstance(error,self.s['_Stop'])) or isinstance(error,OSError):raise StateBlocked('STATE_IO_FAILED') from None
        if isinstance(error,(ValueError,TypeError,KeyError,UnicodeError,RecursionError)):raise StateBlocked('STATE_INPUT_INVALID') from None
        raise error

    def _ready(self):
        if self.closed or self.failed or not self.fds:_stop('HANDLE_NOT_READY')
        try:self._bounds()
        except BaseException as error:self.failed=True;self._error(error)

    def _base_bound(self,fd):
        s=os.fstat(fd);named=os.stat(LOCAL_BASE,follow_symlinks=False)
        if (not stat.S_ISDIR(named.st_mode) or (s.st_dev,s.st_ino)!=(named.st_dev,named.st_ino)
                or s.st_uid!=os.geteuid() or stat.S_IMODE(s.st_mode)&0o022):_stop('UNSAFE_BASE_NAMESPACE')

    def _lock_bound(self):
        fd=self.lock;s=os.fstat(fd);named=os.stat('lock',dir_fd=self.store,follow_symlinks=False)
        if (not stat.S_ISREG(s.st_mode) or s.st_nlink!=1 or s.st_uid!=os.geteuid()
                or stat.S_IMODE(s.st_mode)!=0o600 or s.st_dev!=os.fstat(self.store).st_dev
                or s.st_size!=len(LOCK) or (s.st_dev,s.st_ino)!=(named.st_dev,named.st_ino)
                or os.pread(fd,len(LOCK)+1,0)!=LOCK):_stop('LOCK_METADATA_OR_BINDING')

    def _bounds(self):
        base,local,namespace,store,objects,gens=self.fds[:6]
        self._base_bound(base)
        for parent,name,fd,private in [(base,'local',local,False),(local,'permission-authority',namespace,True),
                (namespace,self.store_id,store,True),(store,'objects',objects,True),(store,'generations',gens,True)]:
            self.s['_bound'](parent,name,fd);s=os.fstat(fd)
            if (s.st_uid!=os.geteuid() or s.st_dev!=os.fstat(parent).st_dev
                    or (stat.S_IMODE(s.st_mode)!=0o700 if private else bool(stat.S_IMODE(s.st_mode)&0o022))):_stop('DIRECTORY_METADATA')
        self._lock_bound()
        if _names(store,8)!=['generations','lock','objects']:_stop('STORE_INVENTORY')

    def _read(self,directory,name,expected=None):
        if expected is not None:_ref(expected)
        fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,dir_fd=directory)
        try:
            before=os.fstat(fd)
            if (not stat.S_ISREG(before.st_mode) or before.st_nlink!=1 or before.st_uid!=os.geteuid()
                    or stat.S_IMODE(before.st_mode)!=0o600 or before.st_dev!=os.fstat(directory).st_dev
                    or before.st_size>LIMIT):_stop('FILE_METADATA')
            chunks=[];remaining=before.st_size+1
            while remaining:
                data=os.read(fd,min(1024*1024,remaining))
                if not data:break
                chunks.append(data);remaining-=len(data)
            raw=b''.join(chunks);after=os.fstat(fd);named=os.stat(name,dir_fd=directory,follow_symlinks=False)
            if (len(raw)!=before.st_size or self.s['_fingerprint'](before)!=self.s['_fingerprint'](after)
                    or not stat.S_ISREG(named.st_mode) or (named.st_dev,named.st_ino)!=(after.st_dev,after.st_ino)):_stop('FILE_BINDING_CHANGED')
            if expected is not None:_pin(raw,expected)
            return raw
        finally:os.close(fd)

    def _doc(self,raw,kind):
        value=self.a['_json'](raw);self.a['_native'](value)
        schema={'$defs':self.sv.schema['$defs'],'$ref':'#/$defs/'+kind}
        if not self.sv.evolve(schema=schema).is_valid(value):_stop('STATE_DOCUMENT_SCHEMA')
        return value

    def _validate_stream(self,head,subject_raw,objects):
        context=encode(_context(head));authority=self.a['establish_local_authority'](context,reference(context),trust_owner_controlled_context=True)
        # Deliberately nonexistent grant: full stream validates first; no intent is invented.
        request=dict(schema_version='1',kind='permission_check',request_id=self.store_id,action='release',
                     context=reference(context),generation=head['generation'],subject=reference(subject_raw),
                     grant=dict(event_id=self.store_id,sha256='0'*64,size_bytes=0),export=None)
        raw=encode(request);events={'permission-events/'+row['event']['event_id']+'.json':objects[row['event']['sha256']] for row in head['sources']}
        report=self.a['evaluate_permission'](raw,reference(raw),subject_raw,reference(subject_raw),events,
                                           authority=authority,expected_current_context=reference(context))
        if report['diagnostics']!=['GRANT_REFERENCE']:_stop('IMPORTED_STREAM_INVALID')

    def _evaluate_check(self,head,request_raw,subject_raw,objects):
        context=objects[head['context']['sha256']]
        authority=self.a['establish_local_authority'](context,head['context'],trust_owner_controlled_context=True)
        events={'permission-events/'+row['event']['event_id']+'.json':objects[row['event']['sha256']] for row in head['sources']}
        return self.a['evaluate_permission'](request_raw,reference(request_raw),subject_raw,reference(subject_raw),events,
                                            authority=authority,expected_current_context=head['context'])

    def _verify(self,expected):
        self._bounds();names=_names(self.gens,GENERATIONS)
        if not 1<=len(names)<=GENERATIONS or names!=['%08d.json'%i for i in range(len(names))]:_stop('GENERATION_INVENTORY')
        raws=[];head_total=0
        for name in names:
            raw=self._read(self.gens,name);head_total+=len(raw)
            if head_total+len(LOCK)>TOTAL:_stop('STATE_BUDGET')
            raws.append(raw)
        _pin(raws[-1],expected)
        heads=[None]*len(raws);parent=expected
        for i in reversed(range(len(raws))):
            _pin(raws[i],parent);h=self._doc(raws[i],'head');heads[i]=h
            if h['store_id']!=self.store_id or h['generation']!=i:_stop('GENERATION_IDENTITY')
            parent=h['parent']
        if parent is not None:_stop('INITIAL_PARENT')
        objects={}
        def get(r):
            r=_plain(r);_ref(r)
            if r['sha256'] not in objects:
                if len(objects)+len(raws)+2>FILES or sum(map(len,objects.values()))+head_total+len(LOCK)+r['size_bytes']>TOTAL:_stop('STATE_BUDGET')
                objects[r['sha256']]=self._read(self.objects_fd,r['sha256'],r)
            _pin(objects[r['sha256']],r);return objects[r['sha256']]
        prior=None
        for h in heads:
            ids=[v['event']['event_id'] for v in h['sources']];checks=[v['request_id'] for v in h['checks']]
            if ids!=sorted(set(ids)) or len(ids)>EVENTS or checks!=sorted(set(checks)):_stop('STATE_ROW_SET')
            context=get(h['context'])
            if context!=encode(_context(h)):_stop('CONTEXT_STATE_BINDING')
            basis_ids=set()
            for row in h['sources']:
                event=get(row['event']);assent=self._doc(get(row['assent']),'assent');subject=get(row['subject'])
                ev=self.a['_doc'](event,'event',self.av)
                if (dict(event_id=ev['event_id'],**reference(event))!=row['event'] or assent['event']!=row['event']
                        or ev['subject']!=row['subject'] or not assent['statement'].strip()):_stop('ASSENT_EVENT_BINDING')
                if assent['basis_id'] in basis_ids:_stop('ASSENT_ID_COLLISION')
                basis_ids.add(assent['basis_id'])
                self.a['_doc'](subject,'subject',self.av)
            for row in h['checks']:
                request=get(row['request']);get(row['subject']);get(row['result'])
                parsed=self.a['_doc'](request,'request',self.av)
                if parsed['request_id']!=row['request_id'] or parsed['subject']!=row['subject']:_stop('CHECK_INPUT_BINDING')
            if prior is None:
                if h['operation']!='initialize' or h['sources'] or h['checks']:_stop('INITIAL_STATE')
            else:
                old_sources={v['event']['event_id']:v for v in prior['sources']};new_sources={v['event']['event_id']:v for v in h['sources']}
                old_checks={v['request_id']:v for v in prior['checks']};new_checks={v['request_id']:v for v in h['checks']}
                if any(new_sources.get(k)!=v for k,v in old_sources.items()) or any(new_checks.get(k)!=v for k,v in old_checks.items()):_stop('HISTORY_REMOVED_OR_CHANGED')
                if h['operation']=='import':
                    added=set(new_sources)-set(old_sources)
                    if len(added)!=1 or new_checks!=old_checks:_stop('IMPORT_TRANSITION')
                    row=new_sources[next(iter(added))];self._validate_stream(h,get(row['subject']),objects)
                elif h['operation']=='check':
                    added=set(new_checks)-set(old_checks)
                    if len(added)!=1 or new_sources!=old_sources:_stop('CHECK_TRANSITION')
                    row=new_checks[next(iter(added))]
                    request=self.a['_doc'](get(row['request']),'request',self.av)
                    if request['context']!=prior['context'] or request['generation']!=prior['generation']:_stop('RECORDED_CHECK_CONTEXT')
                    report=self._evaluate_check(prior,get(row['request']),get(row['subject']),objects)
                    if encode(report)!=get(row['result']):_stop('CHECK_RESULT_BINDING')
                else:_stop('STATE_TRANSITION')
            prior=h
        if _names(self.objects_fd)!=sorted(objects):_stop('PARTIAL_OR_EXTRA_OBJECTS')
        if len(objects)+len(raws)+1>FILES or sum(map(len,objects.values()))+sum(map(len,raws))+len(LOCK)>TOTAL:_stop('STATE_BUDGET')
        self._bounds();self.head=heads[-1];self.head_bytes=raws;self.objects=objects;self.expected=dict(expected)

    def _commit(self,operation,sources,checks,pending):
        self._bounds();generation=0 if self.head is None else self.head['generation']+1
        if generation>=GENERATIONS:_stop('GENERATION_LIMIT')
        h=dict(schema_version='1',kind='owner_authority_generation',profile='local-owner-journal-linux-r0001',
               store_id=self.store_id,generation=generation,parent=None if self.head is None else dict(self.expected),
               operation=operation,context=None,sources=sources,checks=checks)
        context=encode(_context(h));h['context']=reference(context);pending=dict(pending);pending[reference(context)['sha256']]=context
        rawhead=encode(h);self._doc(rawhead,'head')
        new={}
        for sha,raw in pending.items():
            if type(raw) is not bytes or len(raw)>LIMIT or reference(raw)['sha256']!=sha:_stop('OBJECT_INPUT')
            if sha in self.objects:
                if self.objects[sha]!=raw:_stop('OBJECT_COLLISION')
            else:new[sha]=raw
        if (len(self.objects)+len(new)+len(self.head_bytes)+2>FILES or sum(map(len,self.objects.values()))
                +sum(map(len,new.values()))+sum(map(len,self.head_bytes))+len(rawhead)+len(LOCK)>TOTAL):_stop('STATE_BUDGET')
        for sha,raw in new.items():
            self.s['_write_file'](self.objects_fd,sha,raw)
            if self._read(self.objects_fd,sha,reference(raw))!=raw:_stop('OBJECT_READBACK')
        os.fsync(self.objects_fd);self._bounds()
        self.s['_write_file'](self.gens,'%08d.json'%generation,rawhead)
        os.fsync(self.gens);os.fsync(self.store);self._bounds()
        self._verify(reference(rawhead));return self.summary()

    def summary(self):
        self._ready()
        return dict(status='consistent_private_authority_state',store_id=self.store_id,generation=self.head['generation'],
                    head=dict(self.expected),context=dict(self.head['context']),events_count=len(self.head['sources']),
                    checks_count=len(self.head['checks']),performed=False,transition_allowed=False,release_allowed=False,
                    export_allowed=False,activation_allowed=False,overall_admission='not_evaluated',
                    not_checked=['owner_identity_authentication','assent_semantic_truth','global_event_completeness',
                                 'hostile_same_uid_or_root','external_rollback_resistance','action_single_use_claim',
                                 'readiness','actuation','target_environment'])

    def context_packet(self):
        self._ready()
        return dict(context_bytes=self.objects[self.head['context']['sha256']],expected_context=dict(self.head['context']),
                    event_blobs={'permission-events/'+v['event']['event_id']+'.json':self.objects[v['event']['sha256']] for v in self.head['sources']})

    def import_assent(self,event_bytes,expected_event,assent_bytes,expected_assent,subject_bytes,expected_subject,*,attest_exact_owner_assent=False):
        self._ready()
        try:
            if attest_exact_owner_assent is not True:_stop('EXACT_OWNER_ASSENT_REQUIRED')
            for raw,pin in [(event_bytes,expected_event),(assent_bytes,expected_assent),(subject_bytes,expected_subject)]:_pin(raw,pin)
            ev=self.a['_doc'](event_bytes,'event',self.av);assent=self._doc(assent_bytes,'assent')
            self.a['_doc'](subject_bytes,'subject',self.av)
            event_ref=dict(event_id=ev['event_id'],**expected_event)
            if assent['event']!=event_ref or ev['subject']!=expected_subject or not assent['statement'].strip():_stop('ASSENT_EVENT_BINDING')
            if any(v['event']['event_id']==ev['event_id'] for v in self.head['sources']):_stop('EVENT_ALREADY_IMPORTED')
            if any(self._doc(self.objects[v['assent']['sha256']],'assent')['basis_id']==assent['basis_id'] for v in self.head['sources']):_stop('ASSENT_ID_ALREADY_IMPORTED')
            if len(self.head['sources'])>=EVENTS:_stop('EVENT_LIMIT')
            sources=sorted([*self.head['sources'],dict(event=event_ref,assent=expected_assent,subject=expected_subject)],key=lambda v:v['event']['event_id'])
            pending={reference(raw)['sha256']:raw for raw in [event_bytes,assent_bytes,subject_bytes]}
            prospective=dict(self.head,sources=sources,generation=self.head['generation']+1)
            self._validate_stream(prospective,subject_bytes,dict(self.objects,**pending))
            return self._commit('import',sources,self.head['checks'],pending)
        except BaseException as error:self.failed=True;self._error(error)

    def check_once(self,request_bytes,expected_request,subject_bytes,expected_subject):
        self._ready()
        try:
            _pin(request_bytes,expected_request);_pin(subject_bytes,expected_subject)
            request=self.a['_doc'](request_bytes,'request',self.av);self.a['_doc'](subject_bytes,'subject',self.av)
            if request['subject']!=expected_subject:_stop('CHECK_SUBJECT_BINDING')
            if any(v['request_id']==request['request_id'] for v in self.head['checks']):_stop('CHECK_ID_ALREADY_CONSUMED')
            if request['context']!=self.head['context'] or request['generation']!=self.head['generation']:_stop('CHECK_CURRENT_CONTEXT')
            report=self._evaluate_check(self.head,request_bytes,subject_bytes,self.objects)
            rawreport=encode(report)
            row=dict(request_id=request['request_id'],request=expected_request,subject=expected_subject,result=reference(rawreport))
            checks=sorted([*self.head['checks'],row],key=lambda v:v['request_id'])
            pending={reference(raw)['sha256']:raw for raw in [request_bytes,subject_bytes,rawreport]}
            receipt=self._commit('check',self.head['sources'],checks,pending)
            return dict(receipt=receipt,check_result=report,check_id_consumed=True,action_claim_created=False)
        except BaseException as error:self.failed=True;self._error(error)


def create_store(*,trust_owner_controlled_namespace=False):
    with AuthorityStore(str(uuid.uuid4()),None,trust_owner_controlled_namespace=trust_owner_controlled_namespace,_create=True) as store:
        return store.summary()


def run_empty_lab(*,trust_owner_controlled_namespace=False):
    """Actual empty-authority persistence/check demo; creates NO assent/event/grant."""
    receipt=create_store(trust_owner_controlled_namespace=trust_owner_controlled_namespace)
    with AuthorityStore(receipt['store_id'],receipt['head'],trust_owner_controlled_namespace=trust_owner_controlled_namespace) as store:
        packet=store.context_packet();r=reference(b'not-a-real-release\n')
        subject=encode(dict(schema_version='1',kind='release_subject',candidate=r,registry=r,entity_decisions=[],
                            artifacts=[dict(path='lab/unexecuted.txt',**r)],coverage_description=r,procedure=r,prompt=r))
        request=encode(dict(schema_version='1',kind='permission_check',request_id=str(uuid.uuid4()),action='release',
                            context=packet['expected_context'],generation=0,subject=reference(subject),
                            grant=dict(event_id=str(uuid.uuid4()),sha256='0'*64,size_bytes=0),export=None))
        result=store.check_once(request,reference(request),subject,reference(subject))
    with AuthorityStore(receipt['store_id'],result['receipt']['head'],trust_owner_controlled_namespace=trust_owner_controlled_namespace) as store:
        result['reopened']=store.summary()
    return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Empty private authority lab, never a release/export grant')
    parser.add_argument('--trust-owner-controlled-namespace',action='store_true')
    args=parser.parse_args()
    try:value=run_empty_lab(trust_owner_controlled_namespace=args.trust_owner_controlled_namespace)
    except StateBlocked as error:
        print(error.code);raise SystemExit(2)
    except KeyboardInterrupt:
        print('INTERRUPTED_NO_SUCCESS_ASSUMED');raise SystemExit(130)
    except Exception:
        print('UNEXPECTED_FAILURE_NO_SUCCESS_ASSUMED');raise SystemExit(1)
    print(json.dumps(value,ensure_ascii=False))
