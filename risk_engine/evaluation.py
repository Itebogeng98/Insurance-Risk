"""Offline Prudential benchmark. Its feature contract is not the applicant form."""
import hashlib
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from threadpoolctl import threadpool_limits

LABELS = ['HIGH', 'MEDIUM', 'LOW']
NOMINAL_COLUMNS = (
    [f'Product_Info_{i}' for i in (1, 2, 3, 5, 6, 7)]
    + [f'Employment_Info_{i}' for i in (2, 3, 5)]
    + [f'InsuredInfo_{i}' for i in range(1, 8)]
    + [f'Insurance_History_{i}' for i in (1, 2, 3, 4, 7, 8, 9)]
    + ['Family_Hist_1']
    + [f'Medical_History_{i}' for i in range(1, 42) if i not in (1, 10, 15, 24, 32)]
)


def prepare_native_data(frame):
    if not {'Id', 'Response'}.issubset(frame.columns):
        raise ValueError('The native benchmark requires Id and Response columns.')
    if frame['Id'].isna().any() or frame['Id'].duplicated().any():
        raise ValueError('Dataset IDs must be present and unique.')
    if not frame['Response'].isin(range(1, 9)).all():
        raise ValueError('Response must contain only integers 1 through 8.')
    frame = frame.sort_values('Id').reset_index(drop=True)
    features = frame.drop(columns=['Id', 'Response']).copy()
    nominal = [column for column in NOMINAL_COLUMNS if column in features]
    for column in nominal:
        features[column] = features[column].map(lambda value: str(value) if pd.notna(value) else np.nan)
    for column in features.columns.difference(nominal):
        features[column] = pd.to_numeric(features[column], errors='raise')
    # Identical predictor rows must not appear on opposite sides of a split.
    unique = ~features.duplicated()
    target = pd.cut(frame['Response'], [0, 2, 5, 8], labels=LABELS).astype(str)
    return features.loc[unique].reset_index(drop=True), target.loc[unique].reset_index(drop=True), int((~unique).sum())


def split_indices(target, seed):
    development, test = train_test_split(np.arange(len(target)), test_size=0.2, stratify=target, random_state=seed)
    train, validation = train_test_split(development, test_size=0.25, stratify=target.iloc[development], random_state=seed)
    return train, validation, test


def build_candidates(features, seed):
    nominal = [column for column in NOMINAL_COLUMNS if column in features]
    numeric = [column for column in features if column not in nominal]
    linear_preprocessor = ColumnTransformer([
        ('nominal', OneHotEncoder(handle_unknown='ignore'), nominal),
        ('numeric', Pipeline([('impute', SimpleImputer(strategy='median', add_indicator=True)),
                              ('scale', StandardScaler())]), numeric),
    ])
    tree_preprocessor = ColumnTransformer([
        ('nominal', OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=np.nan,
                                   encoded_missing_value=np.nan, max_categories=254), nominal),
        ('numeric', 'passthrough', numeric),
    ])
    candidates = {
        'majority_baseline': Pipeline([('prepare', clone(linear_preprocessor)), ('model', DummyClassifier(strategy='most_frequent'))]),
        'logistic_balanced': Pipeline([('prepare', clone(linear_preprocessor)),
                                      ('model', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=seed))]),
    }
    for name, leaves, weight in [('hist_gradient_15', 15, None), ('hist_gradient_31_balanced', 31, 'balanced')]:
        candidates[name] = Pipeline([
            ('prepare', clone(tree_preprocessor)),
            ('model', HistGradientBoostingClassifier(
                max_iter=200, learning_rate=0.08, max_leaf_nodes=leaves, l2_regularization=1,
                categorical_features=list(range(len(nominal))), class_weight=weight,
                early_stopping=False, random_state=seed,
            )),
        ])
    return candidates


def metrics(target, predicted):
    return {'accuracy': float(accuracy_score(target, predicted)),
            'macro_f1': float(f1_score(target, predicted, labels=LABELS, average='macro', zero_division=0))}


def evaluate_native(frame, seed=20261017, progress=lambda message: None):
    features, target, duplicates = prepare_native_data(frame)
    train, validation, test = split_indices(target, seed)
    candidates = build_candidates(features, seed)
    results = {}
    with threadpool_limits(limits=4):
        for name, candidate in candidates.items():
            progress(f'Fitting {name} on {len(train)} training rows...')
            start = time.perf_counter()
            candidate.fit(features.iloc[train], target.iloc[train])
            result = metrics(target.iloc[validation], candidate.predict(features.iloc[validation]))
            result['fit_and_validation_seconds'] = round(time.perf_counter() - start, 2)
            results[name] = result
            progress(f'{name}: validation accuracy={result["accuracy"]:.3f}, macro_f1={result["macro_f1"]:.3f}')
        selected = max(results, key=lambda name: (results[name]['macro_f1'], results[name]['accuracy']))
        # Freeze selection before touching test predictions. Refit on development data.
        winner = clone(candidates[selected])
        development = np.concatenate([train, validation])
        progress(f'Selected {selected}; refitting before one final test evaluation...')
        winner.fit(features.iloc[development], target.iloc[development])
        predicted = winner.predict(features.iloc[test])
        final_metrics = metrics(target.iloc[test], predicted)
    return {
        'purpose': 'Offline Kaggle benchmark; NOT compatible with live applicant inputs',
        'deployable': False, 'seed': seed, 'sklearn_version': sklearn.__version__,
        'label_definition': {'HIGH': [1, 2], 'MEDIUM': [3, 4, 5], 'LOW': [6, 7, 8]},
        'label_caveat': 'Project grouping of ordinal outcomes, not calibrated clinical risk.',
        'source_rows': len(frame), 'deduplicated_rows': len(features), 'duplicate_predictor_rows_removed': duplicates,
        'feature_columns': list(features.columns),
        'class_counts': {str(key): int(value) for key, value in target.value_counts().items()},
        'split_counts': {'train': len(train), 'validation': len(validation), 'test': len(test)},
        'split_hashes': {name: hashlib.sha256(indices.tobytes()).hexdigest()
                         for name, indices in [('train', train), ('validation', validation), ('test', test)]},
        'selection_rule': 'Highest validation macro F1, then validation accuracy; fixed candidate set.',
        'validation_results': results, 'selected_model': selected, 'test_metrics': final_metrics,
        'test_confusion_matrix_labels': LABELS,
        'test_confusion_matrix': confusion_matrix(target.iloc[test], predicted, labels=LABELS).tolist(),
        'test_classification_report': classification_report(target.iloc[test], predicted, labels=LABELS, output_dict=True, zero_division=0),
        'meets_numeric_targets': final_metrics['accuracy'] >= 0.85 and final_metrics['macro_f1'] >= 0.8,
        'limitations': ['Internal holdout only; this dataset was explored in earlier project experiments.',
                       'Anonymized inputs and normalization cannot be reconstructed from the live form.',
                       'No model is registered or activated by this benchmark.'],
    }
