from datetime import datetime, timedelta
from logger import log_event, send_notification

fermentation_state = {}  # {"tilt_color": {"last_gravity": val, "last_change": datetime, "stable_since": datetime or None, "notified": False}}

def monitor_fermentation(live_tilts):
    now = datetime.utcnow()
    for color, tilt in live_tilts.items():
        gravity = tilt.get("gravity")
        state = fermentation_state.get(color, {})
        last_gravity = state.get("last_gravity")
        last_change = state.get("last_change", now)
        stable_since = state.get("stable_since", None)
        notified = state.get("notified", False)

        if gravity != last_gravity:
            # Gravity changed, reset timers
            fermentation_state[color] = {
                "last_gravity": gravity,
                "last_change": now,
                "stable_since": None,
                "notified": False
            }
        else:
            # Gravity unchanged
            if not stable_since:
                # Start stability timer
                fermentation_state[color]["stable_since"] = last_change
                fermentation_state[color]["notified"] = False
            else:
                # Has it been 48 hours?
                hours_stable = (now - stable_since).total_seconds() / 3600.0
                if hours_stable >= 48 and not notified:
                    # Fermentation finished
                    msg = (
                        f"Fermentation Finished: Tilt {color}, "
                        f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}, "
                        f"Gravity: {gravity}"
                    )
                    log_event("fermentation_finished", msg, tilt_color=color)
                    fermentation_state[color]["notified"] = True