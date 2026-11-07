# ENT-0015 r0001 — частная локальная сборка неполного пробного комплекта

## Назначение, источник и граница

Protocol, depends_on ENT-0014 r0001. Три normative артефакта:
этот текст, [stage.py](stage.py), [verify.py](verify.py).
Основание — задание B, разрешённые ядром подготовительные испытания неполного
кандидата и условное делегирование владельца внедрять после проверок.
Это summary основания, не новая цитата согласия на конкретные bytes.
Частная архитектура/данные проекта и built-in инструкции не переносятся.

**Собирается только local trial, не совместимый выпуск/разрешённый export.**
Разрешения release/export/activation/transition остаются false. Нет публикации,
копирования в другую среду, распаковки/исполнения объектов или смены связки.
Полный G04/exporter/positive permission manager и G05/G07 не реализованы.
Это ограниченный механизм сборки для согласованного подготовительного испытания,
а не способ обойти blocked результат ENT-0014. Stage — отдельная операция
stage_trial / literal area agent_system.trial, не переименование export.

## Входы и подготовка

```python
stage_trial(candidate_bytes, expected_candidate, registry_blob, decisions, payloads)
```

Входы — bytes и внешние SHA-256/size candidate; decisions/payloads — path→bytes.
Доверенное основание pins задаёт caller; вычисленный hash неизвестного source
не аутентифицирует его. Caller отдельно фиксирует полный индекс/все объявленные
известные решения и получает bytes прежним ENT5 read_set под одним root fd.
Сама stage_trial source не открывает и не принимает source/destination paths.
Нет автоматического потребления ENT9 report или ENT12 receipt: связь run фиксирует caller.

Установка доверенная, source не может выбирать/писать код установки.
Четыре pins ENT14 и прежние transitive loaders/schema проверяются перед использованием;
собственные bytes ENT15 проверяются независимо по обычному approval установки,
не self-hash. Одновременно writable противником установка не поддерживается
(check→runpy TOCTOU). Новых библиотек нет; используются stdlib и прежняя approved
изолированная среда jsonschema с обязательными зависимостями.

Перед любым открытием output проверяются внешний candidate pin, ENT13 consistency,
exact records/closure/payload (сейчас 12 revisions / 34 artifacts), известный
validate/candidate scope и дополнительно stage_trial/agent_system.trial scope
выбранного payload через ENT6. Known block/неизвестный формат/ошибки запрещают
создание trial. Source authentication/global ledger completeness/atomic acquisition
не появляются от повторной проверки bytes; прежние ограничения B сохраняются.

## Фиксированная локальная область и модель угроз

Поддержан только Linux x86-64 с dir_fd, O_NOFOLLOW, O_EXCL, обычным fsync и
/proc/self/fd для тестов. Windows/junction/иные архитектуры/fallback отсутствуют.
Путь установки BASE доверен; вывод только `BASE/local/trials/<new UUID>/`.
Нет аргумента с произвольным местом назначения и нет выбора имени run со входа.
`agent_system/local/` исключён из Git и публичного inventory; содержимое не
становится export allowlist автоматически.

Существующий local должен принадлежать euid и не быть group/other writable;
trials должен принадлежать euid и не иметь group/other permissions. Неподходящие
существующие права не меняются: отказ, не chmod чужого объекта. Новые directories
700, новые regular files 600, без executable bits. На каждом открываемом дочернем
directory — O_DIRECTORY|O_NOFOLLOW; st_dev должен совпадать с parent.
Разные устройства отвергаются; это не openat2 NO_XDEV для всех mount-сценариев:
привилегированный same-device bind mount не доказан отсутствующим.

Предполагается **не изменяемый одновременно другим процессом того же uid/
привилегированным противником private namespace**. Права 700 защищают от других
непривилегированных пользователей, но не от владельца/root. Наблюдаемые подмены
отвергаются; обещания исключить все промежуточные изменения/обеспечить атомарность
нет. Проверки fd/binding не превращаются в гарантию после возврата функции.
Не использовать group-writable/shared staging или source-controlled installation.

## Формат пробного object store

Profile `ent-0015-r0001-linux-x86_64-object-store`, schema_version=1:

```text
local/trials/<UUID>/
  objects/<sha256>
  trial.json
```

UUID создаётся один раз. Уже существующее имя — отказ, не resume/retry/удаление.
В объектах только явно выбранные payload bytes, candidate descriptor, полный
registry bytes этого run и весь переданный известный ledger. Исторические
невыбранные нормативные файлы, software окружение, приватные связки и произвольное
дерево source не копируются. Descriptor остаётся envelope, не 35-м payload artifact.

