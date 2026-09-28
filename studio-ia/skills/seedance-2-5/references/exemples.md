# Exemples de prompts Seedance 2.5

Écrits selon les règles sourcées (guides BytePlus, Higgsfield, doctrine
communautaire) ; ce ne sont pas des citations. Point de départ, à valider sur
un brouillon 480p.

## 1. Plan de cinéma (t2v, 8 s, 16:9)

```text
Rain-soaked neon alley at night, anamorphic look, teal-and-amber grade, fine 35mm grain.
A courier in a soaked olive parka stops under a flickering pink sign, pulls back her hood
and exhales a cloud of breath; her eyes track something off-screen left, jaw tightening.
Slow dolly in from medium shot to close-up over 6 seconds, shallow depth of field, pink rim
light, wet reflections on the asphalt. Audio: steady rain, distant traffic hiss
<the neon sign crackles once>. No music.
```

## 2. Pub produit (omni_reference, 10 s, 9:16)

```text
@Image1 defines the perfume bottle only: keep its exact shape, glass color, cap and label;
do not copy its white studio background.
0-3s: the bottle rests on wet black stone, a single drop slides down the glass, macro
close-up, slow push in.
3-7s: smooth 180-degree orbit at eye level, constant distance, warm backlight glows through
the liquid, light haze.
7-10s: locked-off hero shot, a soft light sweep crosses the label.
High-end commercial look, deep blacks, gold highlights, tack-sharp.
(slow deep ambient synth pad) <a crystalline chime as the light sweeps>
```

## 3. UGC face caméra, dialogue en français (omni_reference, 10 s, 9:16)

```text
UGC creator selfie video on a phone front camera, handheld with slight natural shake, soft
window daylight, real lived-in bedroom. A woman with curly auburn hair holds the serum
bottle from @Image1 next to her cheek, looks into the lens, natural blinks, small smile a
half-beat late.
Dialogue language: natural Parisian French, relaxed conversational delivery.
She says: {Franchement, je pensais pas que ça marcherait aussi vite.}
She taps the bottle twice. She says: {Trois jours, et regarde ma peau.}
Audio: clear voice, quiet room tone, faint street noise. No music.
```

Le prompt est en anglais, seules les répliques sont en français. Pour du
français parlé, rester sur Seedance 2.5 : l'audio natif de Kling 3.0 ne liste
pas officiellement le français.

## 4. Action en plusieurs plans (t2v, 12 s, 16:9)

```text
GLOBAL STYLE: gritty action thriller, handheld 35mm look, desaturated steel-blue grade,
3 shots, 12 seconds.
Shot 1 (0-4s): wide shot, rooftop at dusk; a runner in a torn grey hoodie sprints to the
edge, FPV drone chasing low behind him. Hard cut.
Shot 2 (4-8s): side tracking shot; he leaps the gap between buildings, hoodie flaring, city
lights far below, slight slow motion at the peak. Hard cut.
Shot 3 (8-12s): low angle, static; he lands, rolls and rises into frame breathing hard,
looking back at the gap.
PHYSICS: real weight on landing, gravel scatters.
AUDIO: wind rush, footsteps on gravel, heavy landing impact, ragged breathing. No music.
```

## 5. Anime 2D (t2v, 8 s)

```text
Bold 2D anime, flat cel-shaded coloring, thick clean outlines, limited palette of dusty
pink, cream and deep navy. A girl in a navy blazer waits on a train platform as
cherry-blossom petals drift past; the wind lifts her hair and scarf, she turns toward the
incoming train and smiles softly. Static wide shot, then a slow push in to a medium
close-up; anime speed lines as the train rushes past.
(gentle piano melody) <distant train horn, rushing wind>
```

## 6. Image de départ (omni_reference + start_image, 5 s)

```text
@Image1 is the first frame; keep its framing, light and wardrobe. She slowly turns her
head toward the camera as the wind lifts her hair; dust drifts through the sunbeam.
Slow dolly in. Audio: soft wind, distant birds.
```

Décrire le mouvement, pas l'image : elle est déjà donnée.

## 7. Prolongation (video_extension, forward, 8 s)

```text
Extend @Video1 forward by 8 seconds. Continue from its last frame: the courier is still
under the pink neon sign, facing left, hood down, same medium close-up, same rain. Then she
steps out of the light and walks away down the alley while the camera holds, letting her
fade into the haze. Keep the same grade, light and rain sound.
```

Garder les mots « extend / continue ». « Then connect to the source video » est
une formulation connue pour échouer. En `backward`, le nouveau segment doit
finir sur la première image de la source.

## 8. Plan subjectif (POV)

```text
First-person POV, 10 seconds, 16:9. My frost-covered hands rise into frame and a blast of
ice shoots forward, freezing a rusted ship hull solid; I step forward over cracking ice.
No cuts, no zoom, natural head movement. Audio: cracking ice, howling wind, heavy breathing.
```
