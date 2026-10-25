#!/usr/bin/env python3
"""
Visuel « Histoire de clinique » SmileFlow, 1080 × 1350 (4:5), pour LinkedIn,
Facebook et Instagram. Utilisé les jours sans actualité : un récit fictif
avec une scène illustrée, une réplique et la morale de l'histoire.

  python3 tools/story_card/build.py \
      --scene fauteuil --heure "Mardi, 15 h" \
      --title "Le fauteuil 3 est resté vide. Le patient habitait à 5 minutes." \
      --replique "Appelez-moi si une place se libère !" \
      --morale "Un rendez-vous annulé se perd quand personne ne le sait assez vite." \
      --out ads/news/2026-10-25.jpg

Scènes : fauteuil (fauteuil vide + horloge), telephone (téléphone + bulles),
dossier (presse-papiers + crayon), calendrier (agenda + plage libérée).
Le titre est réduit automatiquement s'il est long. Nécessite Playwright (Chromium)
et Pillow. Même charte que tools/news_card.
"""
import argparse, html, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
NEWS = os.path.join(os.path.dirname(HERE), 'news_card')
FONTS = open(os.path.join(NEWS, 'fonts', 'fonts.local.css')).read().replace('url(', f"url(file://{NEWS}/fonts/")
LOGO = f"file://{NEWS}/smileflow-logo.png"
NB = '\u00a0'
V, V2, L, INK = '#8A2BE2', '#5E28D9', '#EDE6F9', '#0F172A'

def fr(t):
    t = html.escape(t)
    for p in (':', ';', '?', '!', '%', '$', '»'):
        t = t.replace(' ' + p, NB + p)
    return t.replace('« ', '«' + NB)

def clock(cx, cy, r, heure):
    return f'''<circle cx="{cx}" cy="{cy}" r="{r}" fill="#fff" stroke="{V}" stroke-width="8"/>
<circle cx="{cx}" cy="{cy}" r="7" fill="{V}"/>
<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy-r*0.62}" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>
<line x1="{cx}" y1="{cy}" x2="{cx+r*0.48}" y2="{cy}" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>
<text x="{cx}" y="{cy+r+44}" text-anchor="middle" font-family="Inter" font-weight="700" font-size="28" fill="#64748B">{fr(heure)}</text>'''

SCENES = {
 'fauteuil': lambda h: f'''<svg viewBox="0 0 920 360" width="920" height="360">
<ellipse cx="380" cy="338" rx="290" ry="16" fill="{L}"/>
<rect x="335" y="250" width="44" height="80" rx="8" fill="#94A3B8"/><rect x="250" y="318" width="214" height="20" rx="10" fill="#94A3B8"/>
<path d="M230 240 L470 240" stroke="{V2}" stroke-width="44" stroke-linecap="round"/>
<path d="M230 240 L150 300" stroke="{V2}" stroke-width="40" stroke-linecap="round"/>
<path d="M470 240 L585 110" stroke="{V2}" stroke-width="46" stroke-linecap="round"/>
<rect x="575" y="48" width="72" height="54" rx="22" transform="rotate(-40 611 75)" fill="{V}"/>
<path d="M260 222 L450 222" stroke="#B89AF0" stroke-width="10" stroke-linecap="round" opacity=".7"/>
<path d="M400 200 L520 200" stroke="#CBD5E1" stroke-width="14" stroke-linecap="round"/>
<path d="M690 330 L690 40 Q690 20 670 20 L560 20" stroke="#CBD5E1" stroke-width="10" fill="none" stroke-linecap="round"/>
<ellipse cx="535" cy="24" rx="34" ry="18" fill="#FDE68A" stroke="#F59E0B" stroke-width="6"/>
{clock(820, 150, 76, h)}</svg>''',
 'telephone': lambda h: f'''<svg viewBox="0 0 920 330" width="920" height="330">
<rect x="130" y="20" width="170" height="290" rx="30" fill="#fff" stroke="{V2}" stroke-width="10"/>
<rect x="155" y="60" width="120" height="190" rx="10" fill="{L}"/>
<rect x="380" y="40" width="300" height="80" rx="28" fill="{V}"/><text x="530" y="92" text-anchor="middle" font-family="Inter" font-weight="700" font-size="30" fill="#fff">OUI</text>
<rect x="340" y="150" width="340" height="80" rx="28" fill="#fff" stroke="{L}" stroke-width="6"/><rect x="370" y="182" width="260" height="16" rx="8" fill="#CBD5E1"/>
{clock(800, 120, 70, h)}</svg>''',
 'dossier': lambda h: f'''<svg viewBox="0 0 920 330" width="920" height="330">
<rect x="160" y="30" width="260" height="290" rx="22" fill="#fff" stroke="{V2}" stroke-width="10"/>
<rect x="230" y="10" width="120" height="44" rx="14" fill="{V}"/>
<rect x="200" y="100" width="180" height="16" rx="8" fill="#CBD5E1"/><rect x="200" y="140" width="150" height="16" rx="8" fill="#CBD5E1"/><rect x="200" y="180" width="170" height="16" rx="8" fill="#CBD5E1"/>
<path d="M210 250 l26 26 l52 -60" stroke="{V}" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
<path d="M470 280 L620 60" stroke="#F59E0B" stroke-width="26" stroke-linecap="round"/>
{clock(800, 120, 70, h)}</svg>''',
 'calendrier': lambda h: f'''<svg viewBox="0 0 920 330" width="920" height="330">
<rect x="120" y="30" width="480" height="280" rx="26" fill="#fff" stroke="{V2}" stroke-width="10"/>
<rect x="120" y="30" width="480" height="64" rx="26" fill="{V}"/>
{''.join(f'<rect x="{150+c*110}" y="{120+r*62}" width="90" height="44" rx="10" fill="{(V if (r,c)==(1,2) else L)}"/>' for r in range(3) for c in range(4))}
{clock(800, 120, 70, h)}</svg>''',
}

