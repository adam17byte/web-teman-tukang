import joblib

svm_model = joblib.load("model/svm_model.pkl")
tfidf_vectorizer = joblib.load("model/tfidf_vectorizer.pkl")

def predict_sentiment(text):
    if not text:
        return "netral"
    vec = tfidf_vectorizer.transform([text])
    result = svm_model.predict(vec)[0]
    return "positif" if result == 1 else "negatif"
