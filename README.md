# 🎧 Mi Spotify
Reproductor de música tipo Spotify (búsqueda en YouTube, streaming completo y descarga MP3).

## Desplegar en Render (gratis)
1. Sube este repo a GitHub.
2. En render.com: New → Blueprint → conecta el repo.
3. Espera el build. Obtendrás una URL tipo `https://mispotify.onrender.com`.

## Mantener despierto (gratis)
Crea un monitor HTTP en uptimerobot.com apuntando a tu URL, cada 5 minutos.

## Local (Termux)
```sh
pip install yt-dlp flask
pkg install ffmpeg
python server.py
```
