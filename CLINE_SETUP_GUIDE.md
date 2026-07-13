# Инструкция: Настройка Cline с нуля на новом ПК
## Максимум качества, минимум токенов, автоматическая проверка

---

## Этап 1: Установка базового ПО

```
Шаг 1.1: Установи Node.js (LTS версия)
  - Скачай: https://nodejs.org (кнопка LTS)
  - Установи: галочка "Add to PATH" ОБЯЗАТЕЛЬНА
  - Проверь: открой cmd.exe -> напиши `node --version` -> должно показать v20.x.x

Шаг 1.2: Установи VS Code
  - Скачай: https://code.visualstudio.com
  - Установи: все галочки по умолчанию

Шаг 1.3: Установи расширение Cline
  - Открой VS Code
  - Нажми Ctrl+Shift+X (откроется вкладка Extensions)
  - В поиске напиши: "Cline"
  - Найди "Cline" от saoudrizwan.claude-dev
  - Нажми "Install"
  - После установки: появится иконка робота в левой панели
```

---

## Этап 2: Копирование твоих настроек со старого ПК

Тебе нужно перенести всего 2 папки и 1 (опционально) файл.

### Папка 1: `.cline` (главная папка со всеми настройками)

**Где лежит на старом ПК:**
```
C:\Users\<ТВОЕ_ИМЯ>\.cline
```
(например `C:\Users\Alexey Shilo\.cline`)

**Куда скопировать на новом ПК:**
```
C:\Users\<ТВОЕ_ИМЯ>\.cline
```
(такая же папка)

**Как скопировать:**
1. Открой проводник
2. В адресной строке введи `%USERPROFILE%`
3. Найди папку `.cline` (может быть скрытой -- включи "Скрытые элементы" в Вид)
4. Скопируй её на флешку / по сети
5. На новом ПК вставь в `%USERPROFILE%`

**Что внутри этой папки и зачем:**

```
.cline/
  rules/
    strict-ai.md          <- ГЛАВНОЕ: заставляет Cline быть кратким,
                              не тратить токены на "Здравствуйте", "Конечно",
                              писать only факты + код (NO_YAPPING)
  data/
    settings/
      cline_mcp_settings.json   <- Подключенные инструменты:
                                    sequential-thinking (логика),
                                    memory (память),
                                    playwright (браузер),
                                    filesystem (файлы),
                                    github (Git)
      providers.json             <- Провайдеры: OpenRouter, DeepSeek и т.д.
      models.json                <- Кастомные модели
      global-settings.json       <- Вкл/выкл автообновления
    globalState.json             <- ВСЕ твои настройки Cline:
                                    - какие модели для Plan и Act режимов
                                    - Auto-Approval (всё включено)
                                    - Parallel Tool Calling
                                    - Background Terminal
                                    - какие Rules включены
    secrets.json                 <- API-ключи (НЕ КОПИРУЙ, вбей заново)
```

### Папка 2: Документы Cline (Rules + Workflows)

**Где лежит на старом ПК:**
```
C:\Users\<ТВОЕ_ИМЯ>\OneDrive - Soudal N.V\Documents\Cline\
```

**Куда скопировать на новом ПК:**
Если есть OneDrive -- туда же. Если нет -- в любую папку, но потом нужно будет
поправить пути в Cline (см. Этап 4).

**Что внутри:**
```
Cline/
  Rules/
    strict-ai.md          <- Те же правила, но в OneDrive для доступа с любого ПК
    loops.md              <- 13 сценариев "замкнутого цикла":
                              - Independent Verifier Pass (проверка кода)
                              - Post-Edit Test Guard (тесты после правок)
                              - Ship PR Until Green (CI до зелёного)
                              - Pre-Commit Guard (тесты перед коммитом)
                              и другие
  Workflows/
    create-pr.md          <- Шаблон для создания Pull Request
  Hooks/                  <- Пусто (пока не используется)
```

### Файл (опционально): История задач

**Где лежит:**
```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\state\taskHistory.json
```

Скопируй, если хочешь видеть историю прошлых сессий. Не критично.

---

## Этап 3: Ввод API-ключей (ВАЖНО!)

**НЕ КОПИРУЙ** файл `secrets.json` со старого ПК!
Токены могли попасть в интернет или украдены. Лучше заведи СВЕЖИЕ.

### Что тебе нужно сделать:

**3.1. Зарегистрируйся на OpenRouter (рекомендуется):**
   - Перейди на https://openrouter.ai
   - Зарегистрируйся (можно через GitHub)
   - Пополни баланс (минимум $5-10)
   - Создай API-ключ: Dashboard -> API Keys -> Create Key

