# Sprint vidéo de 7 jours — SmileFlow (préparé le 20 novembre 2026)

Contenu du dossier
- `scripts.md` : 7 scripts du sprint + 2 en réserve (9:16, 30–45 s).
- `suivi_sprint.csv` : grille de suivi, une ligne par vidéo et par canal (vues à 24 h, 48 h, 7 j, skip, partages…).
- `suivi.py` : calcule la hausse par rapport à la baseline et écrit `rapport_suivi.md`.
- `donnees/baseline_2026-11-06_au_2026-11-20.csv` : baseline réelle (Metricool).
- `donnees/tiktok_recherche_2026-11-20.csv` : échantillon Apify (150 vidéos TikTok, 30 derniers jours).
- `videos/*.json` : le découpage scène par scène de chaque vidéo ; `videos/legendes.md` : les légendes à publier.
- Vidéos finales : `ads/video/sprint/V1.mp4` à `V7.mp4`, `R1.mp4`, `R2.mp4` (9:16), avec une couverture `.jpg` chacune.

Fabrication : `python3 tools/sprint_video/build.py --script strategie/sprint-7j/videos/V1.json --out ads/video/sprint/V1 --models <dossier Kokoro>`.
La voix off est générée localement (Kokoro, voix féminine française « ff_siwis », sans crédits) ; V3 reprend la voix d'Amélie (ElevenLabs) de la version longue, coupée à 40 s.

## 1. Tendances détectées

### Ce qui vient d'Apify (collecté le 20 novembre 2026)
Acteurs utilisés : `clockworks/tiktok-scraper` (recherche vidéo, tri « plus aimées », 30 derniers jours, 6 requêtes × 25 vidéos), `apify/instagram-hashtag-scraper` (6 hashtags, Reels, 174 résultats), `streamers/youtube-scraper` (Shorts, 5 requêtes).

- **T1 · Les vidéos « POV réception / équipe » sont les plus partagées.** Sur TikTok, les meilleurs taux de partage (partages / vues) de l'échantillon viennent de l'humour d'équipe : @sarahjustsmile, 392 680 vues, 5,26 % de partages ; @edcsmiles, 69 464 vues, 3,90 % ; @kidsfirstpd (« ce que fait vraiment la réception »), 202 586 vues, 2,70 %. Ce sont des mèmes de 6 à 8 s. La médiane de l'échantillon est de 0,29 à 0,54 % selon la durée.
- **T2 · Le « vécu d'hygiéniste » fait réagir.** Exemples : @luvlineia (Patient difficile), 146 689 vues, 1,19 % de partages ; @karissabenj (admission en hygiène), 144 255 vues, 1,06 % d'enregistrements ; @kayla.rdhconsultant, 204 283 vues.
- **T3 · La durée n'est pas le problème, les 3 premières secondes oui.** Médianes de l'échantillon TikTok par durée : ≤ 15 s, 34 043 vues, 0,29 % de partages ; 15–30 s, 31 827 vues, **0,54 %** de partages ; 30–60 s, **51 632 vues**, 0,41 % ; > 60 s, 33 913 vues, 0,29 %. La cible de 30–45 s tient.
- **T4 · Presque personne ne fait ce contenu en français québécois.** Seules 10 vidéos sur 150 sont en français. La recherche « dentiste québec » ne remonte aucun créateur du Québec (contenu anglais et ASMR). Sur Instagram, le #dentistequebec remonte un Reel de 9 s de @sante.dentaire.charlesbourg à 75 899 vues et 775 partages (juin 2026) : le court et local fonctionne.
- **T5 · Le « choc de la facture » accroche.** @didn400 (« la facture après une extraction »), 1 620 517 vues : version grand public. Pour nous, la même mécanique s'applique au coût d'une chaise vide (script R2).
- **T6 · Le conseil entre collègues.** @dr.richardlam (« Take notes docs »), 166 961 vues : un dentiste qui parle aux dentistes.

Limites
- YouTube : la recherche de Shorts « dentiste / dentist / hygienist » ne renvoie presque que du contenu pour enfants. Aucun signal utilisable pour un public de dentistes.
- LinkedIn : pas collecté (les acteurs Apify pour LinkedIn demandent une connexion au compte) ; les angles LinkedIn reposent sur la connaissance du métier.
- Les hashtags Instagram mélangent des vidéos anciennes et hors sujet ; seuls des exemples récents et pertinents sont cités.
- Ce sont des échantillons (150 vidéos TikTok, 174 publications Instagram), pas une étude de marché.

### Ce qui vient de la connaissance du métier
Douleurs concrètes des cliniques : blocs d'hygiène qui se libèrent la veille, temps de téléphone pour confirmer et remplir, notes cliniques finies le soir, cartes d'assurance retapées, équipe de réception sous pression. Faits « Radar mondial » vérifiés :
- Kaiser Permanente, communiqué du 14 août 2024 : déploiement de l'outil de documentation clinique d'Abridge dans ses 40 hôpitaux (Fierce Healthcare, Healthcare Dive).
- FDA, dossier K210365 (4 mars 2022) : autorisation de Second Opinion de Pearl, logiciel d'IA qui lit les radiographies dentaires.
- Règlement (UE) 2024/1849 : fin de l'amalgame dentaire dans l'UE au 1er janvier 2025, sauf nécessité médicale.
- Loi 25 : dernières dispositions (droit à la portabilité) en vigueur le 22 septembre 2024 (Québec.ca).

