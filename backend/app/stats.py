from collections import defaultdict
from typing import Any


def calculate_stats(metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Calculate min, max, avg, and sample count for each metric.

    Grouping key:
    - metric_type
    - device
    - metric_name
    """

    grouped_values: dict[tuple[str, str | None, str], list[float]] = defaultdict(list)

    for metric in metrics:
        key = (
            metric["metric_type"],
            metric.get("device"),
            metric["metric_name"],
        )

        grouped_values[key].append(metric["metric_value"])

    results: list[dict[str, Any]] = []

    for (metric_type, device, metric_name), values in grouped_values.items():
        if not values:
            continue

        min_value = min(values)
        max_value = max(values)
        avg_value = sum(values) / len(values)

        results.append(
            {
                "metric_type": metric_type,
                "device": device,
                "metric_name": metric_name,
                "min_value": round(min_value, 4),
                "max_value": round(max_value, 4),
                "avg_value": round(avg_value, 4),
                "sample_count": len(values),
            }
        )

    results.sort(
        key=lambda item: (
            item["metric_type"],
            item["device"] or "",
            item["metric_name"],
        )
    )

    return results
