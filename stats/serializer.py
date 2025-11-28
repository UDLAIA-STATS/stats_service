from rest_framework import serializers
from .models import PlayerStats


class PlayerStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlayerStats
        fields = [
            "id",
            "player_id",
            "match_id",
            "frame_timestamp",
            "has_goal",
            "km_run",
            "shots_on_target",
            "heatmap_image_path",
            "created_at",
        ]


class HeatmapUpdateSerializer(serializers.Serializer):
    heatmap_image_path = serializers.CharField()
