# Ironfield class and skill design

This is the complete intended roster, designed together before skill implementation. Only **Ironvow / Turnwarden** is implemented. All other kits are design specifications, not selectable promises. Four base classes give eight identities without duplicating weapon delivery or decision patterns. Each specialization has exactly six primary active skills; basic attacks, consumables and interaction are not extra class skills.

## Shared design contract

Ranges are meters; times are seconds. Concept numbers outside Turnwarden are starting hypotheses, not balance commitments. A = calculated Attack; later supernatural kits may introduce a separate explicit stat consumer. Damage coefficients scale with equipment and level, so utility skills do not become obsolete. Rank data must improve bounded coefficients or durations without removing telegraphs, resource tradeoffs or counterplay. No passive skill tree is required.

Basic attacks remain free and reliable. Skill cooldowns start on accepted commitment, not on hit; a missed attack costs its cooldown. No unlimited action queue. Windups lock target/direction/ground point. A dead, departed or obstructed target produces a miss, never a retargeted surprise. Ground placement is an explicit second click; Escape cancels placement. Clicking UI never supplies a ground point. PvP notes are design constraints only: no PvP or network authority is implemented.

Conceptual statuses do not imply an implementation obligation now. Current effects are damage, timed guard, opening, slow, collision-aware displacement, limited healing and a persistent defensive area. Future kits add their own small effect handlers when built. Overlapping slows use the strongest, not multiplication; repeated same-source statuses refresh to the greater remaining duration and never accumulate infinite strength. Hard control, if later introduced, requires shared diminishing-return rules before PvP.

## Base class matrix

| Class | Fantasy and weapons | Stat tendencies and basics | Shared inheritance | Two divergent paths |
| --- | --- | --- | --- | --- |
| Ironvow | Road defenders who fight through pledged positions; swords and future two-handed blades | Attack/Defense/HP; deliberate cleaving three-hit sword sequence | Physical reach, committed strikes, readable steel telegraphs; useful basics without a resource bar | Turnwarden answers hostile commitments; Redmarch spends safe ground to maintain a moving front |
| Threadseer | Surveyors of the unseen lines joining people and places; focus rods, future throwing needles | Precision/skill scaling, modest HP; narrow measured ranged bolts | Explicit visible threads, breakable range/LOS links; few simultaneous anchors | Knotbinder manipulates relationships between enemies; Farlistener reads delayed echoes and chooses when to repeat them |
| Cinderhand | Keepers of the March's useful and dangerous fire; staves, hammers | HP/resource efficiency or spell power; close hammer taps or slow cinder shots | Visible heat on placed objects, finite fuel, deliberate setup | Hearthwright constructs a defensible working site; Ashreckoner converts personal exposure into brief destructive opportunity |
| Fenstrider | Hunters who know living ground; bows, short blades, living staves | Movement/precision or duration/utility; mobile single arrows or short blade cuts | Terrain awareness and readable natural tells, no invisible traps | Reedstalker wins through spacing and shot lanes; Briarchanter cultivates connected ground and relocates its benefits |

Ironvow's response windows differ from Cinderhand's preplanned emplacement. Threadseer changes relationships/time, not just damage colors. Fenstrider changes safe geography through movement or cultivation. Avoid borrowing another kit's core mechanism just to fill a missing conventional role.

## Ironvow: Turnwarden - implemented reference

The playable kit was reworked for mobile action combat. All skills cast with one press while running or following click travel. Skills take over basic attacks immediately; one replaceable follow-up can be buffered for 0.4 seconds. Selected enemies remain the aim target while strafing. No selection is required for an offensive cast. Flashstep uses movement direction and shortens its distance near obstructions; Phoenix Ring appears at the caster's feet.

