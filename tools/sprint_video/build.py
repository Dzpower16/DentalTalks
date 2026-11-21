#!/usr/bin/env python3
"""
Vidéos courtes du sprint SmileFlow (9:16, 1080 × 1920, 30 i/s) : voix off féminine
générée localement (Kokoro, voix « ff_siwis »), sous-titres incrustés calés phrase par
phrase sur la voix, musique douce qui s'efface sous la voix, carte de fin avec la phrase
d'abonnement. Charte : fond blanc → lavande, Playfair Display + Inter, violet #8A2BE2.

  python3 tools/sprint_video/build.py --script strategie/sprint-7j/videos/V1.json \
      --out ads/video/sprint/V1 --models /chemin/vers/kokoro

--models : dossier qui contient kokoro-v1.0.onnx et voices-v1.0.bin
           (github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0).
Produit <out>.mp4 (9:16), <out>.jpg (première image = accroche) et <out>.timing.json.

Le JSON : {"tag": "Réception", "pied": "Situation fictive", "scenes": [ ... ]}.
Chaque scène a « dit » (le texte dit et sous-titré, forme écrite : « 8 h 02 », « 40 »)
et un « type » : accroche, heure, chiffre, texte, liste, sms, note, pays, question,
qr, replique, versus, fin. « **mot** » met un mot en violet à l'écran.
« sans_sous »: true masque les sous-titres (quand l'écran dit déjà la même chose).
"""
import argparse, html, json, os, re, subprocess, tempfile, wave
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
NEWS = os.path.join(TOOLS, 'news_card')
FONTS = open(os.path.join(NEWS, 'fonts', 'fonts.local.css')).read().replace('url(', f"url(file://{NEWS}/fonts/")
LOGO = f"file://{NEWS}/smileflow-logo.png"
W, H, FPS, SR_M = 1080, 1920, 30, 48000
V, V2, L, INK = '#8A2BE2', '#5E28D9', '#EDE6F9', '#0F172A'
NB = ' '
ABONNEZ = "Abonnez-vous pour toutes les nouveautés en dentisterie au Québec, au Canada et dans le monde entier."
VOIX = 'ff_siwis'

# ---------- texte ----------
def esc(t, hl=True):
    t = html.escape(t)
    for p in (':', ';', '?', '!', '%', '$', '»'):
        t = t.replace(' ' + p, NB + p)
    t = t.replace('« ', '«' + NB)
    t = re.sub(r'(?<!\d)(\d+) (?=[^\d\s])', lambda m: m[1] + NB, t)
    return re.sub(r'\*\*(.+?)\*\*', (r'<span class="hl">\1</span>' if hl else r'\1'), t)

PRON = [(r'\bSmileFlow\b', 'Smaïle-flo'), (r'\bProgident\b', 'Progidan'), (r'\bFDA\b', 'èf-dé-a'),
        (r'\bIA\b', 'I A'), (r'\bPOV\b', 'pé-o-vé'), (r'\bKaiser\b', 'Kaïzeur'), (r'\bPearl\b', 'Perle'),
        (r'\bPMS\b', 'pé-ème-èsse'), (r'\b1er\b', 'premier'), (r'\b2e\b', 'deuxième'), (r'\bDre\b', 'docteure')]

def prononcer(t):
    from num2words import num2words as n2w
    w = lambda n: n2w(int(n), lang='fr')
    t = t.replace('**', '')
    for a, b in PRON:
        t = re.sub(a, b, t)
    t = re.sub(r'(\d{1,2}) h (\d{2})', lambda m: f"{w(m[1])} heure{'s' if int(m[1]) > 1 else ''} {w(m[2])}", t)
    t = re.sub(r'(\d{1,2}) h\b', lambda m: f"{w(m[1])} heure{'s' if int(m[1]) > 1 else ''}", t)
    t = re.sub(r'\d{1,3}(?: \d{3})+', lambda m: m[0].replace(' ', ''), t)
    t = re.sub(r'(\d+) ?\$', lambda m: w(m[1]) + ' dollars', t)
    t = re.sub(r'\d+', lambda m: w(m[0]), t)
    t = t.replace('«', '').replace('»', '').replace('…', ',')
    return re.sub(r'\s+', ' ', t).strip()

