# app/layers/infraestructure/video_analysis/plotting/services/player_heatmap_drawer.py

import io
import matplotlib.pyplot as plt
import pandas as pd
from mplsoccer import Pitch
from stats.entities.tracks.track_detail import TrackDetailBase
from stats.entities.models.diagram import Diagram
from stats.infraestructure.drawer_service import DrawerService

class PlayerHeatmapDrawer(Diagram):
    """
    Genera un heatmap por jugador y lo retorna como bytes PNG.
    """

    def __init__(self, tracks):
        super().__init__(tracks)
        self.drawer_service = DrawerService()

    def draw_and_save(self) -> dict[int, bytes]:
        """
        Retorna un dict: { player_id: heatmap_bytes }
        """
        result = {}

        player_ids = {
            track.track_id
            for frame_content in self.tracks.values()
            for track in frame_content.values()
        }

        for player_id in player_ids:
            df = pd.DataFrame()

            for _, frame_tracks in self.tracks.items():
                if player_id in frame_tracks:
                    home_df, rival_df = self.drawer_service.process_frame(
                        {player_id: frame_tracks[player_id]}
                    )

                    # Usamos home_df y rival_df dependiendo del equipo
                    if not home_df.empty:
                        df = pd.concat([df, home_df])
                    if not rival_df.empty:
                        df = pd.concat([df, rival_df])

            if df.empty:
                continue

            fig, ax = plt.subplots(figsize=(13, 8.5))
            pitch = Pitch(
                pitch_type='statsbomb',
                pitch_color='#1e4251',
                line_color='white'
            )
            pitch.draw(ax=ax)

            pitch.kdeplot(
                df.x, df.y,
                ax=ax,
                fill=True,
                alpha=0.6,
                levels=100,
                bw_adjust=0.3
            )

            buffer = io.BytesIO()
            plt.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
            plt.close()

            buffer.seek(0)
            result[player_id] = buffer.read()

        return result
