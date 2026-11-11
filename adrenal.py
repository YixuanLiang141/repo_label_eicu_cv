import pandas as pd
import numpy as np

def filter_large_csv_by_stay_ids(input_file, output_file, key_col, chunksize=100_000):
    valid_ids = [
        # Dopamine
        'Dopamine'
        , 'Dopamine ()'
        , 'DOPamine MAX 800 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)'
        , 'Dopamine (mcg/hr)'
        , 'Dopamine (mcg/kg/hr)'
        , 'dopamine (mcg/kg/min)'
        , 'Dopamine (mcg/kg/min)'
        , 'Dopamine (mcg/min)'
        , 'Dopamine (mg/hr)'
        , 'Dopamine (ml/hr)'
        , 'Dopamine (nanograms/kg/min)'
        , 'DOPamine STD 15 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)'
        , 'DOPamine STD 400 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)'
        , 'DOPamine STD 400 mg Dextrose 5% 500 ml  Premix (mcg/kg/min)'
        , 'Dopamine (Unknown)'
        # Dobutamine
        , 'Dobutamine (mcg/kg/min)'
        , 'Dobutamine (mcg/min)'
        , 'Dobutamine (ml/hr)'
        , 'Dobutamine'
        , 'dobutrex (mcg/kg/min)'
        , 'dobutrex (mg/kg/min)'
        , 'dobutrex'
        , 'Dobutamine ()'
        , 'Dobutamine (mcg/kg/hr)'
        , 'Dobutamine (units/min)'
        , 'DOBUTamine STD 500 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)'
        , 'DOBUTamine MAX 1000 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)'
        # Norepinephrine
        , 'Norepinephrine'
        , 'Norepinephrine ()'
        , 'Norepinephrine MAX 32 mg Dextrose 5% 250 ml (mcg/min)'
        , 'Norepinephrine MAX 32 mg Dextrose 5% 500 ml (mcg/min)'
        , 'Norepinephrine (mcg/hr)'
        , 'Norepinephrine (mcg/kg/hr)'
        , 'Norepinephrine (mcg/kg/min)'
        , 'Norepinephrine (mcg/min)'
        , 'Norepinephrine (mg/hr)'
        , 'Norepinephrine (mg/kg/min)'
        , 'Norepinephrine (mg/min)'
        , 'Norepinephrine (ml/hr)'
        , 'Norepinephrine STD 32 mg Dextrose 5% 282 ml (mcg/min)'
        , 'Norepinephrine STD 32 mg Dextrose 5% 500 ml (mcg/min)'
        , 'Norepinephrine STD 4 mg Dextrose 5% 250 ml (mcg/min)'
        , 'Norepinephrine STD 4 mg Dextrose 5% 500 ml (mcg/min)'
        , 'Norepinephrine STD 8 mg Dextrose 5% 250 ml (mcg/min)'
        , 'Norepinephrine STD 8 mg Dextrose 5% 500 ml (mcg/min)'
        , 'Norepinephrine (units/min)'
        , 'Norepinephrine (Unknown)'
        , 'norepinephrine Volume (ml)'
        , 'norepinephrine Volume (ml) (ml/hr)'
        , 'Levophed (mcg/kg/min)'
        , 'levophed  (mcg/min)'
        , 'levophed (mcg/min)'
        , 'Levophed (mcg/min)'
        , 'Levophed (mg/hr)'
        , 'levophed (ml/hr)'
        , 'Levophed (ml/hr)'
        , 'NSS with LEVO (ml/hr)'
        , 'NSS w/ levo/vaso (ml/hr)'
        # Epinephrine
        , 'EPI (mcg/min)'
        , 'Epinepherine (mcg/min)'
        , 'Epinephrine'
        , 'Epinephrine ()'
        , 'EPINEPHrine(Adrenalin)MAX 30 mg Sodium Chloride 0.9% 250 ml (mcg/min)'
        , 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 250 ml (mcg/min)'
        , 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 500 ml (mcg/min)'
        , 'EPINEPHrine(Adrenalin)STD 7 mg Sodium Chloride 0.9% 250 ml (mcg/min)'
        , 'Epinephrine (mcg/hr)'
        , 'Epinephrine (mcg/kg/min)'
        , 'Epinephrine (mcg/min)'
        , 'Epinephrine (mg/hr)'
        , 'Epinephrine (mg/kg/min)'
        , 'Epinephrine (ml/hr)'
    ]

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

        print(f"Chunk {i+1} done. {len(filtered_chunk)} rows kept.")

