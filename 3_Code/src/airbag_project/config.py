from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    dt: float = 1.0e-3
    horizon: float = 0.18
    benign_event_probability: float = 0.16
    occupant_mass: float = 78.0
    torso_mass: float = 72.0
    head_mass: float = 6.0
    belt_stiffness: float = 1.8e4
    belt_damping: float = 2.2e3
    belt_load_limit: float = 6.4e3
    pretensioner_time: float = 0.015
    pretensioner_slack: float = 0.012
    pretensioner_force_peak: float = 1.8e3
    pretensioner_rise_time: float = 0.006
    base_belt_slack: float = 0.045
    unbelted_slack: float = 0.11
    airbag_gap: float = 0.22
    head_forward_offset: float = 0.055
    minimum_torso_gap: float = 0.11
    minimum_head_gap: float = 0.07
    oblique_gap_reduction: float = 0.02
    bag_stiffness: float = 1.7e4
    bag_damping: float = 1.4e3
    pressure_force_coeff: float = 33.0
    head_bag_stiffness: float = 8.5e3
    head_bag_damping: float = 6.2e2
    head_pressure_force_coeff: float = 10.5
    bag_nominal_volume: float = 0.062
    bag_min_volume: float = 0.032
    bag_compression_area: float = 0.040
    bag_pressure_exponent: float = 1.18
    hard_stop_position: float = 0.34
    hard_stop_stiffness: float = 1.25e5
    hard_stop_damping: float = 1.7e3
    head_hard_stop_position: float = 0.29
    head_hard_stop_stiffness: float = 1.35e5
    head_hard_stop_damping: float = 2.3e3
    neck_stiffness: float = 1.6e4
    neck_damping: float = 7.5e2
    torso_structural_damping: float = 4.5e2
    head_structural_damping: float = 1.8e2
    head_accel_filter_tau: float = 0.0035
    head_injury_gain: float = 1.45
    inflate_time_constant: float = 0.012
    pressure_leak_coeff: float = 0.18
    post_late_pressure_fraction: float = 0.88
    nominal_pulse_duration: float = 0.11
    pulse_duration_spread: float = 0.025
    angle_sensitivity: float = 0.22
    chest_response_tau: float = 0.012
    chest_belt_stiffness: float = 5.2e5
    chest_bag_stiffness: float = 7.0e5
    chest_hard_stiffness: float = 1.3e6
    inflator_energy_coeff: float = 0.010
    vent_energy_coeff: float = 0.0012
    seat_position_spread: float = 0.028
    seat_position_bias: float = 0.0
    sensor_tau: float = 0.012
    sensor_sigma: float = 0.006
    trigger_accel_threshold: float = 115.0
    trigger_angle_sensitivity: float = 0.08
    trigger_bias_sigma: float = 16.0
    benign_speed_min_mph: float = 5.0
    benign_speed_max_mph: float = 20.0
    benign_pulse_duration_mean: float = 0.16
    benign_pulse_duration_spread: float = 0.03
    speed_min_mph: float = 30.0
    speed_max_mph: float = 60.0


@dataclass(frozen=True)
class ObjectiveWeights:
    hic_mean: float = 0.55
    chest_mean: float = 0.25
    energy: float = 0.08
    hic_cvar: float = 0.12
    false_deployment: float = 0.20


@dataclass(frozen=True)
class OptimizationConfig:
    seed: int = 7
    training_scenarios: int = 500
    shifted_training_scenarios: int = 300
    evaluation_scenarios: int = 3000
    maxiter: int = 80
    de_maxiter: int = 14
    de_popsize: int = 7
    shift_refine_multistarts: int = 3
    shift_refine_scenarios: int = 240
    hic_limit: float = 500.0
    chance_hic_limit: float = 0.10
    false_deployment_limit: float = 0.02
    delay_bounds_ms: tuple[float, float] = (5.0, 40.0)
    pressure_bounds_kpa: tuple[float, float] = (100.0, 300.0)
    vent_bounds: tuple[float, float] = (4.0, 45.0)
