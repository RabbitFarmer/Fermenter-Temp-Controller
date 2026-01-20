def update_live_tilt(color, gravity, temp_f, rssi):
    cfg = tilt_cfg.get(color, {})
    live_tilts[color] = {
        "gravity": round(gravity, 3) if gravity is not None else None,
        "temp_f": temp_f,
        "rssi": rssi,
        # timestamp in explicit UTC ISO form (trailing Z) so templates parse/convert reliably
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "color_code": COLOR_MAP.get(color, "#333"),
        "beer_name": cfg.get("beer_name", ""),
        "batch_name": cfg.get("batch_name", ""),
        "brewid": cfg.get("brewid", ""),
        "recipe_og": cfg.get("recipe_og", ""),
        "recipe_fg": cfg.get("recipe_fg", ""),
        "recipe_abv": cfg.get("recipe_abv", ""),
        "actual_og": cfg.get("actual_og", ""),
        "og_confirmed": cfg.get("og_confirmed", False),
        "original_gravity": cfg.get("actual_og", 0),
    }