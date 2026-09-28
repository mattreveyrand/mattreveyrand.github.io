# Projet vidéo — <nom>

Réponds en français. Les prompts de génération s'écrivent en anglais.

## But

<une phrase : quelle vidéo, pour qui, quel format (9:16, 16:9), quelle durée>

## Où sont les choses

- `brief/` — une fiche par plan : intention, action, caméra, durée. Lire la fiche avant d'écrire un prompt.
- `refs/` — références validées (planches perso, décors, objets). Images légères ; les originaux restent sur Higgsfield.
- `prompts/` — un fichier par plan, prompt validé + modèle + réglages + coût réel.
- `decisions/` — ce qui a été tranché, daté (`AAAA-MM-JJ-sujet.md`). Lire du plus récent au plus ancien en début de session.
- `renders/` — sorties lourdes. Ne jamais les lire : utiliser `ffprobe` pour les métadonnées.

## Règles Higgsfield

1. Devis avant chaque rendu : même appel avec `"get_cost": true`, annoncer le prix, attendre mon accord au-delà de 50 crédits.
2. Brouillons en 480p, 5 à 8 s. Le 1080p seulement pour un plan validé.
3. Un seul envoi par job. Après un timeout, vérifier le statut du job avant tout renvoi.
4. Genjutsu : `hf_mult_motion_control` (mouvement) ou `hf_mult_replace_object` (remplacement), exactement une vidéo en rôle `video`, images en rôle `image`, des media_id confirmés.
5. Aucune publication (TikTok, YouTube, Instagram) sans mon accord explicite dans la conversation.

## Fin de session

Écrire dans `decisions/` : ce qui a marché, ce qui a échoué et pourquoi, le coût, la prochaine étape. Dix lignes maximum.
