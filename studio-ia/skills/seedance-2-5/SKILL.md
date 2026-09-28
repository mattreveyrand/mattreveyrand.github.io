---
name: seedance-2-5
description: >
  Écrit, chiffre et lance des vidéos Seedance 2.5 sur Higgsfield (modèle
  seedance_2_5) : texte vers vidéo, vidéo à partir de références (personnage,
  décor, objet, image de départ ou de fin), retouche d'une vidéo existante,
  prolongation avant ou après. À utiliser quand l'utilisateur dit « Seedance »,
  « Seedance 2.5 », « génère ce plan », « prolonge cette vidéo », « retouche ce
  clip », « combien ça coûte en crédits », ou veut passer d'un brouillon au
  final. Pas pour : copier un mouvement ou remplacer un objet (higgsfield-genjutsu),
  plusieurs variantes d'une pub (workflow ad-multiplier), la 4K native
  (seedance_2_0 en mode std).
---

# Seedance 2.5 sur Higgsfield

Relevé sur le connecteur Higgsfield le 28.09.2026. Vérifier une fois par mois
avec `models_explore` (`action: "get"`, `model_id: "seedance_2_5"`) ou
`higgsfield model get seedance_2_5 --json`.

## Réglages

| Paramètre | Valeurs | Règle |
|---|---|---|
| `mode` | `t2v` (défaut) · `omni_reference` · `video_edit` · `video_extension` | `t2v` refuse toute référence |
| `duration` | 4 à 30 s (défaut 5) | ignorée en `video_edit` (facturé sur la source) |
| `resolution` | `480p` · `720p` (défaut) · `1080p` | pas de 4K → `seedance_2_0` mode `std`, 15 s max |
| `aspect_ratio` | auto · 21:9 · 16:9 · 4:3 · 1:1 · 3:4 · 9:16 | ignoré en retouche et prolongation |
| `generate_audio` | true (défaut) | le couper ne baisse pas le prix |
| `bitrate_mode` | `standard` · `high` | |
| `extension_mode` | `forward` · `backward` | obligatoire en `video_extension`, interdit ailleurs |
| rôles `medias` | `start_image`, `end_image`, `image_references`, `video_references`, `audio_references` | `start_image`/`end_image` seulement en `omni_reference` ; 50 références max, 30 images max |

## Prix (devis du connecteur, 28.09.2026)

8 s en `t2v` : 24 crédits en 480p, 56 en 720p, 96 en 1080p, soit ~3 / 7 / 12
crédits par seconde. 30 s en 720p : 210 crédits. Les prix bougent : toujours
refaire le devis.

## Protocole

Il n'y a pas de seed sur Higgsfield : un nouveau rendu est toujours une
nouvelle prise. Le brouillon valide le prompt, pas la prise.

1. **Brief** : lire la fiche du plan (`brief/plan-NN.md`) si elle existe.
2. **Prompt** : gabarit ci-dessous, en anglais, moins de ~200 mots ; seules les
   répliques sont dans la langue parlée.
3. **Devis** : même appel avec `"get_cost": true`. Annoncer le prix ; au-delà
   de 50 crédits, attendre l'accord explicite de l'utilisateur.
4. **Brouillon** : 480p, 5 à 8 s. Changer une seule chose par nouvel essai ;
   budget d'environ 3 prises payantes par plan, puis changer de stratégie
   (découper le plan, changer de mode ou de référence) plutôt que relancer.
   Pour régler le cadrage et l'action à moindre coût, `seedance_2_0_mini` en
   480p (~2,5 crédits les 5 s) suffit quand on n'a pas besoin des fonctions
   propres à la 2.5.
5. **Final** :
   - la prise du brouillon te plaît → l'agrandir plutôt que la refaire :
     `upscale_video` (Bytedance, préréglage `aigc`, 1080p à 4K, 24 i/s) ;
   - sinon → même prompt en 1080p, durée finale, un seul envoi, puis
     `jobs_wait` (`timeout_seconds: 15`).
   Jamais de renvoi tant que le premier job n'a pas de statut ; après un
   timeout de transport, vérifier le `job_id`.
6. **Journal** : prompt validé, modèle, réglages, variable changée et coût réel
   dans `prompts/plan-NN.md`.

## Gabarit de prompt

