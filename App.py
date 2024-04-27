import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn.cluster import KMeans

def prepare_data(df_test, df_valid, path):
    data = pd.read_csv(path)
    df = data
    df_baru = pd.concat([df_test.reset_index(drop=True), df.reset_index(drop=True)], axis=0)
    df_baru = df_baru.reset_index(drop=False)
    df_baru = df_baru.drop('index', axis=1)
    categorical_cols = ['kulkas_inverter', 'ac_inverter', 'lamp_type']
    encoder = OneHotEncoder()
    encoded_data = encoder.fit_transform(df_baru[categorical_cols])
    encoded_cols = []
    for col in categorical_cols:
        unique_vals = df_baru[col].unique()
        encoded_cols.extend([f"{col}_{val}" for val in unique_vals])
    encoded_df_baru = pd.DataFrame(encoded_data.toarray(), columns=encoded_cols)
    df_baru = pd.concat([df_baru.drop(categorical_cols, axis=1), encoded_df_baru], axis=1)
    df_baru_normalized = df_baru
    return df_baru_normalized

def cluster_data(df_baru_normalized, n_clusters):
    model_kmeans = KMeans(n_clusters=n_clusters)
    model_kmeans.fit(df_baru_normalized)
    df_baru_normalized['cluster'] = model_kmeans.labels_
    df_cluster = df_baru_normalized.groupby('cluster').median()
    df_cluster = df_cluster.T
    return df_cluster

def get_target(df_baru_normalized):
    data_target = df_baru_normalized.iloc[0]
    target_cluster = data_target['cluster']
    return data_target, target_cluster

def preprocessing(data_target, df_cluster, target_cluster):
    selisih = data_target - df_cluster[target_cluster-1]
    baris_positif = selisih[selisih > 0]
    kolom_filter = ['kulkas_inverter', 'kulkas_num', 'kulkas_power', 'kulkas_consume_hour',
                    'ac_inverter', 'ac_num', 'ac_consume_hour', 'ac_power',
                    'lamp_type', 'lamp_num', 'lamp_consume_hour', 'lamp_power']

    baris_positif_filtered = baris_positif[baris_positif.index.isin(kolom_filter)]
    output = pd.DataFrame(baris_positif_filtered.T)
    data_hasil_rekomendasi = pd.DataFrame(columns=['column', 'decrease_amount'])

    for index, row in output.iterrows():
        column = row.name 
        decrease_amount = row.iloc[0]
        new_row = {'column': column, 'decrease_amount': decrease_amount}
        data_hasil_rekomendasi = pd.concat([data_hasil_rekomendasi, pd.DataFrame([new_row])], ignore_index=True)

    return data_hasil_rekomendasi

def rekomendasi(data_hasil_rekomendasi):
    recommendation_string = "Berdasarkan pola penggunaan anda, saya sarankan untuk melakukan penghematan dengan mengurangi penggunaan sebanyak:\n"
    for index, row in data_hasil_rekomendasi.iterrows():
        column = row['column']
        decrease_amount = row['decrease_amount']
        recommendation_string += f"- {column}: {decrease_amount}\n"
    return recommendation_string

def predict_kwh(daya_listrik, kulkas_inverter, kulkas_num, kulkas_consume_hour, kulkas_power, ac_inverter, ac_num, ac_consume_hour, ac_power, lamp_type, lamp_num, lamp_consume_hour, lamp_power):
    power = (kulkas_num * kulkas_consume_hour * kulkas_power) + (ac_num * ac_consume_hour * ac_power) + (lamp_num * lamp_consume_hour * lamp_power)
    return (power*30) / 1000

def predict_price(daya_listrik, kulkas_inverter, kulkas_num, kulkas_consume_hour, kulkas_power, ac_inverter, ac_num, ac_consume_hour, ac_power, lamp_type, lamp_num, lamp_consume_hour, lamp_power):
    power_kwh = predict_kwh(daya_listrik, kulkas_inverter, kulkas_num, kulkas_consume_hour, kulkas_power, ac_inverter, ac_num, ac_consume_hour, ac_power, lamp_type, lamp_num, lamp_consume_hour, lamp_power)

    if (daya_listrik == 450):
        power_kwh *= 415
    elif (daya_listrik == 900):
        power_kwh *= 1352
    elif (daya_listrik == 1300):
        power_kwh *= 1444
    elif (daya_listrik == 2200):
        power_kwh *= 1444
    else:
        power_kwh *= 1699
    
    return power_kwh

