"""Normalize the existing adrenal rules to mcg/kg/min with an audit trail.

Stages: parse -> source corrections -> unit conversion -> imputation -> naming.
Patient-specific rules and SOFA-oriented fixed values are retained by request;
they are data-processing assumptions, not inferred or confirmed dose corrections.
The three known mislabeled mg/ng groups are explicitly already mcg/kg/min.
Never feed this script's normalized output back as a raw infusion input.
"""
from pathlib import Path
import argparse
import re

import numpy as np
import pandas as pd

TARGET_UNIT = 'mcg/kg/min'
DRUG_NAMES = {'Dopamine': 'dopamine',
 'Dopamine ()': 'dopamine',
 'DOPamine MAX 800 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine',
 'Dopamine (mcg/hr)': 'dopamine',
 'Dopamine (mcg/kg/hr)': 'dopamine',
 'dopamine (mcg/kg/min)': 'dopamine',
 'Dopamine (mcg/kg/min)': 'dopamine',
 'Dopamine (mcg/min)': 'dopamine',
 'Dopamine (mg/hr)': 'dopamine',
 'Dopamine (ml/hr)': 'dopamine',
 'Dopamine (nanograms/kg/min)': 'dopamine',
 'DOPamine STD 15 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine',
 'DOPamine STD 400 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dopamine',
 'DOPamine STD 400 mg Dextrose 5% 500 ml  Premix (mcg/kg/min)': 'dopamine',
 'Dopamine (Unknown)': 'dopamine',
 'Dobutamine (mcg/kg/min)': 'dobutamine',
 'Dobutamine (mcg/min)': 'dobutamine',
 'Dobutamine (ml/hr)': 'dobutamine',
 'Dobutamine': 'dobutamine',
 'dobutrex (mcg/kg/min)': 'dobutamine',
 'dobutrex (mg/kg/min)': 'dobutamine',
 'dobutrex': 'dobutamine',
 'Dobutamine ()': 'dobutamine',
 'Dobutamine (mcg/kg/hr)': 'dobutamine',
 'Dobutamine (units/min)': 'dobutamine',
 'DOBUTamine STD 500 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dobutamine',
 'DOBUTamine MAX 1000 mg Dextrose 5% 250 ml  Premix (mcg/kg/min)': 'dobutamine',
 'Norepinephrine': 'norepinephrine',
 'Norepinephrine ()': 'norepinephrine',
 'Norepinephrine MAX 32 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine MAX 32 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine (mcg/hr)': 'norepinephrine',
 'Norepinephrine (mcg/kg/hr)': 'norepinephrine',
 'Norepinephrine (mcg/kg/min)': 'norepinephrine',
 'Norepinephrine (mcg/min)': 'norepinephrine',
 'Norepinephrine (mg/hr)': 'norepinephrine',
 'Norepinephrine (mg/kg/min)': 'norepinephrine',
 'Norepinephrine (mg/min)': 'norepinephrine',
 'Norepinephrine (ml/hr)': 'norepinephrine',
 'Norepinephrine STD 32 mg Dextrose 5% 282 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine STD 32 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine STD 4 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine STD 4 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine STD 8 mg Dextrose 5% 250 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine STD 8 mg Dextrose 5% 500 ml (mcg/min)': 'norepinephrine',
 'Norepinephrine (units/min)': 'norepinephrine',
 'Norepinephrine (Unknown)': 'norepinephrine',
 'norepinephrine Volume (ml)': 'norepinephrine',
 'norepinephrine Volume (ml) (ml/hr)': 'norepinephrine',
 'Levophed (mcg/kg/min)': 'norepinephrine',
 'levophed  (mcg/min)': 'norepinephrine',
 'levophed (mcg/min)': 'norepinephrine',
 'Levophed (mcg/min)': 'norepinephrine',
 'Levophed (mg/hr)': 'norepinephrine',
 'levophed (ml/hr)': 'norepinephrine',
 'Levophed (ml/hr)': 'norepinephrine',
 'NSS with LEVO (ml/hr)': 'norepinephrine',
 'NSS w/ levo/vaso (ml/hr)': 'norepinephrine',
 'EPI (mcg/min)': 'epinephrine',
 'Epinepherine (mcg/min)': 'epinephrine',
 'Epinephrine': 'epinephrine',
 'Epinephrine ()': 'epinephrine',
 'EPINEPHrine(Adrenalin)MAX 30 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine',
 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine',
 'EPINEPHrine(Adrenalin)STD 4 mg Sodium Chloride 0.9% 500 ml (mcg/min)': 'epinephrine',
 'EPINEPHrine(Adrenalin)STD 7 mg Sodium Chloride 0.9% 250 ml (mcg/min)': 'epinephrine',
 'Epinephrine (mcg/hr)': 'epinephrine',
 'Epinephrine (mcg/kg/min)': 'epinephrine',
 'Epinephrine (mcg/min)': 'epinephrine',
 'Epinephrine (mg/hr)': 'epinephrine',
 'Epinephrine (mg/kg/min)': 'epinephrine',
 'Epinephrine (ml/hr)': 'epinephrine'}
