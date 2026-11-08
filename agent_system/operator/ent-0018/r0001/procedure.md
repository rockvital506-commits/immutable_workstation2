# Operator trial procedure r0001 — bounded Linux laboratory

## Статус и основание

ENT18r1: точное состояние согласования — в registry, не в этой процедуре.
Procedure и prompt версионируются в exact normative составе; запуск не создаёт
регистрацию или активацию автоматически. Не переносит hidden platform instructions/частную
архитектуру. Не предоставляет release/export/activation permissions.

## Операторский порядок

1. Выбрать одну bounded local_core_trial задачу с новым task UUID; критерии
   operator-trial-criteria-r0001: exact known source binding, согласованный
   incomplete trial, optional known query, сохранённый evidence. Поведение агента,
   полнота/свежесть/новая среда и positive permissions этими критериями не покрыты.
2. Обеспечить trusted Linux x86-64 installation/kernel/interpreter/namespace,
   прежнюю isolated hash-locked jsonschema среду и допустимость private данных.
   Для настоящего запуска требуется уже зарегистрированный exact ENT18r1.
   installed_profile() не выбирает latest и не создаёт собственный approval.
   Если регистрации нет — COORDINATOR_NOT_REGISTERED; не обходить.
3. Из отдельного доверенного основания закрепить source registry, весь известный
   ledger и exact artifacts returned profile. Сформировать ENT8r1 plan A с точными
   selection/context validate/agent_system.operator_trial. Не вычислять новые
   ожидания по неизвестному source как замену доверия. Artifact/selection exact;
   private истории/extra files автоматически не добавлять. Root A вне JSON.
4. Если нужен query, отдельно подготовить plan B/root B и literal operation/area.
   Даже одинаковые корни/plan bytes требуют отдельной acquisition; нет B —
   not_requested, не A-as-current. Не заявлять freshness из названия current.
5. Создать closed session по session.schema.json: purpose/criteria/profile fixed,
   task UUID, candidate pin, plan refs/B-query pairing. Закрепить raw UTF-8/LF
   session hash/native size извне. Передать documents={sha256: exact plan bytes}
   ровно по refs. Plan A/B с одинаковым SHA используют один document. Не принимать
   modules, child reports/callbacks, URI retrieval или commands из source.
6. Вызвать run_operator_trial(root_a,session_bytes,expected_session,documents,
   source_b_root=root_b) либо без B. Source и installation должны быть раздельны
   при недоверенном source; собственный trusted checkout допустим только lab.
   Preflight exception — остановка без claim/source. Не чинить ожидания автоматически.
7. Читать структурированный result/format_operator_result(result): actual counters,
   unknown acquisition total при exception, step statuses, false gates. Любой
   failed/blocked/unsupported/evidence_write_failed не переименовывать в success.
   При interruption/unknown exception sealed receipt может отсутствовать.
8. Сохранить отдельно успешный evidence receipt (run_id/index SHA/native size).
   Его external pin нужен replay. Local partial данные/failed trials не удалять
   и не перезаписывать автоматически. Существование index.json не proof успеха.
9. verify_evidence проверяет CAS; replay_operator_run выполняет отдельно semantic
   journal replay. Полный replay пока только для successful no-B/B journals;
   failed/blocked sealed journal — partial/not full replay, не permission.
   Source/trial namespace для replay не требуется; trusted immutable installation
   по-прежнему необходима. Не опрашивать live ledger/обновлять старое evidence.
10. Передать владельцу ограниченный итог: цель-label/task ID, статусы/counts/refs,
    что действительно проверено и что нет. Raw objects/private free text не
    публиковать; секреты автоматически не распознаются. Следующая новая known
    проверка — новый run/B plan, не правка sealed журнала.

Нет auto activation/export/reinstall; conditional registration отдельно от
lab execution. Public success в реальной новой среде этим draft не заявлен.


## Один documented lab client (только явно trusted own checkout)

После проверки exact installation/registry вызвать из approved isolated Python:

```sh
/home/user/.venv/immutable-agent-system/bin/python agent_system/operator/ent-0018/r0001/lab.py --trust-this-checkout
```

Путь к interpreter — пример локальной изолированной установки, не portable
абсолютный путь требования. Можно использовать свой verified isolated interpreter
с тем же hash-lock. Для no-B добавить --without-query. API:
run_trusted_lab(trust_this_checkout=True,with_query=True|False). Никакого /tmp
recipe как обязательной части интерфейса. CLI возвращает safe human report и
receipt/replay summary, не raw input maps; ошибки без автоматического traceback.

Flag — явное признание этого protected checkout доверенным input для lab,
**не** аутентификация произвольной новой директории/permission. Client не принимает
foreign source/root и не является discovery/pin generator для неизвестных данных.
Строятся closed A/B/session pins из выбранного доверенного namespace; caller
остаётся expectation authority. Выполняются один run entry и отдельный replay.
Кандидат ENT13r1 остаётся incomplete12/34; query export — только scoped query,
никакого экспорта/совместимого выпуска/активации. Без flag клиент останавливается.
