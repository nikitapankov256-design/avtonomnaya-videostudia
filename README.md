# За закрытой дверью — бесплатная сборка видео

Репозиторий собирает вертикальный сериал в GitHub Actions без платных API.

## Конвейер
- Python + Pillow: отрисовка кадров и процедурная анимация лиц.
- FFmpeg: сборка MP4, кодирование H.264/AAC.
- Edge TTS: русская речь при доступности сети.
- espeak-ng: офлайн-резерв озвучки.
- ffprobe: проверка готового видео перед публикацией artifact.

## Ограничения качества
Текущая технология создаёт иллюстрированную анимацию (motion comic), а не съёмку живых актёров и не фотореалистичное видео. Движение рта процедурное, не фонемно-точное. Бесплатный GitHub Actions runner не предоставляет GPU для тяжёлой нейросетевой генерации. Резервный espeak-ng синтетический и заметно уступает нейросетевой речи.

## Сборка через GitHub
Откройте Actions → «Собрать За закрытой дверью — серия 1» → Run workflow. После успешного выполнения скачайте artifact `za-zakrytoy-dveryu-episode-01`. Изменения в `series1/**` запускают workflow автоматически.

## Локально
Python 3.11+, FFmpeg, ffprobe, fonts-dejavu-core, espeak-ng:
```bash
python -m pip install -r requirements.txt
python series1/make_episode.py
```
Выход: `output/za_zakrytoy_dveryu_ep01.mp4`.

## Проверки
```bash
python -m compileall -q series1
ffprobe -v error -show_entries format=duration,size -of default=noprint_wrappers=1 output/za_zakrytoy_dveryu_ep01.mp4
```

## Сторонние компоненты
Pillow, FFmpeg, Edge TTS и espeak-ng имеют собственные лицензии и условия. Репозиторий не содержит голосовых моделей и не предоставляет права на коммерческое использование сторонних голосовых сервисов.
