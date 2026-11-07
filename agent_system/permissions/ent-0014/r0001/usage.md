# ENT-0014 r0001 — отдельные предложения разрешения выпуска и экспорта

## Статус, источник и назначение

Универсальный protocol, depends_on ENT-0013 r0001. Четыре нормативных файла:
этот текст, [proposal.schema.json](proposal.schema.json), [check.py](check.py)
и [verify.py](verify.py). Источник — задание B, требование раздельных разрешений
ENT-0001 r0001 и делегирование владельца: внедрение после подтверждения результата
и всех проверок. Это summary основания, не новая цитата одобрения конкретных bytes.
Частная архитектура/данные проекта и built-in инструкции не переносились.

**Реализована только proposal/блокирующая часть модели.** Реальные положительные
release/export decisions, их полноценная событийная модель/отзыв/аутентификация
и исполнение переходов не реализованы. Существующий ENT-0007 r0001 по-прежнему
не поддерживает release events. Новое описание не расширяет его молча.

Результат этапа: точный запрос можно связать с candidate, текущими известными
входами и отдельным намерением release либо export. Для ENT-0013 incomplete
candidate автоматический результат всегда закрытый. Это необходимый bounded
отрицательный путь, **не законченный менеджер разрешений** и не заменитель
положительной проверки покрытия/явного решения владельца.

## Разделение объектов и полномочий

1. approve_revision разрешает конкретный нормативный компонент; не выпускает
   содержащий его комплект и не разрешает копирование/подключение.
2. Candidate descriptor фиксирует payload/refs/пробелы, но не является выпуском.
3. Permission proposal выражает только предложение на одну операцию. Agent
   может подготовить его, но `authority=proposal_only`, transition_allowed=false.
4. Будущее положительное решение владельца должно быть отдельной immutable
   записью с самостоятельной идентичностью, точным предметом/составом/пределами
   и основанием согласия; не переименованным proposal и не summary тестового PASS.
   Его тип/семантика/разбор конфликтов и ограничений пока unsupported.
5. Разрешение конкретного выпуска не означает разрешения конкретного экспорта;
   разрешение экспорта не означает разрешения активации. Для активации нужны
   отдельно обследованная среда/связка/проверки и явное разрешение.

r0001 не принимает kind authorize_release/authorize_export или owner_approved,
не «доверяет» произвольному grant JSON, не создаёт owner decision и не выводит
права из даты, approval компонента или отсутствия известного запрета.
Владельцу не предъявляется заведомо неполный комплект как готовый выпуск:
сначала показываются причины остановки, недостающие реализации и проверки.

## Предмет каждого предложения

Схема — закрытый объект со следующими обязательными полями:

- schema_version=1, kind=permission_proposal, request_id UUID,
  authority=proposal_only, transition_allowed=false;
- action — **одна** release либо export. Release имеет literal area
  agent_system.release; export — agent_system.transfer, без prefix/wildcard;
- candidate — SHA-256/size точных bytes descriptor;
- registry — SHA-256/size полного индекса **этого запуска**;
- decisions — полный объявленный известный набор path/SHA-256/size,
  строго сортированный по уникальным путям. Нельзя оставить только approvals
  выбранных компонентов или отфильтровать неизвестные/отрицательные записи;
- для release: export_paths=null и release_request=null;
- для export: export_paths — отсортированный точный набор путей выбранного
  payload, а release_request — SHA-256/size отдельного release **proposal**.

Export proposal ссылается на release proposal с другим UUID, тем же candidate,
registry и decisions. Parent bytes передаются явно и сверяются целиком. Это
связь **намерений**, не ссылка на разрешение выпуска. Цепи export→export/циклы
не поддержаны. Для текущего candidate export_paths равен 34 selected artifact
paths: subset/лишний файл/историческая версия/descriptor отвергаются. Нет destination
или произвольной shell-команды; spec не является безопасным exporter/публикацией.
Порядок путей каноничен, но стиль JSON object keys/пробелы не задаёт полномочия.

Новый registry/ledger/candidate/allowlist/parent требует нового proposal с новым
UUID и нового запуска. История старого не переписывается. Повторное применение UUID
не контролируется хранилищем r0001: stateful single-use/replay protection отсутствует.
Hashes не доказывают авторство. Pin proposal и candidate задаётся снаружи из
доверенного основания; вычислить hash недоверенного входа — не аутентифицировать его.

## Проверка и постоянная остановка

API:

```python
check_proposal(proposal_bytes, expected_proposal,
               candidate_bytes, expected_candidate,
               registry_blob, decisions, payloads,
               release_request_bytes=None)
```

