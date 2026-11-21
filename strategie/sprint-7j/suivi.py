"""Mesure du sprint de 7 jours : les vues augmentent-elles par rapport à la baseline ?

    python3 strategie/sprint-7j/suivi.py            # écrit rapport_suivi.md à côté de ce fichier

Entrées (même dossier) :
  donnees/baseline_2026-11-06_au_2026-11-20.csv   baseline réelle (Metricool, 14 jours avant le test)
  suivi_sprint.csv                                une ligne par vidéo et par canal, à remplir à H+24, H+48 et J+7

Règles de décision (fixées avant le test) :
  - indicateur principal : vues à 48 h par Reel, comparées à la médiane de la baseline du même canal ;
  - réussite du sprint : médiane des vues à 48 h ≥ 1,5 × la médiane de la baseline (Instagram et Facebook),
    et taux de skip à 3 s médian sur Instagram au moins 10 points sous la baseline ;
  - « gagnante » : une vidéo ≥ 2 × la médiane de la baseline ; « à refaire » : ≤ la médiane de la baseline.
Sans baseline (TikTok, YouTube, LinkedIn), la référence est la médiane des vidéos du sprint sur ce canal.
"""
import csv, os, statistics as st
from collections import defaultdict

ICI = os.path.dirname(os.path.abspath(__file__))
SEUIL_REUSSITE, SEUIL_GAGNANTE, BAISSE_SKIP = 1.5, 2.0, 10.0


def nombre(x):
    try:
        return float(str(x).replace(',', '.').replace(' ', ''))
    except (TypeError, ValueError):
        return None


