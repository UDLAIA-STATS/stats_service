"""
URL configuration for stats_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from .views import (
    PlayerStatsCreateView,
    PlayerStatsByPlayer,
    PlayerStatsByMatch,
    UpdateHeatmapView,
    StatsLogsView
)

urlpatterns = [
    path("stats/create/", PlayerStatsCreateView.as_view(), name="stats-create"),
    path("stats/player/<int:player_id>/", PlayerStatsByPlayer.as_view(), name="stats-player"),
    path("stats/match/<int:match_id>/", PlayerStatsByMatch.as_view(), name="stats-match"),
    path("stats/<int:stat_id>/heatmap/", UpdateHeatmapView.as_view(), name="stats-heatmap"),
    path("stats/<int:stat_id>/logs/", StatsLogsView.as_view(), name="stats-logs"),
]