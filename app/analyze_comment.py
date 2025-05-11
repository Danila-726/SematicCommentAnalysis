from sklearn.linear_model import LogisticRegression
import joblib

def get_data_with_predicted_label(data_for_model, data, path_to_model, column_with_text):
    model = joblib.load(path_to_model)

    data['predicted_label'] = model.predict(data_for_model)
    return data
