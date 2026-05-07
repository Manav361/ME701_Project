from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import ModelConfig
from .uncertainty import CrashScenario


@dataclass(frozen=True)
class DeploymentDesign:
    trigger_delay_ms: float
    pressure_early_kpa: float
    pressure_mid_kpa: float
    pressure_late_kpa: float
    vent_rate: float

    @classmethod
    def from_array(cls, values: np.ndarray) -> "DeploymentDesign":
        return cls(
            trigger_delay_ms=float(values[0]),
            pressure_early_kpa=float(values[1]),
            pressure_mid_kpa=float(values[2]),
            pressure_late_kpa=float(values[3]),
            vent_rate=float(values[4]),
        )

    def to_array(self) -> np.ndarray:
        return np.array(
            [
                self.trigger_delay_ms,
                self.pressure_early_kpa,
                self.pressure_mid_kpa,
                self.pressure_late_kpa,
                self.vent_rate,
            ],
            dtype=float,
        )


@dataclass(frozen=True)
class SimulationResult:
    time_s: np.ndarray
    displacement_m: np.ndarray
    velocity_mps: np.ndarray
    acceleration_mps2: np.ndarray
    head_displacement_m: np.ndarray
    head_velocity_mps: np.ndarray
    head_acceleration_mps2: np.ndarray
    pressure_kpa: np.ndarray
    belt_force_n: np.ndarray
    bag_force_n: np.ndarray
    hard_stop_force_n: np.ndarray
    torso_bag_force_n: np.ndarray
    head_bag_force_n: np.ndarray
    torso_hard_stop_force_n: np.ndarray
    head_hard_stop_force_n: np.ndarray
    neck_force_n: np.ndarray
    chest_deflection_trace_mm: np.ndarray
    deployed: bool
    hic: float
    chest_deflection_mm: float
    deployment_energy: float