| Key | Skill (persistent ID) | Windup / recovery / cooldown | Actual effect |
| --- | --- | --- | --- |
| 1 | Thunder Cleave (`riving_stroke`) | .07 / .16 / 3s | 130-degree lightning cleave, 4.2m, 1.8A. Open for 4s gives +25% basic damage. |
| 2 | Spirit Edge (`held_line`) | .03 / .08 / 12s | Green blade aura for 6s: +45% basic damage and +30% attack speed. Guard one frontal blow by 65% for 2s, earning Answer for 5s. |
| 3 | Flashstep (`heelturn`) | .01 / .16 / 6s | Collision-respecting 5m dash over .16s; 4s of +80% movement speed. Leaves a 1.5s slowing wake. |
| 4 | Bladestorm (`gate_sweep`) | .05 / .18 / 7s | 4m, 360-degree moving field. .9A opening hit, plus four .55A pulses over .8s; slows by 35%. Open adds .4A and is consumed; Answer adds 1.2m push on opening hit. |
| 5 | Phoenix Ring (`standard_of_ash`) | .06 / .18 / 10s | 3.8m fire field for 4s. .5A every .5s, 25% enemy slow, 25% damage reduction for caster inside. One field per caster. |
| 6 | Sunbreaker (`due_return`) | .10 / .22 / 8s | 110-degree radiant cleave, 4.5m, 3A, 1m push, .35A healing on a real hit. Answer adds .5A damage and .6A healing. |

A is final Attack, including equipment and Smith upgrades. Defense applies to each damaging hit. Walls and sanctuary still block damage; movement is physical rather than teleportation. Buffs, damaging areas, pending input and visual effects clear on death/load. Original skill IDs remain stable, and saved old cooldowns clamp to current durations. Other class/spec designs below remain future design notes, not promises of implemented mechanics.

## Ironvow: Redmarch - design only

**Identity: the front moves.** A short chalk front-line remains where the last committed basic finisher landed. Skills reposition or cross it; standing still does not build a passive damage meter. Inherits physical sword cleaves, but rewards territorial advance instead of waiting for a hostile blow.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Roadbreak - move the front | Direction, 4m narrow lane | .35 windup; 9s CD; .8A | Collision-bound advance; redraw front at destination | Low red edge ahead of boots. Push through a thin PvE rank; opponents sidestep the telegraphed lane. Repositions ground for Bannerless and Crosscut. |
| Crosscut - exploit crossing | Forward 100-degree arc, 3m | .3 cast; 6s CD; 1.0A | Crossing your front during windup widens arc to 180, not damage | Two intersecting slashes. Rewards moving through packs; avoid front side to deny widening. Basics supply the line, no extra resource. |
| Bannerless - hold what was gained | Self within 2m of front | .2 cast; 16s CD; scales shield with HP | 3s modest shield; front expires when shield breaks | Small clothless stake flash. Stabilizes a dangerous advance; concentrated damage breaks the foothold. Competes with retreating through Rearward. |
| Rearward Cut - trade front for escape | Direction behind front, 4m | .2 cast; 11s CD; .5A trailing arc | Retreat along ground; erase front, briefly slow crossed enemies | Blade dragged behind, no hidden i-frames. Withdraw from surround; pursue around the cut. Pays earned geography rather than stamina. |
| March Toll - punish pursuit | Place on own front, 4m segment | .45 cast; 14s CD; .9A once per enemy | Crossing deals damage and short slow; 4s duration | Upright low red stakes. Packs can be lured across; PvP can wait out or go around. Consumes front so it cannot also power Bannerless. |
| Last Pace - finish an advance | Selected enemy within 3m | .6 windup; 13s CD; 1.4A | If both stand beyond front, relocate line behind target; no CC | Raised blade and decisive downward step. Strong against a committed single target, avoidable by retreat. Reestablishes geography after Roadbreak without becoming a free gap closer. |

## Threadseer: Knotbinder - design only

