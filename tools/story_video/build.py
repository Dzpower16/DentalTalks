#!/usr/bin/env python3
"""
Vidéo « Histoire de clinique » SmileFlow (9:16 1080×1920 et 4:5 1080×1350),
même charte que tools/story_card : fond blanc → lavande, Playfair Display
pour les phrases, Inter pour les étiquettes, violet #8A2BE2.

  python3 tools/story_video/build.py --script histoire.json --voice voix.mp3 \
      --out ads/video/Histoire_2026-10-25

histoire.json :
{
  "titre": "Le fauteuil 3",
  "scenes": [
    {"heure": "Mardi, 15 h 04", "texte": "Le fauteuil 3 est vide.", "debut": 0.0},
    {"texte": "« J'aurais tellement voulu mon nettoyage avant. »", "style": "replique", "debut": 31.5},
    {"texte": "Un rendez-vous annulé se perd quand personne ne le sait assez vite.", "style": "morale", "debut": 44.0},
    {"texte": "La place libérée part par texto…", "style": "produit", "debut": 50.0},
    {"texte": "Abonnez-vous…", "style": "fin", "debut": 60.0}
  ]
}
« debut » = seconde où la scène apparaît (alignée sur la voix). Styles :
recit (défaut), replique (bulle en italique), morale (carte « La morale »),
produit (carte SmileFlow), fin (logo + abonnement).
Produit <out>_916.mp4, <out>_45.mp4 et <out>_45.jpg (vignette).
Nécessite Playwright (Chromium), Pillow, numpy et ffmpeg.
"""
import argparse, html, json, os, subprocess, sys, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
NEWS = os.path.join(os.path.dirname(HERE), 'news_card')
FONTS = open(os.path.join(NEWS, 'fonts', 'fonts.local.css')).read().replace('url(', f"url(file://{NEWS}/fonts/")
LOGO = f"file://{NEWS}/smileflow-logo.png"
NB = '\u00a0'
FPS = 30

def fr(t):
    t = html.escape(t)
    for p in (':', ';', '?', '!', '%', '$', '»'):
        t = t.replace(' ' + p, NB + p)
    t = t.replace('« ', '«' + NB)
    return ' '.join(f'<span style="white-space:nowrap">{w}</span>' if ('-' in w or NB in w) else w for w in t.split(' '))

CSS = FONTS + """
*{box-sizing:border-box} html,body{margin:0}
.s{position:relative;overflow:hidden;font-family:Inter,sans-serif;color:#0F172A;background:linear-gradient(180deg,#FFFFFF 0%,#F4EEFD 100%)}
.g{position:absolute;border-radius:50%}
.top{position:absolute;left:80px;right:80px;display:flex;justify-content:space-between;align-items:center}
.tag{font-size:24px;font-weight:700;letter-spacing:.14em;color:#8A2BE2;text-transform:uppercase}
.main{position:absolute;left:80px;right:80px;display:flex;flex-direction:column;justify-content:center}
.heure{font-size:34px;font-weight:700;letter-spacing:.06em;color:#8A2BE2;text-transform:uppercase;margin-bottom:28px}
.recit{font-variant-numeric:lining-nums;font-family:'Playfair Display',Georgia,serif;font-weight:700;line-height:1.12;letter-spacing:-.01em;text-wrap:balance}
.bub{font-variant-numeric:lining-nums;align-self:flex-start;background:#fff;border:2px solid #EDE6F9;border-radius:36px;padding:36px 44px;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-weight:700;line-height:1.2;box-shadow:0 24px 60px rgba(94,40,217,.14)}
.card{background:#fff;border:1px solid #EDE6F9;border-radius:36px;box-shadow:0 30px 70px rgba(94,40,217,.14);padding:48px 52px}
.mt{font-size:26px;font-weight:700;letter-spacing:.14em;color:#8A2BE2;text-transform:uppercase;margin-bottom:18px}
.mo{font-weight:600;line-height:1.3;color:#334155}
.prod .mo{color:#0F172A}
.fin{align-items:center;text-align:center}
.fin .mo{color:#5E28D9}
.foot{position:absolute;left:80px;right:80px;font-size:24px;color:#64748B;display:flex;justify-content:space-between}
.bar{position:absolute;left:80px;height:6px;border-radius:3px;background:#8A2BE2}
"""

