#!/usr/bin/env python3
"""
Visuel « Actualité dentaire » SmileFlow, 1080 × 1350 (4:5), pour LinkedIn,
Facebook et Instagram.

  python3 tools/news_card/build.py \
      --zone "Québec" --source "La Presse" --date "16 octobre 2026" \
      --title "Il manque 1 400 hygiénistes au Québec" \
      --chiffre "1 400" --chiffre-label "hygiénistes manquent au Québec" \
      --out ads/news/2026-10-18.jpg

--chiffre et --chiffre-label sont facultatifs (un chiffre clé tiré de l'article).
Le titre est réduit automatiquement s'il est long. Nécessite Playwright (Chromium)
et Pillow.
"""
import argparse, html, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = open(os.path.join(HERE, 'fonts', 'fonts.local.css')).read().replace('url(', f"url(file://{HERE}/fonts/")
LOGO = f"file://{HERE}/smileflow-logo.png"
NB = ' '

def fr(t):
    t = html.escape(t)
    for p in (':', ';', '?', '!', '%', '$', '»'):
        t = t.replace(' ' + p, NB + p)
    return t.replace('« ', '«' + NB)

CSS = FONTS + """
*{box-sizing:border-box} body{margin:0}
.s{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter,sans-serif;color:#0F172A;background:linear-gradient(180deg,#FFFFFF 0%,#F4EEFD 100%)}
.g{position:absolute;border-radius:50%}
.top{position:absolute;left:80px;right:80px;top:70px;display:flex;justify-content:space-between;align-items:center}
.tag{font-size:22px;font-weight:700;letter-spacing:.14em;color:#8A2BE2;text-transform:uppercase}
.main{position:absolute;left:80px;right:80px;top:170px;bottom:200px;display:flex;flex-direction:column;justify-content:center}
.kick{font-size:26px;font-weight:700;letter-spacing:.08em;color:#64748B;text-transform:uppercase}
h1{margin:26px 0 0;font-family:'Playfair Display',Georgia,serif;font-weight:700;font-variant-numeric:lining-nums;line-height:1.08;letter-spacing:-.01em;text-wrap:balance}
.card{margin-top:60px;background:#fff;border:1px solid #EDE6F9;border-radius:32px;box-shadow:0 30px 70px rgba(94,40,217,.12);padding:40px 46px;display:flex;align-items:center;gap:36px}
.big{font-family:'Playfair Display',Georgia,serif;font-weight:700;font-variant-numeric:lining-nums;color:#8A2BE2;font-size:110px;line-height:1;white-space:nowrap}
.lab{font-size:34px;line-height:1.3;font-weight:600;color:#334155}
.foot{position:absolute;left:80px;right:80px;bottom:70px;display:flex;justify-content:space-between;align-items:flex-end}
.src{font-size:26px;color:#475569;line-height:1.4}
.src b{color:#0F172A}
.url{font-size:26px;font-weight:600;color:#5E28D9}
"""

def page(a, size):
    chiffre = ''
    if a.chiffre:
        chiffre = f'<div class="card"><div class="big">{fr(a.chiffre)}</div><div class="lab">{fr(a.chiffre_label or "")}</div></div>'
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class="s">
<div class="g" style="right:-380px;top:-380px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(195,166,247,.45) 0%,rgba(195,166,247,0) 66%)"></div>
<div class="g" style="left:-420px;bottom:-460px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(138,43,226,.16) 0%,rgba(138,43,226,0) 66%)"></div>
<div class="top"><img src="{LOGO}" style="width:250px;height:40px"><div class="tag">Actualité · {fr(a.zone)}</div></div>
<div class="main"><div class="kick">L’actu dentaire du jour</div><h1 style="font-size:{size}px">{fr(a.title)}</h1>{chiffre}</div>
<div class="foot"><div class="src">Source : <b>{fr(a.source)}</b><br>{fr(a.date)}</div><div class="url">Lien de l’article en commentaire</div></div>
</div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--zone', required=True, help='Québec, Canada ou Monde')
    ap.add_argument('--source', required=True)
    ap.add_argument('--date', required=True, help="date de l'article, ex. « 16 octobre 2026 »")
    ap.add_argument('--title', required=True, help='titre court, 12 mots max conseillé')
    ap.add_argument('--chiffre', default='')
    ap.add_argument('--chiffre-label', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350})
        for size in (104, 96, 88, 80, 72, 66, 60, 54):
            f = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8'); f.write(page(a, size)); f.close()
            pg.goto('file://' + f.name); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
            over = pg.evaluate("""()=>{const m=document.querySelector('.main');const r=m.getBoundingClientRect();let w=0;m.querySelectorAll('*').forEach(e=>{const q=e.getBoundingClientRect();if(q.height){w=Math.max(w,r.top-q.top,q.bottom-r.bottom,q.right-r.right)}});return w}""")
            if over <= 2: break
        png = a.out + '.png'; pg.screenshot(path=png); b.close()
    Image.open(png).convert('RGB').save(a.out, quality=92); os.remove(png)
    if over > 2: print(f'ATTENTION : le titre déborde encore ({over:.0f} px) : raccourcis-le.', file=sys.stderr); sys.exit(2)
    print(a.out)

if __name__ == '__main__':
    main()
