# Контекст проекта: Scan_Save_Send_qr

## Архитектура
- PWA-приложение (всё в одном index.html + manifest.json + sw.js)
- Сканер QR-кодов Честного знака через библиотеку html5-qrcode
- Две категории: Лёгкая промышленность / Строительные материалы
- Сохранение, копирование, отправка кодов

## Ключевые файлы
- `index.html` — основное приложение (HTML + CSS + JS)
- `manifest.json` — PWA манифест
- `sw.js` — Service Worker
- `guide.html` — инструкция пользователя
- `icon-192.png`, `icon-512.png` — иконки
- `.clinerules/` — правила для Cline

## Ключевые переменные JS
- `codes` — массив объектов `{text: string, cat: 'light'|'build'}`
- `currentCategory` — 'light' или 'build'
- `scanActive` — флаг активности сканера
- `scanner` — экземпляр Html5Qrcode
- `sessionId` — ID текущей сессии для истории

## Важные замечания
- GitHub Pages: https://shilopy.github.io/Scan_Save_Send_qr/
- PWA scope: /Scan_Save_Send_qr/
- Для установки на телефон: Chrome → "Добавить на главный экран"
- Все данные хранятся в localStorage (ключи: ssq-codes, ssq-history, ssq-theme, ssq-category, ssq-target)

## Правила работы с файлами
- Файлы >10KB писать через `filesystem__write_file`, НЕ через `write_to_file`
- Для git: `git -C C:\Projects\Scan_Save_Send_qr <команда>`
- Для Windows: `cmd /c C: && cd C:\Projects\... && команда`
- После `git init` проверять `git rev-parse --show-toplevel`
- После записи проверять баланс скобок `{}` и `()`
- GitHub API: `create_or_update_file` требует owner, repo, path, content, message, branch
- GitHub API: `push_files` требует массив `files` с `{path, content}`
- После 3 одинаковых ошибок MCP — менять подход
