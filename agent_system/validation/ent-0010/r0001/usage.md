# Независимая проверка согласованности записанного bundle

## Назначение, состав и зависимости
ENT-0010 r0001 — check: bundle.py, verify.py, usage.md. Точная depends_on:
ENT-0009 r0001 и его транзитивное замыкание. Исполнитель не меняется; verifier
НЕ вызывает execute_plan или read_set. Повторно используются pinned preflight,
проверка acquisition input claims, logical-path grammar и чистый semantic checker.
Второго ядра парсинга/графа/событий нет. Новых библиотек нет; прежняя isolated
jsonschema 4.26.0/hash-lock. Проверено на Linux x86-64/Python 3.11, без заявления
о проверенной Windows-совместимости или безопасности другой установки.

Цель — независимо от исходного source сравнить сохранённые bytes, ссылки и
claims, повторить binding/graph/scoped semantics по отдельно переданным bytes.
Это НЕ доказательство факта исполнения, аутентификация или проверка реальности
filesystem observations. Даже полностью согласованная подделка может пройти:
это прямо проверено тестом, остаётся в not_checked и не даёт допуска.

## API и входы
verify_bundle(report_bytes, expected_report, expected_plan, documents, payloads)
возвращает локальный result с layer=recorded_bundle_consistency.

- report_bytes — исходные bytes оболочки ENT-0008.
- expected_report и expected_plan — отдельно закреплённые caller SHA-256/size
  ТОЧНЫХ bytes отчёта/плана, не автоматически вычисленное одобрение из bundle.
- documents — ровно dict digest -> bytes плана и всех child documents, на которые
  ссылаются стадии. Нет лишних/пропущенных объектов, path/URI/retrieval callbacks.
- payloads — отдельный локальный архив dict logical path -> bytes ВСЕХ объявленных
  registry/artifacts/decisions, когда acquisition прошёл; иначе пустой dict.
  ENT-0009 не архивирует эти bytes: caller должен отдельно безопасно сохранить
  объявленный набор, а не выдавать документы-claims за сам source archive.

Нативные maps копируются до проверки; values — immutable bytes. Нет изменения
входов, открытия source/архива по путям или извлечения файла из недоверенного
контейнера. Загрузка такого архива с диска/безопасный collector — отдельная
обязанность caller, эта функция принимает уже полученные bytes. Совпадение
позднее полученных байтов с ожиданием не доказывает, где/когда они прочитаны.
Не менять inputs при вызове; общей атомарности внешних объектов не обещаем.

Пределы: report/plan/каждый child — 16 MiB, максимум 3 documents (plan+2 child),
максимум 10000 payloads, на файл 16 MiB, суммарно 64 MiB payloads. Модель in-memory,
не потоковый декодер. Все поля/числа/пути плана проверяет точный preflight ENT-0009,
включая native integer sizes/суммы/catalog/duplicates. UTF-8 strict JSON, LF,
один финальный LF, duplicate keys/NaN/Infinity/BOM не допускаются. Hash относится
к исходным bytes, не к повторной сериализации/эквивалентному JSON.

## Установка и порядок проверок
Caller доверенно устанавливает сам verifier из отдельно согласованного состава.
Три artifact pins ENT-0009 фиксированы в коде и сверяются до загрузки; ENT-0009
сверяет ещё 21 artifact своего installed closure. Input catalog/байты не выбирают
исполняемый код. Нет latest/fallback. Установка/интерпретатор/kernel доверенны и
неизменяемы противником во время загрузки; check-before-runpy не атомарная загрузка
в writable installed tree. Это тот же явно ограниченный bootstrap, не самодоверие.

1. Размеры/native types, внешний pin report, content addresses всех documents.
2. Schema оболочки ENT-0008; точный набор referenced documents, SHA/size каждой
   ссылки; внешний pin плана, preflight, plan_id/profile согласованы.
3. Если acquisition passed: exact payload paths/hashes/sizes и полные tuples
   evidence сопоставляются с планом; закрытая форма acquisition evidence,
   сохранение всех not_checked, точные имена ledger/до-после, pinned-root claim.
   Directory metadata имеет корректную форму: inode/device согласованы со stat
   fingerprint, directory-mode, links и resolved logical paths. Это проверка
   claims; inode/mtime НЕ сверяются с настоящей файловой системой.
