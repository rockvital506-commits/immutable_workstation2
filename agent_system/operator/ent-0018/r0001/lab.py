"""Explicit trusted-checkout lab client. Not a foreign-source expectation generator."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import uuid

BASE=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent


class LabBlocked(Exception):
    pass


def run_trusted_lab(*,trust_this_checkout=False,with_query=True):
    """One bounded task on the operator's explicitly trusted installed checkout.

    Source and installation coincide ONLY in this acknowledged local lab. Pins
    derive from that trusted namespace, never an arbitrary discovered source.
    No registration/release/export/activation is performed by this client.
    """
    if trust_this_checkout is not True or type(with_query) is not bool:
        raise LabBlocked('EXPLICIT_TRUSTED_CHECKOUT_ACK_REQUIRED')
    runner=runpy.run_path(str(HERE/'run.py'));session=runpy.run_path(str(HERE/'session.py'))
    replay=runpy.run_path(str(HERE/'replay.py'))
    try:profile=runner['installed_profile']()
    except runner['OperatorBlocked'] as error:raise LabBlocked(error.code) from None
    ref=session['reference'];encode=session['encode']
    registry=runner['_installed']('catalog/registry.json')
    names=sorted((BASE/'catalog/approvals').iterdir())
    decisions=[dict(path='catalog/approvals/'+p.name,**ref(runner['_installed']('catalog/approvals/'+p.name))) for p in names]
    def plan():
        value=dict(schema_version='1',kind='validation_plan',plan_id=str(uuid.uuid4()),catalog_id=profile['catalog_id'],
                   execution_profile='linux-observed-set-5r3-6r3',expectation_authority='caller_supplied_not_authenticated',
                   context=dict(operation='validate',area='agent_system.operator_trial'),selection=profile['selection'],
                   registry=dict(path='catalog/registry.json',**ref(registry)),artifacts=profile['artifacts'],decisions=decisions)
        return encode(value)
    a=plan();b=plan() if with_query else None
    value=dict(schema_version='1',kind='operator_trial_session',profile='operator-trial-linux-r0001',task_id=str(uuid.uuid4()),
               purpose='local_core_trial',criteria_version='operator-trial-criteria-r0001',candidate=profile['candidate'],
               plan_a=ref(a),plan_b=ref(b) if b is not None else None,
               query=dict(operation='export',area='agent_system.transfer') if with_query else None)
    raw=encode(value);documents={ref(p)['sha256']:p for p in [a,b] if p is not None}
    try:result=runner['run_operator_trial'](BASE,raw,ref(raw),documents,source_b_root=BASE if with_query else None)
    except runner['OperatorBlocked'] as error:raise LabBlocked(error.code) from None
    summary=dict(operator_result=result,human_report=runner['format_operator_result'](result),replay=None)
    if result['evidence_sealed']:
        receipt=result['evidence']
        try:summary['replay']=replay['replay_operator_run'](receipt['run_id'],receipt['index'])
        except replay['ReplayBlocked']:raise LabBlocked('LAB_REPLAY_FAILED') from None
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Bounded local trial, not permission or activation')
    parser.add_argument('--trust-this-checkout',action='store_true',help='Explicitly trust this installed checkout as lab input')
    parser.add_argument('--without-query',action='store_true')
    args=parser.parse_args()
    try:value=run_trusted_lab(trust_this_checkout=args.trust_this_checkout,with_query=not args.without_query)
    except LabBlocked as error:
        print(str(error),file=sys.stderr);raise SystemExit(2)
    except KeyboardInterrupt:
        print('LAB_INTERRUPTED_NO_SUCCESS_ASSUMED',file=sys.stderr);raise SystemExit(130)
    except Exception:
        print('LAB_UNEXPECTED_FAILURE_NO_SUCCESS_ASSUMED',file=sys.stderr);raise SystemExit(1)
    print(value['human_report'],end='')
    print(json.dumps(dict(evidence=value['operator_result'].get('evidence'),replay=value['replay']),ensure_ascii=False))
    ok=value['operator_result']['status'].startswith('trial_checked_') and value['replay'] and value['replay']['full_replay']
    raise SystemExit(0 if ok else 1)
