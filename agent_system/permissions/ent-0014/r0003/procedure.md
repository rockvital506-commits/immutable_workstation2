# Local authority state procedure r0003

1. Проверить exact installation/approved isolated interpreter и поддержанный Linux
   profile. Обеспечить owner-controlled namespace вне Git и независимое хранение
   external head receipt/high-water. Не брать authority/pin из foreign source.
   Explicit trust flag — acknowledgment, не аутентификация и не release grant.
2. Создать store только для явно выбранной authority области; не обнулять known
   negatives новым UUID. create_store возвращает UUID/head/generation0. Сохранить
   receipt отдельно; history/bootstrap/constraints новой среды согласуются отдельно.
3. Перед import иметь конкретное согласие owner на **exact event** и разрешение
   хранить source. Подготовить full quote/summary+source_id/basis_id, event ref и
   subject. Не превращать «продолжай»/выбор A/implementation approval в grant.
   Operator вручную проверяет смысл/происхождение; код этого не делает.
4. Открыть AuthorityStore с внешним expected_head и explicit True. При busy/stale/
   unsupported/unsafe/partial stop; не удалять lock/частичные данные и не брать
   найденный новый head за автоматически одобренный. Нет lost-receipt recovery API.
5. import_assent получает отдельные bytes/pins и explicit attest_exact_owner_assent.
   Проверить безопасный receipt; source bytes остаются private. Ошибочный source/
   subject/identity/stream не корректировать in-place. Все прежние records
   сохраняются; известные negatives не фильтруются. Сохранить новый external head.
6. Для проверки получить context_packet только внутри protected caller, составить
   новый exact request ID/current context/generation/subject/grant. check_once
   сохраняет result и меняет head. Отрицательный result — не разрешение действия.
   Однократность только request recording: action_claim_created=false, action flags
   false. Для фактического перехода этих API недостаточно, даже при recognition.
7. Закрыть handle/FD lock, reopen с новым expected head и проверить safe summary.
   Caller не должен менять internal attributes/mutable inputs одновременно с
   операцией. Private source/packet не печатать/не экспортировать; только pins/
   UUID/counts/static states. Для actual composition использовать native r2 guard;
   current incomplete ENT13 не может выпускаться/экспортироваться как полный.
8. При failure сохранить diagnostic code/полученный receipt если он был/partial
   данные. Handle после ошибки не переиспользуется; неизвестный outcome не PASS.
   Recovery/adoption/retention policy — отдельное действие с основанием, не auto
   rollback/delete. Предел поколения/объёма не снимается стиранием истории.

## Один documented empty-authority lab

```sh
/home/user/.venv/immutable-agent-system/bin/python agent_system/permissions/ent-0014/r0003/state.py --trust-owner-controlled-namespace
```

Interpreter path — локальный пример прежнего approved hash-lock, не portable
абсолютный путь. API: run_empty_lab(trust_owner_controlled_namespace=True).
Без flag — отказ до local writes. Lab создаёт новый private store, **не** importer
реального согласия:0events/0assents; один valid check неизвестного grant получает
GRANT_REFERENCE, записывается и проверяется reopen. Печатаются safe receipt/result/
summary, не raw source/absolute paths. Никаких реальных approvals/grants/permission
claims, перемещения файлов/activation. Это проверка состояния/отрицательного пути,
не воспроизведение уже имеющегося owner разрешения или готовности комплекта.
UUID/head pin сохранить отдельно. Нет обязательного /tmp recipe или foreign-root
pin generator. Same trusted installation ≠ bootstrap неизвестной новой среды.
