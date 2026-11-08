# Исполнитель плана с контролируемой передачей исходных bytes

## Сущность, источник и статус

ENT-0009 r0002 — check, область agent_system.validation. Полный состав:
execute.py, verify.py, usage.md. Depends_on: ENT-0008 r0001 и ENT-0009 r0001
(последняя нужна regression parity verifier, не runtime worker). Supersedes
ENT-0009 r0001 не перенаправляет старые pins, не отзывает прежнее согласование. Источники:
задание/условное делегирование владельца, проект M1 D05–D07 и реализация r0001.
Точное состояние согласования — в едином registry, не в этом описании.
Новый producer должен быть закреплён caller отдельно по exact revision/artifacts.

## Контракт и применение

```python
execute_plan(root, plan_bytes, expected_plan)  # report_bytes, documents
capture_plan(root, plan_bytes, expected_plan)  # report_bytes, documents, capture
```

Expected_plan — обязательные внешние {sha256, size_bytes}, не вычисленные из
непроверенного входа. Plan — ENT8r1 strict JSON/LF, прежний execution_profile
linux-observed-set-5r3-6r3. Этот profile описывает reader/checker boundary,
**не** producer r1/r2 authenticity. Нельзя определять producer по этому полю.
Root — отдельный trusted caller input, не команда/URI/поле плана.

Обе поверхности используют один _worker, ровно один вызов read_set на прошедший
preflight run. Preflight failure — PlanBlocked без source acquisition. Нет вызова
r1 с runtime patch, второго read_set или pathname reread после проверки.

Worker проверяет план/installed pins, получает source set, проверяет все maps/
refs/inventory, registry CID, binding/context/selection/known restrictions и
полный final envelope. Только **после** final Schema и сериализации report,
при passed_known_inputs, capture имеет вид:

```python
{'registry': bytes, 'artifacts': {relative_path: bytes},
 'decisions': {relative_path: bytes}}
```

Registry исключён из artifacts. Mappings — свежие dict, values — immutable bytes
той же acquisition. Передача не читает source заново. Documents содержит только
исходный plan и child evidence (SHA→bytes); capture отдельно от legacy schema.
execute_plan возвращает ровно два прежних поля, не source maps. Source files не
пишутся; operation=export/activate в плане только проверяемый контекст запретов.

Для failed/blocked_known_scope/unsupported completed run capture=None, даже если
acquisition успешен. Preflight/final serialization/Schema failure и interruption
могут вообще не вернуть результат. Caller не должен подставлять прошлый capture
или извлекать PASS из partial evidence. Полный offline replay failed binding без
capture не обещается. Успешный полный capture пригоден для прежнего ENT10 semantic
replay при сохранении всех documents/payloads; это не проверка capture interface
или producer authenticity самим ENT10.

## Trust, пределы и приватность

21 installed artifact pin сохранён из r1; helpers загружаются из фиксированного
installed дерева, не source. Trusted installation/interpreter/kernel/proc должны
быть защищены от конкурентной записи source/атакующим. Hash-before-runpy не даёт
атомарного исполнения при writable installation. Новых dependencies нет: прежний
изолированный jsonschema с обязательными зависимостями/hash-lock.

Source adapter — Linux x86-64/openat2, one root capability, NOFOLLOW/BENEATH/
NO_SYMLINKS/NO_XDEV и прежние limits/guards. Наблюдения mutable B не атомарны;
reader guard readbacks — не дополнительные read_set и не обещание одного syscall.
Сохраняются 16 MiB/document/file, 10000 source entries, 64 MiB/source set. Capture
увеличивает время жизни raw bytes в памяти; глобальная RAM/CPU quota не заявлена.

Возврат raw source maps расширяет privacy surface. Не печатать capture, не
публиковать/коммитить/экспортировать автоматически. Private local persistence,
allowlist, final handoff binding и полный operator journal — обязанности будущего
coordinator/caller, **не реализованные этой функцией**. Универсального обнаружения
секретов нет. Caller проверяет refs при сохранении/дальнейшей передаче.

Overall_admission=not_evaluated, transition_allowed=false, legacy not_checked
сохраняется целиком. Known success не доказывает freshness/global completeness,
source/owner authentication, реальное поведение, совместимость среды или
разрешения выпуска/export/activation. Same bytes не являются подписью.

## Обоснование и проверки

Выбран общий worker вместо двойной acquisition/перехвата r1: один источник bytes
для отчёта и следующего шага, отсутствие повторной гонки между проверкой и capture.
Плюсы: reuse прежнего стека/схемы, metadata compatibility, явный отказ вместо
partial handoff. Минусы: новая immutable revision/поверхность, in-memory dict
copies и удержание raw bytes; caller обязан обеспечить приватность/проверку.
Риск дальнейшего misuse остаётся; coordinator должен отдельно проверять handoff.
Скорость/универсальная безопасность/полнота не объявляются доказанными benchmark.

verify.py: 30 прежних metadata сценариев, те же 30 через capture с дополнительными
assertions withholding/exact maps, 14 handoff случаев. Среди последних: single
acquisition, r1 semantic parity кроме run_id, ownership, source change после
binding без reread, late failures, unsupported, отсутствие reuse/write и offline
semantic replay. Synthetic fixtures не являются практикой поведения агента или
разрешением реального выпуска. Автоматический adapter/coordinator здесь не создан.
