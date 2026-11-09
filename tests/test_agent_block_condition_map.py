#!/usr/bin/env python3
"""Exhaustive block inventory with author disposition; not NLP proof or independence."""
import copy
import hashlib
import json
import os
import re
from pathlib import Path
import runpy
import unittest

ROOT=Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
PREV=runpy.run_path(str(ROOT/'tests/test_agent_role_composition.py'))
FIXTURE='research/51-agent-system-block-condition-map.json'
MAP='research/51-agent-system-block-map.md'
FIXTURE_SHA='d77e8ff352b3e011b2f637ea3d010a490adeaf935e3530a95b3179ab60c7fbe8'
MAP_SHA='ddce65c679e45e847ebd7d1bb3453d8970ca5d97a0e97ec396ce3c15cb2b1d87'
SHA50='a57ff87a3446c5364d2948fbd65c2e81686b172dde090a1a7396880f38446cc5'
SHA50P='345090331e0601a7657e7231468b9d652591ff8481a6755715bc827f9d835eb4'
BLOCK=re.compile(r'(?s)(?:\A|\n\s*\n)(.*?)(?=\n\s*\n|\Z)')
DISP={'transferable_condition','local_implementation','descriptive_or_evidence'}


def norm(text):
    return re.sub(r'\s+',' ',text).strip()


def live_blocks(root=ROOT):
    inputs=PREV['load_basis'](root);draft=PREV['compose'](*inputs)
    out=[]
    for di,ref in enumerate(draft['semantic_review_queue'],1):
        text=(root/'agent_system'/ref['path']).read_text();bi=0
        for m in BLOCK.finditer(text):
            lines=m.group(1).split('\n')
            while lines and (lines[0].startswith('#') or not lines[0].strip()):lines.pop(0)
            if not lines or lines[0].startswith('```') or lines[0].lstrip().startswith('|'):continue
            b=norm('\n'.join(lines))
            if len(b)<40:continue
            out.append(dict(doc=di,block=bi,path='agent_system/'+ref['path'],chars=len(b),
                            block_sha256=hashlib.sha256(b.encode()).hexdigest()))
            bi+=1
    return out


def render(ledger):
    st=ledger['stats']
    lines=['# Карта смысловых блоков: роль каждого абзаца','',
     '**Производный исследовательский документ. Не активный профиль, не выпуск, не разрешение.**','',
     f"26документов/{st['blocks']}блоков: {st['transferable_condition']} несут переносимые условия, "
     f"{st['local_implementation']} — локальные детали, {st['descriptive_or_evidence']} — описание/свидетельства.",
     '«T» = переносимое условие с привязкой к типу F01–F21; «L» = локальная деталь конкретной реализации;',
     '«D» = описание состава/процедуры/свидетельства. Разметка — авторская, не независимая проверка.','']
    cur=None
    for r in ledger['blocks']:
        if r['path']!=cur:
            cur=r['path'];lines+=['',f"## {cur}",'','| Блок | Роль | Тип/причина |','|---:|---|---|']
        if r['disposition']=='transferable_condition':val='T';why=', '.join(r['families'])
        elif r['disposition']=='local_implementation':val='L';why=r['reason']
        else:val='D';why=r['reason']
        lines.append(f"| {r['block']} | {val} | {why} |")
    return '\n'.join(lines)+'\n'


def load(root=ROOT):
    raw=(root/FIXTURE).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=FIXTURE_SHA:raise ValueError('FIXTURE_PIN')
    ledger=json.loads(raw)
    for ref in (ledger['predecessor']['ledger'],ledger['predecessor']['preview']):
        if hashlib.sha256((root/ref['path']).read_bytes()).hexdigest()!=ref['sha256']:raise ValueError('PREDECESSOR_PIN')
    if ledger['predecessor']['ledger']['sha256']!=SHA50 or ledger['predecessor']['preview']['sha256']!=SHA50P:
        raise ValueError('PREDECESSOR_KNOWN')
    return ledger,json.loads((root/ledger['predecessor']['ledger']['path']).read_bytes())


