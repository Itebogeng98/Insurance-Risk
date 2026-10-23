# Native Kaggle Evaluation

Run date: 2026-10-17. Machine-readable evidence: [kaggle_native.json](kaggle_native.json).
Mapping audit: [MAPPING_AUDIT.md](MAPPING_AUDIT.md).

## Dataset and Selection

59,381 original Prudential records; 30 duplicate predictor rows removed. The
59,351 retained records were split into 35,610 training, 11,870 validation and
11,871 test records. Seed: 20261017. Id and Response are excluded from predictors.
Encoders/imputers are learned within pipelines, not from the full dataset.

| Candidate | Validation accuracy | Validation macro F1 |
| --- | ---: | ---: |
| Majority baseline | 65.25% | 0.2632 |
| Balanced logistic regression | 68.74% | 0.6031 |
| Histogram gradient boosting, 15 leaves | 78.37% | 0.6696 |
| Balanced histogram gradient boosting, 31 leaves | 75.18% | 0.6718 |

The balanced 31-leaf model was selected using the predefined highest-validation-
macro-F1 rule. Its advantage over the other boosting model is small; this single
split does not establish a statistically reliable ranking. Selection preceded
test evaluation. The selected model was refitted on training + validation data.

## Final Internal Test

- Accuracy: **75.06%**, target **85%**: not met.
- Macro F1: **0.6718**, target **0.80**: not met.
- HIGH recall: **56.06%**; 737 of 2,551 HIGH examples were predicted LOW.
- MEDIUM recall: **64.80%**.
- LOW recall: **83.40%**.

Confusion matrix (rows = actual, columns = predicted):

| Actual / Predicted | HIGH | MEDIUM | LOW |
| --- | ---: | ---: | ---: |
| HIGH | 1430 | 384 | 737 |
| MEDIUM | 274 | 1020 | 280 |
| LOW | 969 | 317 | 6460 |

## Decision

Do not deploy this as the applicant scoring model. Besides missing the numeric
targets, its native anonymized inputs cannot be reconstructed from the current
application form. These outcomes are project groupings of ordinal ratings, not
calibrated claims probabilities or diagnoses.

The earlier adapter run (60.8% / 0.514) used different inputs and a different split.
The new result is therefore a separate benchmark, not a controlled claim that
the live model improved by a specific amount. No live model was replaced.

The production guard now requires a verified input contract as well as passing
metrics. Existing demonstration models are explicitly unverified, and native
benchmark models never enter the deployment registry.

## Next Work

For a real applicant scoring system, obtain appropriately authorized data with
the form's actual measured inputs and trustworthy underwriting outcomes, or agree
on a revised input schema supported by a documented dataset. Kaggle can remain an
offline research dataset. Further tuning should use development data only; a new
independent evaluation cohort is needed before production claims. Do not weaken
the targets or invent mappings to make the scores appear better.

Software verification after this work: 56 automated tests pass, including split
isolation, exclusion of identifiers/labels, stable handling of unseen categories,
and rejection of high-scoring models with unverified input mappings. Migration
0005 records that verification status without changing the active model.
