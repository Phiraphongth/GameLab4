extends Enemy

# --------------------------------------------------------------------------- #
#  ศัตรูพุ่งชน (Charger)  ―  ใช้กับฉาก monster_spiky.tscn
#
#  ปกติจะเดินลาดตระเวนช้า ๆ เหมือน Enemy ทั่วไป แต่เมื่อเห็นผู้เล่นอยู่ในระยะ
#  detect_radius และอยู่ระดับความสูงใกล้กัน จะเข้าสู่วงจร 4 สถานะ
#
#      PATROL ─► WINDUP (ตั้งท่า สั่น ๆ) ─► CHARGE (พุ่ง หมุนติ้ว) ─► REST ─┐
#         ▲                                                                │
#         └────────────────────────────────────────────────────────────────┘
#
#  ตอน CHARGE จะเร็วกว่าผู้เล่นเล็กน้อย ต้องกระโดดหลบหรือยิงทิ้งก่อน
#  และจะหยุดพุ่งเมื่อชนกำแพงหรือถึงขอบเหว (ไม่เดินตกเอง)
# --------------------------------------------------------------------------- #

enum State { PATROL, WINDUP, CHARGE, REST }

@export_category("Charger Properties")
@export var detect_radius : float = 330.0     # ระยะที่เริ่มมองเห็นผู้เล่น
@export var height_tolerance : float = 90.0   # ต่างระดับได้ไม่เกินเท่านี้ถึงจะพุ่ง
@export var charge_speed : float = 330.0      # ความเร็วตอนพุ่ง
@export var windup_time : float = 0.45        # เวลาตั้งท่าก่อนพุ่ง
@export var charge_time : float = 1.30        # พุ่งได้นานสุดกี่วินาที
@export var rest_time : float = 0.90          # หยุดหอบหลังพุ่งจบ
@export var shake_strength : float = 3.0      # ความแรงของการสั่นตอนตั้งท่า
@export var spin_speed : float = 14.0         # ความเร็วหมุนตอนพุ่ง (เรเดียน/วินาที)

var state : int = State.PATROL
var state_time : float = 0.0

@onready var animate_sprite : AnimatedSprite2D = $Sprite/AnimateSprite

var sprite_home : Vector2 = Vector2.ZERO


func _ready() -> void:
	super._ready()
	sprite_home = animate_sprite.position
	animate_sprite.play()


# เขียนทับ _physics_process ของ Enemy เพื่อใส่ state machine ของตัวเอง
# (แรงโน้มถ่วงและการเช็คพื้นยังทำเหมือนเดิม)
func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity += get_gravity() * delta

	if not alive:
		velocity.x = 0
		move_and_slide()
		return

	state_time += delta

	match state:
		State.PATROL: _do_patrol()
		State.WINDUP: _do_windup()
		State.CHARGE: _do_charge(delta)
		State.REST:   _do_rest()

	if direction < 0: flip = false
	if direction > 0: flip = true

	move_and_slide()


func set_state(next_state: int) -> void:
	state = next_state
	state_time = 0.0
	animate_sprite.position = sprite_home
	if next_state != State.CHARGE:
		animate_sprite.rotation = 0.0


# --------- สถานะต่าง ๆ ---------- #

func _do_patrol() -> void:
	if not is_on_floor():
		return
	if hits_wall_or_ledge():
		direction = -direction
	velocity.x = speed * direction

	var target := find_player()
	if target == null:
		return
	var offset := target.global_position - global_position
	if absf(offset.x) < detect_radius and absf(offset.y) < height_tolerance:
		direction = 1 if offset.x > 0 else -1     # หันหน้าเข้าหาผู้เล่นก่อนพุ่ง
		set_state(State.WINDUP)


func _do_windup() -> void:
	velocity.x = 0
	# สั่นอยู่กับที่เพื่อส่งสัญญาณเตือนผู้เล่นว่ากำลังจะพุ่ง
	animate_sprite.position.x = sprite_home.x + sin(state_time * 55.0) * shake_strength
	if state_time >= windup_time:
		set_state(State.CHARGE)


func _do_charge(delta: float) -> void:
	velocity.x = charge_speed * direction
	animate_sprite.rotation += direction * spin_speed * delta
	if state_time >= charge_time or hits_wall_or_ledge():
		set_state(State.REST)


func _do_rest() -> void:
	velocity.x = 0
	if state_time >= rest_time:
		set_state(State.PATROL)


# --------- ตัวช่วย ---------- #

# จริงเมื่อชนกำแพงข้างหน้า หรือข้างหน้าเป็นเหวไม่มีพื้นรองรับ
func hits_wall_or_ledge() -> bool:
	return is_on_wall() or wall_ray.is_colliding() or (is_on_floor() and not floor_ray.is_colliding())


func find_player() -> Player:
	if GameManager.player != null and is_instance_valid(GameManager.player):
		return GameManager.player
	return null
