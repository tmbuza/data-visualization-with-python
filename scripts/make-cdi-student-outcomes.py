import numpy as np
import pandas as pd

rng = np.random.default_rng(123)

n = 260
group = rng.choice(["Group A", "Group B"], size=n, p=[0.55, 0.45])
test_prep = rng.choice(["none", "completed"], size=n, p=[0.65, 0.35])

study_hours = rng.normal(6.6, 2.3, size=n).clip(0.5, 16)
prep_boost = np.where(test_prep == "completed", 6.5, 0.0)

math = (50 + 2.15 * study_hours + prep_boost + rng.normal(0, 10, size=n)).clip(0, 100)
reading = (52 + 1.7 * study_hours + 0.7 * prep_boost + rng.normal(0, 9, size=n)).clip(0, 100)
writing = (51 + 1.55 * study_hours + 0.8 * prep_boost + rng.normal(0, 9, size=n)).clip(0, 100)

df = pd.DataFrame({
    "group": group,
    "test_prep": test_prep,
    "study_hours": np.round(study_hours, 1),
    "math_score": np.round(math, 0).astype(int),
    "reading_score": np.round(reading, 0).astype(int),
    "writing_score": np.round(writing, 0).astype(int),
})

df.to_csv("data/cdi-student-outcomes.csv", index=False)
print("Wrote data/cdi-student-outcomes.csv")
