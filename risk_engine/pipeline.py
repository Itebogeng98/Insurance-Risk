from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .features import CATEGORICAL_FEATURES, NUMERIC_FEATURES


def build_risk_pipeline(random_state: int = 42) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ('numeric', Pipeline([
                ('impute', SimpleImputer(strategy='median', keep_empty_features=True)),
                ('scale', StandardScaler()),
            ]), NUMERIC_FEATURES),
            ('categorical', OneHotEncoder(handle_unknown='ignore'), CATEGORICAL_FEATURES),
        ],
        remainder='passthrough',
    )
    model = GradientBoostingClassifier(
        n_estimators=250,
        learning_rate=0.06,
        max_depth=3,
        random_state=random_state,
    )
    pipeline = Pipeline([
        ('preprocessing', preprocessor),
        ('model', model),
    ])
    pipeline.applicant_input_schema = 3
    return pipeline
