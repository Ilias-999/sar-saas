import pytest
from app.parser import (
    parse_sar_text,
    _is_header_line,
    _detect_section,
    _to_float,
    _guess_unit,
)
from app.stats import calculate_stats


class TestParserHelpers:
    """Test helper functions in parser module."""

    def test_is_header_line_cpu(self):
        """Test CPU header detection."""
        assert _is_header_line(["CPU", "%user", "%nice", "%system"])
        assert not _is_header_line(["00:00:01", "all", "0.50", "0.00"])

    def test_is_header_line_memory(self):
        """Test memory header detection."""
        assert _is_header_line(["kbmemfree", "kbmemused", "%memused"])
        assert _is_header_line(["kbavail", "%memused"])

    def test_is_header_line_swap(self):
        """Test swap header detection."""
        assert _is_header_line(["kbswpfree", "kbswpused", "%swpused"])

    def test_is_header_line_load(self):
        """Test load header detection."""
        assert _is_header_line(["runq-sz", "plist-sz", "ldavg-1"])
        assert _is_header_line(["ldavg-1", "ldavg-5", "ldavg-15"])

    def test_is_header_line_disk(self):
        """Test disk header detection."""
        assert _is_header_line(["DEV", "tps", "rkB/s", "wkB/s"])
        assert _is_header_line(["DEV", "await", "%util"])

    def test_is_header_line_network(self):
        """Test network device header detection."""
        assert _is_header_line(["IFACE", "rxpck/s", "txpck/s"])

    def test_detect_section_cpu(self):
        """Test CPU section detection."""
        assert _detect_section(["CPU", "%user", "%nice", "%system"]) == "CPU"

    def test_detect_section_memory(self):
        """Test memory section detection."""
        assert _detect_section(["kbmemfree", "kbmemused", "%memused"]) == "MEMORY"

    def test_detect_section_swap(self):
        """Test swap section detection."""
        assert _detect_section(["kbswpfree", "kbswpused", "%swpused"]) == "SWAP"

    def test_detect_section_load(self):
        """Test load section detection."""
        assert _detect_section(["runq-sz", "plist-sz", "ldavg-1"]) == "LOAD"

    def test_detect_section_disk(self):
        """Test disk section detection."""
        assert _detect_section(["DEV", "tps", "rkB/s", "%util"]) == "DISK"

    def test_detect_section_network(self):
        """Test network section detection."""
        assert _detect_section(["IFACE", "rxpck/s", "txpck/s"]) == "NETWORK_DEV"

    def test_detect_section_unknown(self):
        """Test unknown section returns None."""
        assert _detect_section(["unknown", "column"]) is None

    def test_to_float_valid(self):
        """Test valid float conversion."""
        assert _to_float("1.5") == 1.5
        assert _to_float("100") == 100.0
        assert _to_float("0.00") == 0.0

    def test_to_float_comma_separator(self):
        """Test float conversion with comma separator."""
        assert _to_float("1,5") == 1.5
        assert _to_float("10,25") == 10.25

    def test_to_float_invalid(self):
        """Test invalid float conversion."""
        assert _to_float("invalid") is None
        assert _to_float("") is None
        assert _to_float("N/A") is None

    def test_guess_unit_percent(self):
        """Test percent unit detection."""
        assert _guess_unit("%user") == "%"
        assert _guess_unit("%memused") == "%"

    def test_guess_unit_kilobytes(self):
        """Test kilobyte unit detection."""
        assert _guess_unit("kbmemfree") == "kB"
        assert _guess_unit("rkB/s") == "kB"

    def test_guess_unit_per_second(self):
        """Test per-second unit detection."""
        assert _guess_unit("rxpck/s") == "per_second"
        assert _guess_unit("txpck/s") == "per_second"

    def test_guess_unit_milliseconds(self):
        """Test millisecond unit detection."""
        assert _guess_unit("await") == "ms"

    def test_guess_unit_unknown(self):
        """Test unknown unit."""
        assert _guess_unit("unknown") is None


