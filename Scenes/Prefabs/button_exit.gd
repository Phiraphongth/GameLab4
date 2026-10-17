extends Button

## ปุ่มอเนกประสงค์ของหน้าจอเมนู ตั้งค่าได้จาก Inspector
##   restart_game = true -> เริ่มเกมใหม่ตั้งแต่ด่าน 1 (รีเซ็ตคะแนนกับชีวิตด้วย)
##   ตั้ง exitToScene     -> ไปฉากที่ระบุผ่าน SceneTransition
##   ไม่ตั้งอะไรเลย        -> กลับหน้าเมนูหลัก

@export var exitToScene : PackedScene
@export var restart_game : bool = false


func _on_pressed() -> void:
	if restart_game:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN)
		GameManager.restart()
	elif exitToScene != null:
		SceneTransition.load_scene(exitToScene)
	else:
		get_tree().change_scene_to_file("res://Scenes/Levels/menu.tscn")
