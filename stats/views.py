from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.timezone import now

from .models import PlayerStats, PlayerStatsLog
from .serializers import PlayerStatsSerializer, HeatmapUpdateSerializer


# Crear estadísticas por frame
class PlayerStatsCreateView(generics.CreateAPIView):
    queryset = PlayerStats.objects.all()
    serializer_class = PlayerStatsSerializer

    def perform_create(self, serializer):
        serializer.save(created_at=now())


# Obtener histórico por jugador
class PlayerStatsByPlayer(APIView):
    def get(self, request, player_id):
        stats = PlayerStats.objects.filter(player_id=player_id).order_by("frame_timestamp")
        return Response(PlayerStatsSerializer(stats, many=True).data)


# Historial por partido (filter optional)
class PlayerStatsByMatch(APIView):
    def get(self, request, match_id):
        player_id = request.query_params.get("player_id")
        qs = PlayerStats.objects.filter(match_id=match_id)

        if player_id:
            qs = qs.filter(player_id=player_id)

        return Response(PlayerStatsSerializer(qs, many=True).data)


# Actualizar heatmap
class UpdateHeatmapView(APIView):
    def post(self, request, stat_id):
        serializer = HeatmapUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            stat = PlayerStats.objects.get(id=stat_id)
        except PlayerStats.DoesNotExist:
            return Response({"error": "Registro no encontrado"}, status=404)

        stat.heatmap_image_path = serializer.validated_data["heatmap_image_path"]
        stat.save()

        return Response({"message": "Heatmap guardado"})


# Log de cambios
class StatsLogsView(APIView):
    def get(self, request, stat_id):
        logs = PlayerStatsLog.objects.filter(stat_id=stat_id)
        return Response([
            {
                "id": l.id,
                "change": l.change_data,
                "operation": l.operation,
                "created_at": l.created_at,
            }
            for l in logs
        ])
