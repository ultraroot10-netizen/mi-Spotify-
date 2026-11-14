import os, re, tempfile, shutil, json
import urllib.request, urllib.parse
from flask import Flask, request, jsonify, send_file, redirect
from yt_dlp import YoutubeDL

app = Flask(__name__, static_folder="static", static_url_path="")

SEARCH_OPTS = {"quiet": True, "skip_download": True, "extract_flat": "in_playlist",
               "noplaylist": True}

def clean_title(t):
    return re.sub(r"[\(\[].*?[\)\]]", "", t or "").strip()

def _search(q, n=20):
    n = max(1, min(n, 30))
    with YoutubeDL(SEARCH_OPTS) as ydl:
        info = ydl.extract_info(f"ytsearch{n}:{q}", download=False)
    out = []
    for e in info.get("entries") or []:
        if not e:
            continue
        thumbs = e.get("thumbnails") or []
        thumb = thumbs[0]["url"] if thumbs else (e.get("thumbnail") or "")
        out.append({
            "id": e["id"], "title": e.get("title"),
            "uploader": e.get("channel") or e.get("uploader") or "",
            "duration": e.get("duration"), "thumb": thumb,
        })
    return out

@app.get("/")
def index():
    return app.send_static_file("index.html")

@app.get("/api/search")
def search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify([])
    try:
        return jsonify(_search(q, request.args.get("n", 20, type=int)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/trending")
def trending():
    try:
        q = request.args.get("q", "top songs 2026").strip()
        return jsonify(_search(q, 20))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/lyrics")
def lyrics():
    t = clean_title(request.args.get("t", ""))
    a = (request.args.get("a", "") or "").strip()
    if not t:
        return jsonify({"error": "sin título"}), 400
    for artist in (a, ""):
        try:
            params = urllib.parse.urlencode({"track_name": t, "artist_name": artist})
            url = "https://lrclib.net/api/search?" + params
            req = urllib.request.Request(url, headers={"User-Agent": "MiSpotify/1.0"})
            data = json.load(urllib.request.urlopen(req, timeout=15))
            if data:
                return jsonify({
                    "synced": data[0].get("syncedLyrics") or "",
                    "plain": data[0].get("plainLyrics") or "",
                    "title": data[0].get("trackName", t),
                    "artist": data[0].get("artistName", a),
                })
        except Exception:
            continue
    return jsonify({"synced": "", "plain": ""})

@app.get("/api/stream/<vid>")
def stream(vid):
    try:
        with YoutubeDL({"quiet": True, "format": "bestaudio/best",
                        "skip_download": True, "noplaylist": True}) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
        url = info.get("url") or max(info["formats"], key=lambda f: f.get("abr") or 0)["url"]
        return redirect(url, code=302)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/download/<vid>")
def download(vid):
    tmp = tempfile.mkdtemp()
    use_ffmpeg = shutil.which("ffmpeg") is not None
    opts = {"quiet": True, "format": "bestaudio/best", "noplaylist": True,
            "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s")}
    if use_ffmpeg:
        opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                   "preferredcodec": "mp3", "preferredquality": "192"}]
    try:
        with YoutubeDL(opts) as ydl:
            ydl.extract_info(f"https://www.youtube.com/watch?v={vid}", download=True)
        files = [f for f in os.listdir(tmp) if not f.endswith((".part", ".ytdl"))]
        if use_ffmpeg:
            target = next(f for f in files if f.endswith(".mp3")); ext = "mp3"
        else:
            target = next(f for f in files); ext = "m4a"
        safe = re.sub(r"[^\w\- ]", "", request.args.get("t", "audio"))[:80] or "audio"
        return send_file(os.path.join(tmp, target), as_attachment=True,
                         download_name=f"{safe}.{ext}")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), threaded=True)
