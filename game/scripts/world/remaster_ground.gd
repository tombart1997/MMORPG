class_name RemasterGround
extends RefCounted
## Vertex weights are baked once. Fragment shading never loops over camps/roads.
static var spur_cells: Dictionary = {}
static var houses: Array[Vector2] = [Vector2(-6,9),Vector2(6,11),Vector2(-5,23),Vector2(-20,18),Vector2(20,18),Vector2(-20,32),Vector2(20,32),Vector2(-12,46),Vector2(12,46),Vector2(-27,45),Vector2(27,45)]

static func distance_segment(p: Vector2,a: Vector2,b: Vector2) -> float:
	return p.distance_to(a+(b-a)*clampf((p-a).dot(b-a)/(b-a).length_squared(),0,1))

static func weights(x: float,z: float) -> Color:
	if spur_cells.is_empty():
		for camp in FirstMapContent.POINTS:
			var start := Vector2(camp.x,camp.z)
			var nearest := Vector2.ZERO
			var best := INF
			for route in [ZoneTerrain.ROAD,ZoneTerrain.OUTER_ROAD]:
				for i in range(1,route.size()):
					var a := Vector2(route[i-1].x,route[i-1].z)
					var b := Vector2(route[i].x,route[i].z)
					var end := a+(b-a)*clampf((start-a).dot(b-a)/(b-a).length_squared(),0,1)
					if start.distance_to(end)<best: best=start.distance_to(end); nearest=end
			if best<.2: continue
			for cx in range(floori((minf(start.x,nearest.x)-4)/16),floori((maxf(start.x,nearest.x)+4)/16)+1):
				for cz in range(floori((minf(start.y,nearest.y)-4)/16),floori((maxf(start.y,nearest.y)+4)/16)+1):
					var key := Vector2i(cx,cz)
					if not spur_cells.has(key): spur_cells[key]=[]
					spur_cells[key].append([start,nearest])
	var p := Vector2(x,z)
	var road := ZoneTerrain.path_distance(Vector3(x,0,z))
	for spur in spur_cells.get(Vector2i(floori(x/16),floori(z/16)),[]):
		road = minf(road,distance_segment(p,spur[0],spur[1])+1.0)
	if z > 4:
		for line in [[Vector2(0,5),Vector2(0,55)],[Vector2(-22,22),Vector2(22,22)],[Vector2(-22,36),Vector2(22,36)],[Vector2(-29,48),Vector2(29,48)],[Vector2(-8,9),Vector2(8,9)]]:
			road = minf(road,distance_segment(p,line[0],line[1]))
	var soil := 0.0
	for house in houses:
		if absf(x-house.x) < 6 and absf(z-house.y) < 6: soil = maxf(soil,1.0-smoothstep(2.5,5.5,p.distance_to(house)))
	for camp in ZoneTerrain.nearby_camps(x,z):
		var distance := p.distance_to(Vector2(camp.x,camp.z))
		soil = maxf(soil,(1-smoothstep(2.0,7.5,distance))*.9)
	return Color(clampf(road/12.0,0,1),soil,clampf(-z/260.0,0,1),1)
