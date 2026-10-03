class_name MapCanvas
extends Control
var player: ActorBody
var full: bool = false
var refresh_time: float = 0
var zoom: float = 3.0

func _ready() -> void:
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_STOP
	tooltip_text = "M — Briarwood map\nN up · S Smith · $ Merchant · ! Quest · ? Return\nLandmarks appear when explored. No enemy or loot tracking."

func _process(delta: float) -> void:
	refresh_time += delta
	if visible and refresh_time >= .05: refresh_time = 0; queue_redraw()

func point(world: Vector3) -> Vector2:
	var bounds := player.map_state.region.bounds
	var scale := minf((size.x-40)/bounds.size.x, (size.y-40)/bounds.size.y) if full else zoom
	var center := bounds.get_center() if full else Vector2(player.global_position.x,player.global_position.z)
	return size*.5 + (Vector2(world.x,world.z)-center)*scale

func _draw() -> void:
	if player == null or player.map_state == null: return
	if full:
		draw_style_box(PaintedTheme.frame(),Rect2(Vector2.ZERO,size))
	else:
		draw_circle(size*.5,size.x*.5-2,Color("171611"))
		for radius in [size.x*.5-3,size.x*.5-6,size.x*.5-9]:
			draw_arc(size*.5,radius,0,TAU,96,Color("795635"),2,true)
		draw_arc(size*.5,size.x*.5-4,PI,TAU,48,Color("b0955d"),1,true)
	for road in [player.map_state.region.roads, player.map_state.region.outer_roads]:
		for i in range(1,road.size()):
			_road(point(Vector3(road[i-1].x,0,road[i-1].y)),point(Vector3(road[i].x,0,road[i].y)))
	var font := ThemeDB.fallback_font
	var service_index := 0
	var occupied: Array[Rect2] = []
	for marker in player.map_state.markers():
		var pos := point(marker.position)
		if not Rect2(Vector2(8,8),size-Vector2(16,16)).has_point(pos): continue
		if not full and pos.distance_to(size*.5) > size.x*.5-21: continue
		draw_circle(pos,7,Color("202a23"))
		var glyph: String = str(service_index+1) if full and marker.get("service", false) else marker.glyph
		draw_string(font,pos+Vector2(-4,5),glyph,HORIZONTAL_ALIGNMENT_LEFT,-1,14,marker.color)
		if full:
			if marker.has("service") and marker.service:
				service_index += 1
				var key_pos := Vector2(12, 46 + service_index * 22)
				draw_string(font,key_pos, "%d  %s" % [service_index, marker.label],HORIZONTAL_ALIGNMENT_LEFT,205,12,marker.color)
				continue
			var label_pos := pos + Vector2(11,4)
			label_pos.x = clampf(label_pos.x, 215, size.x - 160)
			var rect := Rect2(label_pos-Vector2(0,12),Vector2(155,18))
			for previous in occupied:
				if previous.intersects(rect):
					label_pos.y = previous.end.y + 13
					rect.position.y = label_pos.y - 12
			occupied.append(rect)
			draw_line(pos,label_pos-Vector2(3,4),Color(.5,.5,.35,.5),1,true)
			draw_string(font,label_pos,marker.label,HORIZONTAL_ALIGNMENT_LEFT,155,12,marker.color)
	var player_point := point(player.global_position)
	var direction := Vector2(-sin(player.rotation.y),-cos(player.rotation.y))
	var side := Vector2(-direction.y,direction.x)
	draw_colored_polygon(PackedVector2Array([player_point+direction*9,player_point-direction*6+side*5,player_point-direction*3,player_point-direction*6-side*5]),Color("f4edc4"))
	draw_string(font,Vector2(size.x*.5-5,17),"N",HORIZONTAL_ALIGNMENT_LEFT,-1,13,Color("ddcf98"))
	if not full: draw_string(font,Vector2(size.x*.5-18,size.y-14),"M  Map",HORIZONTAL_ALIGNMENT_LEFT,-1,12,Color("ddcf98"))

func _gui_input(event: InputEvent) -> void:
	if not full and event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		player.ui_session.open_panel(player.ui_session.world_map)
		accept_event()

func _road(start: Vector2, finish: Vector2) -> void:
	if full:
		draw_line(start,finish,Color("6a5a3b"),3,true)
		return
	# Clip road segments analytically to the circular map interior.
	var delta := finish-start
	var relative := start-size*.5
	var a := delta.length_squared()
	if a < .001: return
	var b := 2*relative.dot(delta)
	var c := relative.length_squared()-pow(size.x*.5-12,2)
	var discriminant := b*b-4*a*c
	if discriminant < 0: return
	var near := maxf(0,(-b-sqrt(discriminant))/(2*a))
	var far := minf(1,(-b+sqrt(discriminant))/(2*a))
	if near <= far: draw_line(start+delta*near,start+delta*far,Color("6a5a3b"),2,true)
