from pydantic import BaseModel, int, conint, str

class PredictInput(BaseModel):
    daya_listrik: int
    kulkas_inverter: str
    kulkas_num: int
    kulkas_consume_hour: int
    ac_inverter: str
    ac_num: int
    ac_consume_hour: int
    ac_power:int
    lamp_type: str
    lamp_num: int
    lamp_consume_hour: int
    lamp_power:int