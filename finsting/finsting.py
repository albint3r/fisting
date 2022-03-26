from dataclasses import dataclass, field
import datetime as dt
from pandas import DataFrame
# maths
import pandas as pd
import numpy as np
import numpy_financial as npf


@dataclass
class Fisting:
    # Globla Variables
    MESES = 12
    TASA_INTERES = 0.0975
    TASA_DESCUENTO = 0.1075

    # __init__
    start_date: dt = field(init=False, default_factory=dt.date.today)
    listing_price: int = field(init=True)
    plazo: int = field(init=True)
    capital: float = field(init=False, default=None)
    renta: float = field(init=True)
    enganche: float = field(init=True)
    plusvalia: float = field(init=True)
    finiquito: float = field(init=False, default=None)
    tir: float = field(init=False, default=None)
    vpn: float = field(init=False, default=None)
    cap: float = field(init=False, default=None)
    resumen_pago: str = field(init=False, default=None)
    dfs: dict[str:DataFrame] = field(init=False, default_factory=dict)

    def renta_proyectada(self) -> float:
        """Genera una corrida del aumento de la renta a lo largo de los periodos del credito y lo promedia
        para obtener un valor que considere el aumento del precio a lo largo del tiempo para la tir y el VPN"""

        periodos = {'periodo': np.arange(0, self.plazo + 1)}
        df = pd.DataFrame(periodos)
        # Agrega renta a todas las columnas para operacion
        df['rent'] = self.renta
        # En caso de tener plusvalia Cero o Negativa, se le aplicara 0
        if self.plusvalia > 0:
            df.loc[1:, 'rent'] = df.loc[1:, 'rent'] * (1 + self.plusvalia) ** df.loc[1:, 'periodo']
        else:
            df.loc[1:, 'rent'] = df.loc[1:, 'rent'] * (1 + 0) ** df.loc[1:, 'periodo']
        # Genera la nueva renta proyectada y la asigna
        self.renta = df.iloc[:-1, 1].mean()
        return self.renta

    def set_capital(self) -> float:
        self.capital = self.listing_price - self.enganche
        return self.capital

    def create_finance_df(self):
        # Nombre de columnas tabla
        columnas = ['pago', 'capital', 'interes', 'saldo', 'flujo_renta', 'flujo_efectivo']
        # Crea Periodos de pago del credito
        fechas_pago = pd.date_range(self.start_date, periods=self.plazo * self.MESES, freq='MS')
        # Crea la tabla con los periodos y las columnas.
        df = pd.DataFrame(index=fechas_pago, columns=columnas, dtype='float16').reset_index() \
            .rename(columns={'index': 'periodo'})
        # El index comienza desde 1 para calcular los periodos
        df.index += 1

        tasa_mensaulizada = self.TASA_INTERES / self.MESES
        n_periodos = self.plazo * self.MESES

        df = df.assign(
            capital=npf.ppmt(tasa_mensaulizada, df.index, n_periodos, self.capital),
            interes=npf.ipmt(tasa_mensaulizada, df.index, n_periodos, self.capital),
            flujo_renta=self.renta,
            pago=npf.pmt(tasa_mensaulizada, n_periodos, self.capital)
        )

        df = df.assign(flujo_efectivo=df.pago + df.flujo_renta, )

        self.dfs['flujos_descontados'] = df
        return self.dfs['flujos_descontados']

    def add_cum_capital(self):
        """Agrega El capital acumulado al DataFrame del Flujo de Efectivo"""

        df = self.dfs['flujos_descontados']
        # AGREGA LA COLUMNA DE CAPITAL ACUMULADO Y DA LA INSTRUCCIÓN DE CORTAR LA TABLA AL LIQUIDAR EL CAPITAL....EN 3 PASOS
        # PASO 1.- Crea la columna de abonos a Capital acumulado y nunca excedan el monto de Capital inicial
        df["capital_acumulado"] = (df["capital"]).cumsum()
        df["capital_acumulado"] = df["capital_acumulado"].clip(lower=-self.capital)

        # PASO 2.- Calcula el saldo para cada periodo
        df["saldo"] = self.capital + df["capital_acumulado"]

        # PASO 3.- Determine la última fecha de pago
        try:
            self.finiquito = df.query("saldo <= 0")["saldo"].idxmax(axis=1, skipna=True)
        except ValueError:
            self.finiquito = df.last_valid_index()

        # CREACIÓN DE TABLAS RESUMEN DE PAGO....en 3 pasos

        # PASO 1.- Crea un DataFrame con la información del escenario transpuesto
        informacion_del_flujo = df[["pago", "capital", "interes"]].sum().to_frame().T

        # PASO 2.- Da formato de fecha al DataFrame
        detalles_de_pago = pd.DataFrame.from_dict(
            dict([('mensualidades', [self.finiquito]), ('interes', [self.TASA_INTERES]),
                  ('mumero de años', [self.plazo])]))

        # PASO3.- Concatena los resultados
        self.resumen_de_pago = pd.concat([detalles_de_pago, informacion_del_flujo], axis=1)

        return df

    def get_VPN(self):
        """Genera el VPN del inmueble """
        df = self.dfs['flujos_descontados']
        # Obtener Obtener Valor Futuro del inmueble comprado
        enganche_serie = pd.Series(-self.enganche)
        inversion_futura = (self.listing_price) * (1 + self.plusvalia) ** (len(df) / self.MESES)
        # Se converte el valor futuro a Serie para agregarlo al final del Flujo de Efectivo

        serie = pd.Series(inversion_futura, index=[len(df["flujo_efectivo"]) + 1])

        # Concatemanos series
        flujo_efectivo = enganche_serie.append(df["flujo_efectivo"]).append(serie)
        # Tasa Mensualizada
        tasa_descuento_mensualizada = self.TASA_DESCUENTO / self.MESES
        # Se aplico un slice a lista de corrida para eliminar el primer valor que es igual al enganche
        self.VPN = npf.npv(tasa_descuento_mensualizada, flujo_efectivo)
        return self.VPN

    def get_TIR(self):
        """Genera la tir del inmueble """
        df = self.dfs['flujos_descontados']
        # Se convierten en series para poder concatenar al flujo de efectivo
        enganche_serie = pd.Series(-self.enganche)
        inversion_futura = pd.Series(
            (self.capital + self.enganche) * (1 + self.plusvalia) ** (len(df) / self.MESES))
        # Concatena enganche al inicio e inversion futura al final
        flujo_efectivo = enganche_serie.append(df["flujo_efectivo"]).append(inversion_futura)
        # Aplica formula de tir
        irr = npf.irr(flujo_efectivo)
        # Anualiza el valor y lo redondea a 2 decimales
        self.TIR = np.round(100 * self.MESES * irr, 2)

        return self.TIR

    def valuate_invest(self):
        if self.TIR > self.TASA_DESCUENTO and self.VPN > 0:
            return True
        else:
            return False
