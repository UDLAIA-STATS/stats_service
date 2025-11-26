# app/layers/infraestructure/video_analysis/plotting/services/heatmap_task_service.py

from stats_service.celery import app as celery_app  # importa la app de celery (no la task)

class HeatmapTaskService:

    def enqueue(self, partido_id: int, tracks_json: dict) -> str:
        """
        Encola la task por nombre evitando importar la función de la task.
        Devuelve el task_id (task request id).
        """
        task_name = "app.generate_player_heatmaps_task"
        async_result = celery_app.send_task(task_name, args=[partido_id, tracks_json], kwargs={})
        return async_result.id