def frame_html(sc, w, h, size):
    top, bottom = (150, 230) if h > 1500 else (120, 130)
    body = ''
    st = sc.get('style', 'recit')
    t = fr(sc['texte'])
    if st == 'recit':
        body = (f'<div class="heure">{fr(sc["heure"])}</div>' if sc.get('heure') else '') + f'<div class="recit" style="font-size:{size}px">{t}</div>'
        if sc.get('scene'):
            sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'story_card'))
            import build as card
            body += f'<div style="margin-top:60px;transform:scale(.95);transform-origin:left top">{card.SCENES[sc["scene"]](sc.get("horloge", ""))}</div>'
    elif st == 'replique':
        body = (f'<div class="heure">{fr(sc["heure"])}</div>' if sc.get('heure') else '') + f'<div class="bub" style="font-size:{size}px">{t}</div>'
    elif st == 'morale':
        body = f'<div class="card"><div class="mt">La morale</div><div class="mo" style="font-size:{int(size*.8)}px">{t}</div></div>'
    elif st == 'produit':
        body = f'<div class="card prod"><img src="{LOGO}" style="width:250px;height:40px;margin-bottom:26px"><div class="mo" style="font-size:{int(size*.7)}px">{t}</div></div>'
    else:
        body = f'<div class="fin" style="display:flex;flex-direction:column"><img src="{LOGO}" style="width:500px;height:80px;margin-bottom:56px"><div class="mo" style="font-size:{int(size*.62)}px;font-weight:600">{t}</div></div>'
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body>
<div class="s" style="width:{w}px;height:{h}px">
<div class="g" style="right:-380px;top:-380px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(195,166,247,.45) 0%,rgba(195,166,247,0) 66%)"></div>
<div class="g" style="left:-420px;bottom:-460px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(138,43,226,.16) 0%,rgba(138,43,226,0) 66%)"></div>
<div class="top" style="top:{top-60}px"><img src="{LOGO}" style="width:220px;height:35px"><div class="tag">Histoire de clinique</div></div>
<div class="main" style="top:{top+40}px;bottom:{bottom}px">{body}</div>
<div class="foot" style="bottom:{bottom-110 if h>1500 else 62}px"><span>Récit fictif · personnages inventés</span><span>smileflow.ca</span></div>
</div></body></html>"""

def render_frames(scenes, w, h, tmp):
    from playwright.sync_api import sync_playwright
    out = []
    base = 92 if h > 1500 else 76
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': w, 'height': h})
        for i, sc in enumerate(scenes):
            size = int(sc.get('taille', 1) * base)
            for s in [size, int(size*.9), int(size*.8), int(size*.7), int(size*.6)]:
                f = os.path.join(tmp, f'f{i}.html'); open(f, 'w', encoding='utf-8').write(frame_html(sc, w, h, s))
                pg.goto('file://' + f); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
                over = pg.evaluate("""()=>{const m=document.querySelector('.main');const r=m.getBoundingClientRect();let o=0;m.querySelectorAll('*').forEach(e=>{const q=e.getBoundingClientRect();if(q.height){o=Math.max(o,r.top-q.top,q.bottom-r.bottom,q.right-r.right)}});return o}""")
                if over <= 2: break
            png = os.path.join(tmp, f's{w}x{h}_{i}.png'); pg.screenshot(path=png); out.append(png)
        b.close()
    return out

def ken(img, t, dur):
    """léger zoom lent (1 → 1,035) pour donner du mouvement"""
    from PIL import Image
    k = 1 + 0.035 * min(1, t / max(dur, .1))
    w, h = img.size; cw, ch = int(w / k), int(h / k)
    x, y = (w - cw) // 2, (h - ch) // 2
    return img.crop((x, y, x + cw, y + ch)).resize((w, h), Image.LANCZOS)

def make_music(dur, path, peak=.18):
    """nappe douce (accords Am–F–C–G), très bas sous la voix"""
    sr = 48000; t = np.arange(int(sr * dur)) / sr
    chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (130.81, 196.0, 261.63), (196.0, 246.94, 293.66)]
    y = np.zeros_like(t); L = 4.0
    for k in range(int(dur // L) + 1):
        a = k * L; m = (t >= a) & (t < a + L + 1.5)
        tt = t[m] - a
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - L) * 2.5)
        for f in chords[k % 4]:
            y[m] += env * (np.sin(2*np.pi*f*tt) + .3*np.sin(2*np.pi*2*f*tt)) / 3
    y *= peak / max(1e-6, np.abs(y).max())
    fade = np.minimum(1, np.minimum(t / 2, (dur - t) / 3)); y *= fade
    import wave
    with wave.open(path, 'w') as wv:
        wv.setnchannels(1); wv.setsampwidth(2); wv.setframerate(sr); wv.writeframes((y * 32767).astype(np.int16).tobytes())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--script', required=True); ap.add_argument('--voice', default='', help='voix off (mp3/wav) ; sans voix, la durée vient de « duree » dans le JSON'); ap.add_argument('--out', required=True)
    ap.add_argument('--no-music', action='store_true')
    a = ap.parse_args()
    from PIL import Image
    data = json.load(open(a.script, encoding='utf-8')); scenes = data['scenes']
    if a.voice:
        vdur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', a.voice]).decode().strip())
        total = max(vdur + 1.5, float(data.get('duree', 0)))
    else:
        total = float(data['duree'])
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    tmp = tempfile.mkdtemp()
    music = os.path.join(tmp, 'music.wav')
    if not a.no_music or not a.voice: make_music(total, music, .32 if not a.voice else .18)
    for (w, h, tag) in [(1080, 1920, '916'), (1080, 1350, '45')]:
        pngs = render_frames(scenes, w, h, tmp)
        imgs = [Image.open(p).convert('RGB') for p in pngs]
        starts = [s['debut'] for s in scenes] + [total]
        vid = os.path.join(tmp, f'v{tag}.mp4')
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(FPS), '-i', '-',
                               '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', vid], stdin=subprocess.PIPE)
        n = int(total * FPS)
        for fi in range(n):
            t = fi / FPS
            i = max(j for j in range(len(scenes)) if starts[j] <= t) if t >= starts[0] else 0
            d = starts[i + 1] - starts[i]; lt = t - starts[i]
            fr_ = ken(imgs[i], lt, d)
            if lt < .45 and i > 0:  # fondu enchaîné
                prev = ken(imgs[i - 1], starts[i] - starts[i - 1], starts[i] - starts[i - 1])
                fr_ = Image.blend(prev, fr_, lt / .45)
            arr = np.asarray(fr_).copy()
            bw = int((w - 160) * t / total); arr[h - 40:h - 34, 80:80 + bw] = (138, 43, 226)  # barre de progression
            ff.stdin.write(arr.tobytes())
        ff.stdin.close(); ff.wait()
        out = f'{a.out}_{tag}.mp4'
        if not a.voice:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', music, '-map', '0:v', '-map', '1:a', '-t', str(total), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ac', '2', '-ar', '48000', '-movflags', '+faststart', out]
        elif a.no_music:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', a.voice, '-filter_complex', '[1:a]adelay=500|500,apad[a]', '-map', '0:v', '-map', '[a]', '-t', str(total), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', out]
        else:
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', a.voice, '-i', music, '-filter_complex',
                   '[1:a]adelay=500|500,aresample=48000,aformat=channel_layouts=stereo[v];[2:a]aformat=channel_layouts=stereo,volume=0.55[m];[v][m]amix=inputs=2:duration=longest:normalize=0[a]',
                   '-map', '0:v', '-map', '[a]', '-t', str(total), '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', out]
        subprocess.check_call(cmd)
        if tag == '45': imgs[0].save(f'{a.out}_45.jpg', quality=90)
        print(out)

if __name__ == '__main__':
    main()