def phrases(t):
    return [p for p in re.split(r'(?<=[.!?…])\s+(?=[A-ZÀ-Ý«0-9])', t.strip()) if p]

def morceaux(phrase, maxc=36):
    """découpe une phrase en sous-titres de 2 lignes au plus"""
    t = re.sub(r' ([:;?!»])', NB + r'\1', phrase.replace('**', '')).replace('« ', '«' + NB)
    out, cur = [], ''
    for mot in t.split(' '):
        if cur and len(cur) + 1 + len(mot) > maxc:
            out.append(cur); cur = mot
        else:
            cur = (cur + ' ' + mot) if cur else mot
        if len(cur) >= 16 and re.search(r'[,:;]$', cur.replace(NB, ' ')):
            out.append(cur); cur = ''
    if cur:
        out.append(cur)
    if len(out) > 1 and len(out[-1]) < 8:  # pas de mot orphelin
        last = out.pop(); out[-1] += ' ' + last
    return out

# ---------- dessins ----------
def svg(name):
    s = {
     'telephone': f'''<svg width="420" height="300" viewBox="0 0 420 300"><rect x="140" y="20" width="140" height="260" rx="28" fill="#fff" stroke="{V2}" stroke-width="10"/><rect x="162" y="58" width="96" height="170" rx="10" fill="{L}"/><circle cx="210" cy="252" r="10" fill="{V2}"/>
<path d="M95 90 q-30 60 0 120" stroke="{V}" stroke-width="10" fill="none" stroke-linecap="round"/><path d="M60 65 q-50 85 0 170" stroke="{V}" stroke-width="10" fill="none" stroke-linecap="round" opacity=".5"/>
<path d="M325 90 q30 60 0 120" stroke="{V}" stroke-width="10" fill="none" stroke-linecap="round"/><path d="M360 65 q50 85 0 170" stroke="{V}" stroke-width="10" fill="none" stroke-linecap="round" opacity=".5"/></svg>''',
     'postit': '''<svg width="420" height="300" viewBox="0 0 420 300"><rect x="100" y="30" width="230" height="230" rx="8" fill="#FDE68A" transform="rotate(-6 215 145)"/><g transform="rotate(-6 215 145)" stroke="#B45309" stroke-width="8" stroke-linecap="round" opacity=".7"><path d="M135 90 h150"/><path d="M135 130 h120"/><path d="M135 170 h140"/><path d="M135 210 h90"/></g></svg>''',
     'vocale': f'''<svg width="420" height="300" viewBox="0 0 420 300"><rect x="140" y="20" width="140" height="260" rx="28" fill="#fff" stroke="{V2}" stroke-width="10"/><circle cx="187" cy="140" r="22" fill="none" stroke="{V2}" stroke-width="9"/><circle cx="233" cy="140" r="22" fill="none" stroke="{V2}" stroke-width="9"/><path d="M187 162 h46" stroke="{V2}" stroke-width="9"/>
<circle cx="290" cy="40" r="40" fill="#EF4444"/><text x="290" y="56" text-anchor="middle" font-family="Inter" font-weight="800" font-size="46" fill="#fff">3</text></svg>''',
     'comptoir': f'''<svg width="460" height="300" viewBox="0 0 460 300"><rect x="70" y="50" width="320" height="200" rx="22" fill="#fff" stroke="{V2}" stroke-width="10"/><rect x="70" y="50" width="320" height="56" rx="22" fill="{V}"/><rect x="100" y="140" width="120" height="18" rx="9" fill="#CBD5E1"/><rect x="100" y="180" width="200" height="18" rx="9" fill="#CBD5E1"/>
<text x="330" y="215" text-anchor="middle" font-family="Inter" font-weight="800" font-size="90" fill="#EF4444">?</text></svg>''',
     'agenda': f'''<svg width="520" height="320" viewBox="0 0 520 320"><rect x="40" y="20" width="440" height="280" rx="26" fill="#fff" stroke="{V2}" stroke-width="10"/><rect x="40" y="20" width="440" height="60" rx="26" fill="{V}"/>
{''.join(f'<rect x="{70+c*100}" y="{105+r*62}" width="80" height="44" rx="10" fill="{L}"/>' for r in range(3) for c in range(4) if (r, c) != (1, 1))}
<rect x="170" y="167" width="80" height="44" rx="10" fill="#fff" stroke="#EF4444" stroke-width="5" stroke-dasharray="10 7"/><text x="210" y="198" text-anchor="middle" font-family="Inter" font-weight="800" font-size="24" fill="#EF4444">10 h</text></svg>''',
     'radio': '''<svg width="560" height="330" viewBox="0 0 560 330"><rect x="20" y="10" width="520" height="310" rx="26" fill="#1E1B2E"/>
<g fill="#CBD5E1" opacity=".85"><path d="M95 70 q40 -20 80 0 l-6 120 q-6 50 -16 70 q-12 -40 -18 -60 q-6 20 -18 60 q-10 -20 -16 -70z"/><path d="M215 70 q40 -20 80 0 l-6 120 q-6 50 -16 70 q-12 -40 -18 -60 q-6 20 -18 60 q-10 -20 -16 -70z"/><path d="M335 70 q40 -20 80 0 l-6 120 q-6 50 -16 70 q-12 -40 -18 -60 q-6 20 -18 60 q-10 -20 -16 -70z"/></g>
<rect x="225" y="78" width="60" height="56" rx="10" fill="none" stroke="#C084FC" stroke-width="6" stroke-dasharray="12 8"/></svg>''',
     'micro': f'''<svg width="420" height="260" viewBox="0 0 420 260"><rect x="170" y="20" width="80" height="140" rx="40" fill="{V}"/><path d="M130 120 q0 80 80 80 q80 0 80 -80" stroke="{V2}" stroke-width="12" fill="none" stroke-linecap="round"/><path d="M210 200 v40" stroke="{V2}" stroke-width="12" stroke-linecap="round"/>
<path d="M90 80 q-20 40 0 80" stroke="{V}" stroke-width="9" fill="none" stroke-linecap="round" opacity=".5"/><path d="M330 80 q20 40 0 80" stroke="{V}" stroke-width="9" fill="none" stroke-linecap="round" opacity=".5"/></svg>''',
    }
    k = {'radio': 1.0}.get(name, 1.45)
    return re.sub(r'width="(\d+)" height="(\d+)"', lambda m: f'width="{int(int(m[1])*k)}" height="{int(int(m[2])*k)}"', s[name], count=1)

