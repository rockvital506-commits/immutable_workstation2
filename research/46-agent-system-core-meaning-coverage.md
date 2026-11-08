# Core meaning coverage: версии, условия делегирования и сборка без дублей

## 1. Критерии до реализации

Основание: продолжение после [45](45-agent-system-linked-meaning-decomposition.md).
Шаг — расширить semantic coverage ENT2/W/governance, получить проверяемый **draft**,
не регистрировать нормативный адаптер и не выдавать разрешение переноса.

Acceptance:

- ENT2r3: дополнить §1–3/5–10; §4 сослать на45, а не переписать его analysis.
- W00–W09: учесть r1 **и** r2. ENT12r1 зависит от ENT11r1; ENT12r2 дополнительно
  выбирает ENT11r2. Совпадение текстов не разрешает retarget dependency на r2/latest.
- Одинаковые фрагменты допускается хранить/показывать одним **draft body** только
  с сохранением всех exact origins и их применимости. Разные условия/добавленные
  обязанности не сливать по похожему смыслу. Не создавать второе нормативное ядро.
- W06: source содержит ранее данное локальное условное делегирование. Оно **не**
  становится новой доверенностью в принимающей среде. Выделить этот фрагмент,
  передать общий условный принцип (только при наличии применимого отдельного
  решения и подтверждённых результата/эффективности/проверок), сохранить запреты.
- Методология r2 дополнительно требует practice.md; одинаковый W09 не означает
  равенство full revisions. Карту результата/reviewer levels не превратить в
  доказательство действительности observations или independent review.
- G01/G02/G03/G06/G07 разобрать с полными условиями. G00/G04/G05/G08/G09 смешивают
  общий смысл с versioned implementation statements: сохранить explicit hold до
  отдельного разбора, не отбрасывать ограничения. Закрытие всей governance не заявлять.
- Собрать draft **из actual pinned source spans**, не из новых копий high texts
  в JSON. Классификация остаётся review автора; согласованность/pins не NLP proof.
- Проверить утрату одного origin, слияние разных scoped units, ошибочное переключение
  r1→r2, потерю practice requirement, перенос local delegation как общего полномочия,
  пропуск hold, полномочия из текста/самохэша. Unknown/FAIL не дают readiness.
- Отразить metadata closure выбранного preparation root отдельно от semantic
  coverage её артефактов. Все неразобранные артефакты — gaps, не молчаливый success.
  Прежние registry/approvals/immutable versions/44–45 не изменяются. Нет actual
  export/release/activation/новой среды и новых сторонних библиотек.

## 2. Обоснование и ограничения

Выигрыш — полный набор W и ENT2 requirements связывается с уже выполненной работой,
а смешение exact versions и полномочий выявляется до переноса. Source references
вместо повторного полного текста уменьшают дублирование evidence.
Цена — требуется явная applicability/alias review и unresolved inventory. Текстовые
совпадения не гарантируют равных полномочий; один автор ledger/materializer/checks
может согласованно ошибиться. Ограничить вывод lab draft и не скрывать эти риски.


## 3. Что добавлено и что не объявляется завершённым

[Ledger](46-agent-system-core-meaning-coverage.json):39групп —31preserve,
1generalize,6hold и1external_reference. Ledger не хранит повторно high texts:
используются exact path/SHA/size и Unicode spans фактических source files.
Это исследовательское evidence, не второй registry или нормативное ядро.

- D01–D03/D05–D10: оставшиеся9требований ENT2r3 полностью с условиями/оговорками.
  D04 ссылается на45; старый разбор не переписан и не принят автоматически.
- W00–W09 обеих точных версий: W06 разбит на три связанных фрагмента. Остальные
  W сохраняются полностью. Вывод «один удачный случай универсален» прямо запрещён
  W03; соразмерность/оптимизация не удаляют mandatory checks.
- WR: одинаковая краткая рабочая запись двух версий; WR2-practice: отдельное
  дополнительное требование r2. Оно не исчезает из-за общего W09.
- PR01/02/03/05: scope/критерии/наблюдение/продолжение практической оценки r2.
  PR04 (labels/reviewer/evidence map) пока hold, не исключённый private текст.
- G01/G02/G03/G06/G07: независимые состояния, изменение/согласование, оба lifecycle,
  история/ограничения. Полные условия сохранены, включая отсутствие полномочия от
  продолжения/новой версии, отдельную активацию, совокупное действие restrict/revoke.
- G00/G04/G05/G08/G09: explicit hold из-за смешения общих требований, exact entry
  points, known implementation limits и отчёта об оптимизациях. Эти ограничения
  не отбрасываются как «неуниверсальные». Полное governance coverage не заявлено.

### W06: важное различение смысла и локального решения

В исходнике есть «в этой системе действует ранее данное условие» с внедрением
по умолчанию после проверок. Копировать это как безусловное разрешение принимающему
агенту нельзя. Новый candidate передаёт **условный общий принцип**: применимое
делегирование должно отдельно существовать, иметь точную область и подтверждённые
условия результата/эффективности/всех относящихся проверок; ключевые несогласованные
ветвления — владельцу. Перенос текста не создаёт делегирования в другой среде.

