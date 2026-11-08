# U01: связанные смыслы путей, ссылок и изменяемого дерева

## 1. Критерии до кода

Владелец подтвердил [44](44-agent-system-universality-trace.md) и продолжение.
Новый bounded шаг — разбор U01, а не переписывание44/ENT2r3 или объявление готового
semantic adapter. Историческая U01/hold остаётся неизменной; новый analysis имеет
явную ссылку на predecessor fixture и точный ENT2r3 source.

Acceptance:

1. Разбить **весь** исходный §4 на связанные группы. Exact source spans должны
   составить исходную цитату без пропусков/повторов/перестановки. Whitespace в source
   evidence сохраняется; proof bytes/coverage вспомогателен к смысловому review.
2. Для каждой группы показать scope, условия/исключения, смысловые связи и причину
   universality class. Не считать любое approved требование автоматически максимально
   универсальным; не делать универсальной конкретную реализацию/формат.
3. Высокая универсальность — границы чтения, полномочия/согласование, доказательные
   пределы, соответствие ожиданию в **области чтения каталога agent_system**; пока
   сохранять полный текст связанных групп с scope (conservative fallback).
4. Ограниченная универсальность — синтаксис индексного формата, названия конкретных
   перенаправлений, названия timestamp fields. Передать обоснованный общий смысл
   без технических particulars. Это derived semantic candidate, **не замена**
   требований выбранного ENT2r3: его формат/поддержка/ограничения по-прежнему обязательны.
5. Не выдумывать non-universal единицы для заполнения квоты: в нормативном §4 может
   не быть private-only инструкций. Не удалять применимые constraints как «частные».
6. Связи обязательны: запрет traversal ↔ допустимые dot segments в link target;
   cycle ↔ допустимые aliases; absolute local target ↔ запрет private path transfer;
   changed identity ↔ совпавший content; mutable observations ↔ отсутствие snapshot;
   limits of evidence ↔ неотменяемая безопасная граница.
7. Отдельный finite **semantic decision model** должен проверять эти различия
   сценариями, а не только literal fixture equality. Explicit unknown не даёт
   успеха; сценарии/модель не выдаются за actual filesystem/agent behavior proof.
8. Нельзя объявить полную closure, semantic equivalence произвольного текста,
   owner/independent review, выпуск/экспорт/активацию. Никаких новых permissions,
   normative revisions/approvals или target environment. Только stdlib lab tests.

## 2. Обоснование и риск

Выигрыш: вместо одной непонятой группы появляется полный разбор связанных смыслов;
условия/исключения проверяются различающими outcome-сценариями. Три потенциальных
обобщения рассматриваются отдельно от обязательной совместимости source protocol.
Цена: ручное связывание с source и finite state model, а не NLP/classifier готового
adapter. Риски: общий автор source mapping/модели/сценариев, неверное обобщение,
неполные состояния, скрытая зависимость от остальных пунктов контракта. Ограничить
вывод выбранной группой, фиксировать gaps; не ослаблять исходные ограничения.


## 3. Разбор источника и смысловая review

[Trace](45-agent-system-linked-meaning-decomposition.json) разбивает U01 на17групп:
14high/preserve и3limited/generalize. Non-universal/private-only групп в самом §4
не найдено: нормативные требования не исключаются ради числа исключений.
Scope каждой группы — чтение каталога agent_system, включая изменение самой системы,
а не все операции любого проекта. Отдельные группы нельзя применять в отрыве от
их условий и связанных групп.

| Unit | Смысловая группа | Маршрут | Связанные группы |
|---|---|---|---|
| P01 | Логический индексный путь | generalize | P04 |
| P02 | Физическая граница и root-symlink | preserve | P04 |
| P03 | Поддержка ссылок | preserve | P09, P04 |
| P04 | Каждый переход и target semantics | preserve | P01, P02, P03, P05, P06, P16 |
| P05 | Блокировки и допустимый alias | preserve | P04 |
| P06 | Состав evidence, не только hash | preserve | P04, P07, P17 |
| P07 | Согласованный link metadata состав | preserve | P06, P12 |
| P08 | Локальный absolute target и перенос | preserve | P09, P10 |
| P09 | Возможности целевой среды | preserve | P03, P08, P10, P11 |
| P10 | Различение типов перенаправления | generalize | P08, P09 |
| P11 | Конфликты target paths | preserve | P09 |
| P12 | Ожидания до чтения и подмена identity | preserve | P07, P13 |
| P13 | Предел observed correspondence | preserve | P12, P14, P15, P16 |
| P14 | Наблюдаемые timestamps | generalize | P13 |
| P15 | Отдельное основание snapshot | preserve | P13 |
| P16 | Безопасная граница без fallback | preserve | P13, P04 |
| P17 | Точные исходные bytes | preserve | P06 |

### Почему три обобщения не отменяют исходный контракт

- **P01:** универсальный смысл — однозначные ссылки на артефакты/свидетельства
  относительно логического корня. Запреты конкретных строковых форм принадлежат
  согласованному индексному формату; общий текст не навязывает его любой ОС.
  Но выбранный ENT2r3 сохраняет **все** конкретные запреты. Нельзя передать
  обобщённый принцип и объявить несовместимый индекс корректным по ENT2r3.
- **P10:** убраны названия Windows/Junction/reparse/symlink из общего вывода;
  сохранено различение типов и запрет выводить поддержку всех из поддержки одного.
  Конкретный адаптер не становится совместимым с неподдерживаемым типом.
