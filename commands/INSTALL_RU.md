# Патч !play и /play для Esil (актуальный GitHub-проект)

Проблема: бот пишет «На Render нужно задать RELAY_URL и RELAY_TOKEN.». Эта строка есть в старом `commands/music_relay.py`, а старый `commands/music_prefix.py` вызывает relay без локального поиска.

## Установка — замените именно файлы, а не загружайте ZIP в репозиторий

1. Распакуйте архив на компьютере.
2. В GitHub откройте репозиторий, ветку **main**, папку **commands**.
3. Откройте и замените содержимое **всех четырёх** существующих файлов:
   - `commands/music_relay.py`
   - `commands/music_prefix.py`
   - `commands/music_search.py`
   - `commands/music_audio.py`
   Если GitHub не даёт перезаписать файлы через Upload files, откройте каждый, нажмите Edit, вставьте новый текст и Commit changes. Можно также использовать git локально, затем push.
4. В `commands/music_relay.py` через поиск текста (Ctrl+F) найдите `HOTFIX-2026-10-17-v2`. Если не нашли — файл не заменён.
5. Убедитесь, что старой фразы `На Render нужно задать RELAY_URL и RELAY_TOKEN.` **нет** в `commands/music_relay.py`.
6. В Render откройте сервис, проверьте branch и последний commit SHA, затем Manual Deploy -> Deploy latest commit. Не запускайте старый коммит.
7. В логах при старте ОБЯЗАТЕЛЬНО найдите:
   `[Music backend] HOTFIX-2026-10-17-v2 loaded; local yt-dlp fallback enabled`
   Если строки нет — загружен не тот код/не та ветка/не тот сервис; не надо вносить RELAY_TOKEN наугад.
8. В Discord, находясь в голосовом канале, проверьте `!play farben`, затем выберите YouTube или SoundCloud. Затем `/play`.

## Важное о сервере

- `yt-dlp` должен быть установлен, а YouTube/SoundCloud должны быть доступны с IP Render. В прежних логах `yt-dlp` установился успешно.
- Для **звука** нужен FFmpeg, которого в обычном Python Runtime Render может не быть. Для этого проект содержит Dockerfile с FFmpeg и Node.js. Если после поиска трека звук не играет — используйте отдельный Docker Web Service, созданный из Dockerfile (старый Python-сервис выключите, чтобы не запускать двойной бот).
- Сама надпись `Your service is live` подтверждает запуск, но не работу музыкального поиска.
- Не добавляйте `groq.py` или `signal.py` в корень. Правильный путь — `core/groq.py`, `core/signal.py`.
- Этот ZIP **не изменяет** AI-модули, команды модерации или данные Supabase.
