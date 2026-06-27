# Git Commit: Conventional Commits

## Что
Стандартизированный формат git commit сообщений по спецификации Conventional Commits. Обеспечивает читаемую историю и автоматическую генерацию changelog.

## Почему
Неформатные коммиты усложняют ревью, автоматическую сборку и поиск регрессий. Conventional Commits даёт единый язык для всей команды.

## Когда применять
При каждом коммите, подготовке к PR.

## Шаги
1. Выполни `git diff --staged` (или `git diff`, если nothing staged)
2. Проанализируй изменения по файлам
3. Сгенерируй commit message по Conventional Commits

## Формат
```
<type>(<scope>): <subject>

<body — что и почему, не как>

<footer — breaking changes, issue refs>
```

## Типы
| Тип | Когда |
|---|---|
| `feat:` | Новая функциональность |
| `fix:` | Исправление бага |
| `refactor:` | Рефакторинг без изменения поведения |
| `docs:` | Документация |
| `test:` | Тесты |
| `chore:` | Инфраструктура, зависимости |

## Правила
- Subject <= 50 символов, без точки в конце
- Body объясняет ПОЧЕМУ, а не ЧТО (что видно в diff)
- Если изменений много — предложи разбить на несколько коммитов

## Пример
```
feat(sender): add Excel attachment validation

Validate .xlsx files before sending to prevent Outlook crashes
on malformed workbooks. Uses openpyxl to check file integrity.

Closes #42
```

## Антипаттерн
```
fixed bug
```
или
```
commit
```
Без типа, без subject, без пояснения — такой коммит бесполезен для истории.
