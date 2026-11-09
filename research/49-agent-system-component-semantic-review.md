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