CSS = FONTS + """
*{box-sizing:border-box} body{margin:0}
.s{width:1080px;height:1350px;position:relative;overflow:hidden;font-family:Inter,sans-serif;color:#0F172A;background:linear-gradient(180deg,#FFFFFF 0%,#F4EEFD 100%)}
.g{position:absolute;border-radius:50%}
.top{position:absolute;left:80px;right:80px;top:70px;display:flex;justify-content:space-between;align-items:center}
.tag{font-size:22px;font-weight:700;letter-spacing:.14em;color:#8A2BE2;text-transform:uppercase}
.main{position:absolute;left:80px;right:80px;top:160px;bottom:170px;display:flex;flex-direction:column;justify-content:center}
.kick{font-size:26px;font-weight:700;letter-spacing:.08em;color:#64748B;text-transform:uppercase}
h1{margin:20px 0 0;font-family:'Playfair Display',Georgia,serif;font-weight:700;font-variant-numeric:lining-nums;line-height:1.08;letter-spacing:-.01em;text-wrap:balance}
.scene{margin-top:34px;position:relative}
.bub{position:absolute;left:0;top:10px;max-width:360px;background:#fff;border:2px solid #EDE6F9;border-radius:26px;padding:16px 24px;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-size:30px;line-height:1.25;box-shadow:0 14px 34px rgba(94,40,217,.10)}
.card{margin-top:30px;background:#fff;border:1px solid #EDE6F9;border-radius:32px;box-shadow:0 30px 70px rgba(94,40,217,.12);padding:34px 42px}
.mt{font-size:22px;font-weight:700;letter-spacing:.14em;color:#8A2BE2;text-transform:uppercase}
.mo{margin-top:10px;font-size:36px;line-height:1.3;font-weight:600;color:#334155}
.foot{position:absolute;left:80px;right:80px;bottom:70px;display:flex;justify-content:space-between;align-items:flex-end}
.src{font-size:24px;color:#475569;line-height:1.4}
.url{font-size:26px;font-weight:600;color:#5E28D9}
"""

def page(a, size):
    bub = (f'<div class="bub"{"" if a.scene == "fauteuil" else " style=position:static;display:inline-block;max-width:none;margin-bottom:18px"}>«{NB}{fr(a.replique)}{NB}»</div>') if a.replique else ''
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class="s">
<div class="g" style="right:-380px;top:-380px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(195,166,247,.45) 0%,rgba(195,166,247,0) 66%)"></div>
<div class="g" style="left:-420px;bottom:-460px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(138,43,226,.16) 0%,rgba(138,43,226,0) 66%)"></div>
<div class="top"><img src="{LOGO}" style="width:250px;height:40px"><div class="tag">Histoire de clinique</div></div>
<div class="main"><div class="kick">Une histoire vraie… ou presque</div><h1 style="font-size:{size}px">{fr(a.title)}</h1>
<div class="scene">{bub if a.scene != 'fauteuil' else ''}{SCENES[a.scene](a.heure)}{bub if a.scene == 'fauteuil' else ''}</div>
<div class="card"><div class="mt">La morale</div><div class="mo">{fr(a.morale)}</div></div></div>
<div class="foot"><div class="src">Récit fictif · personnages inventés</div><div class="url">L’histoire complète en commentaire</div></div>
</div></body></html>"""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene', default='fauteuil', choices=sorted(SCENES))
    ap.add_argument('--heure', default='', help='texte sous l’horloge, ex. « Mardi, 15 h »')
    ap.add_argument('--title', required=True, help='titre court, 14 mots max conseillé')
    ap.add_argument('--replique', default='', help='réplique d’un personnage, 8 mots max conseillé')
    ap.add_argument('--morale', required=True, help='la conclusion, 16 mots max conseillé')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350})
        for size in (84, 78, 72, 66, 60, 54, 48):
            f = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8'); f.write(page(a, size)); f.close()
            pg.goto('file://' + f.name); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
            over = pg.evaluate("""()=>{const m=document.querySelector('.main');const r=m.getBoundingClientRect();let w=0;m.querySelectorAll('*').forEach(e=>{const q=e.getBoundingClientRect();if(q.height){w=Math.max(w,r.top-q.top,q.bottom-r.bottom,q.right-r.right)}});return w}""")
            if over <= 2: break
        png = a.out + '.png'; pg.screenshot(path=png); b.close()
    Image.open(png).convert('RGB').save(a.out, quality=92); os.remove(png)
    if over > 2: print(f'ATTENTION : le contenu déborde encore ({over:.0f} px) : raccourcis le titre ou la morale.', file=sys.stderr); sys.exit(2)
    print(a.out)

if __name__ == '__main__':
    main()
