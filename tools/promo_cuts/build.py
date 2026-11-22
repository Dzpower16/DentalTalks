#!/usr/bin/env python3
"""
Vidéos courtes tirées du film de marque et de la promo SmileFlow.

  python3 tools/promo_cuts/build.py --brand brandfilm1920x1080.mp4 --promo promo1080x1920.mp4 \
      --models /chemin/vers/kokoro [--only scribe]

Pour chaque extrait : coupe du segment, retrait du mot « SOAP » dans l'en-tête de la
note (filtre delogo, seulement pendant que la carte est à l'écran), voix off féminine
générée localement (Kokoro, ff_siwis), musique douce qui s'efface sous la voix, carte
de fin avec la phrase d'abonnement (sans « gratuit » ni « 100 % conforme »).
Sorties : ads/video/Film_<nom>.mp4 + .jpg (première image).
"""
import argparse, importlib.util, os, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
spec = importlib.util.spec_from_file_location('sv', os.path.join(ROOT, 'tools', 'sprint_video', 'build.py'))
sv = importlib.util.module_from_spec(spec); spec.loader.exec_module(sv)

ABONNEZ = sv.ABONNEZ

CLIPS = {
    'scribe': dict(src='promo', start=4.5, end=21.6, theme='dark', out='Film_Scribe_916',
                   delogo=(250, 893, 100, 35, 6.0, 18.5),
                   vo=[(0.3, "L'IA ne remplacera jamais votre équipe. Elle est là pour lui redonner du temps."),
                       (5.8, "Vous dictez pendant la séance. Le brouillon de la note clinique se prépare tout seul."),
                       (11.6, "Vous relisez, vous validez, vous signez. Et l'audio est supprimé après validation.")]),
    'attente': dict(src='promo', start=23.0, end=34.8, theme='dark', out='Film_Liste-attente_916', delogo=None,
                    vo=[(0.3, "Un Patient annule ? La plage part par texto à votre liste d'attente."),
                        (4.6, "Le premier qui répond OUI la prend. Personne n'a décroché le téléphone.")]),
    'avis': dict(src='promo', start=36.0, end=46.0, theme='dark', out='Film_Avis_916', delogo=None,
                 vo=[(0.3, "Après chaque visite, le Patient reçoit un mot de remerciement, puis une invitation à laisser son avis."),
                     (6.4, "Sans que personne n'y pense.")]),
    'marque': dict(src='brand', start=0.0, end=44.5, theme='light', out='Film_Marque_169',
                   delogo=(1156, 243, 100, 30, 9.0, 23.5), garder_son=10.0,
                   vo=[(10.6, "Trente secondes de dictée. Le brouillon de la note clinique est prêt : vous relisez, vous validez, vous signez."),
                       (17.2, "Et l'audio est supprimé après validation."),
                       (22.8, "Un Patient annule ? La plage part par texto à votre liste d'attente. Le premier qui répond OUI la prend."),
                       (29.2, "Personne n'a décroché le téléphone."),
                       (35.0, "Après chaque visite, un mot de remerciement, puis une invitation à laisser un avis Google. Sans que personne n'y pense.")]),
}
FIN = 6.0  # durée de la carte de fin

def carte(theme, w, h, path):
    from playwright.sync_api import sync_playwright
    dark = theme == 'dark'
    bg = ('radial-gradient(circle at 30% 30%, rgba(138,43,226,.35), rgba(10,13,26,0) 55%),'
          'radial-gradient(circle at 70% 75%, rgba(94,40,217,.30), rgba(10,13,26,0) 55%), #0A0D1A') if dark else \
         'radial-gradient(circle at 75% 20%, rgba(195,166,247,.45), rgba(255,255,255,0) 60%), linear-gradient(180deg,#FFFFFF,#F4EEFD)'
    ink = '#FFFFFF' if dark else '#0F172A'
    sub = '#D9C8FF' if dark else '#5E28D9'
    big = w < h
    html = f"""<!doctype html><html><head><meta charset='utf-8'><style>{sv.FONTS}
    html,body{{margin:0}} .c{{width:{w}px;height:{h}px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:Inter,sans-serif;text-align:center}}
    .logo{{display:flex;align-items:center;gap:{26 if big else 22}px;margin-bottom:{90 if big else 56}px}}
    .ic{{width:{110 if big else 92}px;height:{110 if big else 92}px;border-radius:28%;background:linear-gradient(135deg,#9B4DFF,#6A2BE2);display:flex;align-items:center;justify-content:center}}
    .nm{{font-size:{84 if big else 70}px;font-weight:800;color:{ink};letter-spacing:-.02em}}
    .ab{{font-size:{56 if big else 46}px;font-weight:700;line-height:1.25;color:{sub};max-width:{880 if big else 1300}px;text-wrap:balance}}
    .url{{margin-top:{70 if big else 46}px;font-size:{46 if big else 40}px;font-weight:800;color:{ink}}}
    .pill{{margin-top:26px;display:inline-block;background:#8A2BE2;color:#fff;font-weight:800;font-size:{38 if big else 32}px;border-radius:60px;padding:20px 44px}}
    </style></head><body><div class='c'>
    <div class='logo'><div class='ic'><svg width='64' height='64' viewBox='0 0 64 64'><circle cx='32' cy='16' r='7' fill='#fff'/><path d='M10 30 q22 26 44 0' stroke='#fff' stroke-width='9' fill='none' stroke-linecap='round'/></svg></div><div class='nm'>SmileFlow</div></div>
    <div class='ab'>{ABONNEZ}</div><div class='url'>smileflow.ca</div><div class='pill'>Réservez une démo</div></div></body></html>"""
    f = path + '.html'; open(f, 'w', encoding='utf-8').write(html)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': w, 'height': h})
        pg.goto('file://' + f); pg.wait_for_load_state('networkidle'); pg.evaluate('document.fonts.ready')
        pg.screenshot(path=path); b.close()

