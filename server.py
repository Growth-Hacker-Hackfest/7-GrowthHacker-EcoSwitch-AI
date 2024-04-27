from fastapi import FastAPI, File, UploadFile
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import io

app = FastAPI()

# Load model
model = load_model('animall_person_other_v2_fine_tuned.h5')
class_names = ['animal', 'other', 'person']

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    img = Image.open(io.BytesIO(contents))
    img = img.resize((224, 224))
    x = image.img_to_array(img)
    x = np.expand_dims(x, axis=0)
    x = x / 255.0
    predictions = model.predict(x)
    predicted_class = class_names[np.argmax(predictions)]
    return {"class": predicted_class}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)