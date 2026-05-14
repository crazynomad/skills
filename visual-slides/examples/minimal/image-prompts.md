# Image Prompts — Minimal Example

> V2 四段式 · 详见 `../../references/image-prompts-v2.md`

---

## p1-img-hero (HF 全幅封面)

**比例**: 16:9 · **暗罩**: alpha 0.55(scrim_bake)

```
1. 描述
A wide cinematic train carriage interior at dusk, warm tungsten light washing
across empty seats, a single conductor figure silhouetted at the far end.

2. Composition
16:9 aspect ratio. Conductor placed at horizontal 75% (right third). Top 15%
of frame and bottom 15% of frame are void / near-black for safe-zone text
overlay. Center 70% holds the main scene.

3. Style
Cinematic 35mm lens. Tungsten warm coral (hex #FF6B47) bleeding into deep
navy (hex #0A1530). Atmospheric haze, soft focus on background. Mood:
contemplative, in-transit, beginning.

4. Do not include
No text, no logos, no watermarks, no station signs, no on-screen UI.
```

→ 出图后跑:`python ../../scripts/scrim_bake.py images/bg-01-cover.png 0.55`

---

## p2-img-side (R34 右侧竖图)

**比例**: 3:4 · **暗罩**: alpha 0.62(scrim_bake)

```
1. 描述
A vertical close-up of a hand placing a checkmark stamp on a stack of paper
documents, motion blur on the hand, ink fresh on the page.

2. Composition
3:4 aspect ratio (vertical). Hand + stamp positioned at vertical 60% (lower
center). Top 20% of frame is void / dim for breathing room. Left edge of
frame fades to void over 40pt to dissolve into white-text background.

3. Style
Documentary-grade macro photography. Warm tungsten desk lamp, hex #FFA552
key light. Background deep neutral charcoal (hex #1A1A1F). Mood: confident,
verifying, in-control.

4. Do not include
No faces, no text on the documents, no logos, no watermarks.
```

→ 出图后跑:`python ../../scripts/scrim_bake.py images/bg-02-validation.png 0.62`
