# Lossless universal-rule adapter и независимая проверка результата

> **Снято как основное направление после уточнения владельца.** Сохранение
> смысла определяется универсальностью смысловой единицы, а не lossless-копией
> всего набора. Актуальный контракт — [43](43-agent-system-rule-universality.md).
> Lossless может проверять неизменность выбранного source/basis, но не заменяет
> отбор/обобщение/исключение. Начатый unregistered experiment сохранён отдельно
> в stash; исход прерванного запуска tests неизвестен, PASS не заявляется.
> Никаких новых normative revisions/approvals/активации по этому проекту нет.


## 1. Приоритет владельца и граница утверждения

Baselinecadf600:19entities/31revisions/111norm/31approvals/142refs.
Владелец явно поставил **сохранение смысла универсальных правил и проверку
результата в приоритет**. [41](41-agent-system-inactive-binding-planner.md) даёт
лишь declared capability resolution, не semantic adapter/actual activation.

Не доказывать semantics одним hash/green test. Различаем:
1. Полноту/идентичность текста и значимых metadata (version/scope/dependency/
   known decisions/origin role), без paraphrase/summary/filter/new permission.
2. Фактически прочитанный результат материализации, сравнённый с независимо
   закреплённым **до результата** исходным basis, не self-hash output.
3. Операционное применение/precedence/visibility/token limits/agent behavior в
   конкретной среде. Этот уровень отсутствует и не наследуется от1/2.

Выбран первый bounded adapter: lossless inert representation, без смыслового
переписывания вообще. Контейнер data-only, не prompt injection/active context.
Сериализация сохраняет все source bytes в base64, роли/индекс/records/решения
раздельно, без присвоения system/developer priority. Lexical storage order не
instruction precedence. Смысл не «оптимизируется» и не заменяется выжимкой.
Это реальная qualification lossless representation/result, **не** proof поведения
агента/универсальной совместимости/full G05/G07/R6. Изменяющее смысл преобразование
не поддержано; его нельзя принять потому, что текст «похож».

## 2. До кода: архитектура и alternatives

ENT19r2 six files adapters/ent-0019/r0002/{adapter.py,adapter.schema.json,
procedure.md,prompt.md,usage.md,verify.py}. Full explicit profile depends_on
19r1+18r1, supersedes19r1 без switch consumers/history. Старые immutable6files
не трогать. Core/governance/work не копируются как второе нормативное ядро.

Производитель: native ENT9r2 single capture в adapt/agent_system.connection,
полный known entity ledger, exact selected closure. До преобразования private
ENT18 store запечатывает input bytes+plan/native reports/basis descriptor.
Source provenance/freshness/global completeness этим не аутентифицированы.
Операция1 возвращает только external basis receipt. Операция2 читает pinned
basis, строит inert result и пишет его в **другой** private validation store.
Это локальное validation evidence, не destination export/compatible release.
Реального target/agent context нет, hidden instructions/private project вне source.

Verifier получает expected_basis_receipt **от caller отдельно**, не из output,
открывает actual result bytes заново и сравнивает каждый row/body/role/metadata
с исходным basis. Не вызывает renderer как собственный oracle. Повторяет binding
stored source bytes/known graph, но не source acquisition/host observations.
Произвольный caller может солгать о trust anchor — protected installation/operator
остаётся предпосылкой, signature/crypto identity не добавляется.

Alternatives: свободная LLM-paraphrase (meaning proof отсутствует, отклонена);
ручной semantic review любых изменений (нужен отдельно, не для silent rewrite);
lossless/inert + independent per-field/result readback (выбран). Плюсы — не теряет
оговорки/отказы/исключения и даёт физически проверенный результат. Цена — объём
base64/полный snapshot/private storage, нет сокращения context/token budget,
не решены hosted consumer semantics. При лимите stop, не truncation.

## 3. Критерии до реализации

| ID | Критерий | Проверка |
|---|---|---|
| L01 | Explicit private-validation ack/closed pinned request+plan | Preflight failures до IO, native ref types |
| L02 | Exact own6/approved graph/полный normative closure | Missing/extra/version/scope/dependency/source tamper |
| L03 | Один native source capture и sealed basis до renderer | Count/no source reread, separate receipts |
| L04 | Все bytes Unicode/BOM/newline/code/JSON сохраняются без normalization | Exact per-body decode/direct equality |
| L05 | Full known ledger/negative conditions retained; relevant adapt block stops | Native full-stream/unknown/restriction tests |
| L06 | No role promotion/priority/new grant/summary/deletion/reordering | Independent negative verifier tests |
| L07 | Verifier uses external expected basis, not output-derived authority | Wrong/rebound basis tests/coherent forged output |
| L08 | Actual result CAS reopened/readback; no renderer-as-oracle | Physical altered result/fault tests |
| L09 | Result reports representation equality separately from behavior | All effective action/activation flags false |
| L10 | Limits stop rather than shorten; partial retained, no rollback/adopt | Bound/fault tests |
| L11 | Old142refs/records/bytes/consumers unchanged | Full pre/post suites/freeze proof |
| L12 | Actual protected installed-source lab, not actual agent/environment | Documented entry/private receipt/independent readback |

Actual semantic behavior/platform target/R7/R8/activation не выбираются этим
продолжением. Meaning-preservation вне data representation требует explicit
consumer contract и применимых behavioral observations/review, не готового bool.
