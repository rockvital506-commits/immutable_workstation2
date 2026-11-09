#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Запускает все тесты репозитория и сводит результат.

Код возврата: 0 — все тесты прошли, 1 — хотя бы один упал.
"""
from __future__ import annotations

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = ['test_repo.py', 'test_rules.py', 'test_stage42.py',
         'test_stage43.py', 'test_stage44.py', 'test_stage45.py',
         'test_stage46.py', 'test_stage47.py', 'test_stage7.py',
         'test_stage48.py', 'test_stage5.py',
         'test_stage6.py',
         'test_stage8.py',
         'test_stage9.py',
         'test_stage10.py',
         'test_navigation.py',
         'test_alternative.py',
         'test_bestiary.py',
         'test_ps1_lint.py',
         'test_agent_catalog.py',
         'test_agent_schema.py',
         'test_agent_reader.py',
         'test_agent_graph.py',
         'test_agent_events.py',
         'test_agent_plan_report.py',
         'test_agent_executor.py',
         'test_agent_bundle.py',
         'test_agent_work.py',
         'test_agent_work_practice.py',
         'test_agent_governance.py',
         'test_agent_candidate.py',
         'test_agent_permissions.py',
         'test_agent_permission_authority.py',
         'test_agent_authority_state.py',
         'test_agent_action_claim_model.py',
         'test_agent_transfer_preparation.py',
         'test_agent_inactive_binding.py',
         'test_agent_rule_universality.py',
         'test_agent_linked_meanings.py',
         'test_agent_core_meaning_coverage.py',
         'test_agent_mixed_governance.py',
         'test_agent_role_composition.py',
         'test_agent_component_semantic_review.py',
         'test_agent_universal_condition_coverage.py',
         'test_agent_block_condition_map.py',
         'test_agent_condition_loss_check.py',
         'test_agent_condition_rules.py',
         'test_agent_owner_acceptance.py',
         'test_agent_effectiveness_trial.py',
         'test_agent_transfer_closure.py',
         'test_agent_q1q2_decision.py',
         'test_agent_readiness_qualification.py',
         'test_agent_b4_review_harness.py',
         'test_agent_staging.py',
         'test_agent_trial_reader.py',
         'test_agent_known_views.py',
         'test_agent_capture.py',
         'test_agent_trial_capture.py',
         'test_agent_operator_foundation.py',
         'test_agent_operator_runner.py',
         'test_agent_operator_replay.py',
         'test_agent_operator_acceptance.py']


def main() -> int:
    results = []
    for name in TESTS:
        path = os.path.join(HERE, name)
        if not os.path.isfile(path):
            print(f'=== {name}: ФАЙЛ НЕ НАЙДЕН ===')
            results.append((name, 1))
            continue
        print(f'=== {name} ===')
        proc = subprocess.run([sys.executable, path], cwd=os.path.dirname(HERE))
        results.append((name, proc.returncode))
        print()

    print('=' * 60)
    failed = 0
    for name, code in results:
        mark = 'OK  ' if code == 0 else 'FAIL'
        print(f'  {mark} {name} (код {code})')
        if code != 0:
            failed += 1
    print('=' * 60)
    print(f'Тестов: {len(results)}, упало: {failed}')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