def predict_co2(daya_listrik, kulkas_inverter, kulkas_num, kulkas_consume_hour, kulkas_power, ac_inverter, ac_num, ac_consume_hour, ac_power, lamp_type, lamp_num, lamp_consume_hour, lamp_power):
    electric_carbon = predict_kwh(daya_listrik, kulkas_inverter, kulkas_num, kulkas_consume_hour, kulkas_power, ac_inverter, ac_num, ac_consume_hour, ac_power, lamp_type, lamp_num, lamp_consume_hour, lamp_power) * 0.0094

    carbon_ac_non_inverter= 0.10396
    carbon_kulkas_inverter= 0.06500
    carbon_kulkas_non_inverter= 0.06600
    
    lamp_carbon = lamp_consume_hour * lamp_num
    if (lamp_type=="pijar"):
        lamp_carbon *= 0.02150
    elif(lamp_type =="neon"):
        lamp_carbon*=0.00540
    else:
        lamp_carbon*=0.00240

    ac_carbon = ac_num * ac_consume_hour
    if ac_inverter == "belum":
        ac_carbon *= carbon_ac_non_inverter

    kulkas_carbon = (kulkas_num / 24) * kulkas_consume_hour
    if kulkas_inverter == "sudah":
        kulkas_carbon *= carbon_kulkas_inverter
    else:
        kulkas_carbon *= carbon_kulkas_non_inverter

    carbon = electric_carbon + lamp_carbon + ac_carbon + kulkas_carbon
    carbon *= 1000
    rounded_carbon_percentage = round((carbon / 12), 2)
    return rounded_carbon_percentage

def prepare_recommendation(df_cluster, target_cluster, df_test, df_valid):
    target_optimasi = df_cluster[target_cluster-1]
    target_optimasi = target_optimasi[target_optimasi.index.isin(output.index)]
    df_rec = df_test
    df_rec.loc[0, target_optimasi.index] = target_optimasi
    df_rec = df_rec.drop(['kwh_per_month', 'price_per_month', 'co2_per_month'], axis=1)
    data_dict = df_rec.to_dict('records')[0]
    valid_rec = df_valid.drop(['kwh_per_month', 'price_per_month', 'co2_per_month'], axis=1)
    valid_dict = valid_rec.to_dict('records')[0]
    return data_dict, valid_dict

def decrease_percent_co2(data_dict, valid_dict):
    cf1 = predict_co2(**data_dict)
    cf2 = predict_co2(**valid_dict)
    decrease_percent = 100 - ((cf1/cf2)*100)
    return decrease_percent

def decrease_total_co2(data_dict, valid_dict):
    cf1 = predict_co2(**data_dict)
    cf2 = predict_co2(**valid_dict)
    decrease_total = (cf1/cf2)
    return decrease_total

def decrease_percent_kwh(data_dict, valid_dict):
    cf1 = predict_kwh(**data_dict)
    cf2 = predict_kwh(**valid_dict)
    decrease_percent = 100 - ((cf1/cf2)*100)
    return decrease_percent

def decrease_total_kwh(data_dict, valid_dict):
    cf1 = predict_kwh(**data_dict)
    cf2 = predict_kwh(**valid_dict)
    decrease_total = (cf1/cf2)
    return decrease_total

def decrease_percent_price(data_dict, valid_dict):
    cf1 = predict_price(**data_dict)
    cf2 = predict_price(**valid_dict)
    decrease_percent = 100 - ((cf1/cf2)*100)
    return decrease_percent

def decrease_total_price(data_dict, valid_dict):
    cf1 = predict_price(**data_dict)
    cf2 = predict_price(**valid_dict)
    decrease_total = 100 - ((cf1/cf2)*100)
    return decrease_total