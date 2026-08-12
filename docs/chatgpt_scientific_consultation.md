# External ChatGPT scientific consultation

## Status

**Completed on 2026-08-12 using the user's authenticated Chrome session.**

ChatGPT was accessed at the existing conversation **“Project Workflow and Novelty”**:

`https://chatgpt.com/c/6a7c176b-4098-83ed-948a-14a2b6c298ab`

OpenClaw attached through the configured Chrome extension profile. The original
manuscript and reanalysis code were already present in that conversation. The
four Phase-1 reports were inserted verbatim into the composer (44,262 characters
total with the adversarial-review prompt), and all four section markers were
verified before submission.

Phase 1 did not use a separate ChatGPT session. The Phase-1 novelty analysis was produced by the OpenClaw/Codex agent using literature searches and its own reasoning. It must not be represented as an independent ChatGPT consultation.

For Phase 2, the following mechanisms were checked:

- No `OPENAI_API_KEY`/ChatGPT credential or OpenAI API client was configured in the local environment.
- The isolated OpenClaw browser reached `https://chatgpt.com/` but stopped at a Cloudflare “Verify you are human” challenge.
- The existing user-browser profile could not be attached because that gateway profile requires separate credentials/pairing.

No scientific plan was frozen and no refactoring was started before this
independent review completed.

## Context package to provide

The consultation must receive, without omitting inconvenient findings:

1. `docs/project_audit.md`
2. `docs/data_access_report.md`
3. `docs/novelty_analysis.md`
4. `docs/proposed_experimental_plan.md`
5. the original nine-page manuscript PDF
6. the complete 1,044-line exported reanalysis code

## Consultation prompt

> Act as a critical, independent scientific reviewer for a planned peer-reviewed EEG study, not as a supportive coauthor. Review the attached original manuscript, current reanalysis code, project audit, local data-access report, novelty analysis, and proposed experimental plan.
>
> The dataset is PhysioNet EEGMMIDB. ME is defined by runs 3/5/7/9/11/13 and MI by 4/6/8/10/12/14. T1/T2 identify movements within runs, not ME/MI. ME always precedes its paired MI run, so condition is structurally confounded with run order. EEGMMIDB has no dedicated EMG/EOG adequate to prove removal of movement contamination.
>
> Challenge rather than endorse the plan. Address explicitly:
>
> 1. Is the proposed integrated contribution genuinely novel, merely incremental, or already established?
> 2. Which candidate hypotheses are supported by current literature, and which should be weakened or rejected?
> 3. Do the proposed experiments actually identify the stated estimands?
> 4. Which important confounders, negative controls, or robustness checks are missing?
> 5. Does fixed ME-before-MI ordering fundamentally invalidate any proposed inference or claim? Which claims remain defensible?
> 6. Should ERD physiology be primary, co-primary, or secondary, and why?
> 7. Is the participant-heterogeneity analysis sufficiently justified and powered? Which predictors and inferential limits are defensible?
> 8. Is no rejection / 150 µV / 200 µV an adequate artifact-sensitivity design? How should a primary threshold be justified without outcome selection?
> 9. Are additional controls necessary, especially for temporal drift, fatigue, habituation, cue/run effects, EMG/electrode motion, or participant identity?
> 10. Which planned analyses or models should be removed to avoid overreach and multiplicity?
>
> Then provide: (a) a ranked contribution recommendation; (b) revised primary, secondary, sensitivity, and exploratory analyses; (c) an objective participant-eligibility rule; (d) a constrained claim set; (e) a “do not claim” list; and (f) any fatal design issue that should stop the study before computation. Cite current and foundational literature where it materially affects a decision. Do not invent citations.

## Required decision record after response

The verbatim response or complete export will be archived with access date and mechanism. A separate section will map each recommendation to `accepted`, `modified`, or `rejected with reason`, and identify every change made to `docs/final_analysis_plan.md`.

## ChatGPT review outcome

ChatGPT's overall verdict was that the project is publishable after narrowing
the novelty claim. It rejected novelty claims based on cross-subject decoding
alone or on known mu/beta ERD differences. It found the defensible contribution
to be the *combination* of participant-disjoint ME-vs-MI prediction,
movement-resolved physiology, participant-level inference, artifact robustness,
and explicit diagnosis of EEGMMIDB's fixed task order.

Recommended contribution statement:

> A participant-disjoint, physiology-linked assessment of how reliably
> execution and imagery can be distinguished in unseen EEGMMIDB participants,
> how that distinction varies across movements, and how sensitive it is to
> artifact handling and the dataset's fixed task order.

