from typing import Dict
from stats.entities.tracks.track_detail import TrackDetailBase, TrackPlayerDetail

class PlayerJsonTransformer:

    @staticmethod
    def player_tracks_from_json(tracks_json: Dict[int, Dict]) -> Dict[int, TrackPlayerDetail]:
        """
        Convierte un diccionario de track_id → dict (JSON)
        en track_id → TrackPlayerDetail.
        """
        result = {}
        for track_id, track_data in tracks_json.items():
            # Reconstrucción del track desde JSON
            result[track_id] = TrackPlayerDetail(**track_data)
        return result

    @staticmethod
    def player_frames_from_json(frames_json: Dict[int, Dict[int, Dict]]) -> Dict[int, Dict[int, TrackPlayerDetail]]:
        """
        Convierte un diccionario:
            frame_num → track_id → dict
        en:
            frame_num → track_id → TrackPlayerDetail
        """
        result = {}
        for frame_num, tracks_json in frames_json.items():
            result[frame_num] = PlayerJsonTransformer.player_tracks_from_json(tracks_json)
        return result
