# app/layers/infraestructure/video_analysis/plotting/services/heatmap_service.py

from stats.entities.models.heatmap import Heatmap
from stats.infraestructure.heatmap_drawer import PlayerHeatmapDrawer


class HeatmapService:

    def generate_player_heatmaps(self, partido_id: int, tracks: dict):
        drawer = PlayerHeatmapDrawer(tracks)
        heatmaps = drawer.draw_and_save()  # {player_id: bytes}

        results = []

        for player_id, image_bytes in heatmaps.items():
            result = Heatmap.objects.create(
                partido_id=partido_id,
                player_id=player_id,
                player_banner=f"PLAYER_{player_id}",  # puedes cambiar esto a tu lógica real
                heatmap=image_bytes
            )
            results.append(result.id)

        return results
