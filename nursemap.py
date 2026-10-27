import pandas as pd

def filter_large_csv_by_stay_ids(input_file, output_file, key_col, chunksize=100_000):
    valid_ids = ['MAP (mmHg)', 'Arterial Line MAP (mmHg)', 'PA']

    reader = pd.read_csv(input_file, chunksize=chunksize)
    first_chunk = True

    total_rows_kept = 0
    for i, chunk in enumerate(reader):
        filtered_chunk = chunk[chunk[key_col].isin(valid_ids)]
        total_rows_kept += len(filtered_chunk)

        if first_chunk:
            filtered_chunk.to_csv(output_file, index=False, mode='w')
            first_chunk = False
        else:
            filtered_chunk.to_csv(output_file, index=False, mode='a', header=False)

        print(f"✔ 已处理第 {i+1} 块，保留 {len(filtered_chunk)} 行")

def process_columns_rename_time(data_file, output_file):

    df = pd.read_csv(data_file)

    df = df[["patientunitstayid", "nursingchartoffset", "nursingchartcelltypevalname", "nursingchartvalue"]]

    df.rename(columns={'patientunitstayid': 'stay_id'}, inplace=True)
    df.rename(columns={'nursingchartoffset': 'charttime'}, inplace=True)
    df.rename(columns={'nursingchartcelltypevalname': 'item'}, inplace=True)
    df.rename(columns={'nursingchartvalue': 'value'}, inplace=True)
    
    mapping = {'Value': 'MAP', 'PA Diastolic': 'DAP', 'PA Systolic': 'SAP', 'PA Mean': 'MAP'}
    df["item"] = df["item"].map(mapping).fillna(df["item"])

    base_time = pd.Timestamp("2050-01-01 00:00:00")
    df['charttime'] = (
        base_time
        + pd.to_timedelta(pd.to_numeric(df['charttime'], errors="coerce"),
                          unit="min")
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    df.to_csv(output_file, index=False)
    print(f"输出文件保存至：{output_file}")

if __name__ == "__main__":

    #filter_large_csv_by_stay_ids('../../eicu/nurseCharting.csv', './nursemap.csv', 'nursingchartcelltypevallabel')
    process_columns_rename_time('./nursemap.csv', './nursemap2.csv')