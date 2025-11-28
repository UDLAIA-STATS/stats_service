from django.db import models


class PlayerStats(models.Model):
    id = models.BigAutoField(primary_key=True)
    player_id = models.BigIntegerField()
    match_id = models.BigIntegerField()
    frame_timestamp = models.BigIntegerField()
    has_goal = models.BooleanField(default=False)
    km_run = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    shots_on_target = models.IntegerField(default=0)
    heatmap_image_path = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = "player_stats"
        managed = False

    def __str__(self):
        return f"Player {self.player_id} frame {self.frame_timestamp}"
    

class PlayerStatsLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    stat_id = models.BigIntegerField()
    change_data = models.JSONField()
    created_at = models.DateTimeField()
    operation = models.CharField(max_length=10)

    class Meta:
        db_table = "player_stats_log"
        managed = False