**Identity: choose which two foes share a consequence.** At most two visible knot anchors, established by accurate basics; links break at 9m or LOS loss. Never duplicates full damage. Unlike a generic curse caster, the player thinks about pairs and separation.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Tie the Near - place deliberate anchor | Selected enemy, 8m | .35 cast; 4s CD; .4A | Mark 6s; replaces oldest of two anchors | Visible wrist-to-target thread. Starts setup without waiting for basics; break LOS to deny. Enables other five without making it compulsory every cycle. |
| Borrowed Weight - redistribute motion | Linked pair within 9m | .5 cast; 12s CD; no damage | Faster partner is slowed 30% for 3s while close to other | Heavy bead on link. Tames mixed PvE packs; separate to break. Combines with Loom Gate but offers no hard root. |
| Shared Cut - limited damage sharing | One anchored target, 8m | .4 cast; 8s CD; 1A plus .35A to partner | No extra recursive procs | Quick diagonal thread flash. Choose pair to pressure two enemies; partner can step behind cover. Never chains beyond two or replaces basic DPS. |
| Unpick - single-target release | Anchored target, 8m | .2 cast; 10s CD; .8A | Consume its knot to remove one removable self debuff | Thread reels back visibly. Emergency PvE cleansing; in PvP denies setup pressure but sacrifices link. Not a universal invulnerability cleanse. |
| Loom Gate - make the link a boundary | Existing linked segment, up to 9m | .65 cast; 18s CD; .5A per crossing, once per foe | 3s visible trip line, brief slow | Low violet thread fence. Controls a pack's approach; jump is not assumed, walk around endpoints. Strong placement, not automatic homing CC. |
| Sever Distance - conclude setup | Both anchors, 8m to nearer | .7 cast; 16s CD; .7A each, bonus for separation | Consumes both; no pulling through obstacles | Link brightens then snaps. Rewards keeping two dangerous foes separated; close together or break LOS to reduce result. Restarts setup instead of extending it indefinitely. |

## Threadseer: Farlistener - design only

**Identity: revisit one visible echo of a past action.** A basic hit records one four-second echo containing both caster origin and impact position; Second Sound can replace that record when its delayed impact resolves. Only one record exists. Skills act at present or echo; never duplicate a complete spell automatically. Inherits threads/LOS but reads time rather than enemy pairs.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Second Sound - delayed aim | Ground, 9m, 1.5m circle | .3 cast plus 1s delay; 6s CD; 1A | No CC | Pale expanding audible ring. Predict pack movement; leave the ring in PvP. Echo can preserve its location for Aftervoice. |
| Aftervoice - spend history | Existing echo within 9m, 2m circle | .4 cast; 11s CD; .8A | Consume echo, 25% slow 2s | Ghost collapses with thin ripple. Punishes returning to a lane; visible echo warns enemies. Gives basics a location-setting role. |
| Hush Step - reposition to memory | Own recorded movement echo, max 4m | .45 cast; 15s CD; no damage | Travel along validated path, consume echo; no teleport through walls | Dotted path before movement. Correct a PvE positioning mistake; enemy can pressure destination. Competes with Aftervoice's use of history. |
| Measure Silence - interrupt predictability | Selected enemy, 8m | .5 cast; 14s CD; .6A | Next committed enemy skill has a visible warning mark; eventual brief cast delay, no basic lockout | Small pulsing ear glyph. Future caster pressure, not blanket silence. Opponent can use basics or wait. Supports landing Second Sound. |
| Long Note - hold a threatened lane | Direction 10m, .8m width | .8 channel; 10s CD; 1.3A | Stationary caster; lost LOS stops damage | Thin line charges from near to far. Hits aligned packs; obvious side-step/flank counterplay. Echo provides alternative lane origin at cost of consuming it. |
| Keep the Last - decide what to retain | Self/echo, 9m | .15 cast; 20s CD; utility | Extend one echo by 4s, cannot extend it again | Ring around retained ghost fades in segments. Enables deliberate encounter pacing; opponents see the saved setup. No cooldown reset or repeated ultimate loop. |

## Cinderhand: Hearthwright - design only

