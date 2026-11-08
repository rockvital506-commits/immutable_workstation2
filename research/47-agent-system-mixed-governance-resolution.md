# Смешанные governance группы: смысл, implementation facts и ограничения

## 1. Критерии до кода

Основание — продолжение после [46](46-agent-system-core-meaning-coverage.md).
Новый analysis не редактирует46, исходные нормативные версии или approvals.

Acceptance:

1. Для всех6holds и9unmapped spans показать исчерпывающее source partition без
   gaps/перестановок/перекрытий. Это15parent spans; coverage bytes не semantic proof.
2. Высокоуниверсальные обязанности/запреты/условия сохранять точным текстом.
   Меньшая универсальность — reviewed generalization; source-specific implementation
   snapshots/история/названия файлов не становятся требованиями любой среды.
3. Non-universal факты конкретной реализации исключить **из текста общих правил**,
   но retain связанные ограничения применимого exact component отдельно. Нельзя
   удалением «это не exporter» внушить готовность/разрешение экспорта.
4. PR04: сохранить наблюдаемую часть/провал/не наблюдалось/неприменимость с причиной,
   уровень evidence в фактической области, reviewer только по факту, явный pending;
   labels не permission, statements не authentication. Имена labels — specifics
   выбранного формата, его обязательный контракт не изменяется обобщением.
5. G04/G05: before-copy checks, exact permissions/allowlist, отсутствие reread,
   запрет автоматического разыменования, сверка результата, отдельная активация,
   доверенная установка вместо self-hash bootstrap остаются. Prep metadata/known
   no-block/receipt/model не становятся actual action/readiness.
6. В46 context Gscope содержит и общие self-governance нормы, и snapshot возможностей
   r1. Новый context projection должен отделить snapshot от общего scope, без
   удаления его qualification effects. Excluded source facts не просачиваются
   в rule body/свободный context/defaults.
7. Общие bodies обеих methodology versions остаются с exact origins; r1/r2 entry
   points/dependencies не переключаются. Новые решения не выводятся из source history.
8. Собрать и проверить revised **research draft** из pinned source capture,
   отдельно фиксируя rule texts, exclusions, retained limits, external D04 и
   unselected artifacts. Source mapping/generalization — agent self-review,
   не independent approval/NLP-equivalence/behavior qualification.
9. Никаких actual export/release/activation/новой среды, новых normative revisions,
   source mutations/скрытого снятия FAIL/сторонних dependencies.

## 2. Выигрыш, цена, риски

Выигрыш — конкретное «что умеет эта версия» не навязывается всем средам, но не
превращается в молчаливое разрешение. Rule text отделён от status/evidence.
Цена — version-bound qualification records и ручной semantic review обобщений.
Риск — согласованная ошибка mapping/materializer/test одного автора и неполнота
semantic closure; ни устранение15spans, ни зелёные tests её не доказывают.