def check(ok=True):
    c = '#16A34A' if ok else '#DC2626'
    p = '<path d="M14 28 l10 10 l20 -22" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' if ok else '<path d="M18 18 l22 22 M40 18 l-22 22" stroke="#fff" stroke-width="7" stroke-linecap="round"/>'
    return f'<svg width="58" height="58" viewBox="0 0 58 58" style="flex:none"><circle cx="29" cy="29" r="29" fill="{c}"/>{p}</svg>'

def note_card(etat):
    lignes = ''.join(f'<div class="nl" style="width:{w}%"></div>' for w in (92, 78, 86, 64, 80))
    chip = {'ecoute': ('Séance en cours', '#F59E0B'), 'brouillon': ('Brouillon prêt', V), 'relire': ('À relire', V),
            'signe': ('Validée et signée', '#16A34A')}[etat]
    bas = ''
    if etat == 'relire':
        bas = '<div class="btns"><span class="b2">Corriger</span><span class="b1">Valider et signer</span></div>'
    elif etat == 'signe':
        bas = (f'<div class="sig"><svg width="230" height="60" viewBox="0 0 230 60"><path d="M8 44 q20 -40 36 -6 q10 22 26 -10 q14 -26 24 4 q8 20 22 -4 q12 -18 30 8 q10 12 40 -8" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/></svg>'
               f'<span>Signée par le dentiste</span></div><div class="del">{check()}<span>Audio supprimé après validation</span></div>')
    elif etat == 'ecoute':
        bas = f'<div style="display:flex;justify-content:center;margin-top:10px">{svg("micro")}</div>'
        lignes = ''
    return f'<div class="note"><div class="nh"><span>Note clinique</span><span class="chip" style="background:{chip[1]}">{chip[0]}</span></div>{lignes}{bas}</div>'

