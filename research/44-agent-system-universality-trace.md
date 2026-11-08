# Unit-level universality trace: критерии и bounded qualification

## 1. До реализации

Основание: владелец подтвердил [43](43-agent-system-rule-universality.md).
Следующий construct — **лабораторная trace выбранных реальных смысловых единиц**,
не автоматический классификатор и не нормативный адаптер ENT19r2.

Источники: immutable ENT1r1, ENT11r2 и ENT5r3; смешанный случай ENT2r3.
Для каждой единицы фиксировать exact source/version/hash, уникальный literal
locator/quote, контекст, зависимости смысла, justification, маршрут и ожидаемый
результат. В JSON хранится **исследовательская фикстура**, не второй registry и
не полный переносимый комплект. Source refs не превращаются в разрешения.

Acceptance до кода:

- high: сохранить десять связанных требований core, scope и W00–W02 methodology;
  сохранение точного выбранного текста — bounded fallback, не общая semantic proof;
- lower: один обоснованный общий принцип безопасного чтения, без Linux/kernel/path
  particulars; соответствие source проверить agent self-review, не owner approval;
- non-universal: команды запуска/описание платформы конкретного adapter исключить
  из универсальных правил, но не снять ограничения самого адаптера при его выборе;
- mixed/unknown: сложную группу link/mutable-tree требований ENT2§4 не объявлять
  ни классифицированной, ни безопасно отброшенной; обозначить остановленный маршрут;
- проверять и completeness, и отсутствие добавленных единиц/полномочий; reject
  потерянные условия, ослабление, усиление, leakage, неверный маршрут и unknown-as-pass;
- источник/контекст/выбранный результат закреплены независимо от проверяемого
  packet. Мутация packet вместе с его self-reported hashes не должна дать PASS;
- результат всегда limited: semantic_equivalence не установлена, selection не
  полная closure, release/export/activation запрещены, compatible release false.

## 2. Выигрыш, цена и риски

Выигрыш — trace проверяет направление universality→смысл и показывает source→output,
вместо сохранения всех bytes независимо от их роли. Прямой текст high units пока
снижает риск незаметного ослабления. Общий смысл lower unit предъявлен отдельно.

Цена — ручной выбор/обоснование, длиннее контекст high units, отсутствие автоматической
семантической эквивалентности. Exact fixture equality отвергает даже безопасный иной
пересказ: это намеренный bounded oracle, не критерий универсальности всех текстов.
Риск — ошибочная классификация/неполное покрытие/совместная ошибка автора и reviewer.
Поэтому self-review не называется independent, а unknown не обходится readiness flag.

Полные зависимости и связи решений в этом эксперименте **не квалифицированы**.
Registry/immutable bytes не меняются; конкретный adapter не получает новых permissions.

## 3. Trace и собственная semantic review

[Машиночитаемая trace](44-agent-system-universality-trace.json) содержит17единиц.
Полный source quote хранится в исследовательском evidence, не в draft rule payload.
Exact locator включает Unicode offsets и start/end lines, path/version/hash.

| Units | Класс и маршрут | Рассмотрение смысла и предел |
|---|---|---|
| C01–C10, ENT1r1 §Требования1–10 | high / preserve | Все десять требований с взаимными связями и scope сохранены буквально, включая ограничения неполного кандидата, разные permissions, historical versions и неизвестные проверки. Ни одна оговорка не пересказана |
| W00–W02, ENT11r2 | high / preserve | Полные связанные группы о соразмерности, источниках и неизвестном сохранены со scope. Соразмерность не отменяет mandatory checks; blocked target не останавливает независимую безопасную работу |
| G01, ENT5r3: запрет open после resolve при недоступной защите | limited / generalize | Оставлен запрет небезопасной подмены обязательного механизма в безопасном чтении выбранным адаптером; Linux/API не становятся универсальным требованием. Область не расширяется до всех действий агента. Наличие защиты в другой среде не утверждается |
| X01, platform support declaration ENT5r3 | non-universal / exclude | Конкретная поддержка Linux/kernel не включена в universal rules. Source declaration по-прежнему ограничивает выбор самого ENT5r3; exclusion не разрешает его применение в Windows |
| X02, команда verify.py ENT5r3 | non-universal / exclude | Конкретная repo-команда исключена. Общая обязанность проверки не удаляется: C07/W00 остаются; команда остаётся доступной в source |
| U01, ENT2r3§4 | mixed/unknown / hold | Большая связанная группа пока не разбита/не квалифицирована. Не даёт полный перенос ENT2, не выдаёт missing mandatory requirements за optional/irrelevant |

