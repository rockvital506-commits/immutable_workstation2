"""I3 foundation only: closed session/plan validation, no source I/O or run entry."""
import copy
import hashlib
import json
from pathlib import Path
import runpy

BASE=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
LIMIT=16*1024*1024
PINS={'catalog/contracts/agent_system/ent-0001/r0001.md': {'sha256': '684e18cc01dc6b1ffd66899615df03b01e756f40f1354f3ac82a81563a944773', 'size_bytes': 7564}, 'catalog/contracts/agent_system/ent-0002/r0003.md': {'sha256': 'bfdea24314d9f5b26cd54ddaa41fe9aea9843c0f669417c040c1c80991188a1a', 'size_bytes': 17780}, 'specification/ent-0003/r0002/catalog-base.schema.json': {'sha256': '42fab3c453930ad9128b2b422837b82d84db9ed6092872765bd7fe1ffaf9a820', 'size_bytes': 8696}, 'specification/ent-0003/r0002/usage.md': {'sha256': 'a8e6c818ec4bda9eb4d38b3b9abb8ec9e3d694a42329771109931bbc8c5c6ceb', 'size_bytes': 9053}, 'validation/ent-0004/r0002/verify.py': {'sha256': '1523ca399a9aee8f89656591b62e1d776504385fe025131c818c694ebb32aedf', 'size_bytes': 10872}, 'validation/ent-0004/r0002/requirements-linux-cp311.lock': {'sha256': '4f0eda8261647c9bc18d2f013ef914737290e20c6a82de15f476108b6a528e71', 'size_bytes': 746}, 'validation/ent-0004/r0002/usage.md': {'sha256': '78807c10e4ad843472a1413df661c27cdbbd92a889446a000fbc1e9566e1d369', 'size_bytes': 7567}, 'adapters/ent-0005/r0003/reader.py': {'sha256': '0ddfb68d81eaf9e3ba56ca20b909462958b8e9de938d230a02d3a14e8b76fc7f', 'size_bytes': 15565}, 'adapters/ent-0005/r0003/verify.py': {'sha256': '3a8faf2098e99433223678f2dee92e94af3b511ccc946998024e98c943e55336', 'size_bytes': 22384}, 'adapters/ent-0005/r0003/usage.md': {'sha256': '489b9247257472d69ec0266a031edcac09d38e00c117de627a3a38d837262f14', 'size_bytes': 12063}, 'validation/ent-0006/r0003/check.py': {'sha256': 'd94e2c85c2bd40ff31b5d7edd2f0c9755cf5eb3ce6ab42488aeaff4feb8c275c', 'size_bytes': 12042}, 'validation/ent-0006/r0003/verify.py': {'sha256': '9a76cb7cb7d6bb5c5aefdba003cf9c57979ae2f3f9d626dd6e2aeb54ee674e51', 'size_bytes': 18332}, 'validation/ent-0006/r0003/usage.md': {'sha256': '89b80b152f5651bdf6ba1880b24f7175a0e7e2c9fa9915e2b306993204d9bff3', 'size_bytes': 13351}, 'specification/ent-0007/r0001/decision-events.schema.json': {'sha256': '4cce54eaff0d12e1e59a4aeb0eb1dd9f0f0b951f43968317c70adb7c714005c1', 'size_bytes': 12322}, 'specification/ent-0007/r0001/events.py': {'sha256': '26a7dee29f5f5196fd458da90246f343035f2843bed5434f2e71340abb0eaabe', 'size_bytes': 11016}, 'specification/ent-0007/r0001/verify.py': {'sha256': 'fca460f867777250da0348845bbedc1cc6804a57988abfb1c50f6db32dc18378', 'size_bytes': 13994}, 'specification/ent-0007/r0001/usage.md': {'sha256': 'ddaa2074aa5dfe6595f95b24f0e937871a2430be84f9a2c416f87d5d2974b4df', 'size_bytes': 10376}, 'specification/ent-0008/r0001/validation-plan.schema.json': {'sha256': 'e53e11315ebe54566edc5a395e7c4eee57cb82bdac86f9573feed57a0602664b', 'size_bytes': 3590}, 'specification/ent-0008/r0001/validation-run-report.schema.json': {'sha256': '7dece17f75d695484b2814c89f17f4e1623f6fec033d24c92953c740540da8bc', 'size_bytes': 15972}, 'specification/ent-0008/r0001/verify.py': {'sha256': '7196efe0f6b59f74ba791f80f497ce827d517d344e2c84556991db2f7f54a026', 'size_bytes': 14770}, 'specification/ent-0008/r0001/usage.md': {'sha256': 'f775530264c1fa0a76b368a264ce4b343405b6b7b6b0e1a39002e97ea3ea0c65', 'size_bytes': 14765}, 'validation/ent-0009/r0001/execute.py': {'sha256': '1a4340e4dfe4b01841702ffcb88a65caa0f8ccc05d6adce03c1e4b3d2e6ebdf9', 'size_bytes': 12955}, 'validation/ent-0009/r0001/verify.py': {'sha256': 'a082eeb938a62f4005d83f3664d027c403055c1f7851ff73a3a6517a09f41268', 'size_bytes': 11721}, 'validation/ent-0009/r0001/usage.md': {'sha256': '6c9ed888e4d5538a53521fa4406ce6df50e287718d2c5cc4545882432173425f', 'size_bytes': 11256}, 'validation/ent-0009/r0002/execute.py': {'sha256': 'e28329880072ce4a13b4306bfa5c423860ad8e959147b9653f9ed13650be20ba', 'size_bytes': 14202}, 'validation/ent-0009/r0002/verify.py': {'sha256': '54a77f771b518a8af9a0d430b03c49e4f32182a180ee71981970ca550dd74296', 'size_bytes': 19812}, 'validation/ent-0009/r0002/usage.md': {'sha256': '9e8c100d8126c1cda232ddd169a90a95844e62f896bac9b415102c0deb0522c0', 'size_bytes': 7482}, 'validation/ent-0010/r0001/bundle.py': {'sha256': 'edfe812458cce41dbcbcdffa6bd568a57ac287506969cc315e2d8a8a999eba08', 'size_bytes': 10655}, 'validation/ent-0010/r0001/verify.py': {'sha256': '6056350c72c9b94a76d9a7c86cff9890947ea9261f3e5e4936ef4053ca05e544', 'size_bytes': 10526}, 'validation/ent-0010/r0001/usage.md': {'sha256': '8b9d39a9824ce41bb68e3aeecb2bffad2b272d556c95c2148ac8ded6cf19d6d1', 'size_bytes': 12047}, 'protocols/ent-0011/r0001/work.md': {'sha256': '06923c52d5e7311556e8276cea473af71284f985476f970dced83d085a70cbb4', 'size_bytes': 22549}, 'protocols/ent-0011/r0001/scenarios.json': {'sha256': '441d2505e822cdbf37d534a17b4b89c32a54853ff4442d9e019104c0b3ea5f50', 'size_bytes': 12480}, 'protocols/ent-0011/r0001/verify.py': {'sha256': '3984ddb43a4ac7b45694608b891ac17e331bfc3fb8a624bc716bbd0ded834348', 'size_bytes': 6777}, 'protocols/ent-0012/r0001/governance.md': {'sha256': '2402346a739436871ba22b90306cf86c3836eb54f3ddb3801bbfa78398bbc0f9', 'size_bytes': 21236}, 'transfer/ent-0012/r0001/prompt.md': {'sha256': '8ce3983ed99058bfa1d1c559142fd884c60bb92b27331b58d2759e47b6e5866a', 'size_bytes': 4825}, 'transfer/ent-0012/r0001/prepare.py': {'sha256': 'ec2f904f93b15ed234f19b21a87d6a0e8cebc02c538c693c268241dd2420785a', 'size_bytes': 5468}, 'protocols/ent-0012/r0001/verify.py': {'sha256': '82acb918e2b4f99171bc421b3fd028fbb0d0eefef68626fd7adccf65399d9d8c', 'size_bytes': 8946}, 'candidates/ent-0013/r0001/candidate.json': {'sha256': '3a9231b668cc63b1d4a60d032dfe49fb61223a3b2c81b3fd79a42a1ee1b7f428', 'size_bytes': 69062}, 'candidates/ent-0013/r0001/check.py': {'sha256': 'f185875d034bc61697d926c45eedbb4764d281ccb96a8dca8cc7488dea42a660', 'size_bytes': 12871}, 'candidates/ent-0013/r0001/verify.py': {'sha256': '0292c5c700714d7db0cbf27b2e76a56d9d0f1e69e3f19d3488527313dda8a86e', 'size_bytes': 8484}, 'candidates/ent-0013/r0001/usage.md': {'sha256': '080abfa5143db3920ed9eec80380e21e31ac43f99fb8236dc678fd4c009cafca', 'size_bytes': 15101}, 'permissions/ent-0014/r0001/proposal.schema.json': {'sha256': '142a2a628ed5125229ac48a9e1d6768f62cf21ff138cc12a83fa1c220369ac39', 'size_bytes': 4320}, 'permissions/ent-0014/r0001/check.py': {'sha256': '18d47b251a0709ebd021a9473553c7faeb12b8e977d90ed41b20899dde9df1d2', 'size_bytes': 7333}, 'permissions/ent-0014/r0001/verify.py': {'sha256': 'd94ce36432537ce5e13f4d059fc6f0a0772c0e8fc6cbfb19734aa59e1937ed1e', 'size_bytes': 8170}, 'permissions/ent-0014/r0001/usage.md': {'sha256': '3ba366a47b00d576bfb1254dee15404b6e3c245437f3097be301907326eb2fd1', 'size_bytes': 15107}, 'staging/ent-0015/r0001/stage.py': {'sha256': '2cf729cc03e65a4b28e5dbf1afac99de305c75b3422a08181b48c43392f3b9a0', 'size_bytes': 9215}, 'staging/ent-0015/r0001/verify.py': {'sha256': '46c3101cc2b6dd57b879e5e7aa1f9441943b74619ab6875f34bc5cc6d7a20a71', 'size_bytes': 13661}, 'staging/ent-0015/r0001/usage.md': {'sha256': '6e0bb1c173921c269d11da522e1ef290b6995e27cfc6857e16b849445151c14a', 'size_bytes': 14234}, 'staging/ent-0016/r0001/read.py': {'sha256': '942839d7e292cd7f744346f27693cd4e7cc573961d1599f66df4c566548545cf', 'size_bytes': 9691}, 'staging/ent-0016/r0001/verify.py': {'sha256': 'f06e8a76da5f2c9005934d47b0f439b4b8751a0bc50a921bd773bbbd6305967f', 'size_bytes': 11917}, 'staging/ent-0016/r0001/usage.md': {'sha256': '3dccac0b1705a6a9723d8d72228733010c710a2e3a012ad84c1412b3e6210251', 'size_bytes': 12738}, 'staging/ent-0016/r0002/read.py': {'sha256': '3d5377fa1884631e88e3da51abb44222639809be95695f74ca9fa912543b1e33', 'size_bytes': 10620}, 'staging/ent-0016/r0002/verify.py': {'sha256': '3738c49bf88078c5b1e2215e6f107fd1efd00c7da0b7b7bc52281424404035ea', 'size_bytes': 18927}, 'staging/ent-0016/r0002/usage.md': {'sha256': '6b189d32946b6fa33ac8fcf74546262cb703602e9244a5f8a461b6425e382d15', 'size_bytes': 7007}, 'validation/ent-0017/r0001/compare.py': {'sha256': '65cee528ca1e9ab3594f43476ad21c89ac1ce44d40e6511724ec3c7555dcc95c', 'size_bytes': 9453}, 'validation/ent-0017/r0001/verify.py': {'sha256': 'eaeeafe2f135f5a325ee4f1dd6d49cc9fd80707aaff74ba6efee1193d1208aa3', 'size_bytes': 10622}, 'validation/ent-0017/r0001/usage.md': {'sha256': '401ff21a4d3a449ccb81bc865701a4f84abcb8232527e10a230c83e5a9306ad9', 'size_bytes': 11698}}


