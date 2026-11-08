# M1/I3 — основа coordinator, незарегистрированный implementation draft

**Не нормативная внедрённая ENT18r1 и не законченный coordinator.** Каталог r0001
пока рабочий кандидат. Регистрация exact состава/approve_revision намеренно не
выполняется до реализации runner и относящихся проверок. Никаких grants.

## Реализованные границы

session.py/session.schema.json: внутренний validate_session проверяет внешний
session pin, strict JSON/LF/closed fields, фиксированные purpose/criteria/profile,
task UUID, candidate pin, plan A/optional B и literal query pairing. Raw task text
не принимается. Documents ровно referenced plans, без retrieval/extra entries;
нужны native integer sizes, bytes, обязательные external refs. Совпадающие A/B
plan refs допустимы (один document), но будущий runner всё равно обязан сделать
две отдельные acquisitions. Наличие B context не назначает A current.

Plans проверяются прежним ENT9r2 _plan/ENT8r1 schema и пределами, затем exact
catalog/selection/artifact metadata и validate/agent_system.operator_trial context.
Точный profile (catalog_id/selection/artifacts/candidate) — **доверенный внутренний
аргумент**, не вход session и не произвольная source-derived политика. Future
coordinator должен получить его из проверенного installed состава с собственными
артефактами; этот bootstrap ещё НЕ реализован. validate_session сам не читает
source/не claim evidence/не stage и не доказывает permissions или полноту ledger.

Loader закрепляет 57 dependency artifacts/19 revisions будущего dependency
closure ENT9r2/ENT16r2/ENT13r1/ENT15r1/ENT17r1; сверяет bounded bytes до runpy.
Это installed expectation map как в старых tools, не второй registry и не
доказательство authenticity. Сам draft/schema/evidence.py должны быть доверенно
установлены caller; пока нет registry approval этих файлов. Writable hostile
installation/самоподмена защищённого caller не покрываются.

## Private CAS foundation, не общий журнал исполнения

EvidenceStore — single-use private local/operator-runs/new UUID. Relative paths
служебные, пользовательских filenames/destinations нет. Directories открываются
через directory FDs/NOFOLLOW, claims и file writes exclusive, no overwrite/resume/
auto-delete/rollback. Private operator-runs/run/objects 0700, files0600; общий
legacy local ancestor допускает owner-only write/без group/other write и может
быть 0755. Уже unsafe ancestor не исправляется chmod. Same-device/owner/filetype/
single-link/fingerprint и bindings используют pinned ENT15/ENT16 helpers.

put(bytes) — SHA-keyed immutable object, dedup после повторной проверки точных
bytes; seal(metadata) — один index.json с отсортированными refs и private JSON
metadata. Limits: 16 MiB/document, 128 MiB aggregate unique objects **и index**,
20064 files включая index. Duplicates не расходуют budget второй раз. Нарушение
лимита/записи/readback/fsync/final binding poisons store; позднейшее seal/put
запрещено. Partial files сохраняются, no retry overwrite. Финальная ошибка может
оставить index на диске: существование файла НЕ является успешным receipt.

verify_evidence(run_id,expected_index) — readonly exact pinned index/object
inventory/metadata/hashes/bindings check. Не создаёт отсутствующие dirs/файлы,
не chmod/fsync/write. Внешний pin обязателен, без автообновления из unknown файла.
consistent_private_evidence — согласованность CAS, **не** semantic journal/child
replay и не доказательство исполнения. Даже metadata со словом success само по
себе не подтверждает работу агента. Raw objects/metadata не печатаются функцией.

Защита от hostile same-uid/root/privileged mount не заявлена; trusted namespace,
Linux/kernel/interpreter/installation обязательны. Наблюдения не атомарны,
временные исчезнувшие изменения могут быть не замечены; fsync не является полной
моделью crash recovery. RAM/CPU не квотируются; caps не обещают, что максимальные
A/B plus reports одновременно поместятся. Секреты автоматически не распознаются,
данные private и не коммитятся/экспортируются. Owner задаёт допустимые данные.

## Что ещё не реализовано

run_operator_trial, trusted own-profile bootstrap, state machine/child journals,
полная candidate/handoff проверка, общий human report, procedure/versioned prompt,
semantic evidence replay по ENT10/17 и единый практический operator entry. Ни
source acquisition, stage, query, release/export/activation этот draft не запускает.
Полная T01–T30 matrix не исполнена; R2/M1 и I3 целиком не закрыты.

## Альтернативы, оптимизация и проверка

Выбрана небольшая основа над прежними pinned helpers вместо нового storage/
workflow framework. Плюсы: ограничения до write/source execution, без повторения
архивной семантики/дополнительных libraries, CAS dedup. Минусы: raw memory/privacy,
новый private persistence path, повторный hash/readback, необходимость отдельно
доказать orchestration/семантику. Эффективность пока подтверждена узко тестами
caps/dedup/no writes и storage lab, не benchmark coordinator.

verify.py/tests wrapper проверяют session errors/closed profile, mappings,
plan pins/context/limits, dedup/quotas, collisions/unsafe namespace, disk-full/
fsync/late binding/permissions failures, no resume/overwrite, readonly corruption/
FIFO/symlink/hardlink/inventory refusals, FD cleanup. Синтетические варианты внутри
subTests не считаются независимыми end-to-end scenarios. Окружение — прежний
hash-locked jsonschema с обязательными dependencies, без новых библиотек.
