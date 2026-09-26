# Oathkeeper sword: visual iteration record

Each numbered stage was edited in live Blender through MCP, then rendered. The
agent opened actual returned PNGs **before** choosing the next change. The
connection probe first established that image delivery worked with Blender's
startup cube. That probe is not another authored asset.

| Stage | Observed in rendered images | Subsequent action |
| --- | --- | --- |
| 01 rough | Visible gap above rectangular guard; flat slab blade; excessively long plain grip; cylindrical pommel. Readable as a sword, but generic assembled primitives. | Close joint; rebuild blade cross-section and taper; shorten grip; replace guard/pommel silhouette. |
| 02 structure | Broad cutting bevels and fuller give the blade volume. Swept guard improves silhouette, but reads as one thick gold cutout. Bare grip and excessively dark fuller dominate. | Layer steel/brass guard, wrap the grip, lower fuller contrast, introduce a restrained red crest and matching framed pommel. |
| 03 craft | Hilt hierarchy and rear silhouette improved. Close-up shows pale plastic-looking leather and hard shading around metal joins. | Darken and texture leather; pack exportable PBR textures; refine normals; stop fuller before point. |
| 04 finish | Sides reveal sensible blade thickness and assembled guard depth. Grip improves, but repeated metal striping looks manufactured/procedural. Fuller ends with an abrupt rectangular cutoff. | Remove periodic grain, taper the fuller to a point, retain subtle surface variation; set grip-centered attachment origin. |
| 05 final | Cleaner blade face and fuller termination, readable steel/brass boundary, wrapped darker grip, consistent front/back crest. Further small surface decoration offers little at distance. | Stop decorative iteration; validate selected export and inspect Godot output. |

The first two revisions changed major forms and construction, not just color.
The final correction was deliberately smaller: the major silhouette problems
were resolved, and the next proposed details would disappear in the distance view.
This is the observed diminishing-return point for this particular test.

Images are retained in [the gallery](output/gallery.html), with original full-size
PNG links. `03_hilt_closeup` is an intermediate diagnostic, not the final material
appearance. The final set includes front/back, both sides, both three-quarter
views, top and a new hilt close-up; all were opened for visual inspection.

The Godot close and 8 m captures were also opened and inspected. The game renderer
is darker than the Cycles studio. The blade and guard silhouette survive at about
80–90 pixels tall; the red crest and leather wrapping are minor accents. The
distance fixture establishes isolated readability, not visibility against all
game backgrounds, animation quality, or an equipped-character fit.

Technical review found one real export defect: selected objects from the preserved
startup scene entered a second GLB scene. Godot's default-scene view did not expose
this. The GLB structure test caught it; export now requires both named selection
and active scene. The final file has exactly one mesh and excludes the startup cube.

Final validation found no missing materials, nonmanifold edges, degenerate faces,
loose vertices, inconsistent winding, negative signed volume, coincident duplicate
objects or unapplied transforms in the sword selection. These checks support
export readiness; they do not establish visual quality by themselves.

Recommendation: use the workflow for further **individually reviewed static
assets**, not unattended mass production. Next production proof should be an
equipped weapon in motion, then a separately scoped skinned/animated asset. This
task intentionally produced neither a new asset library nor changes to the game.
