# Wildberries Parser (CLI)

Готовый CLI-парсер результатов поиска/категорий/брендов Wildberries.

Возможности:
- Поиск по ключевым словам (пагинация)
- Бренд/категория по ссылке (fallback: извлекается запрос из URL)
- Выгрузка CSV/JSON (с шапкой и датой)
- Повторы/таймауты, прогрессбар

Быстрый старт:
```bash
PYTHONPATH=/workspace/wb_parser \
python3 -m wb_parser.cli --query "xiaomi" --pages 3 --csv out.csv
```

Примеры:
```bash
# Бренд/категория по ссылке (если страница блокирует HTML, используется fallback по запросу из URL)
PYTHONPATH=/workspace/wb_parser \
python3 -m wb_parser.cli --url "https://www.wildberries.ru/brands/xiaomi" --pages 3 --csv out_brand.csv

# JSON-выгрузка
PYTHONPATH=/workspace/wb_parser \
python3 -m wb_parser.cli --query "футболки и майки" --json out.json
```

Параметры окружения:
- `--dest` и `--regions` влияют на релевантность/наличие и цены. Значения по умолчанию подобраны для РФ.

Установка зависимостей (если нужно):
```bash
pip3 install --break-system-packages -r requirements.txt
```