def run(cmd):
    subprocess.check_call(cmd)

def build(name, c, srcs, models, outdir):
    tmp = tempfile.mkdtemp()
    src = srcs[c['src']]
    w, h = (1080, 1920) if c['theme'] == 'dark' else (1920, 1080)
    seg = c['end'] - c['start']; total = seg + FIN
    # 1. segment vidéo (+ retrait du mot SOAP)
    vf = 'fps=30,format=yuv420p'
    if c['delogo']:
        x, y, dw, dh, a, b = c['delogo']
        vf = f"delogo=x={x}:y={y}:w={dw}:h={dh}:enable='between(t,{a},{b})'," + vf
    segv = os.path.join(tmp, 'seg.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-ss', str(c['start']), '-to', str(c['end']), '-i', src, '-vf', vf, '-an',
         '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', segv])
    # 2. carte de fin + fondu enchaîné
    png = os.path.join(tmp, 'fin.png'); carte(c['theme'], w, h, png)
    vid = os.path.join(tmp, 'v.mp4')
    run(['ffmpeg', '-v', 'error', '-y', '-i', segv, '-framerate', '30', '-i', png, '-filter_complex',
         f"[1:v]format=yuv420p,loop=-1:1,trim=duration={FIN + 0.5},setpts=PTS-STARTPTS,fps=30,settb=1/30[f];"
         f"[0:v]fps=30,settb=1/30[s];[s][f]xfade=transition=fade:duration=0.5:offset={seg - 0.5:.3f},format=yuv420p[v]",
         '-map', '[v]', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium', '-t', f'{total:.3f}', vid])
    # 3. voix off
    from kokoro_onnx import Kokoro
    import soundfile as sf
    k = Kokoro(os.path.join(models, 'kokoro-v1.0.onnx'), os.path.join(models, 'voices-v1.0.bin'))
    sr = 24000; buf = np.zeros(int((total + 1) * sr)); parole = []
    lignes = list(c['vo']) + [(seg + 0.3, ABONNEZ)]
    for t0, txt in lignes:
        t = t0
        for ph in sv.phrases(txt):
            x, sr = k.create(sv.prononcer(ph), voice=sv.VOIX, speed=1.0, lang='fr-fr')
            x = sv.rogner(np.asarray(x, dtype=np.float32)); d = len(x) / sr
            s0 = int(t * sr); buf[s0:s0 + len(x)] += x; parole.append((t, t + d)); t += d + .14
        print(f'  voix {t0:5.1f} → {t:5.1f} s : {txt[:50]}')
    vw = os.path.join(tmp, 'voix.wav'); sf.write(vw, buf[:int(total * sr)], sr)
    # 4. musique (effacée sous la voix)
    mw = os.path.join(tmp, 'm.wav'); sv.musique(total, mw, parole)
    garde = c.get('garder_son')
    if garde:  # film de marque : on garde le son d'origine du logo, la musique entre ensuite
        fc = (f"[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];"
              f"[2:a]aresample=48000,aformat=channel_layouts=stereo,volume='if(lt(t,{garde - 1}),0,min(1,(t-{garde - 1})/1.5))':eval=frame[m];"
              f"[3:a]atrim=0:{garde + 0.5},asetpts=PTS-STARTPTS,afade=t=out:st={garde - 1}:d=1.5,aresample=48000,aformat=channel_layouts=stereo,apad[o];"
              "[v][m][o]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]")
        ins = ['-i', vid, '-i', vw, '-i', mw, '-i', src]
    else:
        fc = ("[1:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,aformat=channel_layouts=stereo[v];"
              "[2:a]aresample=48000,aformat=channel_layouts=stereo[m];"
              "[v][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.89:level=false[a]")
        ins = ['-i', vid, '-i', vw, '-i', mw]
    out = os.path.join(outdir, c['out'] + '.mp4')
    run(['ffmpeg', '-v', 'error', '-y', *ins, '-filter_complex', fc, '-map', '0:v', '-map', '[a]', '-c:v', 'copy',
         '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', f'{total:.3f}', '-movflags', '+faststart', out])
    run(['ffmpeg', '-v', 'error', '-y', '-ss', '0.3', '-i', out, '-frames:v', '1', '-q:v', '3', os.path.join(outdir, c['out'] + '.jpg')])
    print(out, round(total, 1), 's')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--brand', required=True); ap.add_argument('--promo', required=True)
    ap.add_argument('--models', required=True); ap.add_argument('--only'); ap.add_argument('--outdir', default=os.path.join(ROOT, 'ads', 'video'))
    a = ap.parse_args()
    srcs = {'brand': a.brand, 'promo': a.promo}
    for name, c in CLIPS.items():
        if a.only and name != a.only:
            continue
        print('==', name); build(name, c, srcs, a.models, a.outdir)

if __name__ == '__main__':
    main()
