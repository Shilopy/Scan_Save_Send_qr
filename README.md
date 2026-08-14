# 📷 QR Сканер ЧЗ

> **PWA-сканер QR-кодов и DataMatrix «Честного знака»**: отсканировал → сохранил → отправил. Работает на любом телефоне, устанавливается на главный экран, доступен офлайн.

<p align="center">
  <img src="icon-512.png" width="120" alt="QR Сканер ЧЗ">
</p>

<p align="center">
  <a href="https://shilopy.github.io/Scan_Save_Send_qr/"><img src="https://img.shields.io/badge/🚀_Открыть_приложение-5b9cf6?style=for-the-badge" alt="Открыть приложение"></a>
  <a href="https://shilopy.github.io/Scan_Save_Send_qr/manifest.json"><img src="https://img.shields.io/badge/PWA-ready-a78bfa?style=for-the-badge" alt="PWA"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-4ade80?style=for-the-badge" alt="License"></a>
</p>

<p align="center">
  📲 Наведи камеру телефона на QR-код, чтобы открыть приложение:
</p>

<p align="center">
  <img src="https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=https%3A%2F%2Fshilopy.github.io%2FScan_Save_Send_qr%2F" alt="QR-код приложения" width="180">
</p>

---

## ✨ Возможности

| | |
|---|---|
| 🔍 **Сканирование** | QR-коды и DataMatrix через камеру, автофокус, зум и фонарик (Chrome) |
| 🏷 **Категории** | Лёгкая промышленность / Строительные материалы |
| ✂️ **Умная обработка** | Автоматически берёт 31 символ кода, чистит служебные символы |
| 🛡 **Защита от дублей** | Повторные коды не добавляются |
| 📳 **Отклик** | Вибрация + звуковой сигнал при каждом скане |
| 🎯 **План сканирования** | Целевое количество с прогресс-баром и оповещением о достижении |
| 💾 **Экспорт** | `.txt` и `.csv` (UTF-8 BOM, CRLF — корректно открывается в Excel и Блокноте) |
| 📋 **Копирование / отправка** | Весь список в буфер или через нативный Share (Telegram, WhatsApp, email) |
| ✏️ **Ручной ввод** | Если камера недоступна |
| 🗂 **История сессий** | Поиск и восстановление предыдущих сканирований |
| 📲 **PWA** | Установка на главный экран любой модели телефона, работа офлайн |
| 🌙 **Тёмная/светлая тема** | Автоматически по настройкам системы |

## 🚀 Быстрый старт

Открой [приложение](https://shilopy.github.io/Scan_Save_Send_qr/) в Chrome или Safari на телефоне:

1. Нажми **«📲 Установить»** внутри приложения (или меню браузера → «Добавить на главный экран»)
2. Выбери категорию товаров
3. Нажми **«📷 Запустить камеру»** и наводи на коды
4. По окончании — **💾 .txt**, **📊 .csv**, **📋 Копировать** или **📤 Поделиться**

## 🧪 Тесты

```bash
node test/run-tests.js
```

Проверяет нормализацию кодов, защиту от дублей, XSS-экранирование, экспорт CSV/TXT и историю — без браузера.

## 🛠 Технологии

- Чистый HTML5 / CSS3 / JavaScript — **ни одной зависимости в рантайме, кроме** [html5-qrcode](https://github.com/mebjas/html5-qrcode) с CDN
- Web Audio API · Vibration API · Share API · Service Worker (offline) · PWA Manifest
- Хостинг: GitHub Pages (деплой автоматический через GitHub Actions)

## 📁 Структура

```
index.html      — всё приложение (HTML + CSS + JS)
sw.js           — Service Worker (офлайн-кэш оболочки)
manifest.json   — PWA-манифест
guide.html      — инструкция пользователя
icon-*.png      — иконки приложения
og-image.png    — превью для соцсетей
test/           — автотесты
```

## 📄 Лицензия

MIT
