# agent_system — состояние внедрения

Созданы компоненты каталога, не полноценный выпуск и не активная связка.
[Единый индекс версий и свидетельств](catalog/registry.json) сохраняет историю.

## Новые точные версии для выбранной модели B

Владелец разрешил проверку изменяемого дерева с ограниченным обещанием.
Этот список — навигация по внедрённым компонентам, не разрешение выпуска.

- [ENT-0001 r0001 — обязательное ядро](catalog/contracts/agent_system/ent-0001/r0001.md).
- [ENT-0002 r0003 — границы проверки изменяемого дерева](catalog/contracts/agent_system/ent-0002/r0003.md).
- [ENT-0003 r0002 — структурная схема](specification/ent-0003/r0002/catalog-base.schema.json).
- [Применение схемы](specification/ent-0003/r0002/usage.md).
- [ENT-0004 r0002 — структурные испытания и среда](validation/ent-0004/r0002/usage.md).
- [ENT-0005 r0003 — закреплённое чтение объявленного набора](adapters/ent-0005/r0003/usage.md).

- [ENT-0006 r0003 — набор входов, состав, граф и scoped-события](validation/ent-0006/r0003/usage.md).

- [ENT-0007 r0001 — формат и вычисление событий](specification/ent-0007/r0001/usage.md).
- [ENT-0008 r0001 — структурный протокол плана и отчёта](specification/ent-0008/r0001/usage.md).
- [ENT-0009 r0001 — исторический metadata исполнитель](validation/ent-0009/r0001/usage.md).
- [ENT-0009 r0002 — shared worker и successful capture](validation/ent-0009/r0002/usage.md).
- [ENT-0010 r0001 — offline-согласованность bundle и semantic replay](validation/ent-0010/r0001/usage.md).
- [ENT-0011 r0001 — базовая методология работы](protocols/ent-0011/r0001/work.md).
- [ENT-0012 r0001 — самоуправление двух жизненных циклов](protocols/ent-0012/r0001/governance.md).
- [ENT-0013 r0001 — точный неполный кандидат и границы покрытия](candidates/ent-0013/r0001/usage.md).
- [Версионированная таблица и frozen component records](candidates/ent-0013/r0001/candidate.json).
- [ENT-0014 r0001 — предложения разрешения выпуска/экспорта, только blocked-путь](permissions/ent-0014/r0001/usage.md).
- [ENT-0015 r0001 — private local trial staging, не публикация](staging/ent-0015/r0001/usage.md).
- [ENT-0016 r0001 — исторический read-only reader](staging/ent-0016/r0001/usage.md).
- [ENT-0016 r0002 — guarded capture pinned private trial](staging/ent-0016/r0002/usage.md).
- [ENT-0017 r0001 — archived/new-declared known views, без допуска](validation/ent-0017/r0001/usage.md).
- [Версионированный промпт подготовки переноса](transfer/ent-0012/r0001/prompt.md).

Артефакт читается только с заранее заданными ожидаемыми SHA-256, размером,
путём и полными метаданными ссылок. Обнаруженные изменения блокируют результат.
Успех не доказывает отсутствие всех промежуточных изменений, атомарность дерева
или полноту истории решений. Временные метки в имена не добавляются.

Исторические ревизии не переписаны, не перенаправлены и не отозваны автоматически.
Их точные старые зависимости сохранены; новый набор их молча не подменяет.
Все artifacts/reference относительны корню agent_system. Индекс не дублирует
нормативный текст; SHA-256 подтверждает связность, а не цифровую подпись владельца.
Свидетельства нового сегмента — summary условного разрешения и выполненных
проверок, не выдуманные отдельные цитаты о конкретных байтах.

## Проверенность и незавершённое

Структурные тесты исполняются jsonschema 4.26.0 с date checker; историческая и
новая версии проверяются отдельно. Среда/hash-lock: Linux x86-64 / Python 3.11.
Файловый адаптер проверен на Linux x86-64 с openat2 и /proc/self/fd, включая
физические символические ссылки. Windows/junction и другие архитектуры пока
не поддержаны этим адаптером; отказ не заменяется небезопасным fallback.

Связывание переданного известного состава с approve_revision и точный граф
depends_on проверяются ENT-0006 r0003. Scoped-события вычисляются ENT-0007
для явно заданных operation/area; несколько запретов действуют совместно.
Неизвестное/неподдержанное событие блокирует результат. Даже отсутствие
известного запрета или passed_known_inputs не даёт общего допуска.

Объявленный набор входов читается под одним root fd, полный плоский инвентарь
catalog/approvals сопоставляется до/после без отбрасывания неизвестных имён.
Ожидания задаёт вызывающий из доверенного основания; это не доказывает
подлинность плана, глобальную полноту или отсутствие невидимых изменений.