class SessionBlocked(Exception):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def reference(raw):return dict(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw))


def encode(value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
    if len(raw)>LIMIT:raise SessionBlocked('DOCUMENT_LIMIT')
    return raw


def _pin(raw,expected):
    if (type(raw) is not bytes or len(raw)>LIMIT or type(expected) is not dict
            or set(expected)!={'sha256','size_bytes'} or type(expected['size_bytes']) is not int
            or type(expected['sha256']) is not str or reference(raw)!=expected):
        raise SessionBlocked('INPUT_REFERENCE_MISMATCH')


def _tools():
    # Fixed installed dependency closure only, never modules selected by source.
    for path,expected in PINS.items():
        with (BASE/path).open('rb') as f:raw=f.read(expected['size_bytes']+1)
        if reference(raw)!=expected:raise SessionBlocked('INSTALLED_PROFILE_CHANGED')
    module=runpy.run_path(str(BASE/'validation/ent-0009/r0002/execute.py'))
    try:parse,validators,_,_,_=module['_load']()
    except module['PlanBlocked'] as error:raise SessionBlocked(error.code) from None
    from jsonschema import Draft202012Validator
    schema=json.loads((HERE/'session.schema.json').read_bytes())
    Draft202012Validator.check_schema(schema)
    return module,parse,validators[0],Draft202012Validator(schema)


def validate_session(session_bytes,expected_session,documents,profile,*,has_source_b):
    """Internal foundation API; profile MUST come from trusted installed composition.

    Not an operator entry: no source roots, claims, writes, acquisition or grants.
    The coordinator, not the session, supplies exact profile metadata.
    """
    try:
        _pin(session_bytes,expected_session)
        module,parse,plan_validator,validator=_tools()
        if (not session_bytes.endswith(b'\n') or session_bytes.endswith(b'\n\n')
                or b'\r' in session_bytes):raise SessionBlocked('SESSION_SERIALIZATION')
        session=parse(session_bytes)
        if not validator.is_valid(session):raise SessionBlocked('SESSION_SCHEMA')
        if type(session['candidate']['size_bytes']) is not int:raise SessionBlocked('SESSION_REFERENCE_TYPE')
        if type(has_source_b) is not bool:raise SessionBlocked('B_PAIRING')
        if (session['plan_b'] is not None)!=has_source_b:raise SessionBlocked('B_PAIRING')
        if type(documents) is not dict:raise SessionBlocked('DOCUMENT_SET')
        expected=[session['plan_a']]+([session['plan_b']] if has_source_b else [])
        if set(documents)!={r['sha256'] for r in expected}:raise SessionBlocked('DOCUMENT_SET')
        # Copy mappings before passing downstream; bytes are immutable.
        documents=dict(documents)
        for r in expected:_pin(documents[r['sha256']],r)
        if (type(profile) is not dict or set(profile)!={'catalog_id','selection','artifacts','candidate'}
                or session['candidate']!=profile['candidate']):raise SessionBlocked('CANDIDATE_PROFILE')
        plans=[]
        for r in expected:
            plan=module['_plan'](documents[r['sha256']],copy.deepcopy(r),parse,plan_validator)
            if (plan['catalog_id']!=profile['catalog_id'] or plan['selection']!=profile['selection']
                    or module['_records'](plan['artifacts'])!=module['_records'](profile['artifacts'])
                    or plan['context']!={'operation':'validate','area':'agent_system.operator_trial'}):
                raise SessionBlocked('PLAN_PROFILE_MISMATCH')
            plans.append(plan)
        return dict(session=copy.deepcopy(session),plans=plans,documents=documents)
    except SessionBlocked:raise
    except (OSError,ImportError,ValueError,TypeError,KeyError,RuntimeError,RecursionError,AttributeError):
        raise SessionBlocked('SESSION_OR_INSTALLATION_INVALID') from None
    except Exception as error:
        if 'module' not in locals() or not isinstance(error,module['PlanBlocked']):raise
        raise SessionBlocked(error.code) from None