def simulate_design(
    design: DeploymentDesign,
    scenario: CrashScenario,
    config: ModelConfig,
) -> SimulationResult:
    dt = config.dt
    time_s = np.arange(0.0, config.horizon + dt, dt)
    n = time_s.size

    x_t = np.zeros(n)
    v_t = np.zeros(n)
    a_t = np.zeros(n)

    x_h = np.zeros(n)
    v_h = np.zeros(n)
    a_h = np.zeros(n)

    pressure_kpa = np.zeros(n)
    belt_force_n = np.zeros(n)
    torso_bag_force_n = np.zeros(n)
    head_bag_force_n = np.zeros(n)
    torso_hard_stop_force_n = np.zeros(n)
    head_hard_stop_force_n = np.zeros(n)
    hard_stop_force_n = np.zeros(n)
    bag_force_n = np.zeros(n)
    neck_force_n = np.zeros(n)
    chest_deflection_state_m = np.zeros(n)
    energy_rate = np.zeros(n)
    filtered_head_acceleration = np.zeros(n)

    crash_pulse = _crash_pulse(time_s, scenario, config)
    deployed = _should_deploy(crash_pulse, scenario, config)
    effective_delay_s = (
        max(0.0, design.trigger_delay_ms / 1000.0 + scenario.sensor_delay_s)
        if deployed
        else config.horizon + 1.0
    )
    torso_gap, head_gap = _airbag_gaps(scenario, config)

    for i in range(1, n):
        t = time_s[i]

        target_pressure_kpa = _target_pressure_kpa(t, effective_delay_s, design, config)
        torso_penetration = max(0.0, x_t[i - 1] - torso_gap)
        head_penetration = max(0.0, x_h[i - 1] - head_gap)
        effective_volume = _effective_airbag_volume(torso_penetration, head_penetration, config)
        equilibrium_pressure_kpa = target_pressure_kpa * (config.bag_nominal_volume / effective_volume) ** config.bag_pressure_exponent
        pressure_kpa[i] = _integrate_pressure(
            pressure_kpa[i - 1],
            equilibrium_pressure_kpa,
            design,
            config,
            dt,
        )

        belt_force_n[i] = _belt_force(
            t=t,
            torso_displacement=x_t[i - 1],
            torso_velocity=v_t[i - 1],
            scenario=scenario,
            config=config,
        )

        torso_bag_force_n[i] = _bag_force(
            penetration=torso_penetration,
            velocity=v_t[i - 1],
            pressure_kpa=pressure_kpa[i],
            pressure_coeff=config.pressure_force_coeff,
            stiffness=config.bag_stiffness,
            damping=config.bag_damping,
        )
        head_bag_force_n[i] = _bag_force(
            penetration=head_penetration,
            velocity=v_h[i - 1],
            pressure_kpa=pressure_kpa[i],
            pressure_coeff=config.head_pressure_force_coeff,
            stiffness=config.head_bag_stiffness,
            damping=config.head_bag_damping,
        )
        bag_force_n[i] = torso_bag_force_n[i] + head_bag_force_n[i]

        torso_hard_stop_force_n[i] = _contact_force(
            penetration=max(0.0, x_t[i - 1] - config.hard_stop_position),
            velocity=v_t[i - 1],
            stiffness=config.hard_stop_stiffness,
            damping=config.hard_stop_damping,
        )
        head_hard_stop_force_n[i] = _contact_force(
            penetration=max(0.0, x_h[i - 1] - config.head_hard_stop_position),
            velocity=v_h[i - 1],
            stiffness=config.head_hard_stop_stiffness,
            damping=config.head_hard_stop_damping,
        )
        hard_stop_force_n[i] = torso_hard_stop_force_n[i] + head_hard_stop_force_n[i]

        neck_force_n[i] = _neck_force(
            head_displacement=x_h[i - 1],
            head_velocity=v_h[i - 1],
            torso_displacement=x_t[i - 1],
            torso_velocity=v_t[i - 1],
            config=config,
        )

        torso_damping_force = config.torso_structural_damping * v_t[i - 1]
        head_damping_force = config.head_structural_damping * v_h[i - 1]

        a_t[i] = (
            crash_pulse[i]
            + neck_force_n[i] / config.torso_mass
            - (
                belt_force_n[i]
                + torso_bag_force_n[i]
                + torso_hard_stop_force_n[i]
                + torso_damping_force
            )
            / config.torso_mass
        )
        a_h[i] = (
            crash_pulse[i]
            - neck_force_n[i] / config.head_mass
            - (
                head_bag_force_n[i]
                + head_hard_stop_force_n[i]
                + head_damping_force
            )
            / config.head_mass
        )

        v_t[i] = v_t[i - 1] + dt * a_t[i]
        x_t[i] = x_t[i - 1] + dt * v_t[i]
        v_h[i] = v_h[i - 1] + dt * a_h[i]
        x_h[i] = x_h[i - 1] + dt * v_h[i]

        chest_deflection_state_m[i] = _update_chest_deflection_state(
            previous_state_m=chest_deflection_state_m[i - 1],
            belt_force_n=belt_force_n[i],
            torso_bag_force_n=torso_bag_force_n[i],
            torso_hard_stop_force_n=torso_hard_stop_force_n[i],
            config=config,
            dt=dt,
        )

        energy_rate[i] = _deployment_power(
            previous_pressure_kpa=pressure_kpa[i - 1],
            equilibrium_pressure_kpa=equilibrium_pressure_kpa,
            current_pressure_kpa=pressure_kpa[i],
            design=design,
            config=config,
        )

        filtered_head_acceleration[i] = filtered_head_acceleration[i - 1] + dt * (
            a_h[i] - filtered_head_acceleration[i - 1]
        ) / config.head_accel_filter_tau

    head_injury_acceleration = config.head_injury_gain * (
        filtered_head_acceleration + 0.22 * np.maximum(neck_force_n, 0.0) / config.head_mass
    )
    hic = _compute_hic(head_injury_acceleration, dt)
    chest_deflection_mm = 1000.0 * float(np.max(chest_deflection_state_m))
    deployment_energy = _deployment_energy(energy_rate, dt)

    return SimulationResult(
        time_s=time_s,
        displacement_m=x_t,
        velocity_mps=v_t,
        acceleration_mps2=a_t,
        head_displacement_m=x_h,
        head_velocity_mps=v_h,
        head_acceleration_mps2=head_injury_acceleration,
        pressure_kpa=pressure_kpa,
        belt_force_n=belt_force_n,
        bag_force_n=bag_force_n,
        hard_stop_force_n=hard_stop_force_n,
        torso_bag_force_n=torso_bag_force_n,
        head_bag_force_n=head_bag_force_n,
        torso_hard_stop_force_n=torso_hard_stop_force_n,
        head_hard_stop_force_n=head_hard_stop_force_n,
        neck_force_n=neck_force_n,
        chest_deflection_trace_mm=1000.0 * chest_deflection_state_m,
        deployed=deployed,
        hic=hic,
        chest_deflection_mm=chest_deflection_mm,
        deployment_energy=deployment_energy,
    )


