class_name RuntimeCosts
extends RefCounted
## Opt-in diagnostic timings; disabled during gameplay and final FPS measurements.
static var enabled := false
static var microseconds: Dictionary = {}
static var long_spans: Array[Dictionary] = []

static func record(metric: StringName, started: int) -> void:
	var elapsed := Time.get_ticks_usec() - started
	microseconds[metric] = int(microseconds.get(metric, 0)) + elapsed
	if elapsed > 5000 and long_spans.size() < 100:
		long_spans.append({"metric":String(metric),"ms":elapsed/1000.0,"physics_frame":Engine.get_physics_frames()})
	Engine.set_meta("profile_costs", microseconds)
