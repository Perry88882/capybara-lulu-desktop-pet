# running-right visual review

Accepted source: `decoded/running-right.png`, generated with built-in image_gen and repaired with built-in image_gen.

- Eight complete separate sprites, all facing screen-right.
- Every mouth is a closed dark curved smile; no visible teeth or white mouth patches in any of the eight native 192x208 extracted frames.
- Canonical smooth yellow 3D toy identity, broad orange muzzle, attached orange, and orange shorts retained.
- Compact and extended stride phases alternate visibly; attached arms move between forward and rearward poses, with mild body bob and leg bend.
- Minor visual warning: passing poses 2 and 3 (one-based) are similar; the row has a stylized compact-versus-extended cadence rather than eight exaggerated distinct poses.
- No detached effects, no clipping, no ground shadow.
- Bundled extraction used components, eight frames recovered.
- Bundled `inspect_frames.py --require-components`: ok true, zero errors and zero warnings.
- Some magenta edge spill remains prior to the parent's required single final-atlas despill pass.

First generation `rejected/running-right-white-mouth.png` was rejected because small white tooth patches remained. The full-strip edit removed those patches while preserving the generated poses. Exact prompts are in `prompts/used-running-right.md` and `prompts/used-running-right-repair.md`.
