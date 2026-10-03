class_name FirstMapContent
extends RefCounted

const POINTS: Array[Vector3] = [
	# ------------------------------------------------------------------
	# NORTH / STARTING AREA
	# ------------------------------------------------------------------
	Vector3(-25, 0, -18),
	Vector3(-20, 0, -23),
	Vector3(-31, 0, -25),
	Vector3(-17, 0, -31),
	Vector3(-36, 0, -15),

	Vector3(-55, 0, -22),
	Vector3(-49, 0, -17),
	Vector3(-62, 0, -27),
	Vector3(-52, 0, -31),
	Vector3(-67, 0, -18),

	Vector3(-88, 0, -22),
	Vector3(-81, 0, -17),
	Vector3(-94, 0, -27),
	Vector3(-84, 0, -32),
	Vector3(-97, 0, -16),

	Vector3(55, 0, -22),
	Vector3(49, 0, -17),
	Vector3(62, 0, -27),
	Vector3(52, 0, -32),
	Vector3(68, 0, -18),

	Vector3(88, 0, -22),
	Vector3(81, 0, -17),
	Vector3(95, 0, -27),
	Vector3(84, 0, -33),
	Vector3(98, 0, -16),

	# ------------------------------------------------------------------
	# UPPER WILDS
	# ------------------------------------------------------------------
	Vector3(-88, 0, -66),
	Vector3(-81, 0, -61),
	Vector3(-95, 0, -70),
	Vector3(-85, 0, -76),
	Vector3(-99, 0, -59),

	Vector3(-57, 0, -66),
	Vector3(-50, 0, -61),
	Vector3(-64, 0, -71),
	Vector3(-54, 0, -77),
	Vector3(-69, 0, -58),

	Vector3(55, 0, -66),
	Vector3(48, 0, -61),
	Vector3(62, 0, -71),
	Vector3(52, 0, -77),
	Vector3(69, 0, -58),

	Vector3(88, 0, -66),
	Vector3(81, 0, -61),
	Vector3(95, 0, -71),
	Vector3(85, 0, -77),
	Vector3(99, 0, -58),

	# ------------------------------------------------------------------
	# MID MAP
	# ------------------------------------------------------------------
	Vector3(-87, 0, -104),
	Vector3(-80, 0, -99),
	Vector3(-94, 0, -109),
	Vector3(-84, 0, -115),
	Vector3(-99, 0, -96),

	Vector3(-48, 0, -108),
	Vector3(-41, 0, -103),
	Vector3(-55, 0, -113),
	Vector3(-45, 0, -119),
	Vector3(-60, 0, -100),

	Vector3(-5, 0, -112),
	Vector3(2, 0, -107),
	Vector3(-12, 0, -117),
	Vector3(-2, 0, -123),
	Vector3(9, 0, -104),

	Vector3(38, 0, -110),
	Vector3(31, 0, -105),
	Vector3(45, 0, -115),
	Vector3(35, 0, -121),
	Vector3(51, 0, -102),

	Vector3(85, 0, -110),
	Vector3(78, 0, -105),
	Vector3(92, 0, -115),
	Vector3(82, 0, -121),
	Vector3(99, 0, -102),

	# ------------------------------------------------------------------
	# DEEPER MID MAP
	# ------------------------------------------------------------------
	Vector3(-87, 0, -153),
	Vector3(-80, 0, -148),
	Vector3(-94, 0, -158),
	Vector3(-84, 0, -164),
	Vector3(-99, 0, -145),

	Vector3(-45, 0, -154),
	Vector3(-38, 0, -149),
	Vector3(-52, 0, -159),
	Vector3(-42, 0, -165),
	Vector3(-57, 0, -146),

	Vector3(0, 0, -155),
	Vector3(7, 0, -150),
	Vector3(-7, 0, -160),
	Vector3(3, 0, -166),
	Vector3(-12, 0, -147),

	Vector3(44, 0, -155),
	Vector3(37, 0, -150),
	Vector3(51, 0, -160),
	Vector3(41, 0, -166),
	Vector3(56, 0, -147),

	Vector3(87, 0, -153),
	Vector3(80, 0, -148),
	Vector3(94, 0, -158),
	Vector3(84, 0, -164),
	Vector3(99, 0, -145),

	# ------------------------------------------------------------------
	# SOUTHERN WILDS
	# ------------------------------------------------------------------
	Vector3(-87, 0, -197),
	Vector3(-80, 0, -192),
	Vector3(-94, 0, -202),
	Vector3(-84, 0, -208),
	Vector3(-99, 0, -189),

	Vector3(-44, 0, -199),
	Vector3(-37, 0, -194),
	Vector3(-51, 0, -204),
	Vector3(-41, 0, -210),
	Vector3(-56, 0, -191),

	Vector3(0, 0, -199),
	Vector3(7, 0, -194),
	Vector3(-7, 0, -204),
	Vector3(3, 0, -210),
	Vector3(-12, 0, -191),

	Vector3(45, 0, -198),
	Vector3(38, 0, -193),
	Vector3(52, 0, -203),
	Vector3(42, 0, -209),
	Vector3(57, 0, -190),

	Vector3(88, 0, -198),
	Vector3(81, 0, -193),
	Vector3(95, 0, -203),
	Vector3(85, 0, -209),
	Vector3(99, 0, -190),

	# ------------------------------------------------------------------
	# ENDGAME / FAR SOUTH
	# ------------------------------------------------------------------
	Vector3(-87, 0, -244),
	Vector3(-80, 0, -239),
	Vector3(-94, 0, -249),
	Vector3(-84, 0, -255),
	Vector3(-99, 0, -236),

	Vector3(-44, 0, -244),
	Vector3(-37, 0, -239),
	Vector3(-51, 0, -249),
	Vector3(-41, 0, -255),
	Vector3(-56, 0, -236),

	Vector3(0, 0, -246),
	Vector3(7, 0, -241),
	Vector3(-7, 0, -251),
	Vector3(3, 0, -257),
	Vector3(-12, 0, -238),

	Vector3(43, 0, -244),
	Vector3(36, 0, -239),
	Vector3(50, 0, -249),
	Vector3(40, 0, -255),
	Vector3(55, 0, -236),

	Vector3(87, 0, -253),
	Vector3(80, 0, -248),
	Vector3(94, 0, -258),
	Vector3(84, 0, -264),
	Vector3(99, 0, -245),

	Vector3(-87, 0, -279),
	Vector3(-80, 0, -274),
	Vector3(-94, 0, -284),
	Vector3(-84, 0, -290),
	Vector3(-99, 0, -271)
]


