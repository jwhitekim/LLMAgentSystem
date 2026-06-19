def tracking_object(tracker, tracker_input, frame_id):
    if len(tracker_input) == 0:
        return []
    return tracker.update(tracker_input, frame_id)
