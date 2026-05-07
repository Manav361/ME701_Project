# Failed Attempts

- Deterministic SQP on a nominal crash produced almost no improvement over the initial design. It was kept as a baseline because it demonstrates the weakness of single-scenario tuning.
- Purely nominal evaluation was not sufficient to show robustness, so a shifted evaluation distribution was added with more severe speeds, obliquity, occupant offset, lower belt usage, and noisier sensing.
- The initial robust optimizer improved performance, but shifted-profile results suggested value in extra local refinement, so a shift-refined local-search stage was added.
- Full industrial crash fidelity was out of scope. A reduced-order model was used instead, with limitations stated clearly in the report and README.
