# Retouche d'une vidéo (mode `video_edit`)

Gabarit officiel des workflows Higgsfield (workflow `ad-multiplier`, fichier
`references/prompt-writer.md`, relevé le 28.09.2026). Seedance 2.5 en
`video_edit` et le modèle `ad_multiplier` utilisent le même contrat.

## Règles

- Étiquettes exactes, sensibles à la casse : `@Video1` pour la source,
  `@Image1` … `@ImageN` dans l'ordre des médias.
- Pas d'identifiant ni d'URL dans le prompt ; 3 900 caractères maximum.
- Les segments de temps couvrent tout le clip, sans trou.
- Pas de « si… ou… » dans le prompt.
- Une image de personne vaut pour le look complet (visage, cheveux, vêtements,
  accessoires), sauf si une image de vêtement séparée est fournie.
- `video_edit` facture toute la durée de la source : couper la source avant.
- Source de 4 à 30 s ; hors de cet intervalle, le workflow refuse.

## Gabarit COMPACT

```text
TASK - VIDEO EDIT:
Preserve every caption, subtitle, and other untargeted on-screen text element from @Video1 exactly as it appears, including its wording, styling, placement, animation, and timing. Text physically attached to a replaced target follows that replacement.
0-4s: keep everything exactly the same
4-8s: Replace only <target> in @Video1 with <replacement> from @Image1. Keep every unrequested element, camera motion, lighting treatment, and overall color grading from @Video1 exactly the same.
```

## Verbes d'opération (un par segment)

- `Replace only <target> in @Video1 with <replacement> from @ImageN`
- `Modify only <target> in @Video1 so that <change>`
- `Remove only <target> from @Video1 and reconstruct the revealed area consistently with its immediate surroundings`
- `Add only <element> at <placement> in @Video1`

## Remplacer une personne (gabarit DÉTAILLÉ obligatoire)

Ajouter la phrase d'exclusion :

```text
The original source person identified as <target> in @Video1 must never appear in any frame of the output. Replace that person completely with <ALIAS> from @ImageN in every appearance, transferring the complete reference-defined look and retaining only the original performance, pose, blocking, interactions, and timing.
```

Puis un bloc IDENTITY, un résumé du rendu, et une dernière phrase
« Everything else — […] — stays exactly the same. »

La personne de remplacement doit être un adulte, avec son consentement si
c'est une personne réelle.