План/локальный отчёт имеют versioned структурный протокол ENT-0008 r0001.
Schema PASS не доказывает связность с выполнением. ENT-0009 r0001 исполняет
заранее закреплённый план, проверяет входы/контекст собственных дочерних вызовов
и создаёт локальную оболочку без допуска. Установка доверенна и защищена от
записи source. ENT-0010 r0001 независимо проверяет сохранённые документы и
отдельно переданный архив bytes, повторяя семантику без обращения к source.
Это согласованность claims, не доказательство факта исполнения/наблюдений.
Аутентификация плана и безопасный collector произвольного архива не реализованы.

Методология ENT-0011 r0001 задаёт полный рабочий текст и 14 разобранных
сценариев. Проверки целостности/связей сценариев не доказывают фактическое
соблюдение агентом. Она применяется и к изменениям самой системы.
Исходный аудит — §43–44 исследования. ENT-0013 фиксирует 16 capability и
9 condition rows для точного неполного payload (12 ревизий/34 артефакта).
Это не утверждённое полное покрытие совместимого выпуска; проверяются binding,
места определений и закрытые gates, не истинность coverage claims/поведение.

ENT-0012 r0001 описывает оба жизненных цикла и историю неактивных связок.
Отдельный transfer/ent-0012/r0001 содержит prompt и prepare.py: фиксируются
точные план/procedure/prompt/компонент/профиль в prepared_only receipt, без source IO
или изменения связки. Это не утверждённый allowlist, не exporter и не активация.
Связь preparation run с отдельным validation run записывает caller;
одноразовое потребление receipt/сквозной workflow пока не реализованы.

Descriptor ENT-0013 учитывается снаружи собственного payload; весь индекс/ledger
фиксируются заново на каждый run, без self-hash cycle и без второго индекса.
Описания check имеют defined_only, не per-capability PASS.

Не завершены полный валидатор, доверие к плану/факту исполнения, безопасный collector,
события о выпусках, семантические коррекции, проверка среды,
сквозное исполнение управления изменениями, адаптация и активация,
проверенное применение всех способностей ядра и таблица покрытия выпуска. Нет экспортёра,
разрешённого выпуска и активации. Частные данные/среда не включаются в экспорт
автоматически. Структурный или файловый PASS не является общим допуском.

ENT-0014 связывает отдельные release/export proposals с exact candidate/index/ledger
и release parent. Operation-specific известные запреты проверяются отдельно.
Для incomplete candidate результат blocked; реальных grants и положительного
пути допуска пока нет. Proposals хранятся local, не в ledger решений.

ENT-0015 собирает только неполный trial object store в fixed local/trials/UUID,
после exact bytes/known scope checks, exclusive writes и повторного readback.
Нет произвольного destination, зеркала paths/исполнения symlink, overwrite/resume
или автоудаления failed_partial. Это не готовый exporter/consumer и не допуск;
права release/export/activation false, private same-uid namespace предполагается доверенным.

ENT-0016 читает fixed local trial по внешнему manifest pin, без создания/исправления
файлов и выполнения содержимого. consistent_archived_trial проверяет captured bytes
и archived ledger, не факт stage execution и не текущие решения/полномочия.
Новый live ledger не обнаруживается автоматически; current_permissions=not_evaluated.

ENT-0017 сравнивает два явно pinned byte views для literal operation/area.
Все archived решения/records сохраняются, новые blocks/lifts вычисляются отдельно.
Старый view под именем current не доказывает свежесть: current_permissions остаётся
not_evaluated, даже если известного запрета не найдено; archive не переписывается.

## Текущий маршрут после ENT17

[Локальный сводный аудит и очередь R1–R8/M1](../research/31-agent-system-core-audit.md)
различает 17-компонентную цепочку инструментов и исторический payload E13 (12/34).
Это исследовательский отчёт вне переносимого нормативного состава, не новый
registry/approval/release. Проект сквозного operator trial зафиксирован отдельно;
не новая ENT ради номера. Все разрешающие переходы закрыты.

[Проект M1 operator trial и byte-handoff](../research/32-agent-system-operator-trial-design.md)
задаёт ENT9r2/ENT16r2 и coordinator без изменения r1. I1/ENT9r2 реализован и
зарегистрирован: capture_plan/metadata projection через один worker, raw maps
только при полном success. I2/ENT16r2 также зарегистрирован: первые manifest/objects
bytes доступны после всех late guards и cleanup. Следующий шаг — I3/coordinator.
Полная acceptance matrix ещё не исполнена; M1 целиком не закрыт.


### I3 в работе: unregistered coordinator foundation

[Рабочий кандидат основы](operator/ent-0018/r0001/usage.md): strict session/plans
и private bounded evidence CAS/read-only structural verification. Это не
зарегистрированная ENT18 и не run_operator_trial. Runner/state machine/own-profile
bootstrap/семантический journal replay/procedure+prompt ещё не реализованы;
I3/M1 целиком не закрыты. Registry и approvals этим подэтапом не меняются.