- **P14:** сохранено «совпадение наблюдаемых меток изменения не доказывает
  неизменность», без имён timestamp fields. Никакой snapshot из этого не следует.

Остальные группы сохраняют точный source text как временный fallback. В частности,
P04 не превращает запрет dot segments **индекса** в запрет допустимых сегментов
**цели ссылки**. P05 не объявляет aliases циклами, но alias не отменяет настоящий
cycle. P08 допускает local absolute target внутри границы, не разрешая перенос
private absolute paths/автоматическое разыменование. P12 блокирует identity change
даже при совпавших bytes; P13/P15 не дают snapshot/полную историю. P16 не разрешает
resolve-only fallback под предлогом ограниченности observations.

Review выполнена автором-агентом. Это явный **proposal классификации и обобщений**,
не independent semantic verification или новая редакция ENT2. Исторический hold
в44 не переписан: новая trace показывает предложенное разложение и оставшиеся gaps.

## 4. Смысловые зависимости и граница покрытия

Pinned registry связывает источник с **ENT2r3 → depends_on ENT1r1**. Старые C01–C10
из44 соотносятся с exact core artifact из registry, а не с latest/новым названием.
Проверены bytes source/dependency artifacts и их approval references; это frozen
known records, не установление текущей authority/действительности всех решений.
Supersedes ENT2r2 не трактуется как обязательная исполняемая dependency.

Внутренние meaning links симметричны и образуют связную группу; это **не** граф
runtime depends_on. Граф не разрешает автоматическое замыкание/пропуск условий.
Всё §4 покрыто source spans, но соседние §1–3/5–10 ещё не классифицированы этим
анализом. Полная semantic closure не заявлена. G01 из44 и P16 здесь имеют общий
смысл запрета небезопасного fallback: при будущей сборке это trace-связь с одним
источником требований, не повод создавать дублирующее нормативное ядро.

## 5. Проверка результата, а не только literal equality

[Лабораторная модель](../tests/test_agent_linked_meanings.py) отделяет:

1. coverage/trace/source pins — отсутствие пропусков и подмены исходного основания;
2. conservative output oracle — exact выбранный proposal, не NLP-equivalence;
3. **39 finite semantic scenarios** — различающиеся исходы связанных условий.

Сценарии включают допустимый root-symlink/внутренний relative-dot/общую цель,
escape с возвратом, настоящий cycle при alias, неправильную базу relative target,
local absolute target против его private-path copy, отсутствие типа/прав создания,
тайную замену ссылок regular files, identity replacement при одинаковых bytes,
неизвестное ожидание, изменение с возвратом между наблюдениями и ложный snapshot
claim. В модели отсутствие отдельной проверенной snapshot процедуры никогда не
компенсируется одним asserted basis или timestamp match.

Все входы модели — **declared assumptions**, не реальные наблюдения ОС. Значение
`declared_gates_satisfied` означает только результат finite model; local/transfer
модель не даёт actual read/admission/export/activation. Integrity ограничена
`matches_declared_observations_only`. Unsupported/unknown/invalid input не даёт
положительного результата; actual behavior/hostile filesystem не моделируются.

Первый запуск19methods дал19errors: отсутствовала связь P03↔P04 между поддержкой
ссылок и безопасностью каждого перехода; graph действительно был несвязным.
Добавлена обоснованная meaning link, проверка связности не ослаблялась. Для
truncate mutation удалены также dangling links: проверяется coherent omission,
а не случайный более ранний отказ по неверному графу. После исправления и добавления
проверки exact external dependency boundary:20methods PASS,39scenario cases PASS.

Эти результаты не доказывают корректность произвольного пересказа, полноту всех
состояний или независимость оценки. Классификация source→meaning и model gates
выполнены одним автором. Ограничения сообщаются, а не превращаются в общий PASS.

## 6. Итог квалификации и следующий шаг

- 20own methods PASS, внутри них39semantic scenario cases. Fixture SHA-256:
  `89656b5ad0f319d3f433120ad7c48e977301f23ebe1319dc5f9dada1aa65c3c7`.
- Полный регрессионный прогон **48/48modules PASS**, approved locked interpreter;
  предыдущие26universality methods также исполнены без изменения44/test bytes.
- Repo38checks/0warnings/0errors; navigation68checks/0errors; rules899checks/
  0errors; CSV/SELF-HASH и pip check PASS. Public inventory:
  242Markdown/86README/46research/48test modules; summary/self-hash пересчитаны.
- Все142catalog refs SHA/declared sizes PASS. Registry и все tracked agent_system
  bytes прежние относительно cadf600;19entities/31revisions/111norm/31approvals.
  Новых approvals/revisions/permissions не создавалось.

Результат — reviewable полный разбор **одной** смешанной группы и finite проверки
связанных смыслов. Необоснованная общая декларация «U01 решена, значит адаптер готов»
не делается: структурная непрояснённость группы снята в предложенной декомпозиции,
но semantic mapping/generalizations пока только agent-reviewed; historical hold
не переписан и full closure не квалифицирована.

Следующий bounded участок — остальные пункты ENT2 и оставшиеся methodology/
governance units: точное покрытие obligations/conditions/exceptions, слияние общих
смыслов без дублирования ядра, explicit gaps и проверка результирующего текста.
После этого потребуется применимая проверка реальной адаптации/поведения, не только
модели. G05full semantics/G07/R4positive actual path/R6/R7/R8 остаются открыты;
release/export/activation/new environment этим шагом не разрешены и не выполнялись.