Все документы — явно переданные bytes; decisions/payloads — path→bytes.
Payloads ровно selected 34 artifacts, не все исторические файлы registry.
Загружается только доверенно установленный код, не код из inputs/source.
Установка сверяется по pins (4 артефакта ENT-0013 + новая schema); прежний
ENT13→ENT9 loader сверяет transitive зависимости. Схема переиспользует локальные
определения base через фиксированный URN и validator registry; retrieval иных
URI остаётся запрещённым. Никаких новых библиотек. Проверка собственных bytes
check.py — обязанность доверенной установки/её отдельного approval, не self-hash.
Одновременно writable противником installation не поддержана (check/runpy TOCTOU).

Порядок:

1. Внешний pin предложения, strict UTF-8/LF JSON без BOM/duplicates/constants,
   ровно один завершающий LF, закрытая schema и native integer sizes.
2. Binding candidate/registry/полного явно переданного ledger, parent/export_paths.
   Discovery/подлинность/глобальная полнота ledger этим не доказаны.
3. ENT-0013 consistency над теми же bytes: exact records/closure/core/refs и gaps.
   Изменение readiness на ready не заменяет отсутствующие реализации/проверки.
4. ENT-0006 известные scoped-запреты выбранного payload отдельно для release /
   agent_system.release; для export также export / agent_system.transfer.
   Validate/candidate scope не заменяет эти проверки. Release-запрет не теряется
   при рассмотрении export-намерения; несколько известных запретов не игнорируются.
5. Если структура/binding/известные scopes прошли, **blocked_incomplete_candidate**:
   INCOMPLETE_CORE_COVERAGE + POSITIVE_PERMISSION_PATH_UNIMPLEMENTED.

Scope block возвращает blocked_known_scope; иные нарушения failed/unsupported.
При любом статусе release/export/activation/transition_allowed/performed=false,
overall_admission=not_evaluated. «Структура принята» не является ни положительным
решением владельца, ни разрешением действия. Claim truth/поведение/новая среда,
полнота/подлинность событий и фактическая публикация остаются not_checked.
Новый положительный путь потребует собственной реализации/версии и проверок,
не удаления этого запрета или ослабления требований ядра.

До 16 MiB на отдельный input, до 10000 registry+decision+payload entries,
до 64 MiB суммарно registry+decisions+payloads; proposal/candidate/parent ограничены
каждый отдельно, не включены в эти 64 MiB. Это не обещание глобального CPU/RAM
лимита процесса. Для known decision refs уникальность путей проверяется напрямую,
без квадратичной проверки уникальности JSON objects в schema.

## Хранение и практическая процедура

Proposal/result — локальные неактивные документы, например
`agent_system/local/permissions/<request_id>/{proposal.json,result.json}`.
Не помещать их в catalog/approvals, не выдавать за реальное событие решения,
не отбрасывать чужие записи ledger ради прохождения validator. ENT7 должен
отвергать неизвестный формат, а не считать proposal разрешением.

Caller отдельно фиксирует план/индекс/ledger прежними средствами и получает
captured bytes reader под одним root fd; validator сам source не читает.
Подготовка и запись local документов — отдельная работа caller, не side effect
check_proposal. Отчёт о consistency не доказывает фактическое исполнение чужих
действий или истинность переданных наблюдений. Нет автоматического связывания
с ENT9/ENT12 run, публикации, изменения активной связки или отправки владельцу.

В подготовленной изолированной среде:

```sh
python agent_system/permissions/ent-0014/r0001/verify.py
python tests/run-all.py
```

Fixtures из trusted checkout — не discovery произвольного source.
Реальные решения/переходы не создаются для проверки. Отрицательный результат
сохраняется как отрицательный; FAIL устраняется и весь затронутый набор повторяется.

## Обоснование, риски и влияние

Выбран closed proposal + блокирующая проверка вместо преждевременного исполнения
положительных grants. Плюсы: разделены три разрешения, зафиксированы exact snapshot
и parent, сохраняются известные operation-specific запреты, повторно используются
прежние binding/coverage checks. Минусы: дополнительный документ и повторные pure
проверки; полный manager и право на действие отсутствуют. Это обоснование узкой
результативности, не измеренное преимущество скорости над альтернативами.

Альтернативы: хранить реальный grant без модели его проверки — отвергнуто;
автоматически считать current candidate готовым — нарушает ядро; ничего не
фиксировать до полного exporter — откладывает выявление смешения полномочий.
Новые core/decision-event форматы не утверждены этим этапом. Основные риски:
подмена внешнего основания/installation, stale/неполный ledger, ложные claims,
переоценка зеленого structural теста. Конкретные ограничения описаны выше.

Влияние: оператор получает проверяемый отказ на связанное с точными bytes
предложение. G04/G05/G07 и positive release permissions остаются незавершёнными.
Изменение самого ENT-0014 подчиняется тому же versioning/согласованию/проверкам;
approval этой сущности не разрешает собственный выпуск и не меняет ядро.
