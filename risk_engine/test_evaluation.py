import numpy as np
import pandas as pd
from django.test import SimpleTestCase

from risk_engine.evaluation import build_candidates, prepare_native_data, split_indices


class EvaluationIsolationTests(SimpleTestCase):
    def test_labels_and_identifiers_never_enter_features(self):
        frame = pd.DataFrame({'Id': [1, 2, 3], 'Response': [1, 4, 8], 'BMI': [0.1, 0.2, 0.3]})
        features, target, duplicates = prepare_native_data(frame)
        self.assertEqual(list(features), ['BMI'])
        self.assertEqual(target.tolist(), ['HIGH', 'MEDIUM', 'LOW'])
        changed = frame.copy()
        changed['Response'] = 8
        pd.testing.assert_frame_equal(features, prepare_native_data(changed)[0])

    def test_duplicates_removed_and_splits_disjoint_and_repeatable(self):
        frame = pd.DataFrame({'Id': [1, 2, 3], 'Response': [1, 4, 8], 'BMI': [0.1, 0.1, 0.3]})
        self.assertEqual(prepare_native_data(frame)[2], 1)
        target = pd.Series(['HIGH', 'MEDIUM', 'LOW'] * 100)
        partitions = split_indices(target, 42)
        self.assertEqual([len(part) for part in partitions], [180, 60, 60])
        self.assertEqual(len(set(np.concatenate(partitions))), 300)
        for first, second in zip(partitions, split_indices(target, 42)):
            np.testing.assert_array_equal(first, second)

    def test_unseen_categories_do_not_refit_encoder(self):
        features = pd.DataFrame({'Product_Info_2': ['A', 'B'] * 15, 'BMI': np.linspace(0.1, 0.9, 30)})
        pipeline = build_candidates(features, 42)['hist_gradient_15']
        pipeline.fit(features, ['HIGH', 'MEDIUM', 'LOW'] * 10)
        encoder = pipeline.named_steps['prepare'].named_transformers_['nominal']
        before = encoder.categories_[0].copy()
        pipeline.predict(pd.DataFrame({'Product_Info_2': ['UNSEEN'], 'BMI': [np.nan]}))
        np.testing.assert_array_equal(before, encoder.categories_[0])