4. Если binding child есть: registry catalog_id совпадает с планом. Чистый
   ENT-0006 повторно вычисляет полный результат по архивным bytes и ТОЧНОЙ
   selection/context плана. Сравнивается весь parsed child, не только status:
   inputs, checked_artifacts, closure, events, diagnostics, not_checked, неизвестные
   добавления и удалённые поля. Списки сохраняют порядок детерминированного tool.
   JSON key-order/indent не являются semantic replay, но raw references точны.
   Envelope stage status/diagnostics совпадают с child, кроме документированного
   KNOWN_SCOPE_BLOCK summary. Второй алгоритм closure не реализован.

Положительный и failed semantic child могут точно replay-совпасть; consistent
failed run остаётся recorded_status=failed, не становится successful execution.
При unsupported replay verifier тоже unsupported, не подтверждает неподдержанную
семантику только из-за совпадения кодов. При failed/unsupported binding без child
проверяется лишь записанная оболочка: checks=binding_failure_claim_only.
Это НЕ подтверждение причины ошибки или выполнения стадии.

При acquisition не completed payloads должны быть пусты; child acquisition
failure evidence пока не имеет определённого формата — unsupported, не игнор.
not_run/incomplete строго сохраняются по матрице ENT-0008. Частичный корректный
bundle может быть согласованным, но НЕ завершённым исполнением; checks точно
показывает, был ли semantic_replay. Непереданные child bytes блокируют проверку.

## Результат и граница обещания
status: consistent_recorded_bundle, failed или unsupported. recorded_status —
записанный итог run после проверки формы/плана (может быть incomplete/failed/
unsupported/blocked_known_scope); это не общий допуск. checks — фактически
пройденные категории проверки; при отказе список может быть частичным.
Диагностика — код, без raw payload/частного пути/цели ссылки. Ошибка/прерывание
не становится успехом; KeyboardInterrupt/неизвестная авария может не дать result.

Всегда overall_admission=not_evaluated, transition_allowed=false. Обязательные
not_checked: execution_authentication, source_observation_truth,
plan_authentication, source_authentication, global_event_completeness,
core_coverage, environment_compatibility, release_permission,
activation_permission, semantic_correction_resolution, release_decisions.

Согласованные fingerprints и ложные observations неотличимы от записанных
настоящих без отдельного доверенного основания. Согласованное переписывание
всего bundle и обоих caller pins не доказывает доверия. Функция не свидетель,
подпись или trusted attestation. Нет атомарности дерева/знания будущих отзывов.
Replayed bytes не доказывают, что executor действительно прочитал именно их
из разрешённого источника; лишь совпадение с планом и согласованность reports.

Нет записи/сети/экспорта/активации, operation не исполняется. Caller хранит
result локально вне Git/экспорта. Архив содержит реальные данные, documents
могут содержать private symlink targets: не публиковать/загружать автоматически.
Git не является разрешением экспорта, consistent_recorded_bundle — не release.

## Обоснование, эффективность и проверки
Повторное применение прежнего checker вместо копирования графа сохраняет один
источник семантики. Exact references и полный replay обнаруживают даже child,
перехэшированный после подмены context/closure/artifacts/not_checked. Цена —
отдельный архив payloads, память до установленных лимитов, проверка installed
closure и повторная семантическая работа. Нет обещания ускорения или benchmark
максимального набора. Форма observations проверяется, их истинность остаётся
неподтверждённой — это риск модели, не исправляемый ещё одним полем PASS.

python agent_system/validation/ent-0010/r0001/verify.py: 35 тестов без skips/
failures/errors. Фикстуры синтетические; source удаляется перед offline-проверкой.
Проверяются pins/наборы/bytes, rehashed substitutions, shape/metadata/обязательства,
полный semantic replay, scoped block/failed/unsupported/partial runs, limits,
отсутствие изменения входов и намеренная граница согласованной подделки observations.