def sms(msgs):
    b = ''
    for m in msgs:
        cl = 'in' if m['de'] == 'clinique' else 'out'
        b += f'<div class="msg {cl}">{esc(m["t"])}</div>'
    return f'<div class="phone"><div class="ph">Clinique · Texto</div>{b}</div>'

# ---------- pages ----------
CSS = FONTS + f"""
*{{box-sizing:border-box}} html,body{{margin:0;background:transparent}}
.s{{position:relative;overflow:hidden;width:{W}px;height:{H}px;font-family:Inter,sans-serif;color:{INK};background:linear-gradient(180deg,#FFFFFF 0%,#F4EEFD 100%)}}
.g{{position:absolute;border-radius:50%}}
.top{{position:absolute;left:80px;right:80px;top:200px;display:flex;justify-content:space-between;align-items:center}}
.tag{{font-size:26px;font-weight:800;letter-spacing:.14em;color:{V};text-transform:uppercase;background:#fff;border:2px solid {L};border-radius:40px;padding:10px 22px}}
.main{{position:absolute;left:80px;right:110px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start}}
.hl{{color:{V}}}
.hook{{font-family:'Playfair Display',Georgia,serif;font-weight:700;line-height:1.08;letter-spacing:-.01em;text-wrap:balance;font-variant-numeric:lining-nums}}
.line{{font-family:'Playfair Display',Georgia,serif;font-weight:700;line-height:1.14;text-wrap:balance;font-variant-numeric:lining-nums}}
.kick{{font-size:32px;font-weight:800;letter-spacing:.1em;color:{V};text-transform:uppercase;margin-bottom:26px}}
.time{{font-weight:800;color:{V};line-height:1;letter-spacing:-.02em;margin-bottom:30px;font-variant-numeric:tabular-nums}}
.num{{font-weight:800;color:{V};line-height:.9;margin-bottom:10px}}
.vis{{margin-top:56px;align-self:center}}
.chips{{display:flex;gap:16px;flex-wrap:wrap;margin-top:40px}}
.chips span{{background:#fff;border:2px solid {L};border-radius:40px;padding:14px 26px;font-size:34px;font-weight:700;color:{V2}}}
.pill{{display:inline-block;background:{V};color:#fff;font-weight:800;font-size:36px;letter-spacing:.08em;text-transform:uppercase;border-radius:50px;padding:16px 34px;margin-bottom:36px}}
.pill.o{{background:#fff;color:{V};border:3px solid {V}}}
.cta{{display:inline-block;margin-top:48px;background:{INK};color:#fff;font-weight:800;font-size:38px;border-radius:50px;padding:20px 38px}}
.items{{display:flex;flex-direction:column;gap:30px;margin-top:10px;width:100%}}
.it{{display:flex;gap:28px;align-items:center;background:#fff;border:2px solid {L};border-radius:30px;padding:28px 32px;box-shadow:0 18px 40px rgba(94,40,217,.10)}}
.it b{{flex:none;width:72px;height:72px;border-radius:50%;background:{V};color:#fff;font-size:40px;display:flex;align-items:center;justify-content:center}}
.it span{{font-size:46px;font-weight:700;line-height:1.2}}
.it.off{{opacity:.16}}
.ans{{margin-top:40px;background:{V};color:#fff;border-radius:34px;padding:34px 40px;font-size:50px;font-weight:700;line-height:1.2;box-shadow:0 24px 50px rgba(94,40,217,.25)}}
.bub{{background:#fff;border:3px solid {L};border-radius:44px;padding:44px 50px;font-family:'Playfair Display',Georgia,serif;font-style:italic;font-weight:700;line-height:1.18;box-shadow:0 24px 60px rgba(94,40,217,.16)}}
.vs{{display:flex;flex-direction:column;gap:34px;width:100%}}
.vs div{{display:flex;gap:28px;align-items:center;font-size:58px;font-weight:700;font-family:'Playfair Display',Georgia,serif}}
.note{{width:820px;align-self:center;background:#fff;border:2px solid {L};border-radius:34px;padding:38px 42px;box-shadow:0 30px 70px rgba(94,40,217,.16)}}
.nh{{display:flex;justify-content:space-between;align-items:center;font-size:36px;font-weight:800;margin-bottom:30px}}
.chip{{color:#fff;font-size:26px;font-weight:800;border-radius:30px;padding:10px 20px}}
.nl{{height:20px;border-radius:10px;background:#E2E8F0;margin:18px 0}}
.btns{{display:flex;gap:18px;justify-content:flex-end;margin-top:34px}}
.btns span{{font-size:30px;font-weight:800;border-radius:24px;padding:18px 28px}}
.b1{{background:{V};color:#fff}} .b2{{background:#fff;color:{V};border:3px solid {V}}}
.sig{{display:flex;align-items:center;gap:20px;margin-top:26px;font-size:30px;font-weight:700;color:#334155}}
.del{{display:flex;align-items:center;gap:18px;margin-top:22px;font-size:32px;font-weight:800;color:#16A34A}}
.phone{{width:760px;align-self:center;background:#fff;border:10px solid {V2};border-radius:56px;padding:40px 36px 46px;box-shadow:0 30px 70px rgba(94,40,217,.16)}}
.ph{{text-align:center;font-size:28px;font-weight:800;color:#64748B;margin-bottom:28px}}
.msg{{font-size:38px;line-height:1.3;font-weight:600;border-radius:30px;padding:24px 30px;margin:16px 0;max-width:86%}}
.msg.in{{background:#F1F5F9;color:{INK}}} .msg.out{{background:{V};color:#fff;margin-left:auto;font-weight:800;font-size:46px;text-align:center;max-width:40%}}
.fin{{align-items:center;text-align:center;width:100%}}
.fin .ab{{font-family:'Playfair Display',Georgia,serif;font-weight:700;line-height:1.2;color:{V2};text-wrap:balance}}
.fin .url{{margin-top:60px;font-size:44px;font-weight:800;color:{INK}}}
.fin .demo{{margin-top:18px;font-size:34px;font-weight:600;color:#64748B}}
.foot{{position:absolute;left:80px;right:110px;top:1560px;font-size:26px;line-height:1.35;color:#64748B}}
.sub{{position:absolute;left:70px;right:110px;bottom:{H-1480}px;display:flex;justify-content:center}}
.sub div{{font-family:Inter,sans-serif;background:{INK};color:#fff;font-weight:800;font-size:56px;line-height:1.22;text-align:center;text-wrap:balance;border-radius:26px;padding:20px 32px;max-width:900px;box-shadow:0 14px 34px rgba(15,23,42,.25)}}
"""