Непосредственно соседние W06a/W06c сохранены: полномочия применяются в точной
области, FAIL не обходится, молчание не решение, release/composition/activation
раздельны. Один обобщённый фрагмент нельзя читать как обход этих запретов.
Review этого mapping — автор-агент, не независимая semantic verification.

## 4. Дедупликация только текста, не версий/полномочий

13одинаковых пар фрагментов r1/r2 показаны по одному draft body с **обоими** origins
и contexts. Это не означает одинаковые полные revisions или слияние bindings.
Проверяются буквальная идентичность body и applicability text; review допустимости
такой ссылки задана явно, а не выводится только из совпавшего hash.

**ENT12r1 → ENT11r1** сохраняется. ENT12r2 отдельно зависит от ENT12r1 и ENT11r2,
поэтому в declared closure одновременно нужны обе methodology revisions.
`supersedes` не выбирает latest и не переключает ENT12r1 на ENT11r2. Разница r2 —
в том числе WR2-practice и полный отдельный practice.md, а не новый смысл W09.
Сборщик не превращает full revision в patch overlay.

Похожие D08/W00, D09/W05, W05/G01, W06c/G06, G02/G07 **не слиты**: различаются
scope, условия и/или последствия. Сходство тем — related link, не доказательство
эквивалентности. Ни один source artifact/registry record не переписан.

## 5. Сборка и проверка фактического draft

[Лабораторный materializer](../tests/test_agent_core_meaning_coverage.py) читает
каждый из5selected sources один раз с независимым от candidate ожидаемым pin,
собирает body из этих же checked bytes, а не повторным чтением по имени.
32draft bodies содержат31literal-preserved и1reviewed generalization;7entries
сохраняются unresolved (6holds + external D04). Полные quotes holds в body не
включаются; сами holds/gaps остаются явными, и перенос заблокирован.

Это trusted local laboratory reader, **не** замена ENT5 safe acquisition, не
hostile-tree/atomic snapshot guarantee. Capture проверяет выбранные bytes, но
не authentic origin/current owner decisions/реальность observations. Новый draft
не активируется в контексте агента, не пишется как portable normative payload.

Pinned registry metadata closure от ENT12r2:24revisions/90normative artifacts.
В этом срезе выбраны только5source files; остальные85показаны как unselected
artifact gaps этого среза (не утверждение, что раньше их вообще не исследовали).
Дополнительно все неразмеченные non-whitespace source spans выбранных файлов
сохранены как not_semantically_mapped — включая неразобранные supporting sections.
Metadata closure не объявляется semantic closure, source-span счётчик не доказательство
полноты универсального смысла. Core C01–C10 ссылается на44, path groups — на45.

Проверки: фактическая сборка draft, все10D и W00–W09, потеря одного alias origin,
изменённый scope/смысл/условие, потеря r2 practice requirement, неверный latest
retarget, локальное делегирование как новая доверенность, исчезновение holds/
artifact gaps/unmapped spans, self-attested authority/coverage/action flags,
coherently repinned ложный результат, source/predecessor mutation и отсутствие
reread при сборке из capture. Exact expected comparison консервативен: безопасный
иной пересказ тоже требует review; NLP-equivalence этим не доказывается.

## 6. Результаты квалификации и следующий шаг

- 18own methods PASS, без пропуска FAIL/skip; полный49/49modules PASS из
  approved hash-lock venv. Прежние44–45JSON/test bytes не менялись.
- Fresh read-only assembly реальных pinned sources:32bodies/13alias pairs;
  independent fresh expected readback/compare PASS. Unresolved:
  D04, PR04, G00, G04, G05, G08, G09;9non-whitespace unmapped supporting spans.
  Все release/export/activation/compatible-release flagsfalse.
- Ledger SHA-256:
  `c94a1b52e01e24339ebdb896b7c78f99ee12900df635c7a21c3ab13618ea5655`.
- Repo38checks/0warnings/0errors; rules901checks/0errors; navigation68checks/
  0errors; CSV/SELF-HASH, diff и pip check PASS. Public inventory пересчитан:
  243Markdown/86README/47research/49test modules.
- Все142catalog refs SHA/declared sizes PASS; registry/все tracked agent_system
  bytes неизменны относительно cadf600.19entities/31revisions/111norm/31approvals,
  без новых normative registrations/approvals/action permissions.

Следующий шаг — разобрать6holds на отдельные смысловые условия и role-specific
implementation statements, затем совместно сверить external D04/9supporting gaps
и реальные semantic dependencies. Сходные тексты не объединять без проверки области/
условий; local delegations/history не переносить как actual grants/active binding.
После полного applicable mapping нужна квалификация результирующего поведения,
не бесконечное расширение literal regression oracle. Произвольная semantic
эквивалентность, G05full semantics/G07/R4positive actual path/R6/R7/R8 открыты.
Результат текущего шага — partial research draft, не разрешённый переносимый выпуск.
