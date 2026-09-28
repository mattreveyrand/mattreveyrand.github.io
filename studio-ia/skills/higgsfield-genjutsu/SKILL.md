---
name: higgsfield-genjutsu
description: >
  Lance Higgsfield Genjutsu sans erreur : transfert de mouvement d'une vidéo
  vers un personnage (hf_mult_motion_control) ou remplacement d'un objet,
  d'un vêtement, d'un produit ou d'un personnage dans une vidéo existante
  (hf_mult_replace_object). À utiliser dès que l'utilisateur dit « genjutsu »,
  « /genjutsu », « copie ce mouvement », « fais danser mon perso comme dans
  cette vidéo », « reprends la chorégraphie », « remplace l'objet / le
  produit / la tenue / le personnage dans cette vidéo », ou quand une
  tentative Genjutsu a échoué. Pas pour : générer une vidéo à partir de
  rien (Seedance 2.5), ni faire 10 variantes d'une pub (workflow ad-multiplier).
---

# Higgsfield Genjutsu

Genjutsu n'est **pas** un identifiant de modèle. C'est une famille de deux
modèles appelés avec `generate_video` (MCP) ou `higgsfield generate create` (CLI).

| Intention | Modèle | Médias |
|---|---|---|
| Copier un mouvement, une danse, un geste, un mouvement de caméra d'une vidéo vers le sujet d'une image | `hf_mult_motion_control` | 1 vidéo « conductrice » + 1 à n images du sujet |
| Remplacer un objet, un produit, un vêtement ou un personnage dans une vidéo source | `hf_mult_replace_object` | 1 vidéo source + 1 à n images du nouvel élément |

Paramètre unique : `resolution` = `480p` · `720p` (défaut) · `1080p`.
Pas de `duration` ni d'`aspect_ratio` : la sortie suit la vidéo source.

## Étape 1 — Choisir le modèle par l'intention

- Le verbe est *copier, reproduire, imiter, transférer, faire danser* → `hf_mult_motion_control`.
- Le verbe est *remplacer, changer, échanger, mettre X à la place de Y* → `hf_mult_replace_object`.
- Plusieurs versions indépendantes d'une même pub → ce n'est pas Genjutsu :
  charger le workflow `ad-multiplier` (`get_workflow_instructions`).
- Ne jamais passer par l'ancien outil `motion_control` ni par `ad-multiplier`
  pour une seule édition Genjutsu.

## Étape 2 — Obtenir des media_id confirmés (cause n°1 des échecs)

`medias[].value` accepte **uniquement** un UUID : `media_id` d'upload ou `job_id`
d'une génération précédente. Jamais une URL https, jamais un chemin local.

- Fichiers sur l'ordinateur, dans l'app Claude : appeler `media_upload_widget`
  avec `type: "auto"`, `multiple: true`, **seul outil du tour**. L'utilisateur
  choisit la vidéo et les photos dans le widget, qui renvoie les media_id.
- Média sur le web : `media_import_url` → `media_id`.
- Rendu Higgsfield précédent : réutiliser son `job_id`.
- CLI (Claude Code) : les flags `--video` / `--image` acceptent un chemin et
  uploadent tout seuls. Vérifier les noms de flags une fois avec
  `higgsfield model get hf_mult_motion_control --json`.

## Étape 3 — Vérifier les entrées avant d'envoyer

- [ ] **Exactement une** vidéo, rôle `video`.
- [ ] Au moins une image, rôle `image` (le serveur les range en `image_references`).
- [ ] Pour le transfert de mouvement : vidéo conductrice avec **un seul sujet**,
      corps entier visible, cadrage stable, sans coupe, bien éclairée, fond lisible.
- [ ] Image du personnage : même cadrage que la vidéo (plein pied si la vidéo est
      en plein pied), pose neutre, membres visibles, pas de flou ni d'accessoires
      qui cachent les mains.
- [ ] Pour le remplacement : l'objet à remplacer est net et visible pendant tout
      le plan ; l'image de référence le montre sous un angle proche.