def validate(ledger,l50):
    if ledger['status']!='block_inventory_with_author_disposition_not_independent_semantics':raise ValueError('STATUS')
    blocks=ledger['blocks'];live=live_blocks()
    if len(blocks)!=303 or len(live)!=303:raise ValueError('COUNT')
    if [(b['doc'],b['block'],b['path'],b['block_sha256'],b['chars']) for b in blocks]!=[(l['doc'],l['block'],l['path'],l['block_sha256'],l['chars']) for l in live]:
        raise ValueError('BLOCK_BINDING')
    fams={f['id'] for f in l50['families']}
    if {f['id'] for f in ledger['families']}!=fams or len(fams)!=21:raise ValueError('FAMILY_SET')
    seen=set()
    for b in blocks:
        key=(b['doc'],b['block'])
        if key in seen:raise ValueError('DUPLICATE')
        seen.add(key)
        if b['disposition'] not in DISP:raise ValueError('DISPOSITION')
        if b['disposition']=='transferable_condition':
            if not b['families'] or not set(b['families'])<=fams:raise ValueError('FAMILY_REF')
            if b['reason']!='universal_condition_traced_to_family':raise ValueError('T_REASON')
        else:
            if b['families']:raise ValueError('NON_T_FAMILY')
            if not b['reason'].strip() or b['reason']=='universal_condition_traced_to_family':raise ValueError('NON_T_REASON')
    from collections import Counter
    c=Counter(b['disposition'] for b in blocks);st=ledger['stats']
    if (st['blocks'],st['transferable_condition'],st['local_implementation'],st['descriptive_or_evidence'])!=(303,c['transferable_condition'],c['local_implementation'],c['descriptive_or_evidence']):
        raise ValueError('STATS')
    used={f for b in blocks for f in b['families']}
    if used!=fams or st['families_used']!=21:raise ValueError('FAMILY_COVERAGE')
    if st['documents']!=26 or st['blocks_without_family']!=c['local_implementation']+c['descriptive_or_evidence']:
        raise ValueError('STATS_DOCS')
    for key in ('independent_review_performed','actual_behavior_verified','full_semantic_equivalence'):
        if st[key] is not False:raise ValueError('FALSE_CLAIM_'+key)
    if any(ledger['permission_gates'].values()):raise ValueError('GATE')
    if not ledger['residual']['not_claimed'] or len(ledger['residual']['not_claimed'])<4:raise ValueError('RESIDUAL')
    m=ledger['method']
    if m['enumeration']!='all_prose_blocks_including_paragraphs_after_headings':
        raise ValueError('METHOD')
    if 'missed' not in m['first_pass_undercoverage']:raise ValueError('METHOD_HONESTY')
    if 'min 40' not in m['extractor']:raise ValueError('METHOD_EXTRACTOR')
    if 'not a classifier' not in m['cue_pass']:raise ValueError('METHOD_CUE')
    # every source anchor from the previous pass must fall inside a transferable block of its family
    docs={}
    for b in live:
        docs.setdefault(b['path'],b['doc'])
    for f in l50['families']:
        for a in f['anchors']:
            doc=docs[a['path']];text=(ROOT/a['path']).read_text()
            hit=None;bi=0
            for mm in BLOCK.finditer(text):
                lines=mm.group(1).split('\n')
                while lines and (lines[0].startswith('#') or not lines[0].strip()):lines.pop(0)
                if not lines or lines[0].startswith('```') or lines[0].lstrip().startswith('|'):continue
                bb=norm('\n'.join(lines))
                if len(bb)<40:continue
                if norm(a['needle']) in bb:hit=bi
                bi+=1
            if hit is None:raise ValueError('ANCHOR_LOST')
            row=next(b for b in blocks if b['doc']==doc and b['block']==hit)
            if row['disposition']!='transferable_condition':raise ValueError('ANCHOR_NOT_TRANSFERABLE')
            if f['id'] not in row['families']:raise ValueError('ANCHOR_FAMILY')
    return True


def verify():
    try:
        ledger,l50=load();validate(ledger,l50)
        return render(ledger)==(ROOT/MAP).read_text()
    except ValueError:return False


