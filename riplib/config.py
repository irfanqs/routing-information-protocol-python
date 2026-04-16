from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

MIN_ROUTER_ID = 1
MAX_ROUTER_ID = 64000
MIN_PORT = 1024
MAX_PORT = 64000
MIN_METRIC = 1
MAX_METRIC = 16


class ConfigError(ValueError):
    """Raised when config file validation fails."""


@dataclass(frozen=True)
class OutputSpec:
    port: int
    metric: int
    neighbor_id: int


@dataclass(frozen=True)
class RouterConfig:
    router_id: int
    input_ports: List[int]
    outputs: List[OutputSpec]
    periodic_timer: float
    timeout_timer: float
    garbage_timer: float
    jitter: bool = True


_DEFAULT_PERIODIC = 5.0
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_GARBAGE = 20.0


def _parse_int(value: str, field_name: str) -> int:
    try:
        return int(value.strip())
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"{field_name} must be an integer, got: {value!r}") from exc


def _check_router_id(router_id: int, field_name: str = "router-id") -> None:
    if not (MIN_ROUTER_ID <= router_id <= MAX_ROUTER_ID):
        raise ConfigError(
            f"{field_name} must be in range [{MIN_ROUTER_ID}, {MAX_ROUTER_ID}], got {router_id}"
        )


def _check_port(port: int, field_name: str = "port") -> None:
    if not (MIN_PORT <= port <= MAX_PORT):
        raise ConfigError(f"{field_name} must be in range [{MIN_PORT}, {MAX_PORT}], got {port}")


def _check_metric(metric: int, field_name: str = "metric") -> None:
    if not (MIN_METRIC <= metric <= MAX_METRIC):
        raise ConfigError(
            f"{field_name} must be in range [{MIN_METRIC}, {MAX_METRIC}], got {metric}"
        )


def _parse_input_ports(raw_value: str) -> List[int]:
    ports = []
    seen = set()
    for token in raw_value.split(","):
        token = token.strip()
        if not token:
            continue
        port = _parse_int(token, "input-ports")
        _check_port(port, "input-ports")
        if port in seen:
            raise ConfigError(f"duplicate port {port} in input-ports")
        seen.add(port)
        ports.append(port)

    if not ports:
        raise ConfigError("input-ports must contain at least one port")
    return ports


def _parse_outputs(raw_value: str) -> List[OutputSpec]:
    outputs: List[OutputSpec] = []
    seen_ports = set()
    seen_neighbors = set()

    for token in raw_value.split(","):
        token = token.strip()
        if not token:
            continue

        parts = [p.strip() for p in token.split("-")]
        if len(parts) != 3:
            raise ConfigError(
                f"output entry must use port-metric-neighbor_id format, got: {token!r}"
            )

        port = _parse_int(parts[0], "outputs port")
        metric = _parse_int(parts[1], "outputs metric")
        neighbor_id = _parse_int(parts[2], "outputs neighbor-id")

        _check_port(port, "outputs port")
        _check_metric(metric, "outputs metric")
        _check_router_id(neighbor_id, "outputs neighbor-id")

        if port in seen_ports:
            raise ConfigError(f"duplicate output port {port}")
        if neighbor_id in seen_neighbors:
            raise ConfigError(f"duplicate output neighbor-id {neighbor_id}")

        seen_ports.add(port)
        seen_neighbors.add(neighbor_id)
        outputs.append(OutputSpec(port=port, metric=metric, neighbor_id=neighbor_id))

    if not outputs:
        raise ConfigError("outputs must contain at least one neighbor")

    return outputs


def _parse_bool(raw_value: str, field_name: str) -> bool:
    value = raw_value.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{field_name} must be true/false, got: {raw_value!r}")


def load_config(path: str | Path) -> RouterConfig:
    cfg_path = Path(path)
    if not cfg_path.exists():
        raise ConfigError(f"config file does not exist: {cfg_path}")

    values: Dict[str, str] = {}

    for line_no, raw_line in enumerate(cfg_path.read_text(encoding="ascii").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if " " not in line and "\t" not in line:
            raise ConfigError(f"line {line_no}: expected '<key> <value>'")

        key, value = line.split(maxsplit=1)
        key = key.strip().lower()
        value = value.strip()
        if not value:
            raise ConfigError(f"line {line_no}: value missing for key {key!r}")

        if key in values:
            raise ConfigError(f"line {line_no}: duplicate key {key!r}")
        values[key] = value

    missing = [k for k in ("router-id", "input-ports", "outputs") if k not in values]
    if missing:
        raise ConfigError(f"missing mandatory keys: {', '.join(missing)}")

    router_id = _parse_int(values["router-id"], "router-id")
    _check_router_id(router_id)

    input_ports = _parse_input_ports(values["input-ports"])
    outputs = _parse_outputs(values["outputs"])

    out_ports = {out.port for out in outputs}
    overlap = sorted(set(input_ports).intersection(out_ports))
    if overlap:
        raise ConfigError(
            f"ports cannot appear in both input-ports and outputs: {', '.join(map(str, overlap))}"
        )

    if any(out.neighbor_id == router_id for out in outputs):
        raise ConfigError("outputs cannot include own router-id as neighbor")

    periodic = (
        float(values["periodic-timer"]) if "periodic-timer" in values else _DEFAULT_PERIODIC
    )
    timeout = float(values["timeout-timer"]) if "timeout-timer" in values else _DEFAULT_TIMEOUT
    garbage = float(values["garbage-timer"]) if "garbage-timer" in values else _DEFAULT_GARBAGE

    if periodic <= 0 or timeout <= 0 or garbage <= 0:
        raise ConfigError("timer values must be positive")

    if "timers" in values:
        parts = [p.strip() for p in values["timers"].split(",")]
        if len(parts) != 3:
            raise ConfigError("timers must be 'periodic,timeout,garbage'")
        periodic = float(parts[0])
        timeout = float(parts[1])
        garbage = float(parts[2])

    jitter = _parse_bool(values["jitter"], "jitter") if "jitter" in values else True

    return RouterConfig(
        router_id=router_id,
        input_ports=input_ports,
        outputs=outputs,
        periodic_timer=periodic,
        timeout_timer=timeout,
        garbage_timer=garbage,
        jitter=jitter,
    )