class TestParseSarText:
    """Test main parse_sar_text function."""

    def test_parse_empty_text(self):
        """Test parsing empty text."""
        result = parse_sar_text("")
        assert result == []

    def test_parse_text_with_linux_header(self):
        """Test that Linux header lines are skipped."""
        text = "Linux 5.10.0"
        result = parse_sar_text(text)
        assert result == []

    def test_parse_cpu_data(self):
        """Test parsing CPU data."""
        text = """Linux 5.10.124-linuxkit (5e521ca86273) 	04/27/26 	_aarch64_	(4 CPU)

18:31:04        CPU     %user     %nice   %system   %iowait    %steal     %idle
18:31:05        all      0.25      0.00      0.00      0.00      0.00     99.75
18:31:06        all      0.25      0.00      0.75      0.00      0.00     99.00"""
        result = parse_sar_text(text)
        assert len(result) >= 1
        assert any(m["metric_type"] == "CPU" for m in result)
        assert any(m["metric_name"] == "user_percent" for m in result)

    def test_parse_multiple_metrics(self):
        """Test parsing multiple metrics from one line."""
        text = """18:31:04        CPU     %user     %nice   %system
18:31:05        all      0.25      0.00      0.00"""
        result = parse_sar_text(text)
        assert len(result) >= 3

    def test_parse_device_extraction(self):
        """Test device extraction from data."""
        text = """Linux 5.10.124-linuxkit (5e521ca86273)

18:34:07          DEV       tps     rkB/s     wkB/s     dkB/s   areq-sz    aqu-sz     await     %util
18:34:08          vda      0.00      0.00      0.00      0.00      0.00      0.00      0.00      0.00
18:34:09          vda      2.00      0.00     12.00      0.00      6.00      0.00      1.50      0.40"""
        result = parse_sar_text(text)
        disk_metrics = [m for m in result if m["metric_type"] == "DISK"]
        assert len(disk_metrics) > 0
        assert all(m["device"] == "vda" for m in disk_metrics)

    def test_parse_mismatched_columns(self):
        """Test that mismatched column counts are skipped."""
        text = """CPU %user %nice
00:00:01 all 1.50 0.00  # Extra column should be skipped"""
        result = parse_sar_text(text)
        # Should still parse valid lines
        assert isinstance(result, list)


class TestCalculateStats:
    """Test calculate_stats function."""

    def test_calculate_stats_empty_list(self):
        """Test with empty metrics list."""
        result = calculate_stats([])
        assert result == []

    def test_calculate_stats_single_metric(self):
        """Test with single metric."""
        metrics = [
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 50.0,
            }
        ]
        result = calculate_stats(metrics)
        assert len(result) == 1
        assert result[0]["min_value"] == 50.0
        assert result[0]["max_value"] == 50.0
        assert result[0]["avg_value"] == 50.0
        assert result[0]["sample_count"] == 1

    def test_calculate_stats_multiple_samples(self):
        """Test with multiple samples of same metric."""
        metrics = [
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 10.0,
            },
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 20.0,
            },
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 30.0,
            },
        ]
        result = calculate_stats(metrics)
        assert len(result) == 1
        assert result[0]["min_value"] == 10.0
        assert result[0]["max_value"] == 30.0
        assert result[0]["avg_value"] == 20.0
        assert result[0]["sample_count"] == 3

    def test_calculate_stats_multiple_devices(self):
        """Test stats grouped by device."""
        metrics = [
            {
                "metric_type": "DISK",
                "device": "sda",
                "metric_name": "util_percent",
                "metric_value": 10.0,
            },
            {
                "metric_type": "DISK",
                "device": "sdb",
                "metric_name": "util_percent",
                "metric_value": 20.0,
            },
        ]
        result = calculate_stats(metrics)
        assert len(result) == 2
        devices = {r["device"] for r in result}
        assert devices == {"sda", "sdb"}

    def test_calculate_stats_multiple_metric_types(self):
        """Test stats grouped by metric type."""
        metrics = [
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 50.0,
            },
            {
                "metric_type": "MEMORY",
                "device": None,
                "metric_name": "mem_used_percent",
                "metric_value": 75.0,
            },
        ]
        result = calculate_stats(metrics)
        assert len(result) == 2
        types = {r["metric_type"] for r in result}
        assert types == {"CPU", "MEMORY"}

    def test_calculate_stats_sorted_output(self):
        """Test that results are sorted properly."""
        metrics = [
            {
                "metric_type": "MEMORY",
                "device": None,
                "metric_name": "mem_used_percent",
                "metric_value": 75.0,
            },
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 50.0,
            },
        ]
        result = calculate_stats(metrics)
        # CPU should come before MEMORY after sorting
        assert result[0]["metric_type"] == "CPU"
        assert result[1]["metric_type"] == "MEMORY"

    def test_calculate_stats_rounding(self):
        """Test that values are rounded to 4 decimals."""
        metrics = [
            {
                "metric_type": "CPU",
                "device": None,
                "metric_name": "user_percent",
                "metric_value": 10.123456,
            },
        ]
        result = calculate_stats(metrics)
        assert result[0]["avg_value"] == 10.1235
