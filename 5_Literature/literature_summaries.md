# Literature Summaries

1. National Highway Traffic Safety Administration, *FMVSS 208 Occupant Crash Protection laboratory test procedure*.
Link: https://www.nhtsa.gov/document/laboratory-test-procedure-fmvss-208-14-occupant-crash-protection

FMVSS 208 defines occupant crash protection requirements used in U.S. vehicle safety evaluation. It is relevant because the project uses injury-oriented metrics and airbag deployment design variables motivated by regulated occupant protection problems.

2. National Highway Traffic Safety Administration, *FMVSS 208 appendices and occupant crash protection procedures*.
Link: https://www.nhtsa.gov/document/laboratory-test-procedure-fmvss-208-14-appendix-h-occupant-crash-protection

The FMVSS 208 appendices provide additional procedural context for occupant crash protection testing. They are useful background for understanding how restraint performance is evaluated across carefully specified crash-test conditions.

3. Versace, J., "A Review of the Severity Index," SAE Technical Paper 710881, 1971.
Link: https://doi.org/10.4271/710881

This paper is one of the historical sources behind head injury severity measures. The project uses HIC as a proxy objective and failure metric, so this work provides context for interpreting acceleration-based injury criteria.

4. Eppinger, R. et al., *Development of Improved Injury Criteria for the Assessment of Advanced Automotive Restraint Systems*, NHTSA, 1999.
Link: https://www.nhtsa.gov/document/development-improved-injury-criteria-assessment-advanced-automotive-restraint-systems-ii-0

This report discusses injury criteria for restraint-system assessment. It supports the project choice to evaluate multiple injury-related quantities rather than optimizing only a single scalar response.

5. Deb, K., "An Efficient Constraint Handling Method for Genetic Algorithms," Computer Methods in Applied Mechanics and Engineering, 2000.
Link: https://doi.org/10.1016/S0045-7825(99)00389-8

The project uses population-based global search through differential evolution before local refinement. Deb's constraint-handling ideas are relevant background for treating bounded engineering design variables and penalized feasibility.

6. Storn, R. and Price, K., "Differential Evolution - A Simple and Efficient Heuristic for Global Optimization over Continuous Spaces," Journal of Global Optimization, 1997.
Link: https://doi.org/10.1023/A:1008202821328

Differential Evolution is the main global exploration method in the robust optimizer. It is suitable here because airbag deployment design is nonlinear, bounded, and evaluated through simulation rather than closed-form gradients.

7. Rockafellar, R. T. and Uryasev, S., "Optimization of Conditional Value-at-Risk," Journal of Risk, 2000.
Link: https://www.risk.net/journal-of-risk/technical-paper/2161159/optimization-conditional-value-risk

CVaR motivates the tail-risk component of the objective. This is important because airbag designs should reduce severe high-injury outcomes, not merely improve average performance.

8. Ben-Tal, A., El Ghaoui, L., and Nemirovski, A., *Robust Optimization*, Princeton University Press, 2009.
Link: https://press.princeton.edu/books/hardcover/9780691143682/robust-optimization

Robust optimization provides the conceptual basis for comparing nominal, stochastic, and shift-aware designs. The project's shifted evaluation profile is a simplified way to study performance under distributional mismatch.
