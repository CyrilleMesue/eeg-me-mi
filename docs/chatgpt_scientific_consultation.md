# External ChatGPT scientific consultation

## Status

**Pending external response — access blocked on 2026-08-12.**

Phase 1 did not use a separate ChatGPT session. The Phase-1 novelty analysis was produced by the OpenClaw/Codex agent using literature searches and its own reasoning. It must not be represented as an independent ChatGPT consultation.

For Phase 2, the following mechanisms were checked:

- No `OPENAI_API_KEY`/ChatGPT credential or OpenAI API client was configured in the local environment.
- The isolated OpenClaw browser reached `https://chatgpt.com/` but stopped at a Cloudflare “Verify you are human” challenge.
- The existing user-browser profile could not be attached because that gateway profile requires separate credentials/pairing.

No scientific plan was frozen and no refactoring was started while the mandatory independent review remained unavailable.

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

