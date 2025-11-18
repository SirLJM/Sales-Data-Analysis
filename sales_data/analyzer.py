import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SalesAnalyzer:
    def __init__(self, data):
        self.data = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.data['data']):
            self.data['data'] = pd.to_datetime(self.data['data'])

    def aggregate_by_sku(self):
        self.data['year_month'] = self.data['data'].dt.to_period('M')

        first_sale = self.data.groupby('sku')['data'].min().reset_index()
        first_sale.columns = ['SKU', 'first_sale']

        monthly_sales = self.data.groupby(['sku', 'year_month'], as_index=False)['ilosc'].sum()

        sku_summary = monthly_sales.groupby('sku', as_index=False).agg({
            'year_month': 'nunique',
            'ilosc': ['sum', 'mean', 'std']
        })

        sku_summary.columns = ['SKU', 'MONTHS', 'QUANTITY', 'AVERAGE SALES', 'SD']

        sku_summary['CV'] = sku_summary['SD'] / sku_summary['AVERAGE SALES']
        sku_summary['CV'] = sku_summary['CV'].fillna(0)

        sku_summary = pd.merge(sku_summary, first_sale, on='SKU', how='left')

        return sku_summary.sort_values('SKU', ascending=False)

    @staticmethod
    def classify_sku_type(sku_summary, cv_basic, cv_seasonal):
        df = sku_summary.copy()

        one_year_ago = datetime.today() - timedelta(days=365)

        df['TYPE'] = 'regular'
        df.loc[df['first_sale'] > one_year_ago, 'TYPE'] = 'new'
        df.loc[(df['TYPE'] != 'new') & (df['CV'] < cv_basic), 'TYPE'] = 'basic'
        df.loc[(df['TYPE'] != 'new') & (df['CV'] > cv_seasonal), 'TYPE'] = 'seasonal'

        return df

    def determine_seasonal_months(self):
        df = self.data.copy()

        two_years_ago = datetime.today() - timedelta(days=730)
        df = df[df['data'] >= two_years_ago]

        df['month'] = df['data'].dt.month
        df['year'] = df['data'].dt.year

        monthly_sales = df.groupby(['sku', 'year', 'month'], as_index=False)['ilosc'].sum()

        avg_monthly_sales = monthly_sales.groupby(['sku', 'month'], as_index=False)['ilosc'].mean()
        avg_monthly_sales = avg_monthly_sales.rename(columns={'sku': 'SKU', 'ilosc': 'avg_sales'})

        overall_avg = avg_monthly_sales.groupby('SKU', as_index=False)['avg_sales'].mean()
        overall_avg = overall_avg.rename(columns={'avg_sales': 'overall_avg'})

        seasonal_data = avg_monthly_sales.merge(overall_avg, on='SKU')
        seasonal_data['seasonal_index'] = seasonal_data['avg_sales'] / seasonal_data['overall_avg']
        seasonal_data['is_in_season'] = seasonal_data['seasonal_index'] > 1.2

        return seasonal_data[['SKU', 'month', 'avg_sales', 'seasonal_index', 'is_in_season']]

    @staticmethod
    def calculate_safety_stock_and_rop(sku_summary, seasonal_data, lead_time, z_basic,
                                       z_seasonal_in, z_seasonal_out, z_new):
        df = sku_summary.copy()
        z_score_map = {
            'basic': z_basic,
            'regular': z_basic,
            'seasonal': z_seasonal_in, #default for seasonal, later overwritten
            'new': z_new
        }
        df['z_score'] = df['TYPE'].map(z_score_map)

        current_month = datetime.today().month

        sqrt_lead_time = np.sqrt(lead_time)

        df['SS'] = df['z_score'] * df['SD'] * sqrt_lead_time
        df['ROP'] = df['AVERAGE SALES'] * lead_time + df['SS']

        seasonal_mask = df['TYPE'] == 'seasonal'
        if isinstance(seasonal_mask, pd.Series) and seasonal_mask.any():
            seasonal_skus = df[seasonal_mask]['SKU'].tolist()
            seasonal_current = seasonal_data[
                (seasonal_data['SKU'].isin(seasonal_skus)) &
                (seasonal_data['month'] == current_month)
            ][['SKU', 'is_in_season']]

            df = df.merge(seasonal_current, on='SKU', how='left')

            df['SS_IN'] = np.where(
                seasonal_mask,
                z_seasonal_in * df['SD'] * sqrt_lead_time,
                np.nan
            )
            df['ROP_IN'] = np.where(
                seasonal_mask,
                df['AVERAGE SALES'] * lead_time + df['SS_IN'],
                np.nan
            )

            df['SS_OUT'] = np.where(
                seasonal_mask,
                z_seasonal_out * df['SD'] * sqrt_lead_time,
                np.nan
            )
            df['ROP_OUT'] = np.where(
                seasonal_mask,
                df['AVERAGE SALES'] * lead_time + df['SS_OUT'],
                np.nan
            )

            in_season_mask = (df['is_in_season'] == True)
            out_season_mask = (df['is_in_season'] != True)

            df.loc[seasonal_mask & in_season_mask, 'SS'] = df['SS_IN']
            df.loc[seasonal_mask & in_season_mask, 'ROP'] = df['ROP_IN']
            df.loc[seasonal_mask & out_season_mask, 'SS'] = df['SS_OUT']
            df.loc[seasonal_mask & out_season_mask, 'ROP'] = df['ROP_OUT']

            df = df.drop(columns=['is_in_season'], errors='ignore')

        df = df.drop(columns=['z_score'], errors='ignore')

        df['SS'] = df['SS'].round(2)
        df['ROP'] = df['ROP'].round(2)
        if 'SS_IN' in df.columns:
            df['SS_IN'] = df['SS_IN'].round(2)
            df['SS_OUT'] = df['SS_OUT'].round(2)
            df['ROP_IN'] = df['ROP_IN'].round(2)
            df['ROP_OUT'] = df['ROP_OUT'].round(2)


        return df[['SKU', 'MONTHS', 'QUANTITY', 'AVERAGE SALES', 'SD', 'CV', 'TYPE', 'SS', 'ROP']]