The review emphasized that fixed ME-before-MI ordering is the study's dominant
limitation. No regression, mixed model, permutation procedure, or cross-validation
scheme can make the condition contrast causally unconfounded. A significant
result establishes reproducible *condition-associated* information under this
protocol, not a purely cortical or causal effect of execution versus imagery.

### Mandatory changes requested by ChatGPT

1. Add **E00 — protocol-confound negative control**: participant-disjoint
   pre-cue baseline-only ME/MI decoding using the -2.0 to -0.5 s interval.
   Baseline-only band power is required; a baseline covariance/tangent-space
   comparator is optional. Above-chance baseline decoding is evidence that
   run/session state contributes before the cued event.
2. Make ERD physiology **secondary**, not co-primary. It remains prominent for
   interpretation but is established physiology rather than the central novelty.
3. Rewrite H1 as prediction under the EEGMMIDB protocol, avoiding an assumption
   that the discriminating information is necessarily cortical physiology.
4. Replace strict all-12-run complete-case eligibility as the primary rule.
   Require valid channels/annotations and at least two of three usable repetitions
   of each of the four task types before amplitude rejection: ME-unilateral,
   MI-unilateral, ME-bilateral, and MI-bilateral. After primary rejection, both
   classes must retain enough epochs to compute participant metrics. The strict
   12-run cohort becomes a sensitivity analysis.
5. Retain **200 µV as the prespecified primary gross-artifact screen**, with
   mandatory 150 µV and no-rejection sensitivities. Do not select a threshold by
   performance. Report rejection and inclusion changes by condition, movement,
   run, and participant.
6. Add a prespecified central-sensorimotor versus non-sensorimotor/peripheral
   channel diagnostic. This is a cortical-plausibility check, not proof of
   artifact removal.
7. Keep participant heterogeneity exploratory and simplify it. Mandatory output
   is descriptive participant-level OOF performance and stability across models,
   movements, and thresholds. Limit association predictors and do not interpret
   ERD-model accuracy versus ERD magnitude as a causal biological explanation.
8. Demote representational similarity to optional supplementary analysis and
   duration sensitivity to supplementary material.
9. Remove from the core matrix: individual-mu-frequency sensitivity, alternative
   references/windows, MDM unless later justified, deep learning, domain
   adaptation, FBCSP expansion, and source localization.
10. Keep 1,000 group-aware permutations, but interpret significance only as
    reproducible condition-associated information under the fixed protocol.

### Recommended frozen hierarchy

| Status | Analysis |
|---|---|
| Primary | E01 unseen-participant ME-vs-MI prediction with ERD-LR |
| Mandatory negative control | E00 pre-cue baseline-only ME/MI decoding |
| Comparators | Dummy, CSP-LDA, Riemannian tangent-space LR |
| Secondary | E02 movement-specific decoding |
| Secondary | E03 movement-resolved mu/beta ERD and lateralization |
| Sensitivity | E05 200/150/no-rejection artifact analysis |
| Sensitivity | Primary eligibility versus strict complete-case cohort |
| Sensitivity | Fixed-order, repetition, and baseline-drift diagnostics |
| Supplementary | E06 first-60-second-event duration analysis |
| Inferential support | E07 1,000 group-aware permutations for the primary model |
| Exploratory | Participant heterogeneity |
| Optional supplementary | Representational similarity |
| Rejected | Model zoo, deep learning, FBCSP expansion, source localization, domain adaptation, and post-hoc window/reference optimization |

### Claim constraints from ChatGPT

Permitted primary wording:

> EEG recorded during execution and imagery runs contained reproducible
> information that generalized to unseen participants.

Conditional wording, only if supported by ERD/topographic/sensitivity evidence:

> The discriminative information was associated with sensorimotor mu/beta
> differences.

Prohibited wording includes claims that the study isolated neural differences
*caused* by execution versus imagery, demonstrated purely cortical differences,
established calibration-free or online BCI performance, or showed rehabilitation
or clinical benefit.

## Project decision record

All ten mandatory changes above are **accepted** for the frozen plan. The only
qualification is that baseline covariance/tangent-space E00 will remain optional
unless toy runtime shows it is inexpensive; baseline-only ERD/band-power decoding
is mandatory. No recommendation was rejected.

These decisions supersede conflicting Phase-1 proposals and will be encoded in
`docs/final_analysis_plan.md` before refactoring.
