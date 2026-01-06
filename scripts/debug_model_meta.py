
import mlflow
from src.inference import load_model

try:
    print("Loading model...")
    model = load_model()
    print(f"Model type: {type(model)}")
    print(f"Has metadata? {hasattr(model, 'metadata')}")
    if hasattr(model, 'metadata'):
        print(f"Metadata: {model.metadata}")
    else:
        print("Model has no 'metadata' attribute.")
except Exception as e:
    print(f"Error loading model: {e}")