**3.2. Зарегистрируйся на DeepSeek:**
   - Перейди на https://platform.deepseek.com
   - Зарегистрируйся
   - Создай API-ключ: API Keys -> Create API Key
   - Пополни баланс

**3.3. GitHub Personal Access Token (для MCP GitHub):**
   - Перейди на https://github.com/settings/tokens
   - Generate new token -> Classic
   - Выбери права: `repo`, `workflow`, `user`
   - Скопируй токен (покажешь только один раз)

### Как ввести ключи в Cline:

**Способ A (через UI Cline -- проще):**
1. Открой Cline (иконка робота слева)
2. В выпадающем списке модели выбери "OpenRouter"
3. Введи API-ключ от OpenRouter
4. Затем переключи на DeepSeek -- введи API-ключ DeepSeek
5. Настройки сохранятся автоматически в `providers.json`

**Способ B (вручную -- если копируешь файлы):**
1. Открой `%USERPROFILE%\.cline\data\settings\providers.json`
2. Вставь новые ключи вместо старых
3. Открой `%USERPROFILE%\.cline\data\settings\cline_mcp_settings.json`
4. Найди `"GITHUB_PERSONAL_ACCESS_TOKEN"` -- замени на новый токен
5. Удали `%USERPROFILE%\.cline\data\secrets.json` -- пусть Cline создаст новый

---

## Этап 4: Настройка Cline в VS Code (все галочки)

Открой VS Code -> нажми на иконку Cline (робот слева).

### 4.1. Подключи MCP-серверы (инструменты)

Нажми на иконку "MCP Server" (пазл) в панели Cline.

Cline автоматически прочитает `cline_mcp_settings.json`.
Убедись, что видны 5 серверов и они зеленые (connected):
- [x] sequential-thinking (логическое мышление)
- [x] memory (память между сессиями)
- [x] playwright (браузер)
- [x] filesystem (работа с файлами c:\Projects)
- [x] github (GitHub)

Если какие-то красные -- нажми "Restart" рядом с ними.

### 4.2. Включи Rules (поведение Cline)

Нажми на иконку "Rules" (свиток) в панели Cline.

В разделе "Global Cline Rules" переключи в Enabled:
- [x] `strict-ai.md` -- **ОБЯЗАТЕЛЬНО**
- [x] `loops.md` -- **ОБЯЗАТЕЛЬНО**

В разделе "Global Workflow Rules" переключи в Enabled:
- [x] `create-pr.md` (если есть)

### 4.3. Настрой модель (самое важное для экономии токенов)

Нажми на иконку "Settings" (шестеренка) в панели Cline.

**Provider:**
- Выбери DeepSeek (или OpenRouter)
- Model: `deepseek-reasoner`

**Включи "Separate Plan/Act Models" (ОЧЕНЬ ВАЖНО):**
- Plan Mode: DeepSeek + `deepseek-reasoner` (дешёвая -- для рассуждений)
- Act Mode: DeepSeek + `deepseek-reasoner` (или OpenRouter + haiku-4.5)
- Это значит: на этапе планирования тратится меньше токенов

### 4.4. Auto-Approval (автоподтверждение -- экономит кучу токенов)

В настройках Cline найди раздел "Auto-Approval".

**Включи:**
- [x] Enable Auto-Approval (главный тумблер)
- Max Requests: `20` (можно 10-20)
- [x] Read files and directories
- [x] Read files externally (browser)
- [x] Edit files
- [x] Execute approved commands
- [x] Execute all commands (включай, если доверяешь)
- [x] Use browser
- [x] Use MCP tools
- Notifications: можешь отключить

### 4.5. Остальные настройки (тоже важные)

В настройках Cline (там же, шестеренка):

- [x] Enable Parallel Tool Calling (параллельные вызовы -- быстрее)
- vscode Terminal Execution Mode: `backgroundExec` (не блокирует VS Code)
- [ ] Auto-update: выключи (если не хочешь сюрпризов)

---

## Этап 5: Что делает каждый из твоих файлов (чтобы понимать)

### strict-ai.md -- почему он экономит токены

Файл содержит директивы, которые я читаю в начале каждой сессии:

```
NO_YAPPING           -> Я не пишу "Здравствуйте", "Конечно", "Давайте..."
                        Только: факты, списки, код. Экономия ~200 токенов/ответ
ZERO_HALLUCINATION   -> Я не выдумываю. Если не знаю -- читаю файл/команду
CITE_SOURCES         -> Каждое утверждение с ссылкой: файл:строка
PRODUCTION_ONLY      -> Запрещены TODO, pass, print(), заглушки
BLOCKER_FIRST        -> Нашёл баг/утечку/проблему -> СТОП и пишу [BLOCKER]
output_format        -> Ответы в таблицах, списках, коде. Мимум текста
refactoring_safety   -> Без тестов код не переписываю. Паттерн Strangler Fig
```