**Identity: a small finite working site.** One kiln and one ember store; basics feed up to three fuel charges only near kiln. Fuel is spent to alter a shared site, not to increase every attack. Hammer/staff foundations remain sturdy and methodical.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Set Kiln - claim a work site | Ground within 6m, 2.5m area | .7 cast; 12s CD; no damage | Place destructible 8s kiln; replacing loses fuel | Small low stone bowl with legible perimeter. PvE staging; enemy can destroy or leave it. All other skills still have weaker off-site forms. |
| Stoke - pressure near home | Kiln or self, 2m burst | .4 cast; 6s CD; .7A, fuel extends radius | Brief burn, strongest refresh only | Low sparks not opaque flame. Deals with melee packs; step out before burst. Uses one fuel for reach rather than mandatory damage amplification. |
| Fired Plate - protect deliberately | Self or ally, 6m | .3 cast; 13s CD; shield scales HP | Spend fuel for shield duration, not shield stacking | Warm faceted shoulder plate. Respond to dangerous hits; wait it out or remove shield. Competes with using fuel offensively. |
| Rake Coals - shape approach | Direction from kiln, 5m strip | .5 cast; 10s CD; small A-scaled DoT | Slow burning strip for 3s | Low red coals show exact lane. Lure PvE pack, walk around in PvP. Relies on kiln position rather than instant targeted denial. |
| Lift Hearth - abandon a site | Self near kiln, 3m | .3 cast; 9s CD; no damage | Consume kiln for limited heal, proportional unspent fuel | Coals collapse into hands. Recover between pressures; enemy can deny by breaking kiln. Sacrifices offense/position for recovery. |
| Bellows Turn - redirect danger | Forward fan, 4m, 90 degrees | .6 cast; 16s CD; .6A | Push over time; kiln adds 1m reach, not stun | Cloth bellows and transparent heat lines. Peels pack from site; evade narrow telegraph. Creates time to Stoke without permanent control. |

## Cinderhand: Ashreckoner - design only

**Identity: exposed heat must be discharged.** Certain skills create one visible Heat burden that increases incoming damage briefly. A safe basic hit vents it; spend it instead for skill utility. No self-kill resource, no stacking burden without bound.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Bare Ember - accept exposure | Selected enemy 7m | .3 cast; 5s CD; 1A | Gain Heat for 4s, incoming +15% | Orange chest glow and small bolt. Reliable setup; pressure the exposed caster. Basic hit can safely vent instead of pursuing combo. |
| Ashfall Debt - risk a delayed area | Ground 7m, 2.8m circle | .7 cast + .8 delay; 13s CD; 1.3A | Heat expands radius but remains until vented | Sparse descending ash telegraph. Good on predictable packs; leave marked area in PvP. Not a guaranteed targeted burst. |
| Cold Palm - choose safety | Self | .2 cast; 10s CD; HP-scaled small shield | Consume Heat; no damage | Chest glow snaps to dull gray shell. Survive retaliation; opponent has already forced lost offensive utility. Shields refresh, do not add. |
| Cinder Wake - leave danger behind | Direction, 3m validated movement | .3 cast; 12s CD; .3A trailing burn | With Heat, trail lasts longer; no i-frames | Short ember footprint trail. Escape melee and punish pursuit; route around. Does not clear exposure, unlike Cold Palm. |
| Reckon - collect accumulated risk | Selected enemy, 6m | .6 cast; 16s CD; 1.2A | Consume Heat for single burst bonus bounded by damage received while exposed | Glowing palm closes visibly. Against strong PvE enemy; break LOS or withhold hits to deny bonus. Never encourages taking lethal damage. |
| Black Breath - redirect a pack | Forward cone 5m, 70 degrees | .5 cast; 14s CD; .7A | Short accuracy debuff on monsters; future PvP damage-output reduction, Heat extends duration | Thin gray gust with clear edges. Mitigates a dangerous pack; flank to avoid. Alternative to Reckon, not another explosion. |

## Fenstrider: Reedstalker - design only