def contenu(sc, s):
    t = sc.get('type', 'texte')
    vis = f'<div class="vis">{svg(sc["visuel"])}</div>' if sc.get('visuel') in ('telephone', 'postit', 'vocale', 'comptoir', 'agenda', 'radio', 'micro') else ''
    if sc.get('visuel') == 'note':
        vis = f'<div class="vis">{note_card(sc.get("etat", "brouillon"))}</div>'
    kick = f'<div class="kick">{esc(sc["kicker"])}</div>' if sc.get('kicker') else ''
    pill = f'<div class="pill{" o" if sc.get("pill_o") else ""}">{esc(sc["pill"])}</div>' if sc.get('pill') else ''
    if t == 'accroche':
        return pill + kick + f'<div class="hook" style="font-size:{s}px">{esc(sc["ecran"])}</div>' + vis
    if t == 'heure':
        return f'<div class="time" style="font-size:{int(s*1.7)}px">{esc(sc["heure"])}</div><div class="line" style="font-size:{int(s*.82)}px">{esc(sc["ecran"])}</div>' + vis
    if t == 'chiffre':
        return kick + f'<div class="num" style="font-size:{int(s*3.6)}px">{esc(sc["chiffre"])}</div><div class="line" style="font-size:{int(s*.82)}px">{esc(sc["ecran"])}</div>' + vis
    if t == 'liste':
        its = ''.join(f'<div class="it{"" if i < sc.get("actif", 99) else " off"}"><b>{i+1}</b><span style="font-size:{int(s*.46)}px">{esc(x)}</span></div>' for i, x in enumerate(sc['items']))
        return kick + (f'<div class="line" style="font-size:{int(s*.7)}px;margin-bottom:40px">{esc(sc["ecran"])}</div>' if sc.get('ecran') else '') + f'<div class="items">{its}</div>'
    if t == 'sms':
        return kick + (f'<div class="line" style="font-size:{int(s*.7)}px;margin-bottom:46px">{esc(sc["ecran"])}</div>' if sc.get('ecran') else '') + sms(sc['messages'])
    if t == 'note':
        return kick + f'<div class="line" style="font-size:{int(s*.74)}px;margin-bottom:46px">{esc(sc["ecran"])}</div><div style="align-self:center">{note_card(sc["etat"])}</div>'
    if t == 'question':
        return kick + f'<div class="hook" style="font-size:{s}px">{esc(sc["ecran"])}</div><div class="cta">{esc(sc.get("cta", "Répondez en commentaire"))}</div>'
    if t == 'qr':
        return kick + f'<div class="hook" style="font-size:{s}px">{esc(sc["question"])}</div><div class="ans" style="font-size:{int(s*.52)}px">{esc(sc["reponse"])}</div>'
    if t == 'replique':
        return kick + f'<div class="bub" style="font-size:{int(s*.9)}px">{esc(sc["ecran"])}</div>'
    if t == 'versus':
        return kick + '<div class="vs">' + ''.join(f'<div style="font-size:{int(s*.62)}px">{check(ok)}<span>{esc(x)}</span></div>' for x, ok in sc['lignes']) + '</div>'
    if t == 'fin':
        return (f'<div class="fin" style="display:flex;flex-direction:column"><img src="{LOGO}" style="width:560px;height:90px;margin-bottom:80px">'
                f'<div class="ab" style="font-size:{int(s*.66)}px">{esc(ABONNEZ)}</div><div class="url">smileflow.ca</div><div class="demo">Réservez une démo</div></div>')
    # texte
    chips = ('<div class="chips">' + ''.join(f'<span>{esc(c)}</span>' for c in sc['chips']) + '</div>') if sc.get('chips') else ''
    return pill + kick + f'<div class="line" style="font-size:{int(s*.9)}px">{esc(sc["ecran"])}</div>' + chips + vis

