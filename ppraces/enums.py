class PPRaceStatus:
    """Enum for PPRace status."""

    LOBBY = "lobby"  # Players joining
    WAITING_TO_START = "waiting_to_start"  # Start and end times set, waiting for start
    IN_PROGRESS = "in_progress"  # Race is currently ongoing
    FINALISING = "finalising"  # Waiting for final scores to be checked
    FINISHED = "finished"  # Scores are final