**Identity: the drawn lane is strongest at its far end.** Basic arrows draw a visible short firing lane; moving sideways invalidates it. Skills choose holding aim versus abandoning it. No invisible traps or permanent ranged kiting lock.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Long Reed - commit to distance | Directional shot 12m, .5m width | .65 draw; 7s CD; 1A, bounded distance bonus | No CC | Bow silhouette and narrow tracer. Pick rear PvE target; sidestep windup in PvP. Uses lane, not homing distance damage. |
| Loose Quiver - split pressure | Three selected nearby foes within 8m | .4 cast; 10s CD; .5A each | No duplicate arrows on lone target | Clearly separate low arc trails. Controlled pack pull; cover denies individual arrows. Complements single-target basics. |
| Cut the Reed - abandon aim | Backward directional step 3m | .15 cast; 9s CD; no damage | Erase lane; collision travel | Broken green line and low hop. Create spacing; opponent can pursue immediately, no immunity. Trade aim for safety. |
| Nail the Hem - limit approach | Selected enemy 9m | .5 draw; 12s CD; .6A | 30% slow 2.5s only if beyond 4m | Arrow with visible vine tether. Helps strong enemies' approach; closing distance denies control. No root chain. |
| Watcher's Gap - prepare a passage | Ground 8m, 3m segment | .6 cast; 18s CD; .8A one crossing | Visible snare line triggers once, short slow | Reed stakes and thin cord. Route PvE pack; opponents can detour or consume it deliberately. Enhances spatial play instead of stealth ambush. |
| Narrow Horizon - finish a held shot | Existing lane, 12m | .9 draw; 17s CD; 1.6A | Pierces first two bodies, no control | Lane brightens progressively. Reward careful alignment; interrupt or step aside. Cannot maintain aim while escaping with Cut the Reed. |

## Fenstrider: Briarchanter - design only

**Identity: cultivate, then transplant.** At most two small visible growths; basic hits near one make it ripe. Skills consume or relocate ripeness, giving a living map without an army of pets. Inherits nature/ground reading but is slower and more positional than Reedstalker.

| Skill / purpose | Target / geometry | Timing / scaling | Status / movement | Presentation, use, counterplay, interaction |
| --- | --- | --- | --- | --- |
| Seed Word - choose future ground | Ground 7m, 1.8m growth | .45 cast; 5s CD; no initial damage | Place 7s seed, oldest replaced at cap two | Small bright sapling, outlined root radius. PvE setup; leave or destroy in PvP. Basics ripen it, skills do not auto-fill it. |
| Thorn Refrain - harvest offense | Growth within 7m, 2.5m pulse | .5 cast; 9s CD; .8A | Ripe growth adds brief slow; consume ripeness | Low outward thorn spokes. Hits packs without hiding them; windup and growth location warn enemies. Keeps plant for later basic cultivation. |
| Graft Step - move the investment | Growth to ground point within 4m | .35 cast; 10s CD; no damage | Relocate plant along validated ground, preserve ripeness | Visible root trail, never instant unseen trap. Adapt to a moving PvE pack; enemy sees destination. Competes with staying to ripen; no player teleport. |
| Shelter Leaf - spend defense | Self near growth, 3m | .25 cast; 14s CD; HP-scaled heal over 3s | Consume ripeness for stronger bounded healing; damage does not grant invulnerability | Two translucent small leaves, no opaque dome. Recovery in group combat; force player out of area to stop ticks. Costs offensive harvest. |
| Root Between - link cultivated ground | Segment between two growths, max 6m | .65 cast; 18s CD; no damage | 3s 35% slow corridor; consumes both ripeness states | Roots emerge along exact boundary. Herds packs; can walk around endpoints. Unlike Knotbinder links, endpoints are fixed destructible world objects. |
| Winter Prune - end a garden | One growth, 7m, 3m ring | .7 cast; 16s CD; 1.2A | Consume plant for pulse; ripe variant weakens enemy damage briefly | Branches fold inward then snap outward. Strong encounter conclusion; leave ring during cast. Ends investment instead of starting an infinite zone cycle. |

