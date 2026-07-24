from django.db import transaction, IntegrityError
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from django.db.models import Sum, Avg, Count, Max
from django.http import HttpResponse
from django.utils.timezone import now
from io import BytesIO

from stats.models import (
    PlayerStatsConsolidated, PlayerEvents,
    PlayerDistanceHistory, PlayerHeatmaps, EventType)
from stats.serializer import (
    PlayerStatsConsolidatedSerializer,
    PlayerStatsConsolidatedPatchSerializer,
    PlayerStatsBulkInputSerializer
)
from stats.utils import (
    format_serializer_errors, success_response,
    error_response, pagination_response,
)
from stats.utils.paginate import paginate_queryset

def upsert_player_consolidated(player_id: int, match_id: int, defaults: dict):
    """Crea o actualiza el registro consolidado de un jugador."""
    return PlayerStatsConsolidated.objects.update_or_create(
        player_id=player_id, match_id=match_id, defaults=defaults
    )[0]


def regenerate_player_child_tables(consolidated: PlayerStatsConsolidated):
    """
    Regenera las tablas hijas (eventos, distancia, heatmap)
    a partir del consolidado.
    """
    # 1. Eventos
    PlayerEvents.objects.filter(
        player_id=consolidated.player_id,
        match_id=consolidated.match_id
    ).delete()

    events = []
    if consolidated.passes:
        events.append(PlayerEvents(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id,
            event_type=EventType.PASS,
            metadata={'count': consolidated.passes}
        ))
    if consolidated.shots_on_target:
        events.append(PlayerEvents(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id,
            event_type=EventType.SHOT_ON_TARGET,
            metadata={'count': consolidated.shots_on_target}
        ))
    if consolidated.has_goal:
        events.append(PlayerEvents(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id,
            event_type=EventType.GOAL
        ))
    if events:
        PlayerEvents.objects.bulk_create(events, batch_size=100)

    # 2. Distancia
    if consolidated.distance_km is not None:
        PlayerDistanceHistory.objects.update_or_create(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id,
            defaults={'total_distance_km': consolidated.distance_km}
        )
    else:
        PlayerDistanceHistory.objects.filter(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id
        ).delete()

    # 3. Heatmap
    if consolidated.heatmap_image_path:
        PlayerHeatmaps.objects.update_or_create(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id,
            defaults={'heatmap_url': consolidated.heatmap_image_path}
        )
    else:
        PlayerHeatmaps.objects.filter(
            player_id=consolidated.player_id,
            match_id=consolidated.match_id
        ).delete()