def extract_weight(input_file, output_file):

    df = pd.read_csv(input_file)

    df = df[['patientunitstayid', 'admissionweight', 'dischargeweight', 'unitdischargeoffset', 'gender']]

    # Handle errors manually 
    mapping = {953.0: 95.3, 855.0: 85.5}
    df["admissionweight"] = df["admissionweight"].map(mapping).fillna(df["admissionweight"])
    mapping = {6814.0: 68.14, 871.0: 87.1}
    df["dischargeweight"] = df["dischargeweight"].map(mapping).fillna(df["dischargeweight"])

    mask = df['admissionweight'] <= 0
    df.loc[mask, 'admissionweight'] = pd.NA

    mask = df['dischargeweight'] <= 0
    df.loc[mask, 'dischargeweight'] = pd.NA

    df.to_csv(output_file, index=False)
    print(f"Done, result save to: {output_file}")

def fill_patientweight(infusion_csv, weight_csv, output_csv):

    df = pd.read_csv(infusion_csv)
    weight = pd.read_csv(weight_csv)

    # Sort
    df = df.sort_values(
        ['patientunitstayid', 'infusionoffset']
    ).reset_index(drop=True)

    df['patientweight'] = pd.to_numeric(
        df['patientweight'], errors='coerce'
    )
    df['infusionoffset'] = pd.to_numeric(
        df['infusionoffset'], errors='coerce'
    )

    for col in ['admissionweight', 'dischargeweight', 'unitdischargeoffset']:
        weight[col] = pd.to_numeric(weight[col], errors='coerce')

    df = df.merge(
        weight[[
            'patientunitstayid',
            'admissionweight',
            'dischargeweight',
            'unitdischargeoffset',
            'gender'
        ]],
        on='patientunitstayid',
        how='left',
        validate='many_to_one'
    )

    # Rule 1: use the nearest patientweight
    grouped = df.groupby('patientunitstayid')

    prev_weight = grouped['patientweight'].ffill()
    next_weight = grouped['patientweight'].bfill()

    valid_offset = df['infusionoffset'].where(
        df['patientweight'].notna()
    )

    prev_offset = valid_offset.groupby(
        df['patientunitstayid']
    ).ffill()

    next_offset = valid_offset.groupby(
        df['patientunitstayid']
    ).bfill()

    use_prev = (
        (df['infusionoffset'] - prev_offset)
        <= (next_offset - df['infusionoffset'])
    )

    nearest_weight = prev_weight.where(use_prev, next_weight)
    nearest_weight = nearest_weight.fillna(prev_weight)

    df['patientweight'] = df['patientweight'].fillna(nearest_weight)

    # Rule 2: use admissionweight and dischargeweight
    mask = df['patientweight'].isna()

    admission = df['admissionweight']
    discharge = df['dischargeweight']

    # Only admissionweight
    m = mask & admission.notna() & discharge.isna()
    df.loc[m, 'patientweight'] = admission[m]

    # Only dischargeweight
    m = mask & admission.isna() & discharge.notna()
    df.loc[m, 'patientweight'] = discharge[m]

    # Have both: judge by unitdischargeoffset / 2
    m = mask & admission.notna() & discharge.notna()

    use_admission = (
        df['infusionoffset'] <= df['unitdischargeoffset'] / 2
    )

    df.loc[m & use_admission, 'patientweight'] = admission
    df.loc[m & ~use_admission, 'patientweight'] = discharge

    # Rule 3: all missing, use median
    mask = df['patientweight'].isna()

    df.loc[mask & (df['gender'] == 'Male'), 'patientweight'] = 85.30
    df.loc[mask & (df['gender'] == 'Female'), 'patientweight'] = 72.50
    df['patientweight'] = df['patientweight'].fillna(78.90)

    df = df.drop(columns=[
        'admissionweight',
        'dischargeweight',
        'unitdischargeoffset',
        'gender'
    ])

    df.to_csv(output_csv, index=False)

    return df

