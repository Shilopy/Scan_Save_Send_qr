# Логирование в AutoSender

## Что
Используй `logging` с `RotatingFileHandler` для всех трёх компонентов (UI, сервис, watchdog). Формат: `%(asctime)s - %(levelname)s - %(message)s`. Уровень: INFO.

## Когда применять
- При запуске/остановке сервиса
- При отправке письма (успех/ошибка)
- При обнаружении новых файлов
- При ошибках любого уровня
- При heartbeat (каждую минуту в service.log)
- При проверке watchdog (каждые 5 минут)

## Когда НЕ применять
- Для отладки циклических операций (используй `logger.debug()`)
- Для сообщений пользователю в UI (используй `st.success()`, `st.error()`, `st.warning()`)

## Почему
- 3 независимых процесса пишут в разные файлы: sender.log (UI), service.log (сервис), watchdog.log (watchdog)
- RotatingFileHandler не даёт логам разрастись бесконечно (5 MB, 3 бэкапа)
- Единый формат упрощает поиск по всем логам

## Пример (правильно)
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/service.log', encoding='utf-8', maxBytes=5*1024*1024, backupCount=3),
        logging.StreamHandler()
    ]
)
```

## Антипаттерн (неправильно)
```python
# Плохо: нет ротации, файл будет расти бесконечно
logging.basicConfig(filename='logs/service.log')
```

## Связанные правила
- `core/error-handling.md` — что логировать при ошибках
