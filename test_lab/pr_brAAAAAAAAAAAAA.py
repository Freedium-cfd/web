from collections import defaultdict
import heapq
from icecream import ic
from loguru import logger


def _split_overlapping_ranges(positions):
    logger.info("Starting improved split_overlapping_range_position")
    if not positions:
        logger.info("No positions to split")
        return []

    events = []
    for i, pos in enumerate(positions):
        heapq.heappush(events, (pos["start"], 0, i))  # 0 for start event
        heapq.heappush(events, (pos["end"], 1, i))  # 1 for end event

    active = set()
    result = []
    last_point = None
    open_ranges = defaultdict(list)

    while events:
        point, event_type, index = heapq.heappop(events)

        if last_point is not None and point > last_point and active:
            for act_index in active:
                open_ranges[act_index].append(
                    {
                        "start": last_point,
                        "end": point,
                        "type": positions[act_index]["type"],
                        "template": positions[act_index]["template"],
                    }
                )

        if event_type == 0:  # Start event
            active.add(index)
        else:  # End event
            active.remove(index)
            if open_ranges[index]:
                result.extend(open_ranges[index])
            del open_ranges[index]

        last_point = point

    # Sort the result based on the original order of positions
    result.sort(
        key=lambda x: next(
            i
            for i, pos in enumerate(positions)
            if pos["type"] == x["type"] and pos["template"] == x["template"]
        )
    )

    logger.info(
        f"Finished improved split_overlapping_range_position. Generated {len(result)} ranges."
    )
    return result
