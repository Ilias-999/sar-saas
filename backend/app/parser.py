from typing import Any


SUPPORTED_SECTIONS = {
    "CPU": {
        "%user": "user_percent",
        "%nice": "nice_percent",
        "%system": "system_percent",
        "%iowait": "iowait_percent",
        "%steal": "steal_percent",
        "%idle": "idle_percent",
    },
    "MEMORY": {
        "kbmemfree": "mem_free_kb",
        "kbavail": "mem_available_kb",
        "kbmemused": "mem_used_kb",
        "%memused": "mem_used_percent",
        "kbbuffers": "buffers_kb",
        "kbcached": "cached_kb",
        "kbcommit": "commit_kb",
        "%commit": "commit_percent",
    },
    "SWAP": {
        "kbswpfree": "swap_free_kb",
        "kbswpused": "swap_used_kb",
        "%swpused": "swap_used_percent",
        "kbswpcad": "swap_cached_kb",
        "%swpcad": "swap_cached_percent",
    },
    "LOAD": {
        "runq-sz": "run_queue_size",
        "plist-sz": "process_list_size",
        "ldavg-1": "load_average_1_min",
        "ldavg-5": "load_average_5_min",
        "ldavg-15": "load_average_15_min",
        "blocked": "blocked_processes",
    },
    "DISK": {
        "tps": "transfers_per_second",
        "rkB/s": "read_kb_per_second",
        "wkB/s": "write_kb_per_second",
        "dkB/s": "discard_kb_per_second",
        "areq-sz": "average_request_size",
        "aqu-sz": "average_queue_size",
        "await": "await_ms",
        "%util": "util_percent",
    },
    "NETWORK_DEV": {
        "rxpck/s": "received_packets_per_second",
        "txpck/s": "transmitted_packets_per_second",
        "rxkB/s": "received_kb_per_second",
        "txkB/s": "transmitted_kb_per_second",
        "rxcmp/s": "received_compressed_per_second",
        "txcmp/s": "transmitted_compressed_per_second",
        "rxmcst/s": "received_multicast_per_second",
        "%ifutil": "interface_util_percent",
    },
}


def parse_sar_text(text: str) -> list[dict[str, Any]]:
    """
    Parse SAR text output.

    This parser supports common outputs from:
    - sar -u
    - sar -r
    - sar -S
    - sar -q
    - sar -d
    - sar -n DEV

    It returns normalized metric objects.
    """

    metrics: list[dict[str, Any]] = []

    current_section: str | None = None
    current_header: list[str] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("Linux"):
            continue

        if line.startswith("Average:"):
            continue

        parts = line.split()

        if len(parts) < 3:
            continue

        if _is_header_line(parts):
            current_section = _detect_section(parts)
            current_header = parts
            continue

        if current_section is None or current_header is None:
            continue

        parsed_metrics = _parse_data_line(
            section=current_section,
            header=current_header,
            parts=parts,
        )

        metrics.extend(parsed_metrics)

    return metrics


def _is_header_line(parts: list[str]) -> bool:
    """
    Detect if a line is a SAR header line.
    """

    joined = " ".join(parts)

    if "CPU" in parts and "%user" in parts:
        return True

    if "kbmemfree" in parts or "%memused" in parts:
        return True

    if "kbswpfree" in parts or "%swpused" in parts:
        return True

    if "runq-sz" in parts or "ldavg-1" in parts:
        return True

    if "DEV" in parts and ("tps" in parts or "await" in parts or "%util" in parts):
        return True

    if "IFACE" in parts and ("rxpck/s" in parts or "txpck/s" in parts):
        return True

    return False


def _detect_section(parts: list[str]) -> str | None:
    """
    Detect the SAR section based on header columns.
    """

    if "CPU" in parts and "%user" in parts:
        return "CPU"

    if "kbmemfree" in parts or "%memused" in parts:
        return "MEMORY"

    if "kbswpfree" in parts or "%swpused" in parts:
        return "SWAP"

    if "runq-sz" in parts or "ldavg-1" in parts:
        return "LOAD"

    if "DEV" in parts and ("tps" in parts or "await" in parts or "%util" in parts):
        return "DISK"

    if "IFACE" in parts and ("rxpck/s" in parts or "txpck/s" in parts):
        return "NETWORK_DEV"

    return None


def _parse_data_line(
    section: str,
    header: list[str],
    parts: list[str],
) -> list[dict[str, Any]]:
    """
    Parse one SAR data line based on the current header.
    """

    if section not in SUPPORTED_SECTIONS:
        return []

    if len(parts) != len(header):
        return []

    timestamp = parts[0]
    section_mapping = SUPPORTED_SECTIONS[section]

    device = _extract_device(section=section, header=header, parts=parts)

    parsed_metrics: list[dict[str, Any]] = []

    for index, column_name in enumerate(header):
        if column_name not in section_mapping:
            continue

        raw_value = parts[index]
        numeric_value = _to_float(raw_value)

        if numeric_value is None:
            continue

        parsed_metrics.append(
            {
                "metric_type": section,
                "recorded_at": timestamp,
                "device": device,
                "metric_name": section_mapping[column_name],
                "metric_value": numeric_value,
                "unit": _guess_unit(column_name),
            }
        )

    return parsed_metrics


def _extract_device(
    section: str,
    header: list[str],
    parts: list[str],
) -> str | None:
    """
    Extract device/interface/CPU identifier depending on section.
    """

    if section == "CPU" and "CPU" in header:
        return parts[header.index("CPU")]

    if section == "DISK" and "DEV" in header:
        return parts[header.index("DEV")]

    if section == "NETWORK_DEV" and "IFACE" in header:
        return parts[header.index("IFACE")]

    return None


def _to_float(value: str) -> float | None:
    """
    Convert string to float safely.
    """

    try:
        return float(value.replace(",", "."))
    except ValueError:
        return None


def _guess_unit(column_name: str) -> str | None:
    """
    Guess unit from SAR column name.
    """

    if column_name.startswith("%"):
        return "%"

    if "kB" in column_name or "kb" in column_name.lower():
        return "kB"

    if column_name.endswith("/s"):
        return "per_second"

    if column_name == "await":
        return "ms"

    return None