def page(sc, s, tag, pied):
    bas = 1480 if (sc.get('sans_sous') or sc.get('type') == 'fin') else 1190
    foot = f'<div class="foot">{esc(sc.get("pied", pied))}</div>' if (sc.get('pied', pied) and sc.get('type') != 'fin') else ''
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class="s">
<div class="g" style="right:-380px;top:-300px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(195,166,247,.45) 0%,rgba(195,166,247,0) 66%)"></div>
<div class="g" style="left:-420px;bottom:-360px;width:1000px;height:1000px;background:radial-gradient(circle,rgba(138,43,226,.16) 0%,rgba(138,43,226,0) 66%)"></div>
<div class="top"><img src="{LOGO}" style="width:240px;height:38px"><div class="tag">{esc(tag)}</div></div>
<div class="main" style="top:300px;height:{bas-300}px">{contenu(sc, s)}</div>{foot}
</div></body></html>"""

def page_sous(texte):
    return f"""<!doctype html><html lang='fr'><head><meta charset='utf-8'><style>{CSS}</style></head><body style="width:{W}px;height:{H}px;position:relative">
<div class="sub"><div>{texte}</div></div></body></html>"""

def rendre(scenes, tag, pied, sous, tmp):
    from playwright.sync_api import sync_playwright
    fonds, calques = [], {}
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': W, 'height': H})
        for i, sc in enumerate(scenes):
            base = int(sc.get('taille', 1) * 104)
            for s in [base, int(base*.92), int(base*.84), int(base*.76), int(base*.68), int(base*.6), int(base*.52)]:
                f = os.path.join(tmp, f'p{i}.html'); open(f, 'w', encoding='utf-8').write(page(sc, s, tag, pied))
                pg.goto('file://' + f); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
                over = pg.evaluate("""()=>{const m=document.querySelector('.main');const r=m.getBoundingClientRect();let o=0;
                  m.querySelectorAll('*').forEach(e=>{const q=e.getBoundingClientRect();if(q.height){o=Math.max(o,r.top-q.top,q.bottom-r.bottom,q.right-r.right,r.left-q.left)}});return o}""")
                if over <= 2: break
            png = os.path.join(tmp, f'fond{i}.png'); pg.screenshot(path=png); fonds.append(png)
        for k, txt in sous.items():
            f = os.path.join(tmp, f'q{k}.html'); open(f, 'w', encoding='utf-8').write(page_sous(txt))
            pg.goto('file://' + f); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
            png = os.path.join(tmp, f'sous{k}.png'); pg.screenshot(path=png, omit_background=True); calques[k] = png
        b.close()
    return fonds, calques

# ---------- son ----------
def musique(dur, path, intervalles, duck=.26):
    """petite boucle C–G–Am–F à 100 bpm (nappe + arpège + basse), effacée sous la voix"""
    sr = SR_M; t = np.arange(int(sr * dur)) / sr
    acc = [(261.63, 329.63, 392.0), (196.0, 246.94, 293.66), (220.0, 261.63, 329.63), (174.61, 220.0, 261.63)]
    y = np.zeros_like(t); mes = 2.4; croche = .3
    for k in range(int(dur // mes) + 1):
        a = k * mes; c = acc[k % 4]
        m = (t >= a) & (t < a + mes + 1.2); tt = t[m] - a
        env = np.minimum(1, tt / .6) * np.exp(-np.maximum(0, tt - mes) * 3)
        for f in c:
            y[m] += .16 * env * np.sin(2*np.pi*f*tt)
        mb = (t >= a) & (t < a + 1.2); tb = t[mb] - a
        y[mb] += .32 * np.exp(-tb * 3.5) * np.sin(2*np.pi*c[0]/2*tb)
        for j in range(8):
            b0 = a + j * croche; mp = (t >= b0) & (t < b0 + .9); tp = t[mp] - b0
            f = [c[0]*2, c[1]*2, c[2]*2, c[1]*2][j % 4]
            y[mp] += .13 * np.exp(-tp * 7) * (np.sin(2*np.pi*f*tp) + .25*np.sin(2*np.pi*2*f*tp))
    y /= max(1e-6, np.abs(y).max())
    pas = 0.01; n = int(dur / pas) + 2; cible = np.ones(n)
    for a, e in intervalles:
        cible[max(0, int((a - .12) / pas)):int((e + .3) / pas)] = duck
    env = np.empty(n); g = 1.0
    for i in range(n):
        x = cible[i]; g = max(x, g - pas / .2) if x < g else min(x, g + pas / .8); env[i] = g
    y *= np.interp(t, np.arange(n) * pas, env)
    y *= np.minimum(1, np.minimum(t / .4, (dur - t) / 1.5)) * .34
    with wave.open(path, 'w') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes())

def rogner(x, seuil=.008):
    i = np.where(np.abs(x) > seuil)[0]
    return x[max(0, i[0] - 240):i[-1] + 480] if len(i) else x

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--script', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--models', required=True); ap.add_argument('--vitesse', type=float, default=None)
    ap.add_argument('--apercu', action='store_true', help='rend seulement les images fixes, sans vidéo')
    a = ap.parse_args()
    data = json.load(open(a.script, encoding='utf-8'))
    scenes = data['scenes'] + [{'type': 'fin', 'dit': ABONNEZ, 'sans_sous': True}]
    vitesse = a.vitesse or data.get('vitesse', 1.0)
    tmp = tempfile.mkdtemp()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)

    # 1. voix, phrase par phrase -> minutage exact
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(a.models, 'kokoro-v1.0.onnx'), os.path.join(a.models, 'voices-v1.0.bin'))
    sr = 24000; t = 0.03; voix = []; parole = []; sous = {}; plan = []
    debuts = []
    for i, sc in enumerate(scenes):
        debuts.append(0.0 if i == 0 else t)
        for j, ph in enumerate(phrases(sc['dit'])):
            x, sr = k.create(prononcer(ph), voice=VOIX, speed=vitesse, lang='fr-fr')
            x = rogner(np.asarray(x, dtype=np.float32)); d = len(x) / sr
            voix.append((t, x)); parole.append((t, t + d))
            if not sc.get('sans_sous'):
                ms = morceaux(ph); tot = sum(len(m) for m in ms); u = t
                for n, m in enumerate(ms):
                    dd = d * len(m) / tot; key = f'{i}_{j}_{n}'
                    sous[key] = esc(m, hl=False); plan.append((u, u + dd + (0.12 if n == len(ms) - 1 else 0), key)); u += dd
            t += d + .14
        t += .22
    total = max(t + .5, debuts[-1] + 3.0)
    debuts.append(total)
    vbuf = np.zeros(int(total * sr) + sr)
    for t0, x in voix:
        s0 = int(t0 * sr); vbuf[s0:s0 + len(x)] += x
    import soundfile as sf
    vw = os.path.join(tmp, 'voix.wav'); sf.write(vw, vbuf[:int(total * sr)], sr)

    # 2. images
    fonds, calques = rendre(scenes, data.get('tag', ''), data.get('pied', ''), sous, tmp)
    imgs = [Image.open(p).convert('RGB') for p in fonds]
    Image.open(fonds[0]).convert('RGB').save(a.out + '.jpg', quality=90)
    if a.apercu:
        for i, p in enumerate(fonds):
            im = Image.open(p).convert('RGB')
            ks = [kk for kk in calques if kk.startswith(f'{i}_')]
            if ks:
                c = Image.open(calques[ks[0]]); im.paste(c, (0, 0), c)
            im.save(f'{a.out}_apercu{i}.jpg', quality=85)
        print('aperçu :', len(fonds), 'scènes,', round(total, 1), 's'); return
    lay = {kk: Image.open(p) for kk, p in calques.items()}

    # 3. vidéo
    vid = os.path.join(tmp, 'v.mp4')
    ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', vid], stdin=subprocess.PIPE)
    def zoom(im, lt, d):
        z = 1 + .025 * min(1, lt / max(d, .1)); cw, ch = int(W / z), int(H / z)
        x, y = (W - cw) // 2, (H - ch) // 2
        return im.resize((W, H), Image.BICUBIC, box=(x, y, x + cw, y + ch))
    for fi in range(int(total * FPS)):
        tt = fi / FPS
        i = max(j for j in range(len(scenes)) if debuts[j] <= tt)
        d = debuts[i + 1] - debuts[i]; lt = tt - debuts[i]
        fr_ = zoom(imgs[i], lt, d)
        if lt < .2 and i > 0:
            fr_ = Image.blend(zoom(imgs[i - 1], debuts[i] - debuts[i - 1], debuts[i] - debuts[i - 1]), fr_, lt / .2)
        cur = [kk for (u0, u1, kk) in plan if u0 <= tt < u1]
        if cur:
            c = lay[cur[-1]]; fr_.paste(c, (0, 0), c)
        ff.stdin.write(fr_.tobytes())
    ff.stdin.close(); ff.wait()

    # 4. son : voix -16 LUFS + musique effacée sous la voix
    mw = os.path.join(tmp, 'm.wav'); musique(total, mw, parole)
    out = a.out + '.mp4'
    subprocess.check_call(['ffmpeg', '-v', 'error', '-y', '-i', vid, '-i', vw, '-i', mw, '-filter_complex',
        '[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];'
        '[2:a]aresample=48000,aformat=channel_layouts=stereo[m];'
        '[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]',
        '-map', '0:v', '-map', '[a]', '-t', f'{total:.2f}', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
        '-movflags', '+faststart', out])
    json.dump({'duree': round(total, 2), 'scenes': [{'debut': round(x, 2), 'dit': s['dit']} for x, s in zip(debuts, scenes)]},
              open(a.out + '.timing.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(out, round(total, 1), 's')

if __name__ == '__main__':
    main()
