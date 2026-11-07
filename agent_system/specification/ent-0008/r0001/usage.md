# План входов и локальный отчёт проверки: структурный протокол

## Статус, состав, зависимости
ENT-0008 r0001 — protocol: этот текст, validation-plan.schema.json,
validation-run-report.schema.json и verify.py. Точные depends_on того же
каталога: ENT-0004 r0002 (движок/строгий парсер), ENT-0005 r0003 (получение),
ENT-0006 r0003 (binding/graph/scoped events). Нормативные $defs берутся из
ENT-0003 r0002 транзитивно, не копируются. JSON Schema Draft 2020-12,
jsonschema 4.26.0 и разрешённый isolated hash-lock, без новых библиотек.

Это ПРОТОКОЛ И СТРУКТУРНЫЕ ПРОВЕРКИ, не готовый orchestrator/CLI или валидатор
связности отчёта. Schema PASS подтверждает форму утверждений, не их истинность.
Проверки verify.py не исполняют запланированную операцию. Внедрение схем не
завершает реализацию обязательств ниже; невыполненное нельзя объявить PASS.

## Точное основание и идентичность
План — отдельные неизменяемые UTF-8 JSON bytes, без BOM; запись LF с одним
финальным LF. Строгий парсер обязан отвергать duplicate keys/NaN/Infinity,
неподдержанные кодировки и неверный тип. Хэшируется исходный bytes, не
повторная сериализация, sorted keys или семантически похожий объект.
Изменение любого поля/байта требует нового plan_id и новых SHA-256/size.
UUID не определяет порядок, новизну или доверие. Временных меток в именах нет.
plan_id не тождественен run_id: один план можно проверять несколько раз с
разными наблюдениями/отказами. Повтор run не изменяет план или старый отчёт.

План содержит catalog_id, непустую selection точных subjects, конкретные
context.operation/area (lowercase identifiers, не wildcard), registry tuple
с фиксированным path catalog/registry.json, artifacts и decisions. Кортежи
ровно базовые path/SHA-256/size и, когда есть ссылки, полная links/resolved_path.
role не переносится в файловый tuple. registry не дублируется в artifacts;
decisions — только прямые lowercase UUID.json в catalog/approvals. Пустой
ledger допустим как план чтения: это не устраняет требование положительных
approvals семантического слоя. Каталог должен существовать даже при пустом ledger.

Профиль execution_profile=linux-observed-set-5r3-6r3 точно обозначает установленные
ENT-0005 r0003 и ENT-0006 r0003 с их immutable dependencies, без latest/fallback.
Он не позволяет входному дереву выбрать исполняемый код. Источник данных не
является источником установленных инструментов. Совпадение profile-строки не
доказывает фактическую проверку инструментов: исполнитель обязан подтвердить
их точные индексные кортежи из отдельно доверенной установки до выполнения.
Если установленный профиль не подтверждён — unsupported, не поиск новой версии.

## Граница доверия
expectation_authority=caller_supplied_not_authenticated обязательно: форма не
самоутверждает доверие к своему содержимому. Вызывающий выбирает и закрепляет
ожидания ДО приобретения source, с отдельным основанием владельца/доверенного
состава; происхождение/подлинность и полнота основания не проверяются схемой.
Нельзя прочитать неизвестное дерево, сделать из него ожидания и объявить его
одобренным на основании совпадения с самим собой. Новое соседнее событие требует
повторного обоснования плана, не автоматического расширения allowlist.

Source locator/caller capability передаётся локально вне переносимого плана;
абсолютный корень/секрет/команда/код/параметры активации в поля не добавляются.
Это не даёт права скрыто выбрать другой источник: исполнитель фиксирует
выбранную capability на проход и привязывает source evidence к тому же run.
Одинаковые байты разных деревьев не доказывают одинаковую историю/владельца.
Планы с absolute symlink targets и локальные evidence могут быть частными:
локальный режим вне Git/экспорта, никакой автоматической публикации.

## Обязанности исполнителя сверх Schema
Перед чтением: bounded strict parse (не более 16 MiB на план/отчёт), Schema,
затем уникальность paths между registry/artifacts/decisions, совпадение
catalog_id у всех selection subjects, сумма файлов не более 10000 и сумма
ожидаемых bytes не более 64 MiB. На файл максимум 16 MiB. Schema задаёт
поштучные пределы, но не сумму/связность. Проверки суммы/дубликатов по path и
cross-document bindings — ещё НЕ реализованы этим структурным артефактом.

После подтверждения installed profile: read_set с registry в обычной группе,
прочими artifacts и decisions. На неизвестное/непереданное имя — отказ, не glob
с фильтром. Входы semantic checker берутся ТОЛЬКО из возвращённых byte maps:
registry отдельно, остальные artifacts и decisions без повторного чтения
source. Нельзя смешать input из одного run с evidence другого. План явно
содержит context и selection; check_catalog обязан получить именно их.
Положительные/отрицательные частичные результаты не подменяют общий результат.