def lire(chemin):
    with open(chemin, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def mediane(valeurs):
    v = [x for x in valeurs if x is not None]
    return st.median(v) if v else None


def fmt(x, d=0):
    if x is None:
        return 'n.d.'
    return f"{x:,.{d}f}".replace(',', ' ').replace('.', ',')


def pct(x):
    return 'n.d.' if x is None else fmt(x, 1) + ' %'


def main():
    base = lire(os.path.join(ICI, 'donnees', 'baseline_2026-11-06_au_2026-11-20.csv'))
    test = lire(os.path.join(ICI, 'suivi_sprint.csv'))

    ref = {}
    for canal in sorted({r['canal'] for r in base}):
        rs = [r for r in base if r['canal'] == canal]
        ref[canal] = {
            'n': len(rs),
            'vues_med': mediane(nombre(r['vues']) for r in rs),
            'vues_tot': sum(nombre(r['vues']) or 0 for r in rs),
            'skip_med': mediane(nombre(r['taux_skip_3s_pct']) for r in rs),
            'temps_med': mediane(nombre(r['temps_moyen_s']) for r in rs),
            'partages': sum(nombre(r['partages']) or 0 for r in rs),
            'enreg': sum(nombre(r['enregistrements']) or 0 for r in rs),
        }

    remplis = [r for r in test if nombre(r['vues_48h']) is not None or nombre(r['vues_24h']) is not None]
    sortie = ['# Sprint 7 jours : suivi des vues', '',
              f"Lignes du sprint remplies : {len(remplis)} sur {len(test)}.", '',
              '## Baseline (14 jours avant le test, Metricool)', '',
              '| Canal | Reels | Vues médianes | Vues totales | Skip 3 s médian | Temps moyen médian | Partages | Enregistrements |',
              '|---|---|---|---|---|---|---|---|']
    for c, b in ref.items():
        sortie.append(f"| {c} | {b['n']} | {fmt(b['vues_med'])} | {fmt(b['vues_tot'])} | {pct(b['skip_med'])} | {fmt(b['temps_med'], 1)} s | {fmt(b['partages'])} | {fmt(b['enreg'])} |")
    sortie += ['', 'TikTok, YouTube et LinkedIn : pas de baseline fiable (voir README) ; référence = médiane du sprint sur le canal.', '']

    # référence interne pour les canaux sans baseline
    par_canal = defaultdict(list)
    for r in remplis:
        par_canal[r['canal']].append(r)
    ref_interne = {c: mediane(nombre(r['vues_48h']) for r in rs) for c, rs in par_canal.items()}

    sortie += ['## Vidéo par vidéo (vues à 48 h)', '',
               '| Jour | Vidéo | Canal | Vues 24 h | Vues 48 h | Vues 7 j | × référence | Skip 3 s | Partages + enreg. / 1 000 vues | Verdict |',
               '|---|---|---|---|---|---|---|---|---|---|']
    for r in remplis:
        c = r['canal']
        v48 = nombre(r['vues_48h'])
        referentiel = ref[c]['vues_med'] if c in ref else ref_interne.get(c)
        mult = (v48 / referentiel) if (v48 is not None and referentiel) else None
        ps = (nombre(r['partages']) or 0) + (nombre(r['enregistrements']) or 0)
        taux_ps = ps / v48 * 1000 if v48 else None
        if mult is None:
            verdict = 'en attente'
        elif mult >= SEUIL_GAGNANTE:
            verdict = 'gagnante : refaire ce format'
        elif mult <= 1:
            verdict = 'à refaire : nouvelle accroche'
        else:
            verdict = 'au-dessus de la référence'
        sortie.append(f"| {r['jour']} | {r['video_id']} | {c} | {fmt(nombre(r['vues_24h']))} | {fmt(v48)} | {fmt(nombre(r['vues_7j']))} | {fmt(mult, 2)} | {fmt(nombre(r['taux_skip_3s_pct']), 1)} | {fmt(taux_ps, 1)} | {verdict} |")

    sortie += ['', '## Total des vues par jour du sprint (48 h, tous canaux)', '', '| Jour | Date | Vues 48 h |', '|---|---|---|']
    par_jour = defaultdict(float)
    dates = {}
    for r in remplis:
        par_jour[r['jour']] += nombre(r['vues_48h']) or 0
        dates[r['jour']] = r['date']
    for j in sorted(par_jour):
        sortie.append(f"| {j} | {dates[j]} | {fmt(par_jour[j])} |")

    sortie += ['', '## Verdict du sprint (Instagram et Facebook)', '']
    for c in ('instagram', 'facebook'):
        rs = [r for r in remplis if r['canal'] == c and nombre(r['vues_48h']) is not None]
        med = mediane(nombre(r['vues_48h']) for r in rs)
        if not rs or not ref.get(c, {}).get('vues_med'):
            sortie.append(f"- {c} : pas encore assez de données.")
            continue
        mult = med / ref[c]['vues_med']
        ligne = f"- {c} : médiane à 48 h = {fmt(med)} vues sur {len(rs)} Reels, soit {fmt(mult, 2)} × la baseline ({fmt(ref[c]['vues_med'])})"
        ok = mult >= SEUIL_REUSSITE
        if c == 'instagram':
            skip = mediane(nombre(r['taux_skip_3s_pct']) for r in rs)
            if skip is not None and ref[c]['skip_med'] is not None:
                baisse = ref[c]['skip_med'] - skip
                ligne += f" ; skip 3 s médian {fmt(skip, 1)} % ({fmt(baisse, 1)} points sous la baseline)"
                ok = ok and baisse >= BAISSE_SKIP
        ligne += ' → objectif atteint.' if ok else ' → objectif pas encore atteint.'
        sortie.append(ligne)
    sortie += ['', f"Seuils fixés avant le test : réussite ≥ {SEUIL_REUSSITE} × la baseline, gagnante ≥ {SEUIL_GAGNANTE} ×, baisse du skip ≥ {BAISSE_SKIP:g} points.",
               'Petits volumes : 7 vidéos ne suffisent pas pour une preuve statistique ; on compare toujours au même âge (48 h) et sur les mêmes créneaux.']

    chemin = os.path.join(ICI, 'rapport_suivi.md')
    with open(chemin, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sortie) + '\n')
    print('\n'.join(sortie))
    print(f"\n→ {chemin}")


if __name__ == '__main__':
    main()
