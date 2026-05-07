from __future__ import annotations
from dataclasses import dataclass
import numpy as np
from .config import ModelConfig


@dataclass(frozen=True)
class CrashScenario:
    speed_mph: float
    angle_deg: float
    occupant_offset_m: float
    belted: bool
    sensor_delay_s: float
    pulse_duration_s: float
    crash_active: bool
    trigger_bias_mps2: float


def sample_scenarios(
    count: int,
    rng: np.random.Generator,
    config: ModelConfig,
    profile: str = "default",
) -> list[CrashScenario]:
    """Sample heavy-tailed crash scenarios from the slide description."""
    shifted = profile == "shifted_eval"

    benign_probability = config.benign_event_probability if not shifted else max(0.05, 0.6 * config.benign_event_probability)
    crash_active = rng.random(size=count) >= benign_probability

    speed_u = rng.beta(2.1, 1.7, size=count) if not shifted else rng.beta(2.8, 1.15, size=count)
    crash_speed_mph = config.speed_min_mph + (config.speed_max_mph - config.speed_min_mph) * speed_u
    benign_speed_u = rng.beta(2.2, 4.0, size=count) if not shifted else rng.beta(2.6, 3.4, size=count)
    benign_speed_mph = config.benign_speed_min_mph + (
        config.benign_speed_max_mph - config.benign_speed_min_mph
    ) * benign_speed_u
    speed_mph = np.where(crash_active, crash_speed_mph, benign_speed_mph)

    angle_beta = rng.beta(2.5, 3.0, size=count) if not shifted else rng.beta(2.0, 1.9, size=count)
    angle_sign = rng.choice(np.array([-1.0, 1.0]), size=count)
    crash_angle_scale = 35.0 if not shifted else 45.0
    crash_angle_deg = crash_angle_scale * angle_sign * angle_beta
    benign_angle_scale = 6.0 if not shifted else 8.0
    benign_angle_deg = rng.normal(loc=0.0, scale=benign_angle_scale, size=count)
    benign_angle_clip = 12.0 if not shifted else 16.0
    angle_deg = np.where(crash_active, crash_angle_deg, np.clip(benign_angle_deg, -benign_angle_clip, benign_angle_clip))

    offset_bias = config.seat_position_bias if not shifted else config.seat_position_bias + 0.012
    offset_spread = config.seat_position_spread if not shifted else 1.35 * config.seat_position_spread
    occupant_offset_m = offset_bias + rng.normal(
        loc=0.0,
        scale=offset_spread,
        size=count,
    )
    occupant_offset_m = np.clip(occupant_offset_m, -0.07, 0.09)

    belt_probability = 0.9 if not shifted else 0.78
    belted = rng.random(size=count) < belt_probability

    sensor_delay_s = _sample_sensor_delay(count, rng, config, shifted=shifted)
    trigger_bias_sigma = config.trigger_bias_sigma if not shifted else 1.25 * config.trigger_bias_sigma
    trigger_bias_mps2 = rng.normal(loc=0.0, scale=trigger_bias_sigma, size=count)

    crash_pulse_duration_s = rng.normal(
        loc=config.nominal_pulse_duration if not shifted else config.nominal_pulse_duration * 0.92,
        scale=config.pulse_duration_spread if not shifted else 1.15 * config.pulse_duration_spread,
        size=count,
    )
    crash_pulse_duration_s = np.clip(crash_pulse_duration_s, 0.070, 0.16)
    benign_pulse_duration_s = rng.normal(
        loc=config.benign_pulse_duration_mean if not shifted else 0.92 * config.benign_pulse_duration_mean,
        scale=config.benign_pulse_duration_spread if not shifted else 1.1 * config.benign_pulse_duration_spread,
        size=count,
    )
    benign_pulse_duration_s = np.clip(benign_pulse_duration_s, 0.10, 0.24)
    pulse_duration_s = np.where(crash_active, crash_pulse_duration_s, benign_pulse_duration_s)

    return [
        CrashScenario(
            speed_mph=float(speed_mph[i]),
            angle_deg=float(angle_deg[i]),
            occupant_offset_m=float(occupant_offset_m[i]),
            belted=bool(belted[i]),
            sensor_delay_s=float(sensor_delay_s[i]),
            pulse_duration_s=float(pulse_duration_s[i]),
            crash_active=bool(crash_active[i]),
            trigger_bias_mps2=float(trigger_bias_mps2[i]),
        )
        for i in range(count)
    ]


def _sample_sensor_delay(
    count: int,
    rng: np.random.Generator,
    config: ModelConfig,
    shifted: bool = False,
) -> np.ndarray:
    steps = 40
    dt = config.dt
    phi = np.exp(-dt / config.sensor_tau)
    sigma_base = config.sensor_sigma if not shifted else 1.35 * config.sensor_sigma
    sigma = sigma_base * np.sqrt(1.0 - phi**2)
    x = np.zeros(count)
    for _ in range(steps):
        x = phi * x + sigma * rng.normal(size=count)
    return np.clip(x, -0.012, 0.022 if shifted else 0.015)
