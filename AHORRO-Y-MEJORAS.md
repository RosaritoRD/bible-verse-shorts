# 💸 Ahorro y mejoras

## Gastar menos

1. **Coste por Short: 0.** No usa ninguna API de pago: Biblia local, FFmpeg local, música de YouTube y fondos de stock gratuitos.
2. **Transcripción sin API.** El clipping usa `faster-whisper` *small* en CPU (int8). No hace falta GPU ni pagar por minuto de audio.
3. **Biblia preparada una vez.** `biblia.py preparar` deja un JSON local, así que no hay consultas a ninguna web en cada vídeo.
4. **Fondos que se repiten solos.** Un clip corto sirve para un Short largo, de modo que necesitas menos material.
5. **Todo en serie.** Un lote de 30 Shorts se hace con un comando mientras duermes.

## Hacerlo mejor

1. **El versículo es el gancho.** Elige versículos que respondan a una necesidad (ansiedad, miedo, familia, provisión). Los genéricos rinden menos.
2. **Un versículo por pantalla.** Los rangos largos cansan; mejor 1–3 versículos por Short.
3. **No dejes material de prueba en `entrada/`.** El sorteo de fondos y música lo usaría en Shorts reales.
4. **Varía la música.** Con 10–20 pistas distintas, los Shorts no suenan todos iguales.
5. **Ideas para ampliarlo:** subida automática a YouTube, voz que lea el versículo con [voz-local](https://github.com/RosaritoRD/voz-local) o miniaturas con el versículo.