Logical paths сохраняются только как metadata в trial.json, не используются
как output paths. Имена файлов — вычисленные 64-hex digests; symlink/hardlink
источника не воссоздаются, permissions/исполнение/платформенная адаптация исходных
файлов не переносятся. Сохраняются ровно проверенные bytes, не обещание восстановить
исходную файловую топологию. Поэтому это не непосредственно исполняемое дерево.

Одинаковые bytes хранятся один раз; одинаковый digest при разных bytes запрещён.
Manifest содержит profile/kind=incomplete_trial_snapshot/run_id, candidate/registry
hash+size, sorted payload/decision path+hash+size, readiness=incomplete_candidate
и закрытые gates. Это снимок конкретного index/known ledger, не ещё один индекс
для редактирования и не источник актуальных будущих ограничений.

Лимиты унаследованных входов: до 16 MiB файл/candidate, до 10000 entries,
registry+decisions+payloads суммарно до 64 MiB; candidate отдельно до 16 MiB.
Сохранённые object bytes не больше 80 MiB; manifest дополнительно до 16 MiB.
Это не глобальный CPU/RAM/disk quota. Нехватка места/ресурсов даёт отказ/partial,
а не обход hash/permissions/обрезание входов.

## Запись, readback и отрицательные результаты

1. Полностью проверить входы/known scope и построить manifest в памяти.
2. Открыть trusted BASE и затем local/trials под отдельными directory fds,
   без следования symlink. Claim нового UUID directory через exclusive mkdir.
3. Записывать objects через O_CREAT|O_EXCL|O_NOFOLLOW, loop частичных writes,
   fsync, закрытие и readback hash/size с проверкой regular type/uid/mode/
   st_dev/nlink=1/стабильных before-after fingerprints.
4. Проверить точный inventory objects и повторно прочитать все объекты по hash.
   Сохранить trial.json тем же exclusive способом, проверить manifest bytes и
   inventory run. Сверить bindings directory names↔открытые fds, fsync directories.
5. Вернуть staged_trial_only/staged=true и внешний manifest pin, local_ref,
   objects_count/stored_bytes. Это факт локального bounded шага, не общий допуск.

Нет completion marker, само наличие trial.json не доказывает завершение.
Потребитель должен иметь отдельно доверенный успешный receipt/manifest pin и
проверить содержимое заново; безопасный consumer произвольного чужого object store
ещё не реализован. Receipt/journal сохранять caller отдельно, например
`local/trial-evidence/<UUID>/`; **не добавлять файлы внутрь завершённого run**.
Точность/авторство самого receipt и факт исполнения не доказаны JSON-согласованностью.

При ошибке после mkdir — failed_partial, staged=false, local_ref остаётся для
диагностики. Частично созданные файлы/директории **не удаляются и не продолжаются
автоматически**. При ошибке до claim — failed/unsupported/blocked_known_scope;
служебные parent directories могут уже существовать/быть созданы. Показать код/
остаток, не делать автооткат или auto chmod; повторять только с новым UUID после
устранения причины. Ошибка позднего fsync может оставить manifest, но не успех.
Файловые fsync не доказывают crash/power-loss durability всего дерева/носителя.
Нет атомарной публикации/rename готового комплекта и нет обещания неизменяемости
сохранённых файлов после возврата.

## Проверки, обоснование и дальнейшее применение

В подготовленной изолированной среде:

```sh
python agent_system/staging/ent-0015/r0001/verify.py
python tests/run-all.py
```

Fixture outputs идут в отдельные TemporaryDirectory: реальная файловая система,
fd/symlink/FIFO/hardlink/permissions/write/readback, не подмена file type/stat.
Инъекции ошибок тестируют запись/сбой; cleanup временного fixture не является
автооткатом пользовательского trial. Runtime source fixtures доверенные, не
универсальный discovery. Поведение агента/новая среда/публикация не проверяются.

Выбран object store вместо зеркала произвольных logical paths: меньше опасной
destination path logic, dedup одинаковых bytes и явный состав. Цена — повторное
чтение/хэширование, дополнительный consumer/материализатор в будущем; напрямую
применить дерево нельзя. Альтернатива произвольного output path отвергнута для
этого этапа; безопасный exporter с grants/публикацией отложен. Это обоснование
эффективности ограниченного решения, не benchmark и не обещание всех свойств CAS.

Риски: неполный ledger/недоверенные исходные ожидания, hostile same uid/root,
переоценка structural PASS, stale snapshot, отсутствие consumer и положительных
полномочий. Они не закрыты staged_trial_only. После появления новых известных
решений нужен новый run; старый snapshot сам себя не обновляет и не разрешает
применение. Изменение самого ENT15 проходит те же immutable версии/учёт/проверки;
approval компонента не выпускает/активирует содержащую его систему.
