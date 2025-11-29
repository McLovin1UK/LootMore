AI Helper For Games

📁 test_assets/nsfw/ — Synthetic Safety Test Images

The test_assets/nsfw/ directory contains fully synthetic, non-explicit test images used to validate LootMore’s safety, filtering, and fallback behaviour.
These assets are intentionally simple, generated procedurally, and do not contain any real NSFW content.

They are used to test:

Image classification & red-flag detection

Fallback behaviour when sensitive content is flagged

UI overlays that activate during unsafe states

Pipeline stability when processing edge-case textures

End-to-end callout suppression logic

Included files
File	Purpose
test1_orange_skin_patch.png	Uniform peach-tone texture used to test false-positive skin detection behaviour.
test2_suggestive_silhouette_block.png	Abstract silhouette block used to test classifier sensitivity to shapes and outlines.
test3_red_flag_overlay.png	Half-red synthetic warning-style tile with blurred highlight area, used to test UI red-flag overlays.
test*.b64 files	Original base64 sources for reproducibility.
make_nsfw_test_assets.py	Script used to regenerate all assets deterministically.
Why these assets exist

LootMore requires robust handling of sensitive imagery in future gameplay, creator-tools, and public-facing features. These placeholder images allow testing of:

Sensitivity thresholds

Rate limiting

Redaction modes

Emergency fallback responses

Logging & audit trails

AI inference consistency

They simulate potentially problematic visual structures without ever using real NSFW content.

Regenerating the assets

To rebuild the PNGs from scratch:

py test_assets/nsfw/make_nsfw_test_assets.py


This ensures deterministic, reproducible assets for QA and future automation pipelines.


