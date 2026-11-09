# Component boundary review: не потерять смысл при обобщении

## 1. Критерии до кода

Владелец подтвердил48/продолжение. Шаг — focused semantic boundary review всех
26component documents и challenge review фактического preview. Это **не** заявление
о полном clause-level покрытии26файлов и не automated NLP evaluator.

Acceptance:

- Для каждого документа закрепить exact reference и source anchor существенной
  границы, её условия/предел, соответствующие уже предъявленные правила или gap.
- Не добавлять правило за каждое повторение темы. Различить hash≠auth и отдельное
  требование independently established expected basis; record-once≠action-once;
  replay/archive≠new acquisition; safe namespace/schema≠разрешённое содержимое.
- Для найденных gaps предъявить только source-backed conditional application
  notes, с общей формулировкой без Linux/API/private-path particulars. Оригинальные
  контракты и ограничения выбранных components остаются обязательными.
- Не ослабить high-universality rules и не усилить их до «всегда перечитывать»,
  «никогда не делать recovery», «любая модель запрещена», «нужна криптография».
  Независимая безопасная работа, согласованный recovery и допустимое reuse остаются.
- Challenge cases должны иметь source/rule refs, явные условия, требуемый вывод
  и запрещённый вывод, включая ослабление **и усиление**. Review — фактически
  выполненный автором разбор, не выдуманный independent/owner review.
- Mechanical tests подтверждают refs/draft/data/неизменность/negative mutations,
  **не** correctness arbitrary language answers. Semantic judgement отдельно
  предъявлено как agent self-review, не повышается до machine/NLP proof.
- Новый предмет review —48preview + conditional notes из этого report. Старые
  preview/fixtures не переписываются, параллельного нормативного ядра/patch-overlay
  для active versions нет. Все actuation/authority/readiness gates по-прежнемуfalse.
- Никаких новых normative registrations/approvals/export/activation/новой среды
  или сторонних dependencies. Все26 имеют focused result и оставшийся review scope,
  но не фиктивную «полную semantic qualification» по одному anchor.

## 2. Выигрыш, цена, риски

Выигрыш — оценка конкретных выводов из текста вместо одних hash/counter checks;
выявление утраты условий на стыке общих правил и component contracts.
Цена — source mapping и ручное суждение о применимости. Риск — один автор audit/
обобщений/challenge cases; независимость не заявлять. Новый gap не должен просто
переименовываться в PASS после добавления expected строки в regression fixture.

## 3. Что фактически просмотрено

Для каждого из26documents выбран **один** участок, где текст задаёт границу
доверия/полномочия/приобретения/однократности/публикации, и проверено, покрыт ли
его смысл уже предъявленными правилами. Это сознательно не полное clause-level
отображение: файлы суммарно содержат сотни предложений, многие из которых
описывают локальные API/лимиты/структуру. Один anchor на документ не объявлен
полным semantic coverage.

Результат:7documents покрыты выбранной границей существующими правилами и
19нуждаются в дополнительном условии. 26review rows содержат exact path, смещения,
дословный needle, judgement, ссылки на существующие rule ids и remaining scope.

## 4. Пять условных примечаний

Вместо26повторов добавлены5source-backed обобщений. Они не заменяют исходные
контракты и действуют только там, где выбранный контракт требует их условия.

- **N1 — независимое основание и метки.** Ожидания/authority context ставятся
  независимо от проверяемого source до оценки; hash, actor label, explicit flag,
  согласованный с собой отчёт и установленные входом tools не создают доверие,
  согласие или полномочие. Не читать как обещание криптографии/универсальной
  защиты от враждебной среды.
- **N2 — запись проверки не действие.** Request UUID/record/recognition не
  доказывают однократность внешнего эффекта и не создают разрешение; для действия
  нужен предусмотренный контракт полномочия/claim/исполнителя и отдельная проверка
  результата.