TEXT_REPAIRS = {'30\\.br\\': 30, '50 mcg/min': 50, '50mcg/min\\.br\\': 50}
VOLUME_NAMES = {
    'Dopamine (ml/hr)', 'Dobutamine (ml/hr)', 'Norepinephrine (ml/hr)',
    'norepinephrine Volume (ml)', 'norepinephrine Volume (ml) (ml/hr)',
    'levophed (ml/hr)', 'Levophed (ml/hr)', 'NSS with LEVO (ml/hr)',
    'NSS w/ levo/vaso (ml/hr)', 'Epinephrine (ml/hr)',
}
EMPTY_NAMES = {'Dobutamine ()', 'Dopamine ()', 'Epinephrine ()', 'Norepinephrine ()'}
BARE_NAMES = {'Dobutamine', 'Dopamine', 'Epinephrine', 'Norepinephrine'}


def _note(df, mask, rule):
    """Append every applied rule, including rules whose numeric effect is zero."""
    mask = mask.fillna(False)
    old = df.loc[mask, 'correction_rule']
    df.loc[mask, 'correction_rule'] = old.where(old.eq(''), old + ';') + rule


def _mask(df, name, ids=None, minimum=None, positive=False):
    mask = df.drugname.eq(name)
    if ids is not None:
        mask &= df.patientunitstayid.isin(ids)
    if minimum is not None:
        mask &= df['_rate'].ge(minimum)
    if positive:
        mask &= df['_rate'].gt(0)
    return mask.fillna(False)


def _source_unit(df, mask, unit, rule):
    df.loc[mask, '_unit'] = unit
    _note(df, mask, rule)


def _scale(df, mask, divisor, rule):
    df.loc[mask, '_rate'] /= divisor
    _note(df, mask, rule)


def _fill_later(df, mask, value, unit, rule):
    df.loc[mask, '_fill_value'] = value
    df.loc[mask, '_fill_unit'] = unit
    _note(df, mask, rule)


def _from_infusion(df, mask, rule, rate_is_pump=False):
    if rate_is_pump:
        # The old parser used zero for a missing source rate before this rule.
        df.loc[mask, '_pump'] = df.loc[mask, '_rate'].fillna(0)
    df.loc[mask, '_mode'] = 'infusion'
    _note(df, mask, rule)


