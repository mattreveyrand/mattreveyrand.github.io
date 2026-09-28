# Retouche d'une vidéo (mode `video_edit`)

Gabarit officiel des workflows Higgsfield (workflow `ad-multiplier`, fichier
`references/prompt-writer.md`, relevé le 28.09.2026). Seedance 2.5 en
`video_edit` : le modèle `ad_multiplier` est « powered by Seedance 2.5 » (même schéma de paramètres) ; ce contrat est écrit pour lui et on l'applique par extension à `seedance_2_5`, à valider sur un brouillon 480p.

## Règles

- Étiquettes exactes, sensibles à la casse : `@Video1` pour la source,
  `@Image1` … `@ImageN` dans l'ordre des médias.
- Pas d'identifiant ni d'URL dans le prompt ; 3 900 caractères maximum.
- Les segments de temps couvrent tout le clip, sans trou.
- Pas de « si… ou… » dans le prompt.
- Une image de personne vaut pour le look complet (visage, cheveux, vêtements,
  accessoires), sauf si une image de vêtement séparée est fournie.
- `video_edit` facture toute la durée de la source : couper la source avant.
- Son : le workflow ad-multiplier rend la retouche en muet (`generate_audio: false`) puis remet l'audio d'origine de la source au montage (ffmpeg). Faire de même pour garder la bande-son et les voix intactes.
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

Ordre complet du gabarit DÉTAILLÉ : 1) avant tout, une déclaration par référence : « @ImageN — <ALIAS>, the complete replacement look for <TARGET>: <identité, cheveux, tenue, chaussures, accessoires>. Transfer this entire look from @ImageN, including the full outfit and all worn accessories. » ; 2) le bloc « Preserve every caption… » ; 3) « Video edit. Keep this @Video1 clip exactly as it is — the same shots and cuts, camera moves, framing, […]. Change only <périmètre>… » ; 4) des blocs numérotés « 1. REPLACE — … » (une opération par bloc, avec la phrase d'exclusion ci-dessus) ; 5) « IDENTITY lock: … » ; 6) une phrase « Render … » ; 7) la dernière phrase
« Everything else — […] — stays exactly the same. »

La personne de remplacement doit être un adulte, avec son consentement si
c'est une personne réelle.
