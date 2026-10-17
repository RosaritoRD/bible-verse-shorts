# 💸 Savings and tips

## Spend less

1. **Cost per Short: 0.** It uses no paid API: local Bible, local FFmpeg, YouTube music and free stock backgrounds.
2. **Transcription without an API.** Clipping uses `faster-whisper` *small* on the CPU (int8). No GPU needed and no paying per minute of audio.
3. **The Bible is prepared once.** `biblia.py preparar` leaves a local JSON, so there are no web lookups for each video.
4. **Backgrounds loop on their own.** A short clip covers a long Short, so you need less footage.
5. **Everything in batches.** A batch of 30 Shorts runs with one command while you sleep.

## Do it better

1. **The verse is the hook.** Pick verses that answer a need (anxiety, fear, family, provision). Generic ones perform worse.
2. **One verse per screen.** Long ranges are tiring; 1–3 verses per Short is better.
3. **Don't leave test material in `entrada/`.** The random background and music picker would use it in real Shorts.
4. **Vary the music.** With 10–20 different tracks, your Shorts don't all sound the same.
5. **Ideas to extend it:** automatic upload to YouTube, a voice reading the verse with [voz-local](https://github.com/RosaritoRD/local-voice), or thumbnails with the verse.