def parse_input(frame):
    df = frame.copy()
    required = {
        'patientunitstayid', 'infusionoffset', 'drugname', 'drugrate',
        'infusionrate', 'drugamount', 'volumeoffluid', 'patientweight',
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f'Missing raw input columns: {sorted(missing)}')
    df['raw_drugrate'] = df.drugrate.copy()
    df['raw_unit'] = df.drugname.str.extract(r'\(([^()]*)\)\s*$', expand=False).fillna('')
    df['raw_unit'] = df.raw_unit.replace('', 'unknown')
    df['correction_rule'] = ''
    df['is_imputed'] = False
    repaired = df.drugrate.map(TEXT_REPAIRS).fillna(df.drugrate)
    _note(df, df.drugrate.isin(TEXT_REPAIRS), 'parse:repair_annotated_numeric')
    df['_rate'] = pd.to_numeric(repaired, errors='coerce')
    df['_parse_missing'] = df['_rate'].isna()
    for col in ('infusionrate', 'drugamount', 'volumeoffluid', 'patientweight', 'infusionoffset'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df['_pump'] = df.infusionrate
    df['_unit'] = df.raw_unit
    df['_mode'] = 'rate'
    df['_fill_value'] = np.nan
    df['_fill_unit'] = TARGET_UNIT
    return df


def correct_sources(df):
    """Correct source interpretations; defer dimensional conversion and fills."""
    epi = 'Epinephrine (mcg/kg/min)'
    nor = 'Norepinephrine (mcg/kg/min)'
    nmin = 'Norepinephrine (mcg/min)'
    mask = _mask(df, epi) & df['_rate'].eq(999)
    _fill_later(df, mask, 0, TARGET_UNIT, 'override:epinephrine_999_to_zero')
    # Set the sentinel's working value to zero so later >0 masks retain ordering.
    df.loc[mask, '_rate'] = 0
    mask = _mask(df, epi, [445085,2558121,3128773,3217452,3232684,3232809,3227358]) & df.infusionrate.gt(500)
    _source_unit(df, mask, 'mcg/min', 'source:epinephrine_patient_actual_mcg_min')
    _scale(df, _mask(df, epi, [1783949,1834162]), 100, 'correct:epinephrine_patient_divide_100')
    mask = _mask(df, epi, [3245684]) & df.infusionrate.gt(500)
    _from_infusion(df, mask, 'source:epinephrine_patient_rate_is_ml_hr', rate_is_pump=True)

    # Corrected mcg/min selectors. 0.1 here retains the old source-unit constant,
    # unlike the explicit final-target 0.01 SOFA-oriented fills below.
    emin = 'Epinephrine (mcg/min)'
    _fill_later(df, _mask(df, emin, [981819,1003162,1052114], positive=True),
                0.1, 'mcg/min', 'override:epinephrine_patient_source_rate_0.1')
    _scale(df, _mask(df, emin, [1070252], minimum=300), 1000, 'correct:epinephrine_patient_divide_1000')
    _scale(df, _mask(df, emin, [3134486], minimum=300), 15, 'correct:epinephrine_patient_divide_15')

    _source_unit(df, _mask(df, nor, [460261,965967,3203687,3245946]), 'mcg/min', 'source:norepinephrine_entire_patient_actual_mcg_min')
    _source_unit(df, _mask(df, nor, [965579,1747813,1834162,3035238,3061586,3202311,3208702,3224156,3238368], minimum=5), 'mcg/min', 'source:norepinephrine_high_actual_mcg_min')
    _from_infusion(df, _mask(df, nor, [497354,1603190]), 'source:norepinephrine_entire_patient_rate_is_ml_hr', rate_is_pump=True)
    _from_infusion(df, _mask(df, nor, [3216540,3241952], minimum=5), 'source:norepinephrine_high_rate_is_ml_hr', rate_is_pump=True)
    _scale(df, _mask(df, nor, [1744546,3205292], minimum=5), 1000, 'correct:norepinephrine_patient_divide_1000')
    _scale(df, _mask(df, nor, [1811491]), 100, 'correct:norepinephrine_entire_patient_divide_100')
    _scale(df, _mask(df, nor, [3225607], minimum=5), 100, 'correct:norepinephrine_high_divide_100')
    _source_unit(df, _mask(df, nor, [3146936]), 'mcg/hr', 'source:norepinephrine_patient_actual_mcg_hr')
    _fill_later(df, _mask(df, nor, [3226596], positive=True), 0.01, TARGET_UNIT, 'impute:norepinephrine_patient_sofa_0.01')

    mask = _mask(df, nmin, [272551], minimum=300)
    df = df.loc[~mask].copy()  # Retain the existing exclusion rule.
    _scale(df, _mask(df, nmin, [292154]), 1000, 'correct:norepinephrine_mcg_min_divide_1000')
    _scale(df, _mask(df, nmin, [514037], minimum=300), 10, 'correct:norepinephrine_mcg_min_divide_10')
    _fill_later(df, _mask(df, nmin, [981819]), 0.1, 'mcg/min', 'override:norepinephrine_patient_source_rate_0.1')
    _source_unit(df, _mask(df, 'Levophed (mcg/kg/min)'), 'mcg/min', 'source:levophed_actual_mcg_min')

    mask = _mask(df, 'Dopamine (mg/hr)') & df['_rate'].eq(26.46)
    _source_unit(df, mask, TARGET_UNIT, 'source:dopamine_26.46_already_target')
    mask = _mask(df, 'Dopamine (mg/hr)') & ~df['_rate'].eq(26.46)
    _source_unit(df, mask, 'ml/hr', 'source:dopamine_remaining_mg_hr_actual_ml_hr')
    mask = _mask(df, 'Dopamine (mcg/min)') & df['_rate'].gt(200)
    _from_infusion(df, mask, 'source:dopamine_high_use_infusion')

    mask = _mask(df, 'Norepinephrine (mg/hr)') & df.infusionrate.notna()
    _from_infusion(df, mask, 'source:norepinephrine_mg_hr_rate_is_ml_hr', rate_is_pump=True)
    mask = _mask(df, 'Norepinephrine (units/min)') & df.infusionrate.eq(7500)
    df.loc[mask, '_pump'] = 7.5
    _note(df, mask, 'correct:norepinephrine_units_min_pump_7500_to_7.5')
    _from_infusion(df, _mask(df, 'Norepinephrine (units/min)'), 'source:norepinephrine_units_min_use_infusion')
    # Drug identity is retained as epinephrine throughout.
    _from_infusion(df, _mask(df, 'Epinephrine (mg/hr)'), 'source:epinephrine_mg_hr_use_infusion')

    for name, limit in [('Norepinephrine (mg/kg/min)',9000), ('Norepinephrine (mg/min)',10000)]:
        mask = _mask(df, name) & df.infusionrate.gt(limit)
        df.loc[mask, '_pump'] /= 1000
        _note(df, mask, f'correct:{name}_pump_divide_1000')
        _from_infusion(df, _mask(df, name) & df.infusionrate.notna(), f'source:{name}_use_infusion')

    # Confirmed source-label corrections: deliberately NO mass-unit scaling.
    for name in ('Epinephrine (mg/kg/min)', 'dobutrex (mg/kg/min)', 'Dopamine (nanograms/kg/min)'):
        _source_unit(df, _mask(df, name), TARGET_UNIT, 'source:mislabeled_mass_unit_already_target')
    return df


def _normalize_rate(values, units, weight):
    result = pd.Series(np.nan, index=values.index, dtype=float)
    weight = weight.where(weight.gt(0))
    factors = {
        TARGET_UNIT: 1., 'mcg/min': 1/weight, 'mcg/hr': 1/60/weight,
        'mcg/kg/hr': 1/60, 'mg/hr': 1000/60/weight,
        'mg/min': 1000/weight, 'mg/kg/min': 1000.,
        'nanograms/kg/min': 1/1000,
    }
    for unit, factor in factors.items():
        mask = units.eq(unit)
        result.loc[mask] = values.loc[mask] * (factor.loc[mask] if isinstance(factor,pd.Series) else factor)
    # A documented zero remains zero even when the source unit is unknown.
    result.loc[values.eq(0)] = 0.
    return result


def convert_units(df):
    complete = df[['infusionrate','drugamount','volumeoffluid']].notna().all(axis=1)
    generic_volume = df.drugname.isin(VOLUME_NAMES) | (
        df.drugname.eq('Dopamine (mg/hr)') & df['_unit'].eq('ml/hr'))
    generic_empty = df.drugname.isin(EMPTY_NAMES)
    generic = generic_volume | generic_empty
    use_pump = generic & complete
    _from_infusion(df, use_pump, 'convert:generic_concentration_and_pump')
    # Fill values are final mcg/kg/min, so they must NOT be divided by weight.
    _fill_later(df, generic & ~complete & df['_rate'].gt(0), 0.01, TARGET_UNIT,
                'impute:incomplete_volume_or_unknown_unit_sofa_0.01')
    _fill_later(df, df.drugname.isin(BARE_NAMES), 0, TARGET_UNIT, 'impute:bare_drugname_zero')

    df['_normalized'] = _normalize_rate(df['_rate'], df['_unit'], df.patientweight)
    mask = df['_mode'].eq('rate') & ~generic & ~df.drugname.isin(BARE_NAMES)
    _note(df, mask, 'convert:effective_unit_to_mcg_kg_min')
    mask = df['_mode'].eq('infusion')
    volume = df.volumeoffluid.where(df.volumeoffluid.gt(0))
    weight = df.patientweight.where(df.patientweight.gt(0))
    df.loc[mask, '_normalized'] = (
        df.drugamount * 1000 / volume * df['_pump'] / 60 / weight
    ).loc[mask]
    _note(df, mask, 'convert:mg_per_ml_times_ml_hr_divide_60_weight')
    df['_normalized_fill'] = _normalize_rate(df['_fill_value'], df['_fill_unit'], df.patientweight)
    mask = (df.patientweight.isna() | df.patientweight.le(0)) & df['_normalized'].isna() & df['_rate'].gt(0) & df['_fill_value'].isna()
    _note(df, mask, 'convert:missing_or_nonpositive_weight_result_missing')
    return df


def impute_rates(df):
    # Defer the old initial missing->zero policy until after conversion. Do not
    # erase a valid value recovered from concentration and infusionrate.
    mask = df['_parse_missing'] & df['_mode'].eq('rate') & df['_normalized'].isna()
    df.loc[mask, '_normalized'] = 0
    df.loc[mask, 'is_imputed'] = True
    _note(df, mask, 'impute:missing_or_nonnumeric_source_zero')
    mask = df['_fill_value'].notna()
    df.loc[mask, '_normalized'] = df.loc[mask, '_normalized_fill']
    df.loc[mask, 'is_imputed'] = True
    df['drugrate'] = df['_normalized']
    return df


def finalize_output(df):
    unknown = sorted(set(df.drugname) - set(DRUG_NAMES))
    if unknown:
        raise ValueError(f'Unmapped raw drug names: {unknown}')
    df['drugname'] = df.drugname.map(DRUG_NAMES)
    df['infusionoffset'] = (
        pd.Timestamp('2050-01-01') + pd.to_timedelta(df.infusionoffset, unit='min')
    ).dt.strftime('%Y-%m-%d %H:%M:%S')
    output = df[[
        'patientunitstayid','infusionoffset','drugname','drugrate','patientweight',
        'raw_drugrate','raw_unit','correction_rule','is_imputed',
    ]].rename(columns={
        'patientunitstayid':'subject_id','infusionoffset':'charttime',
        'drugname':'item','patientweight':'weight',
    })
    return output


def transform_drugrate(frame):
    """Pure DataFrame entry point for checking rules without writing files."""
    df = parse_input(frame)
    df = correct_sources(df)
    df = convert_units(df)
    df = impute_rates(df)
    return finalize_output(df)


def handle_drugrate(input_csv, output_csv):
    if Path(input_csv).resolve() == Path(output_csv).resolve():
        raise ValueError('Use a separate output file to preserve the raw input.')
    df = pd.read_csv(input_csv, dtype={'drugrate':'string'}, low_memory=False)
    result = transform_drugrate(df)
    result.to_csv(output_csv,index=False,encoding='utf-8-sig')
    print(f'Saved {len(result)} records to {output_csv}')
    return result


if __name__ == '__main__':
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_csv', nargs='?', type=Path, default=folder/'adrenal.csv')
    parser.add_argument('output_csv', nargs='?', type=Path, default=folder/'adrenal_processed.csv')
    args = parser.parse_args()
    handle_drugrate(args.input_csv, args.output_csv)
