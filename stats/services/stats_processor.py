def process_frame_payload(data):
    """
    Procesa el JSON del modelo de IA antes de guardarlo.
    """
    cleaned = {
        "player_id": data["player_id"],
        "match_id": data["match_id"],
        "frame_timestamp": data["frame_timestamp"],
        "km_run": round(float(data.get("km_run", 0)), 2),
        "has_goal": bool(data.get("has_goal", False)),
        "shots_on_target": int(data.get("shots_on_target", 0)),
        "heatmap_image_path": data.get("heatmap_image_path"),
    }

    return cleaned
