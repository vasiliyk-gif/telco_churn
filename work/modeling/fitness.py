"""Earth GA fitness entry for Workshop 1 churn F1 search.

Uploaded alongside pipeline.py. Defines FitnessCalculationResult locally.
"""

from __future__ import annotations

import glob
import os
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from pydantic import BaseModel
from sklearn.metrics import f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split

from pipeline import FEATURE_COLUMNS, INNER_VALIDATION_SIZE, SEED, TARGET, build_pipeline


class FitnessCalculationResult(BaseModel):
    score: float
    scalars: Optional[Dict[str, Union[float, int]]] = None
    rows: Optional[Dict[str, List[Union[str, float, int]]]] = None


class FitnessClass:
    def __init__(self, dataset_root: str):
        csv_files = sorted(glob.glob(os.path.join(dataset_root, "*.csv")))
        if not csv_files:
            raise FileNotFoundError(f"No CSV found under {dataset_root}")
        df = pd.read_csv(csv_files[0])
        X = df[FEATURE_COLUMNS]
        y = df[TARGET].astype(int)
        self.X_inner, self.X_val, self.y_inner, self.y_val = train_test_split(
            X,
            y,
            test_size=INNER_VALIDATION_SIZE,
            random_state=SEED,
            stratify=y,
        )

    def calculate_fitness(self, chromosome: Any) -> FitnessCalculationResult:
        try:
            pipe = build_pipeline(chromosome, y_inner_train=self.y_inner.to_numpy())
            pipe.fit(self.X_inner, self.y_inner)
            y_pred = pipe.predict(self.X_val)
            f1 = float(
                f1_score(self.y_val, y_pred, pos_label=1, zero_division=0)
            )
            precision = float(
                precision_score(self.y_val, y_pred, pos_label=1, zero_division=0)
            )
            recall = float(
                recall_score(self.y_val, y_pred, pos_label=1, zero_division=0)
            )
            score = max(f1, 1e-9)
            return FitnessCalculationResult(
                score=score,
                scalars={
                    "f1": f1,
                    "precision": precision,
                    "recall": recall,
                },
            )
        except Exception as exc:  # noqa: BLE001 — Earth contract: never raise
            print(f"fitness error: {exc}")
            return FitnessCalculationResult(score=1e-9)