def _crash_pulse(time_s: np.ndarray, scenario: CrashScenario, config: ModelConfig) -> np.ndarray:
    duration = max(scenario.pulse_duration_s, 1.0e-6)
    delta_v = scenario.speed_mph * 0.44704
    angle_ratio = abs(scenario.angle_deg) / 35.0
    obliquity_factor = 1.0 + config.angle_sensitivity * angle_ratio
    belt_factor = 1.05 if not scenario.belted else 1.0

    tau = time_s / duration
    within_pulse = (tau >= 0.0) & (tau <= 1.0)

    main = np.zeros_like(time_s)
    main[within_pulse] = np.power(tau[within_pulse], 1.6) * np.power(1.0 - tau[within_pulse], 2.2)
    tail_center = 0.72 + 0.04 * angle_ratio
    tail = 0.18 * np.exp(-0.5 * np.square((tau - tail_center) / 0.11))
    shape = main + tail * within_pulse

    integral = np.trapezoid(shape, time_s)
    if integral <= 0.0:
        return np.zeros_like(time_s)
    return delta_v * obliquity_factor * belt_factor * shape / integral


def _should_deploy(crash_pulse: np.ndarray, scenario: CrashScenario, config: ModelConfig) -> bool:
    sensed_peak = float(np.max(crash_pulse))
    sensed_peak *= 1.0 + config.trigger_angle_sensitivity * abs(scenario.angle_deg) / 35.0
    sensed_peak += scenario.trigger_bias_mps2
    return sensed_peak >= config.trigger_accel_threshold


def _target_pressure_kpa(t: float, delay_s: float, design: DeploymentDesign, config: ModelConfig) -> float:
    if t < delay_s:
        return 0.0
    tau = t - delay_s
    if tau < 0.016:
        return design.pressure_early_kpa
    if tau < 0.044:
        return design.pressure_mid_kpa
    if tau < 0.090:
        return design.pressure_late_kpa
    return max(0.0, config.post_late_pressure_fraction * design.pressure_late_kpa)


def _airbag_gaps(scenario: CrashScenario, config: ModelConfig) -> tuple[float, float]:
    angle_reduction = config.oblique_gap_reduction * abs(scenario.angle_deg) / 35.0
    torso_gap = max(
        config.minimum_torso_gap,
        config.airbag_gap - scenario.occupant_offset_m - angle_reduction,
    )
    head_gap = max(config.minimum_head_gap, torso_gap - config.head_forward_offset)
    return torso_gap, head_gap


def _effective_airbag_volume(
    torso_penetration: float,
    head_penetration: float,
    config: ModelConfig,
) -> float:
    volume_loss = config.bag_compression_area * (torso_penetration + 0.65 * head_penetration)
    return max(config.bag_min_volume, config.bag_nominal_volume - volume_loss)


def _integrate_pressure(
    previous_pressure_kpa: float,
    equilibrium_pressure_kpa: float,
    design: DeploymentDesign,
    config: ModelConfig,
    dt: float,
) -> float:
    vent_decay = (0.0035 * design.vent_rate + config.pressure_leak_coeff) * previous_pressure_kpa
    dp = (equilibrium_pressure_kpa - previous_pressure_kpa) / config.inflate_time_constant - vent_decay
    return max(0.0, previous_pressure_kpa + dt * dp)


def _belt_force(
    t: float,
    torso_displacement: float,
    torso_velocity: float,
    scenario: CrashScenario,
    config: ModelConfig,
) -> float:
    belt_scale = _belt_scale(scenario)
    slack = _belt_slack(t, scenario, config)
    extension = max(0.0, torso_displacement - slack)
    forward_velocity = max(0.0, torso_velocity)
    raw_force = belt_scale * (
        config.belt_stiffness * np.power(extension, 1.05)
        + config.belt_damping * forward_velocity
        + _pretensioner_force(t, scenario, config)
    )
    return _apply_load_limiter(raw_force, scenario, config)


