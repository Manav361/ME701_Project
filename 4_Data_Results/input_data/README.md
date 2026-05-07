# Input Data

No external measured dataset is required for the main workflow. Crash scenarios are generated synthetically by `3_Code/src/airbag_project/uncertainty.py` using the random seed and configuration in `3_Code/src/airbag_project/config.py`.

The generated uncertainty variables include crash speed, impact angle, occupant seat offset, belt usage, sensor delay, and crash pulse duration.
