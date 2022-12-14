import pandas as pd
import joblib
from azureml.core.model import Model
from azureml.train.automl.runtime.automl_explain_utilities import automl_setup_model_explanations
import scipy as sp


def init():

    global automl_model
    global scoring_explainer

    # Retrieve the path to the model file using the model name
    # Assume original model is named original_prediction_model
    automl_model_path = Model.get_model_path('automl_model')
    scoring_explainer_path = Model.get_model_path('scoring_explainer')

    automl_model = joblib.load(automl_model_path)
    scoring_explainer = joblib.load(scoring_explainer_path)


def is_multi_dimensional(matrix):
    if hasattr(matrix, 'ndim') and matrix.ndim > 1:
        return True
    if hasattr(matrix, 'shape') and matrix.shape[1]:
        return True
    return False


def convert_matrix(matrix):
    if sp.sparse.issparse(matrix):
        matrix = matrix.todense()
    if is_multi_dimensional(matrix):
        matrix = matrix.tolist()
    return matrix


def run(raw_data):
    # Get predictions and explanations for each data point
    data = pd.read_json(raw_data, orient='records')
    # Make prediction
    predictions = automl_model.predict(data)
    # Setup for inferencing explanations
    automl_explainer_setup_obj = automl_setup_model_explanations(automl_model,
                                                                 X_test=data, task='regression')
    # Retrieve model explanations for engineered explanations
    engineered_local_importance_values = scoring_explainer.explain(automl_explainer_setup_obj.X_test_transform)
    engineered_local_importance_values = convert_matrix(engineered_local_importance_values)

    # Retrieve model explanations for raw explanations
    raw_local_importance_values = scoring_explainer.explain(automl_explainer_setup_obj.X_test_transform, get_raw=True)
    raw_local_importance_values = convert_matrix(raw_local_importance_values)

    # You can return any data type as long as it is JSON-serializable
    return {'predictions': predictions.tolist(),
            'engineered_local_importance_values': engineered_local_importance_values,
            'raw_local_importance_values': raw_local_importance_values}
