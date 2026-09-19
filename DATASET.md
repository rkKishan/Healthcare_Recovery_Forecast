# Dataset & Train/Test Split

Reference notes on where the training data comes from and how it is split.

---

## 1. Where the dataset comes from

The dataset is **not downloaded from anywhere — it is generated in code.** There is
no external or real patient dataset in this repository.

**Source:** [`ml/data_generator.py`](ml/data_generator.py) — `generate_dataset(n_samples, random_state=42)`

The saved model records its provenance in
[`models/20260904T174937Z/metadata.json`](models/20260904T174937Z/metadata.json):

```json
"data_source": "synthetic (rows=24000, seed=42)"
```

### What it is

"SPARCS-shaped" synthetic admissions — modelled on the **shape** of New York State's
SPARCS (Statewide Planning and Research Cooperative System) hospital discharge data,
but none of the actual SPARCS records are used. From the module docstring:

> This exists so the application is demoable with no dataset in hand.

### How rows are built

`ml/data_generator.py:70-125`. Fields are drawn from hand-set distributions:

| Column | How it is generated |
|---|---|
| `patient_id` | Sequential `PT000001`, `PT000002`, … |
| `diagnosis_code` | 10 groups (CIRC, RESP, INFX, MUSC, DIGE, NEUR, ONCO, TRMA, PSYC, OBST) with fixed weights |
| `department` | Routed from the diagnosis via a plausibility table (`_department_for_diagnosis`), weights `0.6 / 0.25 / 0.15` |
| `admission_type` | Elective, Urgent, Emergency, Trauma, Newborn — weights `0.24 / 0.22 / 0.38 / 0.10 / 0.06` |
| `gender` | M / F / U — weights `0.48 / 0.50 / 0.02` |
| `age` | `Normal(58, 19)` clipped to 0–100; forced to 0–1 for Newborn admissions so the data stays internally consistent |
| `comorbidity_count` | Poisson with `λ = 0.4 + (age / 100) * 2.2`, clipped 0–12 |
| `prior_admissions` | Poisson with `λ = 0.6 + comorbidity_count * 0.35`, clipped 0–25 |
| `length_of_stay` | Clinical signal + Gaussian noise (target) |

### The target

`length_of_stay` is a deterministic clinical signal (`_clinical_signal`,
`ml/data_generator.py:128`) plus noise:

```
signal = diagnosis_baseline
       × department_factor
       × admission_type_factor
       × age_factor          (1 + 0.004·age + 0.00012·max(age−65, 0)²)
       × comorbidity_factor  (1 + 0.155·comorbidity_count)
       × prior_factor        (1 + 0.048·prior_admissions)
       × interaction         (1 + 0.02·comorbidity_count·[age > 70])

length_of_stay = clip(signal + Normal(0, 0.5), min=0.5)
```

`NOISE_STD = 0.5` days is deliberate. It is the regressor's irreducible error floor,
so it sets RMSE directly, and it caps classifier accuracy too — the risk tier is
derived from the noisy target, so any noise crossing a tier boundary is unlearnable.
0.5 days beats the RMSE target while leaving a ~93% tier accuracy ceiling.

The frail-elderly interaction term exists so the tree models have a non-linear
pattern to find that a linear model cannot.

### Data-quality simulation

`_punch_holes()` can blank out a fraction of `gender`, `department` and
`prior_admissions` cells (`missing_rate` argument) to exercise the validator's
data-quality reporting.

### Files on disk

| File | Rows | Notes |
|---|---|---|
| `data/sample_admissions.csv` | 1,200 | Demo upload file, includes the target |
| `data/sample_admissions_no_target.csv` | 40 | Prediction-only sample |
| `data/uploads/*.csv` | 1,200 each | Copies of the sample uploaded through the UI |

These are generator output as well. The training run used 24,000 freshly generated
rows, not these files.

### Regenerating

```bash
python -m ml.data_generator --rows 6000 --seed 42 --out data/sample_admissions.csv
python -m ml.data_generator --rows 40 --no-target --out data/sample_admissions_no_target.csv
```

---

## 2. Train / test split

**80% train / 20% test** — a single hold-out split, with no separate validation set.

### Where it is set

| Location | What it does |
|---|---|
| `ml/train.py:118` | `def train(frame, test_size: float = 0.2, ...)` — the default |
| `ml/train.py:132-137` | `train_test_split(X_raw, y_los, y_tier, test_size=test_size, random_state=RANDOM_STATE, stratify=y_tier)` |
| `ml/train.py:348` | `--test-size` CLI flag to override it |

### Properties

- **Stratified** on the risk-tier label (`y_tier`), so tier proportions are preserved
  across both splits.
- **Seeded** with `RANDOM_STATE` for reproducibility.
- The preprocessor is fitted **on the training split only** (`ml/train.py:139-142`)
  and then applied to test, so there is no leakage into the hold-out set.

### Actual numbers for the current model

From [`models/20260904T174937Z/metadata.json`](models/20260904T174937Z/metadata.json):

| Split | Rows | Share |
|---|---|---|
| Total dataset | 24,000 | 100% |
| Train | 19,200 | 80% |
| Test | 4,800 | 20% |

Note: the `training_rows: 24000` field in that file is the **full dataset size**, not
the train split. The train fold is 24,000 − 4,800 = 19,200.

### Retraining

```bash
python -m ml.train --rows 24000                  # synthetic, default 80/20
python -m ml.train --rows 24000 --test-size 0.3  # 70/30
python -m ml.train --data path/to/real.csv       # train on a real extract
```

---

## 3. Known limitation

Metrics come from synthetic data with a **known generating function**, so they are an
upper bound. Real SPARCS extracts carry far more unexplained variance than
`NOISE_STD = 0.5` days implies. Retrain with `--data` before drawing any clinical
conclusion — this is a decision-support demo, not a medical device.