def handle_drugrate(input_csv, output_csv):

    df = pd.read_csv(input_csv)

    # Handle nan manually
    mapping = {'30\\.br\\': 30, '50 mcg/min': 50, '50mcg/min\\.br\\': 50}
    df["drugrate"] = df["drugrate"].map(mapping).fillna(df["drugrate"])

    # Convert nan into 0
    df["drugrate"] = pd.to_numeric(df["drugrate"], errors='coerce')
    mask = (df['drugrate'].isna())
    df.loc[mask, 'drugrate'] = 0

    # Handle Epinephrine (mcg/kg/min)
    mask = (df['drugname'] == 'Epinephrine (mcg/kg/min)') & (df['drugrate'] == 999)
    df.loc[mask, 'drugrate'] = 0
    mask = (df['drugname'] == 'Epinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([445085, 2558121, 3128773, 3217452, 3232684, 3232809, 3227358])) & (df['infusionrate'] > 500)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / df.loc[mask, 'patientweight']
    mask = (df['drugname'] == 'Epinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([1783949, 1834162]))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 100
    mask = (df['drugname'] == 'Epinephrine (mcg/kg/min)') & (df['patientunitstayid'] == 3245684) & (df['infusionrate'] > 500)
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'drugrate']
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60

    # Handle outliers Epinephrine (mcg/min)
    mask = (df['drugname'] == 'Epinephrine (mcg/min)') & (df['patientunitstayid'].isin([981819, 1003162, 1052114])) & (df['drugrate'] > 0)
    df.loc[mask, 'drugrate'] = 0.1
    mask = (df['drugname'] == 'Epinephrine (mcg/min)') & (df['patientunitstayid'].isin([1070252])) & (df['drugrate'] >= 300)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 1000
    mask = (df['drugname'] == 'Epinephrine (mcg/min)') & (df['patientunitstayid'].isin([3134486])) & (df['drugrate'] >= 300)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 15

    # Handle >=5 Norepinephrine (mcg/kg/min)
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([460261, 965967, 3203687, 3245946]))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / df.loc[mask, 'patientweight']
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([965579, 1747813, 1834162, 3035238, 3061586, 3202311, 3208702, 3224156, 3238368])) & (df['drugrate'] >= 5)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / df.loc[mask, 'patientweight']
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([497354, 1603190]))
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'drugrate']
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([3216540, 3241952])) & (df['drugrate'] >= 5)
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'drugrate']
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([1744546, 3205292])) & (df['drugrate'] >= 5)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 1000
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([1811491]))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 100
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([3225607])) & (df['drugrate'] >= 5)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 100
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([3146936]))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 60 / df.loc[mask, 'patientweight']
    mask = (df['drugname'] == 'Norepinephrine (mcg/kg/min)') & (df['patientunitstayid'].isin([3226596])) & (df['drugrate'] > 0)
    df.loc[mask, 'drugrate'] = 0.01

    # Handle outlier Norepinephrine (mcg/min)
    mask = (df['drugname'] == 'Norepinephrine (mcg/min)') & (df['patientunitstayid'].isin([272551])) & (df['drugrate'] >= 300)
    df = df[~mask]
    mask = (df['drugname'] == 'Norepinephrine (mcg/min)') & (df['patientunitstayid'].isin([292154]))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 1000
    mask = (df['drugname'] == 'Norepinephrine (mcg/min)') & (df['patientunitstayid'].isin([514037])) & (df['drugrate'] >= 300)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 10
    mask = (df['drugname'] == 'Norepinephrine (mcg/min)') & (df['patientunitstayid'].isin([981819]))
    df.loc[mask, 'drugrate'] = 0.1

    # Handle Levophed (mcg/kg/min)
    mask = (df['drugname'] == 'Levophed (mcg/kg/min)')
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / df.loc[mask, 'patientweight']

    # Handle 2 Dopamine (mg/hr) manually
    mask = (df['drugname'] == 'Dopamine (mg/hr)') & (df['drugrate'] == 26.46)
    df.loc[mask, 'drugname'] = 'Dopamine (mcg/kg/min)'
    mapping = {'Dopamine (mg/hr)': 'Dopamine (ml/hr)'}
    df["drugname"] = df["drugname"].map(mapping).fillna(df["drugname"])

    # Handle Dopamine (mcg/min)
    mask = (df['drugname'] == 'Dopamine (mcg/min)') & (df['drugrate'] > 200)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / 60

    # Handle Norepinephrine (mg/hr) with other data
    mask = (df['drugname'] == 'Norepinephrine (mg/hr)') & (df['infusionrate'].notna())
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'drugrate']
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    df.loc[mask, 'drugname'] = 'Norepinephrine (mcg/kg/min)'
    # Assume those without other data are correct
    mask = (df['drugname'] == 'Norepinephrine (mg/hr)')
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] * 1000 / 60 / df.loc[mask, 'patientweight']
    df.loc[mask, 'drugname'] = 'Norepinephrine (mcg/kg/min)'

    # Handle Norepinephrine (units/min)
    mask = (df['drugname'] == 'Norepinephrine (units/min)') & (df['infusionrate'] == 7500)
    df.loc[mask, 'infusionrate'] = 7.5
    mask = (df['drugname'] == 'Norepinephrine (units/min)')
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60

    # Handle Epinephrine (mg/hr)
    mask = (df['drugname'] == 'Epinephrine (mg/hr)')
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    df.loc[mask, 'drugname'] = 'Epinephrine (mcg/kg/min)'

    # Handle Norepinephrine (mg/kg/min)
    mask = (df['drugname'] == 'Norepinephrine (mg/kg/min)') & (df['infusionrate'] > 9000)
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'infusionrate'] / 1000
    mask = (df['drugname'] == 'Norepinephrine (mg/kg/min)') & (df['infusionrate'].notna())
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    df.loc[mask, 'drugname'] = 'Norepinephrine (mcg/kg/min)'

    # Handle Norepinephrine (mg/min)
    mask = (df['drugname'] == 'Norepinephrine (mg/min)') & (df['infusionrate'] > 10000)
    df.loc[mask, 'infusionrate'] = df.loc[mask, 'infusionrate'] / 1000
    mask = (df['drugname'] == 'Norepinephrine (mg/min)') & (df['infusionrate'].notna())
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / df.loc[mask, 'patientweight'] / 60
    df.loc[mask, 'drugname'] = 'Norepinephrine (mcg/kg/min)'


    hr =    ['Dopamine (mcg/hr)',
            'Dopamine (mcg/kg/hr)',
            'Dobutamine (mcg/kg/hr)',
            'Norepinephrine (mcg/hr)',
            'Norepinephrine (mcg/kg/hr)',
            'Levophed (mg/hr)',
            'Epinephrine (mcg/hr)']
    mask = df['drugname'].isin(hr)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / 60

    mg = ['Levophed (mg/hr)']
    mask = df['drugname'].isin(mg)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] * 1000

    ml = ['Dopamine (ml/hr)', 'Dobutamine (ml/hr)', 'Norepinephrine (ml/hr)',
              'norepinephrine Volume (ml)', 'norepinephrine Volume (ml) (ml/hr)',
              'levophed (ml/hr)', 'Levophed (ml/hr)', 'NSS with LEVO (ml/hr)',
              'NSS w/ levo/vaso (ml/hr)', 'Epinephrine (ml/hr)']
    mask = ((df['drugname'].isin(ml)) & (df['infusionrate'].notna()) & (df['drugamount'].notna()) & (df['volumeoffluid'].notna()))
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / 60

    mask = ((df['drugname'].isin(ml)) & ((df['infusionrate'].isna()) | (df['drugamount'].isna()) | (df['volumeoffluid'].isna()))) & (df['drugrate'] > 0)
    df.loc[mask, 'drugrate'] = 0.01

    weight = ['Dobutamine (mcg/min)', 'Dopamine (mcg/hr)', 'EPI (mcg/min)', 'EPINEPHrine(Adrenalin)MAX 30 mg Sodium Chloride 0.9% 250 ml (mcg/min)',
              'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 250 ml (mcg/min)', 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 500 ml (mcg/min)',
              'EPINEPHrine(Adrenalin)STD 7 mg Sodium Chloride 0.9% 250 ml (mcg/min)', 'Epinephrine (mcg/hr)', 'Epinephrine (mcg/min)', 'Levophed (mcg/min)',
              'Levophed (mg/hr)', 'Norepinephrine (mcg/hr)', 'Norepinephrine (mcg/min)', 'Norepinephrine MAX 32 mg Dextrose 5% 250 ml (mcg/min)',
              'Norepinephrine MAX 32 mg Dextrose 5% 500 ml (mcg/min)', 'Norepinephrine STD 32 mg Dextrose 5% 282 ml (mcg/min)',
              'Norepinephrine STD 32 mg Dextrose 5% 500 ml (mcg/min)', 'Norepinephrine STD 4 mg Dextrose 5% 250 ml (mcg/min)',
              'Norepinephrine STD 4 mg Dextrose 5% 500 ml (mcg/min)', 'Norepinephrine STD 8 mg Dextrose 5% 250 ml (mcg/min)',
              'Norepinephrine STD 8 mg Dextrose 5% 500 ml (mcg/min)', 'levophed  (mcg/min)', 'levophed (mcg/min)', 'Dopamine (mcg/min)',
              'Epinepherine (mcg/min)']
    mask = df['drugname'].isin(weight)
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugrate'] / df.loc[mask, 'patientweight']

    mask = df['drugname'].isin(['Dobutamine', 'Dopamine', 'Epinephrine', 'Norepinephrine'])
    df.loc[mask, 'drugrate'] = 0

    mask = (df['drugname'].isin(['Dobutamine ()', 'Dopamine ()', 'Epinephrine ()', 'Norepinephrine ()'])) & (df['infusionrate'].notna()) & (df['drugamount'].notna()) & (df['volumeoffluid'].notna())
    df.loc[mask, 'drugrate'] = df.loc[mask, 'drugamount'] * 1000 / df.loc[mask, 'volumeoffluid'] * df.loc[mask, 'infusionrate'] / 60
    mask = ((df['drugname'].isin(['Dobutamine ()', 'Dopamine ()', 'Epinephrine ()', 'Norepinephrine ()'])) & ((df['infusionrate'].isna()) | (df['drugamount'].isna()) | (df['volumeoffluid'].isna()))) & (df['drugrate'] > 0)
    df.loc[mask, 'drugrate'] = 0.01

    mapping = {
                # Dopamine
                'Dopamine': 'dopamine'
                , 'Dopamine ()': 'dopamine'
                , 'DOPamine MAX 800 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine'
                , 'Dopamine (mcg/hr)': 'dopamine'
                , 'Dopamine (mcg/kg/hr)': 'dopamine'
                , 'dopamine (mcg/kg/min)': 'dopamine'
                , 'Dopamine (mcg/kg/min)': 'dopamine'
                , 'Dopamine (mcg/min)': 'dopamine'
                , 'Dopamine (mg/hr)': 'dopamine'
                , 'Dopamine (ml/hr)': 'dopamine'
                , 'Dopamine (nanograms/kg/min)': 'dopamine'
                , 'DOPamine STD 15 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine'
                , 'DOPamine STD 400 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine'
                , 'DOPamine STD 400 mg Dextrose 5% 500 ml  Premix (mcg/kg/min)': 'dopamine'
                , 'Dopamine (Unknown)': 'dopamine'
                # Dobutamine
                , 'Dobutamine (mcg/kg/min)': 'dobutamine'
                , 'Dobutamine (mcg/min)': 'dobutamine'
                , 'Dobutamine (ml/hr)': 'dobutamine'
                , 'Dobutamine': 'dobutamine'
                , 'dobutrex (mcg/kg/min)': 'dobutamine'
                , 'dobutrex (mg/kg/min)': 'dobutamine'
                , 'dobutrex': 'dobutamine'
                , 'Dobutamine ()': 'dobutamine'
                , 'Dobutamine (mcg/kg/hr)': 'dobutamine'
                , 'Dobutamine (units/min)': 'dobutamine'
                , 'DOBUTamine STD 500 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dobutamine'
                , 'DOBUTamine MAX 1000 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dobutamine'
                # Norepinephrine
                , 'Norepinephrine': 'norepinephrine'
                , 'Norepinephrine ()': 'norepinephrine'
                , 'Norepinephrine MAX 32 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine MAX 32 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine (mcg/hr)': 'norepinephrine'
                , 'Norepinephrine (mcg/kg/hr)': 'norepinephrine'
                , 'Norepinephrine (mcg/kg/min)': 'norepinephrine'
                , 'Norepinephrine (mcg/min)': 'norepinephrine'
                , 'Norepinephrine (mg/hr)': 'norepinephrine'
                , 'Norepinephrine (mg/kg/min)': 'norepinephrine'
                , 'Norepinephrine (mg/min)': 'norepinephrine'
                , 'Norepinephrine (ml/hr)': 'norepinephrine'
                , 'Norepinephrine STD 32 mg Dextrose 5% 282 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine STD 32 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine STD 4 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine STD 4 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine STD 8 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine STD 8 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine'
                , 'Norepinephrine (units/min)': 'norepinephrine'
                , 'Norepinephrine (Unknown)': 'norepinephrine'
                , 'norepinephrine Volume (ml)': 'norepinephrine'
                , 'norepinephrine Volume (ml) (ml/hr)': 'norepinephrine'
                , 'Levophed (mcg/kg/min)': 'norepinephrine'
                , 'levophed  (mcg/min)': 'norepinephrine'
                , 'levophed (mcg/min)': 'norepinephrine'
                , 'Levophed (mcg/min)': 'norepinephrine'
                , 'Levophed (mg/hr)': 'norepinephrine'
                , 'levophed (ml/hr)': 'norepinephrine'
                , 'Levophed (ml/hr)': 'norepinephrine'
                , 'NSS with LEVO (ml/hr)': 'norepinephrine'
                , 'NSS w/ levo/vaso (ml/hr)': 'norepinephrine'
                # Epinephrine
                , 'EPI (mcg/min)': 'epinephrine'
                , 'Epinepherine (mcg/min)': 'epinephrine'
                , 'Epinephrine': 'epinephrine'
                , 'Epinephrine ()': 'epinephrine'
                , 'EPINEPHrine(Adrenalin)MAX 30 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine'
                , 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine'
                , 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 500 ml (mcg/min)': 'epinephrine'
                , 'EPINEPHrine(Adrenalin)STD 7 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine'
                , 'Epinephrine (mcg/hr)': 'epinephrine'
                , 'Epinephrine (mcg/kg/min)': 'epinephrine'
                , 'Epinephrine (mcg/min)': 'epinephrine'
                , 'Epinephrine (mg/hr)': 'epinephrine'
                , 'Epinephrine (mg/kg/min)': 'epinephrine'
                , 'Epinephrine (ml/hr)': 'epinephrine'
        }
    df["drugname"] = df["drugname"].map(mapping).fillna(df["drugname"])
    
    df = df[['patientunitstayid','infusionoffset','drugname','drugrate','patientweight']]
    df.rename(columns={'patientunitstayid': 'subject_id'}, inplace=True)
    df.rename(columns={'drugname': 'item'}, inplace=True)
    df.rename(columns={'infusionoffset': 'charttime'}, inplace=True)
    df.rename(columns={'patientweight': 'weight'}, inplace=True)

    base_time = pd.Timestamp("2050-01-01 00:00:00")
    df['charttime'] = (
        base_time
        + pd.to_timedelta(pd.to_numeric(df['charttime'], errors="coerce"),
                          unit="min")
    ).dt.strftime("%Y-%m-%d %H:%M:%S")

    df.to_csv(output_csv, index=False)
    print(f"Done, result save to: {output_csv}")

if __name__ == "__main__":

    #filter_large_csv_by_stay_ids('../../eicu/infusionDrug.csv', './adrenal.csv', 'drugname')
    #extract_weight('../../eicu/patient.csv', './weight.csv')
    #fill_patientweight('./adrenal.csv', './weight.csv', './adrenal.csv')
    handle_drugrate('./adrenal.csv', './adrenal2.csv')