# Full Audit Workflow

## Проверка после изменений
1. `git -C C:\Projects\Scan_Save_Send_qr status` — чистота рабочей директории
2. Синтаксис JS: проверить баланс `{}` и `()`, наличие `</html>`, `</script>`, `</body>`
3. `git -C C:\Projects\Scan_Save_Send_qr log --oneline -3` — последние коммиты
4. `git -C C:\Projects\Scan_Save_Send_qr diff --cached --stat` — объём изменений

## Проверки для PWA
- `manifest.json`: проверить start_url, scope, icons
- `sw.js`: проверить PRECACHE_URLS соответствуют реальным файлам
- `index.html`: проверить `<link rel="manifest">` и регистрацию SW

## Проверки для сканера
- `index.html`: проверить `qrbox`, `fps`, `formatsToSupport`
- Проверить что `addCode()` вызывается в `onScanSuccess()`
- Проверить что `saveSessionToHistory()` вызывается при `clearAll()`
