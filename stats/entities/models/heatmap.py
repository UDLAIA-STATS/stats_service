# app/layers/infraestructure/models/heatmap.py
from django.db import models

class Heatmap(models.Model):
    id = models.AutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    partido_id = models.IntegerField(null=False, blank=False)
    player_id = models.IntegerField(null=False, blank=False)
    player_banner = models.CharField(max_length=100, null=False, blank=False)

    heatmap = models.BinaryField(null=False, blank=False)  

    def __str__(self):
        return f"Heatmap Result {self.partido_id} ({self.id}) - Player {self.player_id} ({self.player_banner})"