extends Node2D

@onready var btn_continue: Button = $UI/Menu/btnContinue

# Called when the node enters the scene tree for the first time.
func _ready() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	# ปิดปุ่ม Continue ถ้ายังไม่เคยเซฟ
	btn_continue.disabled = !GameManager.has_gamesaved()
	GameManager.load_option()

	pass # Replace with function body.

# Called every frame. 'delta' is the elapsed time since the previous frame.
func _process(delta: float) -> void:
	pass


func _on_btn_start_pressed() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
	GameManager.restart()


func _on_btn_option_pressed() -> void:
	get_tree().change_scene_to_file("res://Scenes/Levels/options.tscn")


func _on_btn_credit_pressed() -> void:
	get_tree().change_scene_to_file("res://Scenes/Levels/credit.tscn")


func _on_btn_continue_pressed() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
	GameManager.load_game()
