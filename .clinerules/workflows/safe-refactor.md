# Safe Refactor Workflow

## 1. Предварительный анализ
- Прочитать все файлы, которые планируется менять
- Проверить `git status` и `git log --oneline -3`
- Убедиться, что рабочая директория чиста

## 2. Критические проверки для больших файлов
- Если файл >10KB — использовать `filesystem__write_file`, НЕ `write_to_file`
- После записи проверить синтаксис: сбалансированность скобок `{}` и `()`
- Проверить что файл завершается `</html>` или корректным закрывающим тегом

## 3. Git операции
- Всегда использовать `git -C <абсолютный_путь>` вместо `cd`
- Для Windows: `cmd /c C: && cd C:\Projects\... && git ...`
- После `git init` сразу проверять `git rev-parse --show-toplevel`
- Перед commit проверять `git status --short` для отслеживания изменений

## 4. GitHub API
- Перед вызовом MCP проверять обязательные параметры по документации
- `create_or_update_file` требует: owner, repo, path, content, message, branch
- `push_files` требует массив `files` с полями `path` и `content`
- Если 3 одинаковых вызова подряд вернули ошибку — остановиться и сменить подход

## 5. Откат при ошибке
- Если commit ещё не сделан: `git restore --staged .` и `git checkout -- .`
- Если commit сделан: `git revert HEAD`
- Если push сделан: `git revert HEAD && git push origin main`
