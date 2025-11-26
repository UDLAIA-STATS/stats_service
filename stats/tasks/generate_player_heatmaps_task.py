from celery import shared_task
from stats.entities.utils.json_convert import PlayerJsonTransformer
from stats.infraestructure.heatmap_service import HeatmapService

@shared_task(bind=True, name="app.generate_player_heatmaps_task", max_retries=3)
def generate_player_heatmaps_task(self, partido_id: int, tracks_json: dict):
    try:
        tracks = PlayerJsonTransformer.player_frames_from_json(tracks_json)
        service = HeatmapService()
        result_ids = service.generate_player_heatmaps(partido_id, tracks)
        return {"heatmap_ids": result_ids}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)