## Отчёт и ссылки на evidence
Отчёт содержит run_id, plan_id и plan={sha256,size_bytes} ТОЧНЫХ исходных bytes
плана. execution_profile тот же, source_consistency=mutable_tree_observations.
Слои stages.acquisition и stages.binding имеют status, diagnostics из кодов
без частных путей/содержимого и при наличии evidence={sha256,size_bytes}.
Ссылки content-addressed, не пути/URI для автоматической загрузки. Связанные
bytes сохраняются локально отдельно неизменно; их отсутствие/несовпадение
делает результат непроверяемым. Hash не является подписью или аутентификацией.

Успешный acquisition ссылается на точную сериализацию возвращённого evidence
ENT-0005 r0003, а не на byte maps (bytes не JSON). Binding ссылается на точную
сериализацию полного report ENT-0006 r0003, включая restriction_evaluation и
not_checked. Сериализация evidence один раз фиксируется до вычисления ссылки;
произвольное повторное форматирование создаёт другие bytes/хэш. Полные дочерние
данные не редактируются ради унификации имен статусов/сокрытия not_checked.

ReadBlocked/ошибка загрузки может не дать дочернего report: evidence тогда
отсутствует, failure code обязателен. Не создавать поддельный successful child.
При blocked_known_scope envelope обязан иметь код KNOWN_SCOPE_BLOCK, даже если
сам semantic child имеет пустую diagnostics: это явное summary wrapper, не
изменение дочернего отчёта. Схема проверяет форму кода, не его реальное основание.

Матрица результирующих статусов (всё ещё без общего допуска):

| acquisition | binding | status отчёта |
|---|---|---|
| not_run | not_run | incomplete |
| passed_known_inputs | not_run | incomplete |
| passed_known_inputs | passed_known_inputs | passed_known_inputs |
| passed_known_inputs | blocked_known_scope | blocked_known_scope |
| failed | not_run | failed |
| unsupported | not_run | unsupported |
| passed_known_inputs | failed | failed |
| passed_known_inputs | unsupported | unsupported |

Иные комбинации отвергаются схемой. not_run не имеет evidence/diagnostics;
положительный/blocked слой требует evidence; failed/unsupported/blocked требуют
непустую diagnostics. Ошибка acquisition не разрешает запуск binding над
старыми или частично полученными данными. incomplete — не тихий PASS.
Прерывание/авария без финального отчёта не равны incomplete или успеху: run
остаётся незавершённым по локальному журналу, финальный результат не выдумывать.
Частичный diagnostic report при отказе сохраняется отдельно, не overwrite плана.

Проверяющий связность дополнительно обязан сопоставить plan bytes/hash/id,
profile, реальные статусы/коды child, все input tuples, inventory, registry,
selection/context/closure и соответствие фактически переданных byte maps.
Одного наличия двух корректных по форме child reports мало. Это отдельная
будущая реализация и отрицательные integration-тесты; эта версия не выдаёт
заготовленную shape-valid оболочку за доказанное выполнение. Примеры в verify.py
синтетические и намеренно показывают этот предел.

overall_admission всегда not_evaluated, transition_allowed всегда false.
Фиксированный not_checked: plan_authentication, source_authentication,
global_event_completeness, core_coverage, environment_compatibility,
release_permission, activation_permission, semantic_correction_resolution,
release_decisions. Локальный успех не устраняет эти обязанности. Source evidence
не обещает атомарность/невидимые изменения/будущие отзывы. Новый протокол не
является выпуском, allowlist экспорта, генератором доверия или активной связкой.

## Обоснование выбора и ограничения
Два небольших JSON документа и content-addressed ссылки вместо копирования
byte maps/всего ledger уменьшают дублирование и отделяют неизменяемый план от
каждого run. Плюсы: явный контекст, exact inputs, честный not_run, отсутствие
корней/кода и разрешающих состояний. Минусы: ссылки требуют отдельного локального
хранения bytes; SHA не доказывает происхождение; нельзя независимо проверить
run без plan/evidence. Максимальный размер evidence ограничен 16 MiB, слишком
большой report блокирует композицию, а не обрезается молча.

Повторно используются базовые $defs и установленный строгий парсер; сетевой
schema retrieval запрещён, неизвестные поля не игнорируются. Риск — принять
структурный PASS за истинность claims; поэтому границы отдельно закреплены
в тексте, константах not_checked и тестах. Runtime binding/orchestration ещё
не подтверждены. Размеры/пределы — ограничения, не benchmark максимальной нагрузки.

## Проверка
В разрешённой isolated среде выполнить:
python agent_system/specification/ent-0008/r0001/verify.py
Тесты формы, strict JSON, матрицы отказов, закрытого retrieval и регрессии
базовых tuples должны пройти без skips/errors/failures. Ни один тест не создаёт
реальных решений/выпуска, не читает private source и не активирует профиль.
