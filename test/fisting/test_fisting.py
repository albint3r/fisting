import pytest
from finsting.finsting import Fisting
import numpy as np
import pandas as pd
import numpy_financial as npf

price = 5000000
plazo = 5
enganche = price * 0.10
renta = (price * 0.05) / 12
plusvalia = 0.05


class TestFisting(object):

    def test_renta_proyectada(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        actual = cf.renta_proyectada()
        expected = 23023.463541666664
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_create_finance_df_len(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        actual = len(cf.create_finance_df())
        expected = 60
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_create_finance_df_pago(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        df = cf.create_finance_df()
        actual = np.round(df.pago.sum())
        expected = np.round(df.capital.sum() + df.interes.sum())
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_create_finance_df_capital(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        df = cf.create_finance_df()
        actual = np.round(df.capital.sum())
        expected = (price - enganche) * -1
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_create_finance_df_interes(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        df = cf.create_finance_df()
        new_serie = pd.Series((price - enganche)).append(df.pago)
        actual = npf.irr(new_serie.round())
        expected = 0.008124963573300725
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_add_cum_capital_saldo(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        actual = cf.add_cum_capital().saldo.iloc[-1]
        expected = 0
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_add_cum_capital_capital_acumulado(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        actual = cf.add_cum_capital().capital_acumulado.iloc[-1]
        expected = (price - enganche) * -1
        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_get_VPN(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        cf.add_cum_capital()
        actual = cf.get_VPN()
        expected = -128397.61085366504

        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_get_VPN(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        cf.add_cum_capital()
        actual = cf.get_VPN()
        expected = -128397.61085366504

        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_get_TIR(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        cf.add_cum_capital()
        actual = cf.get_TIR()
        expected = 9.62

        msg = f'Se esperaba {expected}, pero se obtuvo {actual}'
        assert actual == expected, msg

    def test_valuate_invest(self):
        cf = Fisting(price, plazo, renta, enganche, plusvalia)
        cf.renta_proyectada()
        cf.set_capital()
        cf.create_finance_df()
        cf.add_cum_capital()
        cf.get_TIR()
        cf.get_VPN()
        actual = cf.valuate_invest()

        msg = f'Se esperaba {False}, pero se obtuvo {actual}'
        assert not actual, msg
