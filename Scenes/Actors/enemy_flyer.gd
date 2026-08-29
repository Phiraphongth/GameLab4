extends Enemy

# --------------------------------------------------------------------------- #
#  ศัตรูบิน (Flyer)  ―  ใช้กับฉาก monster_bat.tscn
#
#  ต่างจาก Enemy ปกติตรงที่ "ไม่สนแรงโน้มถ่วง" และไม่ต้องยืนบนพื้น
#    PATROL : ลอยไปทางซ้าย/ขวา พร้อมส่ายขึ้นลงเป็นคลื่นไซน์รอบ ๆ ความสูงเริ่มต้น
#    CHASE  : ถ้าผู้เล่นเข้ามาใกล้กว่า detect_radius จะบินตรงเข้าไล่
#  ถ้าชนกำแพงจะกลับทิศเหมือนศัตรูเดินดิน  โดนกระสุนแล้วตายด้วย death_tween()
#  ของคลาสแม่เหมือนเดิม  ปรับค่าทุกตัวได้จาก Inspector
# --------------------------------------------------------------------------- #

@export_category("Flyer Properties")
@export var wave_amplitude : float = 36.0   # ระยะส่ายขึ้นลง (พิกเซล)
@export var wave_speed : float = 1.2        # จำนวนรอบการส่ายต่อวินาที
@export var patrol_range : float = 150.0    # บินออกจากจุดวางได้ไกลสุดกี่พิกเซล (0 = ไม่จำกัด)
@export var detect_radius : float = 280.0   # ระยะที่เริ่มมองเห็นผู้เล่น
@export var chase_speed : float = 190.0     # ความเร็วตอนไล่ผู้เล่น
@export var chase_leash : float = 180.0     # ไล่ออกนอกเขตลาดตระเวนได้ไกลสุดเท่าไร
@export var return_force : float = 5.0      # แรงดึงกลับเข้าความสูงเดิม

var home_x : float = 0.0        # จุดกึ่งกลางของเส้นทางลาดตระเวน
var home_y : float = 0.0        # ความสูงที่ใช้ลอยตามปกติ
var wave_time : float = 0.0
var chasing : bool = false


func _ready() -> void:
	super._ready()
	home_x = global_position.x
	home_y = global_position.y
	# สุ่มเฟสเริ่มต้น เพื่อไม่ให้ค้างคาวทุกตัวส่ายพร้อมกันเป๊ะ ๆ
	wave_time = randf() * TAU
	$Sprite/AnimateSprite.play()


# เขียนทับ _physics_process ของ Enemy ทั้งหมด (ไม่เรียก super)
# เพราะตัวนี้บินได้ จึงไม่ใช้แรงโน้มถ่วงและไม่เช็ค is_on_floor()
func _physics_process(delta: float) -> void:
	if not alive:
		velocity = Vector2.ZERO
		move_and_slide()
		return

	wave_time += delta

	# ถ้าไล่ออกมาไกลจากเขตของตัวเองเกิน chase_leash ให้เลิกไล่แล้วบินกลับ
	# ไม่งั้นค้างคาวตัวเดียวจะตามผู้เล่นข้ามด่านไปได้เรื่อย ๆ
	var target := find_player()
	var leash_limit := patrol_range + chase_leash
	var out_of_leash := patrol_range > 0.0 and absf(global_position.x - home_x) > leash_limit
	var in_sight := target != null and global_position.distance_to(target.global_position) < detect_radius
	chasing = in_sight and not out_of_leash

	if chasing:
		# บินตรงเข้าหาผู้เล่น
		var to_player := (target.global_position - global_position).normalized()
		velocity = to_player * chase_speed
		direction = 1 if to_player.x > 0 else -1
	else:
		# ลาดตระเวน: บินไปกลับในระยะที่กำหนด และกลับทิศเมื่อชนกำแพง
		# (จำกัดระยะไว้เพื่อไม่ให้ลอยหลุดออกนอกโซนที่วางไว้ไปชนกับดักเอง)
		if is_on_wall():
			direction = -direction
		elif patrol_range > 0.0:
			var drift := global_position.x - home_x
			if drift > patrol_range and direction > 0:
				direction = -1
			elif drift < -patrol_range and direction < 0:
				direction = 1
		velocity.x = speed * direction
		# ดึงตัวเองกลับเข้าหาความสูงเดิม พร้อมส่ายเป็นคลื่น
		var wanted_y := home_y + sin(wave_time * wave_speed * TAU) * wave_amplitude
		velocity.y = clampf((wanted_y - global_position.y) * return_force, -240.0, 240.0)

	if direction < 0: flip = false
	if direction > 0: flip = true

	move_and_slide()


# GameManager เก็บ reference ของผู้เล่นไว้ให้แล้วตอน base_level._ready()
func find_player() -> Player:
	if GameManager.player != null and is_instance_valid(GameManager.player):
		return GameManager.player
	return null
