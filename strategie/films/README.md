# Vidéos tirées du film de marque et de la promo (22 novembre 2026)

Sources : `smileflowbrandfilm1920x1080.mp4` (film de marque, 16:9) et `smileflowpromo1080x1920.mp4` (promo, 9:16), fournis par Hacene le 22 novembre 2026.

Fabrication : `python3 tools/promo_cuts/build.py --brand <film> --promo <promo> --models <dossier Kokoro>`.
Chaque extrait garde l'image d'origine, retire le mot « SOAP » de l'en-tête de la note (le reste de la carte est intact), ajoute une voix off féminine locale (Kokoro, ff_siwis), une musique douce sous la voix et une carte de fin (logo, phrase d'abonnement, smileflow.ca, « Réservez une démo »). Les passages « démo gratuite » et « 100 % conforme Loi 25 » des sources ne sont pas repris.

| Fichier | Format | Durée | Contenu |
|---|---|---|---|
| `ads/video/Film_Scribe_916.mp4` | 9:16 | 23 s | Dictée, brouillon de note clinique, validation et signature, audio supprimé |
| `ads/video/Film_Liste-attente_916.mp4` | 9:16 | 18 s | Annulation, plage offerte par texto à la liste d'attente |
| `ads/video/Film_Avis_916.mp4` | 9:16 | 16 s | Remerciement après la visite, invitation à laisser un avis |
| `ads/video/Film_Marque_169.mp4` | 16:9 | 50 s | Le film de marque complet, voix off sur les trois tâches |

## Programmation

| Date (heure de Montréal) | Vidéo | Réseau | Où |
|---|---|---|---|
| lun. 23 nov., 8 h 30 | Marque | LinkedIn (page SmileFlow) | file Make 184383, `li-2026-11-23-film-marque` |
| lun. 23 nov., 17 h | Marque | YouTube | `yt-2026-11-23-film-marque` |
| mar. 24 nov., 17 h | Liste d'attente | YouTube Shorts | `yt-2026-11-24-film-attente` |
| mar. 24 nov., 17 h 30 | Liste d'attente | Reel Instagram + Facebook | calendrier DentalTalks 173736, `FILM-attente` |
| jeu. 26 nov., 17 h | Notes cliniques | YouTube Shorts | `yt-2026-11-26-film-scribe` |
| jeu. 26 nov., 17 h 30 | Notes cliniques | Reel Instagram + Facebook | `FILM-scribe` |
| sam. 28 nov., 11 h | Après la visite | Reel Instagram + Facebook | `FILM-avis` |
| sam. 28 nov., 17 h | Après la visite | YouTube Shorts | `yt-2026-11-28-film-avis` |
| lun. 30 nov., 8 h 30 | Notes cliniques | LinkedIn (page SmileFlow) | `li-2026-11-30-film-scribe` |

Rien n'est programmé du 1er au 7 décembre (sprint vidéo). TikTok : pas programmé (forfait Metricool plein en novembre et presque plein en décembre).

## À savoir sur les sources
Les titres d'origine restent visibles dans les extraits : « 30 secondes de dictée. Zéro paperasse. » (Notes cliniques et Marque), « Une annulation ? Fauteuil comblé en 60 secondes. » et « 0 appel téléphonique » (Liste d'attente et Marque), « Votre clinique au sommet de Google Maps. » avec une note 4,9 sur 127 avis en maquette (Après la visite et Marque). Pour les remplacer par un titre neutre, il faut refaire le rendu des extraits concernés.