class PlayerStatsBulkCreateView(APIView):
    """
    POST /api/players/stats/bulk/
    Payload: {"players": [ {player_id, match_id, ...}, ... ] }
    """
    @transaction.atomic
    def post(self, request):
        try:
            serializer = PlayerStatsBulkInputSerializer(data=request.data)
            if not serializer.is_valid():
                raise ValidationError(format_serializer_errors(serializer.errors))

            players_data = serializer.validated_data['players']
            if not players_data:
                raise ValidationError("No se enviaron jugadores.")

            consolidated_list = []
            for player_data in players_data:
                consolidated = upsert_player_consolidated(
                    player_id=player_data['player_id'],
                    match_id=player_data['match_id'],
                    defaults={
                        'shirt_number': player_data.get('shirt_number'),
                        'team': player_data.get('team'),
                        'team_color': player_data.get('team_color'),
                        'passes': player_data.get('passes', 0),
                        'shots_on_target': player_data.get('shots_on_target', 0),
                        'has_goal': player_data.get('has_goal', False),
                        'avg_speed_kmh': player_data.get('avg_speed_kmh'),
                        'avg_possession_time_s': player_data.get('avg_possession_time_s'),
                        'distance_km': player_data.get('distance_km'),
                        'heatmap_image_path': player_data.get('heatmap_image_path', ''),
                    }
                )
                regenerate_player_child_tables(consolidated)
                consolidated_list.append(consolidated)

            return success_response(
                "Estadísticas guardadas",
                PlayerStatsConsolidatedSerializer(consolidated_list, many=True).data,
                status.HTTP_201_CREATED
            )

        except ValidationError as ve:
            return error_response("Error de validación", ve.detail, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie:
            return error_response("Error de integridad", str(ie), status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return error_response("Error inesperado", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------
# 2.  Partial update
# -----------------------------------------------------------
class PlayerStatsPartialUpdateView(generics.UpdateAPIView):
    """
    PATCH /api/players/stats/<pk>/
    """
    queryset = PlayerStatsConsolidated.objects.all()
    serializer_class = PlayerStatsConsolidatedPatchSerializer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop('partial', True)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if not serializer.is_valid():
                raise ValidationError(format_serializer_errors(serializer.errors))

            self.perform_update(serializer)
            regenerate_player_child_tables(serializer.instance)

            return success_response(
                "Estadística actualizada",
                PlayerStatsConsolidatedSerializer(serializer.instance).data,
                status.HTTP_200_OK
            )

        except ValidationError as ve:
            return error_response("Error de validación", ve.detail, status.HTTP_400_BAD_REQUEST)
        except IntegrityError as ie:
            return error_response("Error de integridad", str(ie), status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return error_response("Error inesperado", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerStatsListView(generics.ListAPIView):
    """
    GET /api/players/stats/?match_id=<id>&page=<n>&offset=<m>
    """
    serializer_class = PlayerStatsConsolidatedSerializer

    def get_queryset(self):
        qs = PlayerStatsConsolidated.objects.all()
        match_id = self.request.query_params.get('match_id')
        if match_id:
            qs = qs.filter(match_id=match_id)
        return qs.order_by('-created_at')

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            return paginate_queryset(
                queryset,
                self.get_serializer_class(),
                request
            )
        except Exception as exc:
            return error_response("Error al listar", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)


class PlayerStatsDetailView(generics.RetrieveAPIView):
    """
    GET /api/players/stats/<pk>/
    """
    queryset = PlayerStatsConsolidated.objects.all()
    serializer_class = PlayerStatsConsolidatedSerializer
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response("Estadística", serializer.data, status.HTTP_200_OK)
        except Exception as exc:
            return error_response("Error al recuperar", str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)


class TeamStatsPdfView(APIView):
    """
    Descarga en PDF las estadísticas consolidadas de un partido (equipo).
    GET /api/matches/<match_id>/stats/pdf/
    """

    def get(self, request, match_id):
        stats = PlayerStats.objects.filter(match_id=match_id)

        if not stats.exists():
            return Response(
                {"error": "No hay estadísticas para este partido"}, status=404
            )

        # Agregación por jugador
        per_player = (
            stats.values("player_id")
            .annotate(
                total_goals=Sum("has_goal"),
                total_km=Sum("km_run"),
                total_shots=Sum("shots_on_target"),
                frames=Count("id"),
                last_update=Max("created_at"),
            )
            .order_by("-total_goals", "-total_shots")
        )

        # Totales del equipo
        team_totals = stats.aggregate(
            total_goals=Sum("has_goal"),
            total_km=Sum("km_run"),
            total_shots=Sum("shots_on_target"),
            avg_km=Avg("km_run"),
        )

        pdf_buffer = self._build_pdf(match_id, per_player, team_totals)

        filename = f"team_stats_match_{match_id}.pdf"
        response = HttpResponse(pdf_buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    def _build_pdf(self, match_id, per_player, team_totals):
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        styles = getSampleStyleSheet()
        story = []

        # Título
        story.append(Paragraph(f"Estadísticas consolidadas - Partido #{match_id}", styles["Title"]))
        story.append(Paragraph(f"Generado el {now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 16))

        # Resumen del equipo
        story.append(Paragraph("Resumen del equipo", styles["Heading2"]))
        resumen_data = [
            ["Goles totales", str(team_totals["total_goals"] or 0)],
            ["Km recorridos (total)", f"{team_totals['total_km'] or 0:.2f}"],
            ["Km recorridos (promedio)", f"{team_totals['avg_km'] or 0:.2f}"],
            ["Remates al arco", str(team_totals["total_shots"] or 0)],
        ]
        resumen_table = Table(resumen_data, colWidths=[8 * cm, 6 * cm])
        resumen_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(resumen_table)
        story.append(Spacer(1, 20))

        # Detalle por jugador
        story.append(Paragraph("Detalle por jugador", styles["Heading2"]))
        table_data = [["Jugador", "Goles", "Km", "Remates", "Frames"]]
        for row in per_player:
            table_data.append(
                [
                    str(row["player_id"]),
                    str(row["total_goals"] or 0),
                    f"{row['total_km'] or 0:.2f}",
                    str(row["total_shots"] or 0),
                    str(row["frames"]),
                ]
            )

        player_table = Table(table_data, colWidths=[4 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
        player_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(player_table)

        doc.build(story)
        buffer.seek(0)
        return buffer