# ENT-0017 r0001 — архивный payload и новое явно объявленное known view

## Назначение и граница

Protocol, depends_on ENT-0016 r0001. Normative: этот текст,
[compare.py](compare.py), [verify.py](verify.py). Основание — задание B, раздельные
состав/решения/полномочия и условное делегирование владельца после проверок.
Это summary основания, не новая прямая цитата одобрения конкретных bytes.
Частная архитектура/built-in инструкции не извлекались, реальных запретов/
снятий/выпусков/активаций эта разработка не создаёт.

Проверяются **две явно переданные byte views**, а не «актуальность всего мира».
Термин current в API — заявленное caller новое known view, не доказанная свежесть.
Архив не редактируется, старые решения не заменяются новой датой/положительным
approval. Нужны отдельные внешние ожидания нового run. Совпадающие old/new views
допустимы, но не доказывают, что новых событий вне них нет.

Успех `compared_known_views_no_admission` — ограниченное согласование и вычисление
known scope. overall_admission/current_permissions=not_evaluated, release/export/
activation/transition/performed=false **при любом результате**. Неполный candidate
остаётся неполным. Отсутствие известного запрета не поддерживает положительное
разрешение ENT14 и не создаёт готовый совместимый выпуск.

## API и закреплённый план

```python
compare_views(plan_bytes, expected_plan, manifest_bytes, objects,
              current_registry, current_decisions)
```

- plan_bytes — strict UTF-8/LF JSON, внешние sha256/native size в expected_plan;
- manifest_bytes — bytes manifest ENT15, не путь к нему;
- objects — digest→bytes ровно всех referenced archive objects;
- current_registry — bytes полного объявленного индекса нового view;
- current_decisions — path→bytes всего явно объявленного known ledger нового view.

План — закрытый объект schema_version=1/kind=known_view_comparison_plan, plan_id
canonical UUID, archive_manifest и current_registry (sha256/size), current_decisions
(sorted уникальные path/sha256/size), context (одна literal operation и area).
Оба context идентификатора соответствуют `[a-z][a-z0-9_.-]{0,255}`, не wildcard/
prefix/glob/команды. Это scope query, не подтверждение реализации произвольной
названной операции. Даже query export/release/activate ничего не выполняет.
Смена context/inputs требует нового plan/run; r0001 не имеет stateful single-use
хранилища и не предотвращает повторное предъявление UUID.

Внешнее основание задаёт caller: пересчитанный hash неизвестного входа не
аутентифицирует его. Для physical trial использовать отдельный ENT16 с внешним
manifest pin; для new-known acquisition — прежний ENT5 read_set/ENT9 с полным
объявленным inventory ledger, без filtering отрицательных/неизвестных событий.
Новый compare не потребляет/не аутентифицирует отчёт ENT16/ENT9. Caller отдельно
связывает результаты на одинаковые raw refs; автоматического workflow не появилось.

## Проверка архивной части и монотонности known истории

Загрузка только из доверенно установленного кода: pins 3 артефакта ENT16,
прежний стек проверяет transitive зависимости. Новых библиотек нет. Проверка
собственных bytes ENT17 — отдельное обычное основание установки, не self-hash.
Конкурентно writable противником installation не поддержана (check/runpy TOCTOU).

1. До разбора проверить plan pin/limits, закрытый план и refs всех входов.
2. Проверить ENT15 manifest profile/run UUID/closed gates/readiness, native sizes,
   sorted unique path rows, exact digest set/hash/size каждого archive object.
   Logical paths не открываются, bytes Python не исполняются.
3. ENT13 проверяет archive candidate/registry/ledger/payload. Это проверка exact
   records/closure/core/refs и gaps, не факт исходной записи файла. Physical
   file type/permissions/inode acquisition — отдельная задача ENT16, не этого API.
4. **Каждая архивная запись ledger, включая unreferenced restrict/revoke,
   должна присутствовать в новом view по тому же path и с теми же bytes.**
   Оригинал не удаляется после lift/correction; новые события только добавляются.
5. Все архивные revision records должны присутствовать в новом registry без
   изменений, включая невыбранную историю. Новые сущности/ревизии разрешены.
   Сравнение semantic JSON с различением numeric types; order object keys/whitespace
   не изменяет record, но raw registry bytes всё равно отдельно pinned. Catalog ID
   тот же. Миграция/обрезание registry/ledger history не поддержана.
6. ENT13 проверяет тот же неизменный candidate/payload на новом index/ledger;
   новый latest не выбирается. Известный block validation/candidate scope может
   остановить этот preflight, без попытки обойти его для выполнения query.
7. ENT6 вычисляет запрошенную operation/area отдельно на archived и new-declared
   ledger. Архивный query block не является вечным: точный новый lift может снять
   только свой старый запрет по прежней ENT7 семантике, без удаления оригинала.
   Снятие одного из нескольких запретов не отменяет остальные.

В resulting metadata: archive_query и declared_query, context, added_decisions,
known_view_relation=declared_extension. Если new-declared query blocked —
blocked_known_scope с DECLARED_KNOWN_SCOPE_BLOCK. Неподдержанный тип/коррекция не
фильтруется; failed/unsupported останавливает проверку. Нельзя считать новую дату,
порядок файлов или approve_revision заменой lift. Старые scoped ограничения
вычисляются только для selected payload subjects, не всех произвольных tooling subjects.

## Пределы и сохранение данных

Код не читает source/trial/current catalog, не делает discovery/публикацию/
перезапись/активацию и не принимает filesystem roots. Только installed dependencies
читаются loader. Maps копируются поверхностно, bytes immutable, данные входов
не меняются. Вывод — refs/status/context/counts/diagnostic codes, не raw payload.
Архивная и новая known views остаются отдельными документами; не записывать новые
решения в старый trial.json ради прохождения проверки.

До 16 MiB каждый input document/object, objects до 10001 и 80 MiB суммарно;
new registry+decisions+тот же payload до 64 MiB/10000 entries. Manifest/plan
отдельно до 16 MiB. Это не общий CPU/RAM quota. Старый и новый byte sets могут
одновременно занимать память; сохранение объектов не выполняется этой функцией.

view_freshness/global_event_completeness/source/plan authentication остаются
not_checked. Caller может повторно передать старый view как «current» и получить
согласованный результат — это известный предел, не ошибка, которую исправляют
добавлением даты или latest. Положительная authorization модель/полнота покрытия/
поведение агента/среда не реализованы этим этапом.

## Проверка и оценка

В подготовленной approved изолированной среде:

```sh
python agent_system/validation/ent-0017/r0001/verify.py
python tests/run-all.py
```

Fixtures synthetic byte views, не реальные решения владельца и не наблюдения
файловой системы. Тесты включают новый block, удержание negative originals,
точный lift и оставшийся второй block, контекст, metadata history, wrong pins,
объекты и неизменность входов. Физический reader проверяется отдельно ENT16.

Выбран pure двух-view comparison вместо auto-discovery и перезаписи archive.
Плюсы: exact context/refs, no lost known negatives, сохранение immutable истории,
reuse прежней семантики. Минусы: дополнительные copies/checks и память, зависимость
от общего trusted стека; защита от непредъявленных событий не появляется.
Это обоснование узкой результативности/эффективности, не benchmark альтернатив.
Альтернатива читать «последний» ledger не выбрана: без отдельного acquisition/trust
это скрыла бы пределы. Миграция/compaction истории и positive grants отложены.

Для дальнейшего действия требуется отдельное действительное разрешение и его
проверки; compare result не основание снять gates. Изменение ENT17 проходит
те же immutable versioning/согласование/проверки, не автоматическое самоодобрение.
