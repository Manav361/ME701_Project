# Literature Summaries

This file summarizes the main references used to motivate the project. The references are grouped around occupant protection, injury metrics, stochastic/robust optimization, and the numerical methods used in the implementation.

## 1. NHTSA, FMVSS 208 Occupant Crash Protection Laboratory Test Procedure

**Link:** https://www.nhtsa.gov/document/laboratory-test-procedure-fmvss-208-14-occupant-crash-protection

FMVSS 208 is one of the central U.S. regulatory references for occupant crash protection. It describes how occupant protection performance is evaluated under prescribed crash-test procedures. Although this project does not attempt to reproduce the full regulatory test protocol, FMVSS 208 provides the engineering context for why restraint systems are judged using occupant injury-related outputs rather than only vehicle-level crash response.

This reference supports the project framing: airbag deployment is not just a mechanical timing problem, but an occupant safety problem. The project therefore evaluates deployment designs using HIC, chest deflection, failure rate, and false deployment behavior instead of optimizing only deployment energy or pressure.

## 2. NHTSA, FMVSS 208 Appendices and Occupant Crash Protection Procedures

**Link:** https://www.nhtsa.gov/document/laboratory-test-procedure-fmvss-208-14-appendix-h-occupant-crash-protection

The FMVSS 208 appendices provide additional procedural detail for occupant crash protection testing. They show that restraint evaluation is highly structured and depends on specific test conditions, dummy responses, and performance criteria. This is useful background because the project simplifies these ideas into a reproducible computational setting.

The main connection to this project is the idea that occupant protection must be evaluated consistently across scenarios. The simulator uses repeated stochastic crash scenarios as a simplified substitute for a full test matrix, allowing different deployment algorithms to be compared under the same sampled conditions.

## 3. Versace, J., "A Review of the Severity Index," SAE Technical Paper 710881, 1971

**Link:** https://doi.org/10.4271/710881

Versace's paper is an important historical reference for head injury severity measures. It discusses limitations of earlier severity-index approaches and motivates more careful treatment of acceleration-based injury metrics. This is directly relevant because the project uses a HIC-style proxy as one of the main performance measures.

The project does not claim to compute a certified regulatory HIC from a validated dummy model. Instead, it uses a simplified head-acceleration proxy to compare designs consistently. Versace's work helps justify why head acceleration and time-windowed injury measures are meaningful, while also reminding us that simplified injury metrics must be interpreted carefully.

## 4. Eppinger, R. et al., Development of Improved Injury Criteria for the Assessment of Advanced Automotive Restraint Systems, NHTSA, 1999

**Link:** https://www.nhtsa.gov/document/development-improved-injury-criteria-assessment-advanced-automotive-restraint-systems-ii-0

This NHTSA report discusses injury criteria for advanced automotive restraint systems. It explains why restraint assessment should consider multiple injury mechanisms and occupant responses, not just one scalar output. This aligns with the project decision to evaluate mean HIC, HIC tail risk, chest deflection, deployment energy, and failure rate.

The report is especially relevant to the project's limitations. Real restraint-system assessment relies on calibrated dummies, injury thresholds, and detailed test procedures. The project intentionally uses a reduced-order model, so this reference helps frame the gap between a classroom optimization model and regulatory-grade occupant safety evaluation.

## 5. Storn, R. and Price, K., "Differential Evolution - A Simple and Efficient Heuristic for Global Optimization over Continuous Spaces," Journal of Global Optimization, 1997

**Link:** https://doi.org/10.1023/A:1008202821328

Storn and Price introduced Differential Evolution as a population-based method for continuous global optimization. The method is useful for nonlinear problems where gradients are unavailable, unreliable, or expensive to compute. This matches the project setting because every candidate airbag design must be evaluated through simulation over many crash scenarios.

In the code, Differential Evolution is used for broad global search before local SLSQP refinement. This choice reduces the risk of accepting a poor local optimum in a bounded five-variable design space. The final robust method, `Robust DE+SLSQP`, is based on this global-then-local strategy.

## 6. Deb, K., "An Efficient Constraint Handling Method for Genetic Algorithms," Computer Methods in Applied Mechanics and Engineering, 2000

**Link:** https://doi.org/10.1016/S0045-7825(99)00389-8

Deb's work is a useful reference for handling constraints in population-based optimization. The paper is not about airbags specifically, but it addresses a common issue in engineering optimization: candidate designs must be judged not only by objective value but also by feasibility and constraint violation.

The project uses bounded design variables and penalty terms for unsafe behavior such as excessive HIC failure rate or false deployment. Deb's work supports the general idea of combining heuristic search with constraint-aware evaluation when the design space is nonlinear and simulation-based.

## 7. Rockafellar, R. T. and Uryasev, S., "Optimization of Conditional Value-at-Risk," Journal of Risk, 2000

**Link:** https://doi.org/10.21314/JOR.2000.038

Rockafellar and Uryasev developed an optimization framework for Conditional Value-at-Risk (CVaR), a tail-risk measure widely used when rare severe outcomes matter. In this project, rare high-HIC outcomes are important because a design with acceptable average performance can still be unacceptable if it performs badly in severe crashes.

This reference motivates the HIC CVaR90 term in the objective. Including CVaR90 encourages the optimizer to reduce the upper tail of the injury distribution rather than only lowering mean HIC. That is why the project reports both mean HIC and tail/failure metrics.

## 8. Ben-Tal, A., El Ghaoui, L., and Nemirovski, A., Robust Optimization, Princeton University Press, 2009

**Link:** https://press.princeton.edu/books/hardcover/9780691143682/robust-optimization

Ben-Tal, El Ghaoui, and Nemirovski provide a broad foundation for robust optimization. The central idea is to choose decisions that remain effective when uncertain parameters vary within a modeled uncertainty set or distributional family. This is closely related to airbag deployment because crash conditions cannot be known exactly before deployment.

The project uses this robust-design perspective in two ways. First, it trains and evaluates on many sampled crash scenarios instead of a single nominal case. Second, it includes a shifted evaluation profile to test whether a design remains useful when the crash distribution becomes more severe. The shift-robust and shift-refined methods are simplified project-level versions of this broader robustness idea.

## How the Literature Informed the Project

The occupant-protection references motivated the use of injury-centered metrics such as HIC and chest deflection. The injury-criteria references also helped define the limitations of the reduced-order simulator, since regulatory safety evaluation requires more detailed models and calibrated test procedures than this project uses.

The optimization references motivated the algorithmic structure. Differential Evolution supports global search over continuous deployment parameters, SLSQP provides local refinement, CVaR adds tail-risk sensitivity, and robust optimization motivates testing designs under both default and shifted crash distributions.
