extends CharacterBody2D

# --------------------------------------------------------------------------- #
#  กับดักหนามร่วง (Falling Spike)
#
#  ลอยค้างอยู่กลางอากาศเหนือทางเดิน  เมื่อผู้เล่นเดินเข้ามาในโซนตรวจจับด้านล่าง
#  มันจะ "สั่นเตือน" warn_time วินาที แล้วร่วงลงมาอย่างเร็ว
#  ตัวกับดักอยู่ในกลุ่ม "Traps" ⇒ ผู้เล่นแตะโดนแล้วตายทันที (เสีย 1 ชีวิต)
#  หลังตกถึงพื้นจะรอ wait_time แล้วค่อย ๆ ลอยกลับที่เดิม พร้อมทำงานรอบใหม่
#
#      READY ─(ผู้เล่นเข้าโซน)─► WARN ─► FALL ─(ถึงพื้น)─► WAIT ─► RETURN ─┐
#        ▲                                                                 │
#        └─────────────────────────────────────────────────────────────────┘
# --------------------------------------------------------------------------- #

enum State { READY, WARN, FALL, WAIT, RETURN }

@export_category("Falling Spike")
@export var warn_time : float = 0.45        # สั่นเตือนกี่วินาทีก่อนร่วง
@export var fall_gravity : float = 2400.0   # ความเร่งตอนร่วง
@export var max_fall_speed : float = 1500.0 # ความเร็วร่วงสูงสุด
@export var wait_time : float = 1.10        # ค้างอยู่บนพื้นกี่วินาที
@export var return_speed : float = 210.0    # ความเร็วตอนลอยกลับขึ้นที่เดิม
@export var shake_strength : float = 4.0    # ความแรงของการสั่นตอนเตือน

var state : int = State.READY
var state_time : float = 0.0
var home_position : Vector2 = Vector2.ZERO

@onready var body_sprite : Node2D = $Body
@onready var impact_dust : CPUParticles2D = $ImpactDust


func _ready() -> void:
	home_position = position
	impact_dust.emitting = false


func _physics_process(delta: float) -> void:
	state_time += delta

	match state:
		State.READY:
			velocity = Vector2.ZERO

		State.WARN:
			velocity = Vector2.ZERO
			body_sprite.position.x = sin(state_time * 60.0) * shake_strength
			if state_time >= warn_time:
				body_sprite.position.x = 0.0
				set_state(State.FALL)

		State.FALL:
			velocity.y = minf(velocity.y + fall_gravity * delta, max_fall_speed)
			if is_on_floor():
				velocity = Vector2.ZERO
				impact_dust.emitting = true
				set_state(State.WAIT)

		State.WAIT:
			velocity = Vector2.ZERO
			if state_time >= wait_time:
				set_state(State.RETURN)

		State.RETURN:
			velocity = Vector2(0, -return_speed)
			if position.y <= home_position.y:
				position = home_position
				velocity = Vector2.ZERO
				set_state(State.READY)

	move_and_slide()


func set_state(next_state: int) -> void:
	state = next_state
	state_time = 0.0


# สัญญาณจากโหนดลูก DetectZone (Area2D) ที่วางคลุมพื้นที่ด้านล่างกับดัก
func _on_detect_zone_body_entered(body: Node2D) -> void:
	if state == State.READY and body.is_in_group("Player"):
		set_state(State.WARN)