def _pretensioner_force(t: float, scenario: CrashScenario, config: ModelConfig) -> float:
    if (not scenario.belted) or t < config.pretensioner_time:
        return 0.0
    tau = t - config.pretensioner_time
    return config.pretensioner_force_peak * (1.0 - np.exp(-tau / config.pretensioner_rise_time))


def _apply_load_limiter(raw_force_n: float, scenario: CrashScenario, config: ModelConfig) -> float:
    load_limit = config.belt_load_limit * (1.0 + 0.05 * abs(scenario.angle_deg) / 35.0)
    if raw_force_n <= load_limit:
        return raw_force_n
    return load_limit + 0.12 * (raw_force_n - load_limit)


def _belt_slack(t: float, scenario: CrashScenario, config: ModelConfig) -> float:
    slack = config.base_belt_slack if scenario.belted else config.unbelted_slack
    if t >= config.pretensioner_time and scenario.belted:
        slack = min(slack, config.pretensioner_slack)
    return slack


def _belt_scale(scenario: CrashScenario) -> float:
    return 1.0 if scenario.belted else 0.28


def _bag_force(
    penetration: float,
    velocity: float,
    pressure_kpa: float,
    pressure_coeff: float,
    stiffness: float,
    damping: float,
) -> float:
    if penetration <= 0.0:
        return 0.0
    forward_velocity = max(0.0, velocity)
    return pressure_coeff * pressure_kpa + stiffness * penetration + damping * forward_velocity


def _contact_force(
    penetration: float,
    velocity: float,
    stiffness: float,
    damping: float,
) -> float:
    if penetration <= 0.0:
        return 0.0
    forward_velocity = max(0.0, velocity)
    return stiffness * penetration + damping * forward_velocity


def _neck_force(
    head_displacement: float,
    head_velocity: float,
    torso_displacement: float,
    torso_velocity: float,
    config: ModelConfig,
) -> float:
    relative_displacement = head_displacement - torso_displacement
    relative_velocity = head_velocity - torso_velocity
    return config.neck_stiffness * relative_displacement + config.neck_damping * relative_velocity


def _update_chest_deflection_state(
    previous_state_m: float,
    belt_force_n: float,
    torso_bag_force_n: float,
    torso_hard_stop_force_n: float,
    config: ModelConfig,
    dt: float,
) -> float:
    equilibrium_deflection_m = (
        belt_force_n / config.chest_belt_stiffness
        + torso_bag_force_n / config.chest_bag_stiffness
        + torso_hard_stop_force_n / config.chest_hard_stiffness
    )
    derivative = (equilibrium_deflection_m - previous_state_m) / config.chest_response_tau
    return max(0.0, previous_state_m + dt * derivative)


def _compute_hic(acceleration_mps2: np.ndarray, dt: float) -> float:
    accel_g = np.abs(acceleration_mps2) / 9.81
    max_window = max(1, int(round(0.036 / dt)))
    cumsum = np.concatenate(([0.0], np.cumsum(accel_g)))
    hic = 0.0
    for window in range(1, max_window + 1):
        averages = (cumsum[window:] - cumsum[:-window]) / window
        duration = window * dt
        candidate = np.max(duration * np.power(averages, 2.5))
        hic = max(hic, float(candidate))
    return hic


def _deployment_power(
    previous_pressure_kpa: float,
    equilibrium_pressure_kpa: float,
    current_pressure_kpa: float,
    design: DeploymentDesign,
    config: ModelConfig,
) -> float:
    pressure_rise = max(0.0, equilibrium_pressure_kpa - previous_pressure_kpa)
    stored_energy = config.inflator_energy_coeff * config.bag_nominal_volume * pressure_rise
    vent_loss = config.vent_energy_coeff * design.vent_rate * current_pressure_kpa
    return stored_energy + vent_loss


def _deployment_energy(energy_rate: np.ndarray, dt: float) -> float:
    return float(np.sum(energy_rate) * dt)
