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

## Ключевые переменные JS
- `codes` — массив объектов `{text: string, cat: 'light'|'build'}`
- `currentCategory` — 'light' или 'build'

## Важные замечания
- GitHub Pages деплоит из корня репозитория
- URL: https://shilopy.github.io/Scan_Save_Send_qr/
- PWA scope: /Scan_Save_Send_qr/