**Это review автора-агента**, не independent review и не новое согласование17
конкретных classifications владельцем. На C01–C10/W00–W02 используется буквальный
fallback внутри явно сохранённой области. G01 — кандидат обобщения; его контроль
в тестах — сравнение с предъявленным здесь expected text, не NLP semantic oracle.
W03+ и другие сущности/полная closure в эту выборку не входят. Не делается вывод,
что неизвестные вне выборки можно исключить или полный комплект готов.

## 4. Проверяемый механизм и первая ошибка

[Лабораторный regression oracle](../tests/test_agent_rule_universality.py) закрепляет
trace SHA независимо от candidate packet, проверяет hashes реальных source files,
unique quote/offsets/lines, contexts/dependencies и exact expected draft. Другой
пересказ не объявляется эквивалентным автоматически. Только стандартная библиотека;
новых зависимостей/production adapter/activation path нет.

Первый запуск дал25errors: locator G01 начинался/заканчивался внутри строк, а
первый reader ошибочно требовал whole-line equality. Исправлены locator format и
reader: добавлены точные Unicode offsets, проверка lines сохранена. Это исправление
фикстуры до freeze, не изменение immutable source. Ошибка не замаскирована PASS.

Негативные случаи: потеря high unit/scope/dependency/exception, ослабление и
усиление, unknown-as-approved/пропуск unknown, promotion non-universal command,
Linux/API overgeneralization, unsafe fallback, extra rule/metadata/context,
coherently repinned ложный результат, другая revision, self-attested independent
approval, fictional complete coverage, любой action flag, bool/int confusion.
Отдельно проверяется отсутствие excluded/held source quotes в draft и Linux
particulars в rule texts. Реальные source files не меняются; fault injection
выполняется на временных копиях.

PASS этих случаев значит лишь соответствие фиксированной trace и отказ от
конкретных мутаций. Один автор fixture/verifier может ошибиться согласованно;
злоумышленник, меняющий оба, не покрыт. Нет доказательства произвольной semantic
equivalence, полной классификации, правильности поведения агента или новой среды.

## 5. Результат квалификации и продолжение

- 26 собственных methods PASS: source pins/locators, выборка, positive draft и
  перечисленные mutation scenarios. Fixture SHA-256:
  `9ddbd974dc1cb691289d28ae2d48bc5a0bb4e4f9a8acda0807dcf4ee8e33dc82`.
- Первый full47modules:46PASS/1FAIL. Две style checks нового harness требовали
  `os.path.abspath(__file__)` и переход в ROOT. Исправлены без ослабления checks.
  Повторный **полный47modules:47PASS/0FAIL**, interpreter из approved hash-lock venv.
- Отдельно repo38checks/0warnings/0errors, pip check, relative links и diff checks
  PASS. Все142catalog refs SHA/declared sizes PASS; registry и все tracked
  agent_system bytes неизменны относительно cadf600. Новых approvals нет.
- Public inventory пересчитан:241Markdown/86README/45research/47test modules;
  summary и его SELF-HASH в manifest обновлены. Private state не включено.

Рабочий результат — проверяемая unit-level trace и консервативный regression oracle,
**не завершённый semantic adapter**. Исследовательский JSON хранит source evidence,
не предназначен для экспорта/активации. Draft rule payload не содержит literal
quotes excluded/held units; metadata references не дают разрешения переносить
полный source. При реальной упаковке будет нужен отдельный export allowlist.

Дальше: разбирать U01 на связанные смыслы с условиями/исключениями/зависимостями,
затем оставшиеся части methodology/governance и проверять completeness по точной
closure. Не разрешать generalization через потерю обязательных смыслов. Фактическая
адаптация и проверка поведения в согласованной новой среде — последующие уровни.
R4actual positive path/G05semantic completeness/G07/R6/R7/R8 этим не закрыты.
