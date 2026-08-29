extends Area2D

# --------------------------------------------------------------------------- #
#  กับดักไฟพ่น (Flame Jet)
#
#  พ่นไฟขึ้นจากพื้นเป็นจังหวะซ้ำไปเรื่อย ๆ ไม่ต้องมีใครไปกระตุ้น
#      OFF (ดับ off_time วิ) ─► WARN (กะพริบเตือน warn_time วิ) ─► ON (พ่น on_time วิ)
#  ระหว่างพ่นไฟ ถ้าผู้เล่นยืนทับจะเสีย HP ทีละ damage_amount ทุก damage_cooldown วินาที
#  (ต่างจากหนามร่วงที่โดนแล้วตายทันที — อันนี้แค่เสียเลือด จึงวิ่งฝ่าได้ถ้าเลือดพอ)
#
#  เคล็ดลับ: ตั้ง start_delay ต่างกันในแต่ละต้น จะได้พ่นสลับจังหวะกันเป็นด่านจับเวลา
# --------------------------------------------------------------------------- #

enum State { OFF, WARN, ON }

@export_category("Flame Jet")
@export var off_time : float = 2.00         # ดับอยู่กี่วินาที
@export var warn_time : float = 0.60        # กะพริบเตือนกี่วินาทีก่อนพ่นจริง
@export var on_time : float = 1.40          # พ่นไฟกี่วินาที
@export var start_delay : float = 0.00      # หน่วงตอนเริ่มด่าน (ใช้ทำจังหวะสลับ)
@export var damage_amount : int = 12        # เสีย HP ต่อครั้ง
@export var damage_cooldown : float = 0.80  # เว้นกี่วินาทีถึงจะโดนซ้ำได้

var state : int = State.OFF
var state_time : float = 0.0
var damage_timer : float = 0.0

@onready var flame : Node2D = $Flame
@onready var sparks : CPUParticles2D = $Sparks


func _ready() -> void:
	set_state(State.OFF)
	# start_delay ทำได้ง่าย ๆ ด้วยการเริ่มนับเวลาติดลบ
	state_time = -start_delay


func _process(delta: float) -> void:
	state_time += delta
	damage_timer -= delta

	match state:
		State.OFF:
			if state_time >= off_time:
				set_state(State.WARN)

		State.WARN:
			# โผล่มาแค่นิดเดียวแล้วกะพริบ เพื่อให้ผู้เล่นรู้ตัวทัน
			flame.visible = true
			flame.modulate.a = 0.55
			flame.scale.y = 0.18 + sin(state_time * 30.0) * 0.06
			if state_time >= warn_time:
				set_state(State.ON)

		State.ON:
			flame.visible = true
			flame.modulate.a = 1.0
			flame.scale.y = minf(1.0, flame.scale.y + delta * 8.0)
			burn_player()
			if state_time >= on_time:
				set_state(State.OFF)


func set_state(next_state: int) -> void:
	state = next_state
	state_time = 0.0
	match next_state:
		State.OFF:
			flame.visible = false
			flame.scale.y = 0.0
			sparks.emitting = false
		State.WARN:
			sparks.emitting = false
		State.ON:
			sparks.emitting = true


# ทำดาเมจเฉพาะตอนไฟติดจริงเท่านั้น (ฟังก์ชันนี้ถูกเรียกจากสถานะ ON อย่างเดียว)
func burn_player() -> void:
	if damage_timer > 0.0:
		return
	for body in get_overlapping_bodies():
		if body is Player:
			GameManager.damage(damage_amount)
			body.damage_tween()
			damage_timer = damage_cooldown
			return