### Notre baseline (14 jours, du 6 au 20 novembre 2026, Metricool)
| Canal | Reels | Vues médianes | Vues totales | Skip à 3 s médian | Temps moyen médian |
|---|---|---|---|---|---|
| Instagram | 12 | 70 | 967 | 87,2 % | 3,3 s |
| Facebook | 13 | 107 | 1 269 | n.d. | 2,0 s |

- Sur Instagram, 72 à 95 % des gens quittent nos Reels avant 3 secondes, alors que nos capsules durent 60 à 96 s. **Le levier principal, c'est l'accroche et le rythme des premières secondes.**
- TikTok : pas de baseline (les statistiques TikTok de Metricool s'arrêtent au 21 octobre ; le compte « directementgagne » est introuvable ou privé pour Apify).
- YouTube : Apify lit 0 vue sur les deux Shorts vérifiés et 3 abonnés (à confirmer dans YouTube Studio).
- LinkedIn : pas de statistiques (connexion Metricool cassée) ; à relever à la main dans les statistiques de la page.

## 2. Scripts
Voir `scripts.md`.

## 3. Sprint de 7 jours

Production : du 23 au 29 novembre. Voix : ElevenLabs (voix d'Amélie) dès que les crédits sont renouvelés (environ 600 à 700 crédits par vidéo de 40 s), ou la voix de Hacene enregistrée au téléphone. Images : cartes texte de `tools/story_video` et captures SmileFlow sans le mot « SOAP ».

| Jour | Date | Vidéo | Instagram + Facebook | TikTok | YouTube Shorts | LinkedIn |
|---|---|---|---|---|---|---|
| J1 | mar. 1er déc. | V2 · Bloc de 14 h : 1, 2 ou 3 ? | 12 h 15 | 12 h | 11 h | 8 h 30 |
| J2 | mer. 2 déc. | V1 · POV réception | 12 h 15 | 12 h | 11 h | — |
| J3 | jeu. 3 déc. | V5 · 40 hôpitaux, un scribe IA | 12 h 15 | 12 h | 11 h | 8 h 30 |
| J4 | ven. 4 déc. | V4 · Note prête avant le paiement | 12 h 15 | 12 h | 11 h | 8 h 30 |
| J5 | sam. 5 déc. | V3 · Table de la cuisine, 40 s (test de durée) | 11 h | 12 h | — | — |
| J6 | dim. 6 déc. | V7 · L'amalgame interdit en Europe | 7 h 30 | 12 h | 11 h | — |
| J7 | lun. 7 déc. | V6 · L'IA qui lit les radios (FDA) | 12 h 15 | 12 h | 11 h | 8 h 30 |

Pour un test propre
- **Mêmes créneaux que la baseline** sur Instagram et Facebook (fenêtres de 7 h 31, 12 h 16 et 11 h 01 le samedi du scénario Make) : seule la vidéo change.
- **Une seule vidéo par jour** sur Instagram et Facebook : les capsules DentalTalks prévues ces jours-là (B12, A06, A09, B31, B05 et leurs affiches) sont décalées d'une semaine.
- LinkedIn : les posts prévus les 1er, 3 et 4 décembre sont décalés ; le 7 décembre est libre.
- TikTok : les capsules prévues à 19 h restent ; les vidéos du sprint passent à 12 h.

Ajustement en cours de route (après J3)
- Une vidéo à ≥ 2 × la médiane de la baseline à 24 h → on refait ce format pour J6–J7 (script R1 ou R2, ou variante).
- Une vidéo ≤ la médiane de la baseline à 48 h → nouvelle première image et nouvelle phrase d'accroche, republiée la semaine suivante.

## 4. Protocole de mesure
- Relevés à **H+24, H+48 et J+7** pour chaque vidéo et chaque canal, dans `suivi_sprint.csv` (Metricool pour Instagram et Facebook, l'application TikTok, YouTube Studio, les statistiques de la page LinkedIn).
- **Indicateur principal** : vues à 48 h par Reel, comparées à la médiane de la baseline du même canal (Instagram 70, Facebook 107).
- **Secondaires** : skip à 3 s et temps moyen (Instagram), partages + enregistrements pour 1 000 vues, commentaires, clics vers smileflow.ca, messages privés.
- **Objectif fixé avant le test** : médiane des vues à 48 h ≥ 1,5 × la baseline sur Instagram (≥ 105) et sur Facebook (≥ 161), et skip médian à 3 s sur Instagram au moins 10 points plus bas (≤ 77,2 %).
- Calcul : `python3 strategie/sprint-7j/suivi.py` écrit `rapport_suivi.md` (tableau par vidéo, total par jour, verdict).
- Limites : 7 vidéos, c'est un signal, pas une preuve statistique ; on compare toujours au même âge et sur les mêmes créneaux ; Metricool peut avoir 24 à 48 h de retard sur Instagram.
