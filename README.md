# Observer Patch Holography (OPH)

> Observer Patch Holography starts from a simple idea: no observer ever sees the whole world at once. Each observer only has access to a local patch, and neighboring patches have to agree where they overlap. If that is the starting point, then spacetime, gauge symmetry, particle physics, and classical records do not need to be assumed at the beginning. They can emerge as the stable structure that survives consistent stitching across many partial viewpoints on a finite holographic screen.
>
> This repository collects the current OPH papers, code, and supporting material. The program now includes a concrete finite-resolution framework, a route to General Relativity, a route to Standard Model structure, a growing particle-mass program with early quantitative results, and a measurement-and-observer package built into the physics itself. OPH is still unfinished: some results are already strong, some remain conditional, and some are still open. The bigger philosophical story about why reality exists at all is optional interpretation, not the main technical claim.

**French version:** [README_FR.md](README_FR.md)

**Quick links:** [website](https://floatingpragma.io/oph/) | [start with the main paper](paper/observers_are_all_you_need.pdf) | [OPH Book](https://oph-book.floatingpragma.io) | [OPH Lab](https://oph-lab.floatingpragma.io) | [disproval challenge](https://challenge.floatingpragma.io)

Physics is in an extraordinary position. The Standard Model works. General Relativity works. Quantum theory works with astonishing precision. The hard part is that these successes still do not fit together into one clean picture.

That is where the deepest questions begin. Why a `3+1`-dimensional Lorentzian world? Why this exact Standard Model structure? Why these particle masses? Why does measurement still feel less unified than many physicists would like?

OPH starts from a different question: what if the laws of physics are the rules required for many local observers to stay synchronized about the same world?

Instead of taking spacetime, particles, gauge fields, and measurement as basic ingredients, OPH tries to recover them from overlap consistency on a holographic screen. If you like simulation theory, this is the version that tries to turn that intuition into concrete mathematics instead of leaving it as a metaphor.

That is why OPH is interesting. It tries to show that many strange facts belong to one structure. In the best cases, they start to look inevitable.

## The Core Idea

Each observer only sees a limited patch of information.

Different observers see overlapping patches.

Those overlaps have to agree.

That simple demand does a surprising amount of work. In OPH, objective reality is the part that survives agreement across all those local viewpoints.

- Space and time are reconstructed from overlap consistency.
- Gauge symmetry comes from the freedom in how overlapping descriptions are glued together.
- Particles are stable patterns that survive transport across patches.
- Measurement and records are treated as part of the physics, not as an afterthought.

<a href="assets/screen.svg"><img src="assets/screen.svg" alt="The holographic screen in OPH" width="800"></a>

## What OPH Explains

The cleanest way to judge OPH is to ask whether it clarifies real problems. If you take the starting point seriously, which long-standing puzzles suddenly become less mysterious?

- Why we seem to live in a `3+1`-dimensional Lorentzian universe.
- Why General Relativity appears at large scales.
- Why the Standard Model gauge structure has the shape it does.
- Why familiar particle masses and neutrino mixing patterns appear.
- Why measurement and observers belong inside the theory.
- Why string-like descriptions may reappear as an effective language in some regimes.
- Why questions about cosmology, black-hole information, and dark-sector phenomena might have a common structural home.

## Where The Project Stands

OPH is active research. Some parts are already strong, some are conditional, and some are still open.

### What already works

- A concrete finite-resolution framework for local observer patches and their synchronization.
- A concrete route from local observer agreement to a `3+1` relativistic spacetime and Einstein dynamics.
- A route to the Standard Model gauge structure `SU(3) x SU(2) x U(1) / Z_6`.
- A natural low-energy picture that looks like the Standard Model plus General Relativity.
- Exact structural masslessness for the photon, gluons, and graviton.
- Strong quantitative rows for the `W` and `Z` bosons, the Higgs boson, the top quark, and the observed neutrino hierarchy pattern.
- A built-in account of records, measurement, and observers at finite resolution.

### What is still open

- Parts of the refinement and continuum story that would complete the relativity branch from a fully explicit microscopic screen model.
- Large parts of the mass program, especially the charged-lepton absolute scale, the reduced neutrino bridge-correction invariant `C_nu` above the emitted proxy, the still-open physical quark branch after the local selector has already closed to `sigma_ref`, and the production-backend bundle needed before hadron rows can be promoted.
- Several proof completions and cleanup steps across the paper stack.

### Selected current particle outputs

| Quantity | OPH | Reference |
| --- | ---: | ---: |
| `W` boson mass | `80.37700001539531 GeV` | `80.377 GeV` |
| `Z` boson mass | `91.18797807794321 GeV` | `91.1879781 GeV` |
| Higgs boson mass | `125.218922 GeV` | `125.19953 GeV` |
| Top quark mass | `172.388646 GeV` | `172.352355 GeV` |
| Neutrino hierarchy ratio `Δm21² / Δm32²` | `0.030721110097966534` | `0.030721903199343724` |

The particle program is real, but it is not being sold here as complete. The current paper stack does not claim that the full observed particle spectrum has already been finished.

## Best Place To Start

If you only read one paper, start with **Observers Are All You Need**. It is the synthesis paper: what OPH is trying to do, what the strongest current results are, which parts are already on solid ground, and where the real open problems still sit.

- **PDF:** [Observers Are All You Need](paper/observers_are_all_you_need.pdf)
- **LaTeX source:** [observers_are_all_you_need.tex](paper/observers_are_all_you_need.tex)

## Paper Guide

**Recovering Relativity and Standard Model Structure from Observer-Overlap Consistency** is the clearest technical route from overlap consistency to spacetime physics and Standard Model structure.

- **PDF:** [Recovering Relativity and Standard Model Structure from Observer-Overlap Consistency](paper/recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact.pdf)
- **LaTeX source:** [recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact.tex](paper/recovering_relativity_and_standard_model_structure_from_observer_overlap_consistency_compact.tex)

**Deriving the Particle Zoo from Observer Consistency** is the current particle-status paper. It covers the massless carriers, the derived `W` and `Z`, and the present quantitative status for the Higgs, the top quark, several quark masses, and the neutrino hierarchy pattern. It also makes clear which pieces remain unfinished, especially the charged-lepton absolute scale, the still-open physical quark branch after the local selector has already closed to `sigma_ref` with `intrinsic_scale_law_D12` next on the emitted D12 mass ray, the reduced neutrino bridge-correction invariant `C_nu` above the emitted proxy, and the production-backend bundle plus systematics still required for hadrons.

- **PDF:** [Deriving the Particle Zoo from Observer Consistency](paper/deriving_the_particle_zoo_from_observer_consistency.pdf)
- **LaTeX source:** [deriving_the_particle_zoo_from_observer_consistency.tex](paper/deriving_the_particle_zoo_from_observer_consistency.tex)

**Reality as a Consensus Protocol** presents the computer-science view of OPH: local repair, synchronization, and objective law as a stable fixed point of many partial updates.

- **PDF:** [Reality as a Consensus Protocol](paper/reality_as_consensus_protocol.pdf)
- **LaTeX source:** [reality_as_consensus_protocol.tex](paper/reality_as_consensus_protocol.tex)

**Screen Microphysics and Observer Synchronization** gives the concrete finite screen architecture: local registers, overlap observables, records, repair moves, and observer machinery.

- **PDF:** [Screen Microphysics and Observer Synchronization](paper/screen_microphysics_and_observer_synchronization.pdf)
- **LaTeX source:** [screen_microphysics_and_observer_synchronization.tex](paper/screen_microphysics_and_observer_synchronization.tex)

## More To Explore

- **Simulation theory explainer:** [floatingpragma.io/oph/simulation-theory](https://floatingpragma.io/oph/simulation-theory/)
- **Theory of everything explainer:** [floatingpragma.io/oph/theory-of-everything](https://floatingpragma.io/oph/theory-of-everything/)
- **NotebookLM notebook:** [Introduction video and guided Q&A](https://notebooklm.google.com/notebook/d5249760-6ce8-44a0-927b-ccf90402711a?artifactId=fb7c0ebd-4375-4997-9cae-6558ff8977b4)
- **Third-party video course:** [Sriharsha Karamchati's OPH playlist on YouTube](https://www.youtube.com/playlist?list=PLff0tYtg64Egc2sTtKgThcPRNRdR6i83O)
- **Practical outlook:** [Potential practical applications of OPH](extra/PRACTICAL_APPLICATIONS.md)
- **Common objections:** [COMMON_OBJECTIONS.md](extra/COMMON_OBJECTIONS.md)
- **OPH Sage on Telegram:** [t.me/HoloObserverBot](https://t.me/HoloObserverBot)
- **OPH Sage on X:** [x.com/OphSage](https://x.com/OphSage)
- **OPH Sage on Bluesky:** [ophsage.bsky.social](https://bsky.app/profile/ophsage.bsky.social)

## Experiments

A first IBM Quantum Cloud benchmark bundle is included in this repository. These runs test local OPH-motivated structure. On their own they do not test the full theory directly. They still form part of the public evidence trail.

- **Experimental note:** [IBM Quantum Cloud Evidence for OPH](extra/IBM_QUANTUM_CLOUD.md)
- **Code and data:** [code/ibm_quantum_cloud/](code/ibm_quantum_cloud/)

## Repository Guide

- **[`paper/`](paper):** papers, PDFs, LaTeX sources, and release metadata.
- **[`book/`](book):** Markdown source for the OPH Book.
- **[`code/`](code):** code and supporting computational material.
- **[`extra/`](extra):** explainers, objections, and supporting notes.
- **[`assets/`](assets):** diagrams and figures used across the project.

## Contributing

For corrections, suggestions, or additions, please open a pull request.

## License

This repository is licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (`CC BY-NC-SA 4.0`).

You are free to share and adapt the material for non-commercial purposes, provided proper attribution is given and derivative works are licensed under identical terms.

For commercial licensing inquiries, contact `bernhard@floatingpragma.io`.