class BlockMapTests(unittest.TestCase):
    def setUp(self):self.ledger,self.l50=load()

    def test_pins_and_exhaustive_enumeration(self):
        self.assertEqual(MAP_SHA,hashlib.sha256((ROOT/MAP).read_bytes()).hexdigest())
        self.assertTrue(verify())
        self.assertEqual(303,len(self.ledger['blocks']))
        self.assertEqual(26,self.ledger['stats']['documents'])

    def test_every_block_has_one_role(self):
        roles={b['disposition'] for b in self.ledger['blocks']}
        self.assertTrue(roles<=DISP)
        self.assertEqual({'transferable_condition','local_implementation'},roles)
        self.assertEqual(200,self.ledger['stats']['transferable_condition'])
        self.assertEqual(103,self.ledger['stats']['local_implementation'])
        self.assertEqual(0,self.ledger['stats']['descriptive_or_evidence'])

    def test_all_families_survive_the_inventory(self):
        self.assertEqual(21,self.ledger['stats']['families_used'])
        used={f for b in self.ledger['blocks'] for f in b['families']}
        self.assertEqual({f['id'] for f in self.l50['families']},used)

    def test_previous_anchors_remain_transferable(self):
        anchors=[(a['path'],a['needle'],f['id']) for f in self.l50['families'] for a in f['anchors']]
        self.assertEqual(53,len(anchors))
        self.assertTrue(all(a[0].startswith('agent_system/') for a in anchors))
        self.assertEqual(53,len({(a[0],a[1]) for a in anchors}))

    def test_local_details_are_named_not_deleted(self):
        reasons={b['reason'] for b in self.ledger['blocks'] if b['disposition']=='local_implementation'}
        for reason in ('limits','schema_fields','evidence_test','fs_details','design_rationale'):
            self.assertIn(reason,reasons)
        self.assertTrue(self.ledger['residual']['statement'])

    def test_no_false_qualification(self):
        self.assertFalse(self.ledger['stats']['independent_review_performed'])
        self.assertFalse(self.ledger['stats']['actual_behavior_verified'])
        self.assertFalse(self.ledger['stats']['full_semantic_equivalence'])
        self.assertFalse(any(self.ledger['permission_gates'].values()))
        self.assertIn('not independent review',self.ledger['residual']['statement'])

    def test_map_is_reproducible(self):
        self.assertEqual(render(self.ledger),(ROOT/MAP).read_text())
        text=(ROOT/MAP).read_text()
        self.assertIn('не независимая проверка',text)

    def test_mutations_rejected(self):
        def mutate(fn):
            ledger=copy.deepcopy(self.ledger);fn(ledger)
            with self.assertRaises(ValueError):validate(ledger,self.l50)
        mutate(lambda x:x['blocks'].pop())
        mutate(lambda x:x['blocks'].append(copy.deepcopy(x['blocks'][0])))
        mutate(lambda x:x['blocks'][0].__setitem__('block_sha256','0'*64))
        mutate(lambda x:next(b for b in x['blocks'] if b['disposition']=='transferable_condition')['families'].append('F99'))
        mutate(lambda x:next(b for b in x['blocks'] if b['disposition']=='transferable_condition').__setitem__('families',[]))
        mutate(lambda x:next(b for b in x['blocks'] if b['disposition']=='local_implementation').__setitem__('families',['F01']))
        mutate(lambda x:next(b for b in x['blocks'] if b['disposition']=='local_implementation').__setitem__('reason',''))
        mutate(lambda x:x['stats'].__setitem__('transferable_condition',181))
        mutate(lambda x:x['stats'].__setitem__('independent_review_performed',True))
        mutate(lambda x:x['stats'].__setitem__('full_semantic_equivalence',True))
        mutate(lambda x:x['permission_gates'].__setitem__('release_allowed',True))
        mutate(lambda x:x['method'].__setitem__('cue_pass','classifier'))
        mutate(lambda x:x['residual'].__setitem__('not_claimed',[]))


if __name__=='__main__':unittest.main(verbosity=2)