const IDS: Array[String] = [
	# Starting area
	"meadow_wolf",
	"meadow_wolf",
	"young_mosslings",
	"young_mosslings",
	"meadow_wolf",

	"blue_wolf",
	"blue_wolf",
	"meadow_wolf",
	"young_mosslings",
	"blue_wolf",

	"red_wolf",
	"red_wolf",
	"blue_wolf",
	"red_wolf",
	"young_mosslings",

	"bristle_boar",
	"bristle_boar",
	"young_mosslings",
	"meadow_wolf",
	"bristle_boar",

	"reed_spider",
	"reed_spider",
	"bristle_boar",
	"reed_spider",
	"young_mosslings",

	# Upper wilds
	"grey_wolf",
	"grey_wolf",
	"blue_wolf",
	"grey_wolf",
	"meadow_wolf",

	"mire_boar",
	"mire_boar",
	"bristle_boar",
	"mire_boar",
	"grey_wolf",

	"copper_spider",
	"copper_spider",
	"reed_spider",
	"copper_spider",
	"mire_boar",

	"road_bandit",
	"road_bandit",
	"grey_wolf",
	"road_bandit",
	"copper_spider",

	# Mid map
	"moonfang",
	"thicket_wolf",
	"moonfang",
	"grey_wolf",
	"thicket_wolf",

	"thicket_wolf",
	"thicket_wolf",
	"blacktusk",
	"grey_wolf",
	"blacktusk",

	"blacktusk",
	"mire_boar",
	"blacktusk",
	"venom_spider",
	"mire_boar",

	"venom_spider",
	"venom_spider",
	"copper_spider",
	"venom_spider",
	"hollow_raider",

	"hollow_raider",
	"hollow_raider",
	"road_bandit",
	"hollow_raider",
	"venom_spider",

	# Deeper mid map
	"cinder_wisp",
	"cinder_wisp",
	"hollow_raider",
	"cinder_wisp",
	"venom_spider",

	"slate_guardian",
	"slate_guardian",
	"cinder_wisp",
	"slate_guardian",
	"hollow_raider",

	"frost_wolf",
	"frost_wolf",
	"moonfang",
	"frost_wolf",
	"slate_guardian",

	"ironhide_boar",
	"ironhide_boar",
	"blacktusk",
	"ironhide_boar",
	"frost_wolf",

	"silk_matron",
	"widow_spider",
	"silk_matron",
	"venom_spider",
	"ironhide_boar",

	# Southern wilds
	"ash_bandit",
	"ash_bandit",
	"hollow_raider",
	"ash_bandit",
	"frost_wolf",

	"grave_wisp",
	"grave_wisp",
	"cinder_wisp",
	"grave_wisp",
	"ash_bandit",

	"cairn_sentinel",
	"cairn_sentinel",
	"slate_guardian",
	"cairn_sentinel",
	"grave_wisp",

	"bloodfang",
	"bloodfang",
	"frost_wolf",
	"bloodfang",
	"cairn_sentinel",

	"dusk_stalker",
	"dusk_stalker",
	"ash_bandit",
	"dusk_stalker",
	"bloodfang",

	# Endgame / far south
	"obsidian_boar",
	"obsidian_boar",
	"ironhide_boar",
	"obsidian_boar",
	"dusk_stalker",

	"widow_spider",
	"widow_spider",
	"silk_matron",
	"widow_spider",
	"obsidian_boar",

	"exile_captain",
	"ash_bandit",
	"exile_captain",
	"dusk_stalker",
	"exile_captain",

	"storm_wisp",
	"storm_wisp",
	"grave_wisp",
	"storm_wisp",
	"exile_captain",

	"cairn_colossus",
	"cairn_sentinel",
	"cairn_colossus",
	"storm_wisp",
	"cairn_colossus",

	"ancient_warden",
	"cairn_sentinel",
	"storm_wisp",
	"cairn_colossus",
	"ancient_warden"
]