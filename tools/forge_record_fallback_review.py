"""Record the completed human/model visual judgments, separately from checks.

These observations were made by opening the saved Godot sheets, all sampled
clips and staged gameplay screenshots. Running this script does not perform
or simulate another visual review.
"""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];docs=ROOT/'docs/asset_review'
rows=json.loads((docs/'fallback_inventory.json').read_text())['assets']
out={}
for row in rows:
    key=row['key'];family=row['family'];category=row['category']
    notes='Retained previous mesh has intact separated parts and stable sampled animation, replacing the documented deforming generated candidate.'
    limitation='Temporary previous visual; stylized forms and material language differ from the current concept. Artist-authored anatomy, UV and skin work remains.'
    if family=='wolf':
        notes='The already reviewed meadow wolf keeps a forward-facing head and four distinct moving limbs. Running, attack, hit, idle and death samples remain intact; unlike the rejected red/grey meshes there are no large limb sheets.'
        limitation='Temporary shared meadow-wolf anatomy. Species coat tint is subtle; red/grey concept-specific face, fur and color work remains.'
    elif family=='boar':
        notes='The already reviewed blacktusk retains a recognizable boar body and stable five-clip samples. A tiny underside irregularity remains acceptable at 11 m; severe lower-leg fans in the rejected variants are absent.'
        limitation='Temporary shared blacktusk anatomy; unique ironhide armor, bristles, eyes and variant materials still require artist work.'
    elif family=='spider':
        notes='Saved spider has eight separated rigid limb chains and a clear abdomen, intact in all five sampled clips. No generated leg/abdomen fans remain.'
        limitation='Temporary stylized spider; unique venom, copper, widow, silk and glass markings are missing.'
    elif family=='stonekin':
        notes='Saved stone guardian keeps independent hands and feet through attack and run samples. Rocky hide is intentional; broad cartoon proportions differ from the concept but movement remains readable.'
        limitation='Temporary common guardian body; tier-specific carved rock silhouette and concept details remain.'
    elif family=='mossling':
        notes='Saved briarling has a full separated branch body. All five sampled clips retain feet and hands without generated stretching sheets.'
        limitation='Temporary briarling template; young/grown/ironback need unique bark, foliage and matched body proportions.'
    elif family=='bandit' or key=='hero_ironvow':
        notes='Saved modular humanoid has a full side silhouette, defined face, separated cloth and stable samples of all 16 clips. Actual game composition retains separate armor and weapon sockets. Front/side/three-quarter rider and mounted views were opened; ankle error 6.7 mm, rein error 0.7 mm.'
        limitation='Temporary stylized armored warden, which differs from the neutral bandit/hero concept and has rigid decorative cloth. New neutral references and authored skinning remain.'
    if '/npcs/' in row['target'] or key in ('npc_keeper','npc_smith','npc_stablemaster'):
        notes='Actual resident module selection and clothing paint were rendered, opened and inspected in three idle/interact clips. Full body thickness, complete hands and separated sleeves replace the flat generated torso. Settlement navigation and service composition pass.'
        limitation='Temporary selected townfolk kit with role-specific colors/accessories; each resident still needs a faithful neutral concept and authored final model.'
    if key=='derived_characters_townfolk_kit':
        notes='All kit modules remain retained for selection. The raw kit shows overlapping alternatives, so acceptance is based on the ten opened actual resident selections and all three sampled clips, plus the live nine-service settlement.'
        limitation='Temporary modular kit; the standalone unselected kit is not a single resident. Final concept-specific bodies remain required.'
    if key in ('derived_characters_traveler','derived_characters_turnwarden_v2'):
        notes='Previous humanoid keeps readable separated sleeves, arms and cloth in all 12 sampled clips. The large generated hand/cloth deformation sheets are absent.'
        limitation='Temporary previous humanoid style, with simpler rigid clothing and broad armor. Final reference fidelity needs authored local modeling and skinning.'
    if key=='horse_bay':
        notes='Previous bay horse preserves four separate leg/hoof chains in idle/walk/trot/canter sheets. Opened exported front, side and three-quarter horse/rider/mounted views show a coherent neck, body, saddle and mounted pose. All 23 bones and four gait names survive. Only 28 zero-area index triangles were removed; all other binary data remains identical.'
        limitation='Retained previous bay horse is safer than the rejected generated limbs. This is a working fallback, not a newly completed anatomy reconstruction; finer mane/tail and coat fidelity remain.'
    if category=='foliage' or any(s in key for s in ('tree','shrub','sedge','grass')):
        notes='Saved foliage restores individual leaves/blades and visible gaps between fronds/branches, with an unchanged ground pivot. Opened front/side/back/three-quarter, clay, wire and 11 m views show no fused generated canopy lumps.'
        limitation='Temporary previous foliage style. Leaf cards and broad tree trunks differ from the concept; canopy proximity fade addresses gameplay camera clearance separately.'
    if key in ('derived_characters_jade_ironback_mantle','derived_characters_traveler_guard'):
        notes='The saved overlay contains intact independent armor pieces. Cropped standalone framing is intentional; actual worn front and rear game-composition screenshots were opened, confirming chest/shoulder fit on the retained full humanoid.'
        limitation='Temporary previous modular overlay; elaborate concept cloth and custom arm shaping remain. Armor must always be reviewed worn.'
    out[key]={'decision':'accept_temporary_fallback','original_status':row['status'],'views_opened':True,'animations_opened':True,
        'source_sha256':row['fallback_sha256'],'evidence_key':row['evidence_key'],'confidence':'high for sampled runtime safety; concept limitations explicit','notes':notes,'limitations':limitation}
(docs/'fallback_judgments.json').write_text(json.dumps({'reviewer':'Codex: actual opened saved renders and mesh evidence','scope':'Four rest views, textured/clay/wire/detail/gameplay, four samples per clip; actual NPC appearance and worn armor; not a proof of continuous deformation quality. Shared identical source hashes reuse evidence explicitly.','assets':out},indent=2)+'\n')
print('Recorded',len(out),'explicit temporary-fallback judgments.')
