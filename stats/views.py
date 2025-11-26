
from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from stats.infraestructure.heatmap_task_service import HeatmapTaskService


class GeneratePlayerHeatmapsView(APIView):

    def post(self, request):
        partido_id = request.data["partido_id"]
        tracks_json = request.data["tracks"]

        service = HeatmapTaskService()
        task_id = service.enqueue(partido_id, tracks_json)

        return Response({"task_id": task_id}, status=status.HTTP_202_ACCEPTED)


class HeatmapTaskStatusView(APIView):

    def get(self, request, task_id):
        task = AsyncResult(task_id)

        return Response({
            "task_id": task_id,
            "state": task.state,
            "result": task.result
        })