### loops.md -- почему он гарантирует качество

Когда ты пишешь команду-активатор, я запускаю цикл:

| Твоя фраза | Что происходит | Сколько итераций |
|-----------|----------------|------------------|
| "верификация" или "Independent Verifier Pass" | Запускаю `npm run build && npm run lint && npm test`. Если упало -- фиксю и снова. | до 8 |
| "проверка после правок" | После каждого изменения файла запускаю связанные тесты | ∞ |
| "Ship PR Until Green" | Коммит -> пуш -> PR -> CI. Если CI красный -- фиксю | до 10 |
| "Pre-Commit Guard" | Перед коммитом запускаю тесты. Если падают -- не коммичу | ∞ |
| "CI Failure Watcher" | Проверяю последний CI-run на ветке | до 12 |
| "npm Audit Fix Loop" | Фиксю по одной уязвимости за раз с тестами | до 10 |
| "Docs Sync After Edits" | После правок проверяю, обновил ли я документацию | до 3 |

### create-pr.md -- шаблон PR

Без него я бы спрашивал "как оформить PR?". С ним -- сразу делаю по шаблону.

---

## Этап 6: Финальная проверка (всё ли работает)

После настройки выполни эти тесты:

```
Тест 1: Запусти новую сессию Cline
  Напиши: "Как меня зовут?"
  Ожидаю: Короткий ответ (NO_YAPPING), не "Здравствуйте"

Тест 2: Проверка strict-ai
  Напиши: "Напиши hello world на Python"
  Ожидаю: Только код, без "Конечно, вот решение..."

Тест 3: Проверка MCP
  Напиши: "Какие MCP серверы у тебя подключены?"
  Ожидаю: Список sequential-thinking, memory, playwright, filesystem, github

Тест 4: Проверка Parallel Tool Calling
  Напиши: "Прочитай файлы C:\config\app.json и C:\config\db.json"
  Ожидаю: Читает ОБА файла одновременно, не по очереди

Тест 5 (опционально): Проверка Loop
  Напиши: "Сделай верификацию текущего проекта"
  Ожидаю: Запускает build -> lint -> test. Если ошибки -- фиксит.
```

---

## Шпаргалка: что писать Cline чтобы он проверял себя

| Ситуация | Команда Cline |
|----------|---------------|
| Хочу чтобы код прошёл все проверки | "верификация" |
| После правок проверь тесты | "проверка после правок" |
| Закоммитить и запушить в CI | "Ship PR Until Green" |
| Проверь перед коммитом | "Pre-Commit Guard" |
| Почини уязвимости npm | "npm Audit Fix Loop" |
| CI упал, разберись | "CI Failure Watcher" |
| Обнови документацию | "Docs Sync After Edits" |
| Проверь доступность UI | "A11y Audit Until Clean" |
| После мержа проверь всё | "Post-Merge Regression Guard" |

---

## Итого: что перенести на новый ПК (минимум)

Обязательно:
1. `%USERPROFILE%\.cline\` -- вся папка целиком
2. `%USERPROFILE%\OneDrive - Soudal N.V\Documents\Cline\` -- Rules + Workflows

Заменить (создать свежие):
3. API-ключи OpenRouter и DeepSeek
4. GitHub Personal Access Token

Не нужно (пересоздастся само):
- `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\cache\`
- `.cline\data\sessions\`
- `.cline\data\db\`
- `.cline\data\logs\`

---

## Почему эта конфигурация оптимальна по токенам

1. **NO_YAPPING** -- экономит ~200-500 токенов на каждом ответе
2. **Compact output (таблицы, списки, код)** -- меньше токенов чем текст
3. **Parallel Tool Calling** -- несколько инструментов за один ответ
4. **Auto-Approval** -- не ждёт твоего "Yes" на каждое чтение/запись
5. **Background Terminal** -- команды бегут в фоне, не тратят контекст на ожидание
6. **Separate Plan/Act** -- дешёвая модель для размышлений, быстрая для действий
7. **Loops** -- не нужно каждый раз объяснять "проверь код", достаточно одного слова

---

*Файл создан на основе реальной конфигурации Cline v4.0.8 с рабочего ПК Alexey Shilo.*
*Дата: 12.07.2026*