- **N3 — актуальное состояние и unknown outcome.** Найденный head/новая дата/
  согласованный старый snapshot не заменяют внешнее ожидание; при stale/busy/
  partial/неизвестном исходе — остановка затронутого перехода без слепого retry/
  adoption/удаления/rollback. Согласованный recovery/read-only история не
  запрещены; глобальная свежесть не обещается.
- **N4 — допустимый namespace не разрешение публикации.** Schema/path/safe label
  не доказывают допустимость фактического private content; вынос — по согласованной
  проекции полей, без raw maps/секретов по умолчанию и без обещания автоматического
  secret detection.
- **N5 — отдельная acquisition, когда контракт её требует.** Архив/replay/те же
  root и plan bytes/readback не заменяют предписанную новую acquisition; отсутствие
  B фиксируется как not_requested, A не выдаётся за current B. Это не требует
  перечитывать source на каждом шаге: reuse одного verified capture сохраняется.

Примечания включены в [уточнённый preview](49-agent-system-rule-preview.md)
отдельным разделом, после86смысловых блоков, чтобы reviewer видел и правила, и
предлагаемое дополнение. Preview48 сохранён в прежнем виде; это производный
документ, не новая версия/active context.

## 5. Challenge review фактического preview

24cases проверяют вывод в обе стороны — ослабление и **усиление**. Примеры:

- self-computed pins/`trusted`/actor label → нельзя вывести одобрение; при
  независимо закреплённом основании нельзя требовать новой криптографии от одной
  фразы source (Q01–Q03).
- coherent offline bundle/check_once/UUID → нельзя объявить исполнение, release или
  физическое потребление grant; будущий отдельно согласованный actuator нельзя
  одновременно запретить текущей границей (Q04–Q07).
- найденный head/старый snapshot/прерванный write → нельзя adopt или повторить
  слепо; разрешённый recovery и historical read-only не запрещены (Q08–Q12).
- allowlisted prefix/safe report/schema → нельзя публиковать private content и
  нельзя обещать полную очистку секретов; безопасная проекция допустима (Q13–Q15).
- отсутствие B/совпавшие bytes/тот же capture → нельзя подменить B архивом, но
  reuse разрешённого capture не требует нового чтения; отсутствие optional B не
  останавливает независимую безопасную работу (Q16–Q19).
- URI/новое approval/defined-only locator/существующий manifest/«начать задачу» →
  не дают network execution, scoped lift, semantic PASS, ready release или
  independent review (Q20–Q24).

Всеcases имеют `agent_semantic_self_review_not_independent`. Механический тест
проверяет наличие/структуру/refs/неизменность, **не** правильность произвольного
языкового вывода.

## 6. Проверки

[Лабораторный semantic-review validator](../tests/test_agent_component_semantic_review.py):
8own methods PASS. Проверяются pins48fixture/preview,26real anchors (границы строк
и присутствие needle), уникальность очереди, ссылки на существующие rule ids,
условные примечания/их пределы и negation markers,24challenges в обе стороны,
воспроизводимость preview, а также отклонение подмены anchor/review level/
invented rule/active authority/удалённых reviews/notes/challenges/ложных
full-mapping/independence/contract flags.

Preview SHA-256: `8950c0d91e70f11e551fff46ec2252218030f490b9caab9e45a8a0099071eb80`.
Review ledger SHA-256:
`2a403f29961bf6e12aba707b21b2cda6c3c0b4f2936943c590202ab8110bdc7e`.
48preview/fixture байты не менялись.

## 7. Предел и следующий шаг

Это один agent pass по выбранным границам. Полное clause-level отображение всех26
файлов не выполнено; независимый/owner review не проводился; реальное поведение,
target rendering, совместимость и актуальные полномочия не проверены. Оставшиеся
вопросы — не «добавить ещё PASS», а проверить, не пропущены ли иные существенные
условия в невыбранных участках, и подтвердить вывод независимо.

Следующий предметный шаг — второй проход по оставшимся участкам с приоритетом
условий/исключений, затем независимая проверка выбранных выводов и preview.
R4actual positive path/G05full/G07/R6/R7/R8 остаются открыты; release/export/
activation/новая среда не выполнялись и не разрешались.