- [ ] Prompt court qui nomme ce qui doit changer et ce qui doit rester
      (voir modèles ci-dessous).
- [ ] Devis : même appel avec `get_cost: true` (ne lance rien).

## Étape 4 — Devis, puis un seul envoi

Le prix n'est pas fixe : il dépend de la durée et de la résolution de la vidéo
source (relevés réels en septembre 2026 : de 15 à 35 crédits pour des clips
courts, 297 crédits pour un transfert de mouvement long en haute définition).
Toujours demander le devis d'abord, l'annoncer, et attendre l'accord au-delà
de 50 crédits.

```json
{
  "params": {
    "model": "hf_mult_motion_control",
    "prompt": "Transfer the full-body dance, timing and camera motion of the performer in @Video1 onto the woman in @Image1. Keep her face, hair, skin tone, outfit and proportions exactly as in @Image1 in every frame. Keep the background of @Image1. Natural anatomy, no extra people, no text, no watermark.",
    "resolution": "720p",
    "medias": [
      { "role": "video", "value": "<media_id de la vidéo conductrice>" },
      { "role": "image", "value": "<media_id de la photo du personnage>" }
    ],
    "get_cost": true
  }
}
```

Retirer `get_cost` pour lancer. Remplacement d'objet : même forme avec
`"model": "hf_mult_replace_object"` et un prompt construit sur le contrat
d'édition des workflows Higgsfield :

> Replace only the white sneakers worn by the man in @Video1 with the shoes from @Image1, matching their exact shape, colors, materials and logo placement. Keep the man, his motion, the camera moves, cuts, lighting, background, timing and every on-screen text from @Video1 exactly the same.

- `@Video1`, `@Image1`, `@Image2`… suivent l'ordre des médias dans `medias`.
- Une seule cible, désignée sans ambiguïté (couleur, position, qui la porte).
- Pas d'identifiant ni d'URL dans le prompt.
- Prompt en anglais, même si la conversation est en français.

Après l'envoi : `jobs_wait` avec `timeout_seconds: 15` ; le widget se met à
jour seul. **Ne jamais renvoyer** tant que le premier job n'a pas de statut
(terminé ou échoué) : chaque envoi est facturé. Sur un timeout de transport,
réutiliser le `job_id` et vérifier son statut avant toute nouvelle tentative.

## Diagnostic d'un échec

| Symptôme | Cause probable | Correction |
|---|---|---|
| « unknown model » / modèle introuvable | `model: "genjutsu"` | `hf_mult_motion_control` ou `hf_mult_replace_object` |
| Refus sur `medias` | 0 ou 2 vidéos, ou rôle absent | exactement 1 `video` + ≥ 1 `image` |
| Refus sur `value` | URL ou chemin au lieu d'un UUID | `media_upload_widget` / `media_import_url` |
| « free gens » refusés | essais gratuits demandés via MCP | non disponibles sur le connecteur : web uniquement |
| Crédits insuffisants | solde | `balance`, puis `get_cost` pour dimensionner |
| Le job tourne mais le résultat est faux (mauvaise cible, membres qui fondent) | vidéo chargée (plusieurs sujets, coupes, sujet qui sort du cadre), cible mal nommée | recouper la vidéo à un seul plan net (4 à 15 s conseillés ; la durée max n'est pas documentée), prompt « Replace only… / Keep … exactly the same » |
| Facture bien plus haute que prévu | renvois pendant qu'un job tourne ; source longue en 1080p | un seul envoi + `jobs_wait` ; devis ; brouillon 480p |
| Visage qui dérive | image de référence trop petite ou de profil | portrait net de face, même lumière que la vidéo |
| Rien ne change (remplacement) | prompt vague | nommer l'objet source *et* l'objet cible, préciser « keep everything else unchanged » |

Brouillon en `480p` pour valider le mouvement, puis relancer en `1080p`
seulement quand le résultat est bon.

Vérifié le 28.09.2026 : `get_preset_instructions("/genjutsu")` et
`models_explore(get)` sur le connecteur Higgsfield.
