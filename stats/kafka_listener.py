import json
from kafka import KafkaConsumer
from django.utils.timezone import now
from .models import PlayerStats


def start_kafka_listener():
    consumer = KafkaConsumer(
        "player_stats_topic",
        bootstrap_servers=["localhost:9092"],
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    for msg in consumer:
        data = msg.value

        PlayerStats.objects.create(
            player_id=data["player_id"],
            match_id=data["match_id"],
            frame_timestamp=data["frame_timestamp"],
            km_run=data.get("km_run"),
            has_goal=data.get("has_goal", False),
            shots_on_target=data.get("shots_on_target", 0),
            heatmap_image_path=data.get("heatmap_image_path"),
            created_at=now()
        )
