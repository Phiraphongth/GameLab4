extends Node2D

## หน้าตั้งค่า — เปิด/ปิดเสียงเอฟเฟกต์กับเพลง แล้วบันทึกลงไฟล์ทันที
## ค่าทั้งหมดเก็บไว้ใน GameManager และเซฟที่ user://option.json

@onready var btn_sound: Button = $UI/Menu/btnSound
@onready var btn_music: Button = $UI/Menu/btnMusic


func _ready() -> void:
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	GameManager.load_option()
	refresh()


func refresh() -> void:
	btn_sound.text = "Sound : %s" % ("ON" if GameManager.sfx_on else "OFF")
	btn_music.text = "Music : %s" % ("ON" if GameManager.music_on else "OFF")


func apply() -> void:
	GameManager.update_option()
	GameManager.save_option()
	refresh()


func _on_btn_sound_pressed() -> void:
	GameManager.sfx_on = !GameManager.sfx_on
	apply()


func _on_btn_music_pressed() -> void:
	GameManager.music_on = !GameManager.music_on
	apply()
