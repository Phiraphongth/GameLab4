extends Area2D

@export var damage_amount: int = 10
@export var damage_cooldown: float = 1.0

var can_damage: bool = true


func _on_body_entered(body: Node2D) -> void:
	if body is Player and can_damage:
		GameManager.damage(damage_amount)
		body.damage_tween()
		can_damage = false
		await get_tree().create_timer(damage_cooldown).timeout
		can_damage = true
