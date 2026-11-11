"""Dimensional and regression checks. Run with python -m unittest ... ."""
import unittest

import numpy as np
import pandas as pd

from adrenal_refactored import transform_drugrate


def row(name='Norepinephrine (mcg/kg/min)', rate=1., **updates):
    data = dict(infusiondrugid=1, patientunitstayid=90000000, infusionoffset=0,
                drugname=name, drugrate=rate, infusionrate=300., drugamount=4.,
                volumeoffluid=250., patientweight=80.)
    data.update(updates)
    return data


def process(*rows):
    return transform_drugrate(pd.DataFrame(rows))


class DrugrateTests(unittest.TestCase):
    def test_standard_dimensions_all_yield_one(self):
        cases = [
            ('Norepinephrine (mcg/kg/min)',1), ('Dopamine (mcg/min)',80),
            ('Dobutamine (mcg/min)',80), ('Norepinephrine (mcg/min)',80),
            ('Epinepherine (mcg/min)',80), ('Epinephrine (mcg/min)',80),
            ('Dopamine (mcg/hr)',4800), ('Dopamine (mcg/kg/hr)',60),
            ('Dobutamine (mcg/kg/hr)',60), ('Norepinephrine (mcg/kg/hr)',60),
            ('Norepinephrine (mcg/hr)',4800), ('Epinephrine (mcg/hr)',4800),
            ('Levophed (mg/hr)',4.8), ('Dopamine (ml/hr)',300),
            ('Norepinephrine ()',300), ('Epinephrine (mg/hr)',4.8),
            ('Norepinephrine (mg/kg/min)',.001), ('Norepinephrine (mg/min)',.08),
        ]
        result = process(*(row(n,v) for n,v in cases))
        np.testing.assert_allclose(result.drugrate,1.)
        self.assertEqual(result.iloc[-3]['item'],'epinephrine')

    def test_confirmed_mislabels_are_not_converted_again(self):
        cases = ['Epinephrine (mg/kg/min)','dobutrex (mg/kg/min)',
                 'Dopamine (nanograms/kg/min)']
        result = process(*(row(n,1.35) for n in cases))
        np.testing.assert_allclose(result.drugrate,1.35)
        self.assertTrue(result.correction_rule.str.contains('already_target').all())

    def test_concentration_recalculation_divides_weight_once(self):
        result = process(row('Dopamine (mcg/min)',266.67))
        self.assertAlmostEqual(result.iloc[0].drugrate,1.)

    def test_patient_unit_correction_divides_weight_once(self):
        result = process(row(rate=40,patientunitstayid=460261))
        self.assertAlmostEqual(result.iloc[0].drugrate,.5)

    def test_fixed_sofa_values_do_not_get_weight_scaled(self):
        result = process(
            row('Dopamine (ml/hr)',20,infusionrate=np.nan),
            row('Norepinephrine ()',20,drugamount=np.nan),
            row(rate=20,patientunitstayid=3226596),
        )
        np.testing.assert_allclose(result.drugrate,.01)
        self.assertTrue(result.is_imputed.all())

    def test_source_unit_constant_is_converted(self):
        result = process(row('Epinephrine (mcg/min)',999,patientunitstayid=981819))
        self.assertAlmostEqual(result.iloc[0].drugrate,.1/80)
        self.assertTrue(result.iloc[0].is_imputed)

    def test_missing_and_sentinel_rules(self):
        result = process(row(rate='ERROR'),row('Epinephrine (mcg/kg/min)',999),
                         row('Norepinephrine (ml/hr)',None))
        # Third record is recoverable from pump/concentration, not filled zero.
        np.testing.assert_allclose(result.drugrate,[0,0,1])
        self.assertEqual(result.is_imputed.tolist(),[True,True,False])

    def test_zero_missing_infusion_and_invalid_weight(self):
        result = process(row('Norepinephrine (mg/min)',0,infusionrate=np.nan),
                         row('Norepinephrine (mcg/min)',160,patientweight=0))
        self.assertEqual(result.iloc[0].drugrate,0)
        self.assertTrue(pd.isna(result.iloc[1].drugrate))
        self.assertIn('nonpositive_weight',result.iloc[1].correction_rule)

    def test_exclusion_trace_and_raw_lexeme(self):
        result = process(row('Norepinephrine (mcg/min)',1000,patientunitstayid=272551),
                         row('Epinephrine (mcg/min)','50 mcg/min'))
        self.assertEqual(len(result),1)
        self.assertEqual(result.iloc[0].raw_drugrate,'50 mcg/min')
        self.assertEqual(result.iloc[0].raw_unit,'mcg/min')
        self.assertAlmostEqual(result.iloc[0].drugrate,50/80)
        self.assertIn('repair_annotated_numeric',result.iloc[0].correction_rule)


if __name__ == '__main__':
    unittest.main()