Ordre officiel des blocs (guide Seedance 2.5) : sujet + action + décor + style
+ caméra ou coupe + son. Seuls le sujet et l'action sont obligatoires : omettre
plutôt que remplir. Mettre sujet, action et cadrage dans les 20 à 30 premiers
mots, qui pèsent le plus.

```text
GLOBAL STYLE: <une règle visuelle : pellicule, contraste, palette>

CHARACTERS:
@Image1 defines <Name>'s face, hairstyle and clothing.
@Image2 defines <the location> and its light. Do not use the people in this image.

SHOT 1 (0-4s) — <valeur de plan + un seul mouvement de caméra>: <action>. Ends with <état visible>.
SHOT 2 (4-8s) — <valeur de plan + caméra>: <action>. Ends with <état visible>.

Dialogue language: natural Parisian French.   ← seulement s'il y a des répliques
<Name> says: {<réplique en français>}

AUDIO: (<musique>) <<bruitages>>. No music.   ← « No music. » en texte simple, jamais entre ()
```

Règles :
- Une ligne par sujet de référence, avec ce qu'il faut ignorer. Jamais
  « @Images 1 to 4 define four characters ». Plusieurs vues d'un même sujet :
  « All three images define one lamp. The output must contain only one lamp. »
- Planche personnage en référence : ajouter « Do not take the gray backdrop,
  the panel borders, or the multi-view layout. »
- Une caméra par plan. Pour une action rapide, décrire la position de départ
  et d'arrivée du corps, pas le mouvement intermédiaire.
- Formuler en positif (pas de prompt négatif) : « tack sharp », pas « no blur ».
- Pas de personnalité réelle, de marque ou de personnage sous licence :
  décrire sans nommer (sinon refus pour propriété intellectuelle).
- Action physique lourde et gros plan de jeu : deux générations séparées.
- Plusieurs angles : format plan par plan, jamais un paragraphe continu ;
  annoncer en tête le nombre de plans, la durée et le format.
- Pas de texte entre guillemets dans les actions (il serait prononcé) : toute
  parole va dans `{}`.
- Français parlé : Seedance 2.5 (l'audio natif de Kling 3.0 ne liste pas le
  français). Répliques courtes, une langue par prompt.

Les étiquettes `@Image1`, `@Video1`, `@Audio1` suivent l'ordre des médias
dans `medias`. Les crochets du son (`()` musique, `<>` bruitages, `{}` dialogue)
viennent de la doctrine Seedance reprise par la communauté : valider sur un
brouillon 480p.

## Appels

Texte vers vidéo :

```json
{"params": {"model": "seedance_2_5", "mode": "t2v", "prompt": "…",
  "duration": 8, "resolution": "480p", "aspect_ratio": "9:16",
  "generate_audio": true, "get_cost": true}}
```

Références + image de départ :

```json
{"params": {"model": "seedance_2_5", "mode": "omni_reference", "prompt": "@Image1 is the opening frame. …",
  "duration": 8, "resolution": "480p", "aspect_ratio": "9:16",
  "medias": [
    {"role": "start_image", "value": "<media_id>"},
    {"role": "image_references", "value": "<media_id personnage>"},
    {"role": "image_references", "value": "<media_id objet>"}],
  "get_cost": true}}
```

Prolongation (`backward` pour ajouter avant) :

```json
{"params": {"model": "seedance_2_5", "mode": "video_extension", "extension_mode": "forward",
  "prompt": "The first frame of the extended segment directly continues from the last frame of @Video1: …",
  "duration": 8, "resolution": "720p",
  "medias": [{"role": "video_references", "value": "<media_id ou job_id>"}],
  "get_cost": true}}
```

Retouche : lire `references/retouche.md` (gabarit officiel « TASK - VIDEO EDIT »).
Vocabulaire de caméra, de lumière et de style : `references/camera.md`.
Huit exemples complets (cinéma, pub, UGC en français, action, anime, image de
départ, prolongation, POV) : `references/exemples.md`.

CLI (Claude Code) : `higgsfield generate cost seedance_2_5 --duration 8 --resolution 480p`
puis `higgsfield generate create seedance_2_5 --prompt "…" --mode omni_reference --start-image ./first.png --duration 8 --resolution 480p --wait`.
