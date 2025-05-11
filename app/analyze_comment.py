from sklearn.linear_model import LogisticRegression
import joblib

def get_analyzed_comment(data, path_to_model, column_with_text):
    model = joblib.load(path_to_model)

    data['predicted_label'] = model.predict(data[column_with_text])

    return data
