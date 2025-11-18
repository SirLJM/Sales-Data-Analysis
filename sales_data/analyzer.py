import pandas as pd

class SalesAnalyzer:
    def __init__(self, data):
        self.data = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.data['data']):
            self.data['data'] = pd.to_datetime(self.data['data'])

    def aggregate_by_sku(self):

        self.data['year_month'] = self.data['data'].dt.to_period('M')

        monthly_sales = self.data.groupby(['sku', 'year_month'], as_index=False)['ilosc'].sum()

        sku_summary = monthly_sales('sku', as_index=False).agg({
            'year_month': 'nunique',
            'ilosc': ['sum', 'mean', 'std']
        })

        sku_summary.columns = ['sku', 'months_count', 'total_quantity', 'avg_sales', 'std_dev']

        

        sku_summary.columns = ['sku', 'months_count', 'total_quantity']
        return sku_summary.sort_values('total_quantity', ascending=False)