## Implementation boundaries and future checks

Turnwarden alone is selectable. Future class selection must validate class/spec pairing and weapon policy through data; documentation entries must never produce empty action bars. Skill rank slots are persisted at rank 1 now; changing maximum rank requires authored tuning and save validation. Combat opportunities, cast state, zones and cooldown time are not progression ranks.

Before another kit is implemented, compare its central decisions with this matrix, test real basic/skill alternation, and validate missing target, dead target, walls, sanctuary, UI, equipment swaps, load and death. New resource bars need stronger justification than visual flavor. No new ordinary enemies, multiplayer, PvP, giant skill tree, random affixes or unrelated world expansion belongs to this milestone.

## Reviewed identity guardrails (2026-09-20)

The complete roster review found all four classes, all eight specializations and all 48 skill concepts distinct enough to retain. Each six-skill kit contains setup, payoff, positioning, defense or utility, and a concluding choice rather than six variations of damage. Preserve the following differences during implementation; matching numbers or VFX are not sufficient evidence that two mechanics play differently.

| Specialization | Decision that must remain central | Implementation pressure to resist |
| --- | --- | --- |
| Turnwarden | Read one frontal attack, earn one short Answer, then choose Sweep or Return | Do not turn Answer into a stacking meter or require a fixed six-button sequence |
| Redmarch | Advance, cross or surrender a moving melee front created by committed basics | Do not make every skill require a front; Roadbreak and Last Pace must recover geography without a setup tax |
| Knotbinder | Choose two enemies whose relationship matters, then react to separation and LOS | Do not reduce knots to two ordinary marks or make Tie the Near mandatory before every useful action |
| Farlistener | Choose whether to act now or spend one visible record of a past place/action | Do not make an echo an automatic duplicate cast or a general cooldown-reset resource |
| Hearthwright | Build, fuel and eventually abandon one destructible working site | Do not turn fuel into constant upkeep or make every off-site skill nonfunctional |
| Ashreckoner | Accept one bounded vulnerability and decide whether to vent it safely or spend it | Do not reward lethal self-damage, allow unbounded Heat stacks or disguise an ordinary builder/spender bar as risk |
| Reedstalker | Hold a visible ranged firing lane for stronger spacing, or erase it to escape | Do not make the lane a hidden aim buff, homing projectile rule or permanent kiting lock |
| Briarchanter | Cultivate at most two visible world growths, then harvest, move or end them | Do not make ripeness passive upkeep or allow a growing army of persistent pets/zones |

Three pairs need an explicit playtest check because their diagrams can look similar. Redmarch owns a moving melee boundary while Reedstalker owns a stationary ranged shot lane. Knotbinder connects enemy-attached anchors while Briarchanter connects fixed, destructible world growths. Hearthwright maintains one fortified site with finite fuel while Briarchanter maintains two relocatable living nodes with ripeness. If either member of a pair can be implemented by renaming the other's state and effects, its design identity has been lost.

Turnwarden is a strong reference for commitment, predictable rejection, readable geometry, equipment/stat scaling, basic-skill alternation, one short opportunity with two payoffs, and effects that remain authoritative outside the UI. It is deliberately not the universal skill template. It proves immediate melee, self guard, physical movement and finite areas; it does not prove projectiles, channels, delayed resolution, allies, shields, damage-over-time, interrupts, destructible objects, multiple anchors, damage types, boss control rules or PvP authority.

Before implementing a second specialization, remove the single-reference assumptions called out in `PROJECT.md` and add only the abstractions required by that chosen kit. Do not force all future mechanics into the current target-shape enum, `CombatStatuses` ID dictionary or Turnwarden-specific effect fields. Every future kit review must still answer: what useful choice can be made without setup, what makes basics useful, which effects compete for the central opportunity, how an enemy reads and counters it, and what prevents an optimal rigid rotation.
