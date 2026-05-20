#!/usr/bin/env python3
"""
Poll MTA GTFS-RT for live 4/5/6 train positions. Runs once and exits.

The MTA feed has no GPS coordinates — vehicle location is stop-based.
We derive lat/lon by looking up the current stop in nyct-gtfs's bundled
station table (which comes from the MTA's GTFS static data).

Trains with no assigned location in the feed are printed with N/A for
lat/lon; these are typically scheduled-but-not-yet-dispatched trips.
"""
import sys
import datetime

try:
    from nyct_gtfs import NYCTFeed
except ImportError:
    print("Missing dependency. Run: pip install -r backend/requirements.txt", file=sys.stderr)
    sys.exit(1)

# IRT feed — covers 1/2/3/4/5/6/7/S
FEED_ID = "1"
LEX_LINES = {"4", "5", "6", "6X"}


def stop_coords(stops_obj, stop_id):
    """Return (lat, lon) floats for a stop_id, or (None, None) if not found."""
    if not stop_id:
        return None, None
    entry = stops_obj.stops.get(stop_id)
    if not entry:
        return None, None
    try:
        return float(entry["stop_lat"]), float(entry["stop_lon"])
    except (KeyError, ValueError):
        return None, None


def fmt_time(dt):
    """Format a datetime (or None) as HH:MM:SS."""
    if not dt:
        return "N/A"
    if isinstance(dt, datetime.datetime):
        return dt.strftime("%H:%M:%S")
    return str(dt)


def main():
    print("Fetching MTA Lex Ave (4/5/6) feed...")

    try:
        feed = NYCTFeed(FEED_ID)
    except Exception as exc:
        print(f"Failed to fetch feed: {exc}", file=sys.stderr)
        sys.exit(1)

    trains = [
        t for t in feed.filter_trips(line_id=list(LEX_LINES))
        if t.stop_time_updates
    ]

    if not trains:
        print("No active 4/5/6 trains right now (may be overnight hours).")
        return

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{len(trains)} active 4/5/6 train(s) — polled at {now}\n")

    row = "{:<26} {:<5} {:<4} {:<6} {:<30} {:>10} {:>11}  {}"
    header = row.format("Trip ID", "Line", "Dir", "Status", "Current / Next Stop", "Lat", "Lon", "Last Update")
    print(header)
    print("-" * len(header))

    no_loc = 0
    stops_obj = trains[0]._stops

    for train in sorted(trains, key=lambda t: (t.route_id, t.direction or "")):
        trip_id = train.trip_id or "?"
        line = train.route_id or "?"
        direction = str(train.direction) if train.direction else "?"

        # location is the current stop_id if the train is at/near a stop
        current_stop_id = train.location
        status_raw = str(train.location_status) if train.location_status else ""
        # Shorten verbose enum strings like "VehicleStopStatus.STOPPED_AT"
        status = status_raw.split(".")[-1] if "." in status_raw else status_raw
        status = status[:6] or "?"  # "STOPD" / "TRANS" / "?"

        # Next stop from the schedule
        next_stu = train.stop_time_updates[0] if train.stop_time_updates else None
        next_stop_id = next_stu.stop_id if next_stu else None
        next_stop_name = (next_stu.stop_name or next_stop_id) if next_stu else "N/A"

        # Prefer current stop for position; fall back to next scheduled stop
        loc_stop_id = current_stop_id or next_stop_id
        lat, lon = stop_coords(stops_obj, loc_stop_id)

        if lat is not None:
            lat_str = f"{lat:10.5f}"
            lon_str = f"{lon:11.5f}"
        else:
            lat_str = "       N/A"
            lon_str = "        N/A"
            no_loc += 1

        # Combine current/next stop label
        if current_stop_id and current_stop_id != next_stop_id:
            cur_name = stops_obj.get_station_name(current_stop_id) or current_stop_id
            stop_label = f"{cur_name} → {next_stop_name}"
        else:
            stop_label = next_stop_name or "N/A"
        stop_label = stop_label[:30]

        ts_str = fmt_time(train.last_position_update)

        print(row.format(trip_id, line, direction, status, stop_label,
                         lat_str, lon_str, ts_str))

    if no_loc:
        print(f"\n  ({no_loc} train(s) had no stop location — scheduled but not yet dispatched)")

    print(f"\nNote: lat/lon derived from station table (MTA feed is stop-based, not GPS).")


if __name__ == "__main__":
    main()
