import uvicorn
from fastapi import FastAPI
import joblib
from CarbonFootPrint import CarbonFootPrint

app = FastAPI()
joblib_in = open("ModelPrediksi.joblib","rb")
model=joblib.load(joblib_in)

@app.on_event("startup")
async def load_model():
    global model
    joblib_in = open("ModelPrediksi.joblib","rb")
    model=joblib.load(joblib_in)

@app.post("/predict_co2")
async def get_prediction(data: CarbonFootPrint):
    prediction = model.predict_co2(data)
    return {"CO2 yang anda hasilkan diprediksi akan mencapai ": prediction[0] + " kg/bulan"}

@app.post("/predict_kwh")
async def get_prediction(data: CarbonFootPrint):
    prediction = model.predict_co2(data)
    return {"Daya yang anda gunakan diprediksi akan mencapai ": prediction[0] + " kwh/bulan"}

@app.post("/predict_price")
async def get_prediction(data: CarbonFootPrint):
    prediction = model.predict_co2(data)
    return {"Biaya yang perlu anda keluarkan mencapai ": prediction[0] + " rupiah"}

if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)