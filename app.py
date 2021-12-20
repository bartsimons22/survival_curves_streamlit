import streamlit as st
from streamlit import cli as stcli
import pandas as pd
import numpy as np
import sys
import matplotlib.pyplot as plt
import pyodbc
import time
from dotenv import load_dotenv
import os

# ------- ENVIRONMENT VARIABLES --------
load_dotenv()

DRIVER = os.environ.get('DRIVER')
SERVER_NAME = os.environ.get('SERVER_NAME')
PORT_NUM = os.environ.get('PORT_NUM')
DATABASE = os.environ.get('DATABASE')
UID = os.environ.get('UID')
PASSWORD = os.environ.get('PASSWORD')

#Title and description
st.title('Quality Detection Tool /w Survival Curves')
st.text('There is data available for 2019-2020, for three fake products: A, B and C.')

#Creating submission form
with st.form(key='my_form'):
    start = '2019-01-01'
    stop = '2020-12-01'
    products = ['A', 'B', 'C']
    default_a = products.index('A')
    default_b = products.index('B')
    months = pd.date_range(start, stop, freq='MS').tolist()
    product_a = st.selectbox('First Product to compare', products, index=default_a)
    product_b = st.selectbox('Second product to compare', products, index=default_b)
    start = st.selectbox('Start Date', (months), index=0)
    stop = st.selectbox('Stop Date', (months), index=len(months)-1)
    submit_button = st.form_submit_button(label='Submit')

#Functions
@st.cache()
def get_data():
    cnxn = pyodbc.connect(f'Driver={DRIVER};Server={SERVER_NAME},{PORT_NUM};Database={DATABASE};Uid={UID};Pwd={PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;')
    sql_sales = "SELECT * FROM [SalesLT].[sales]"
    sql_claims = "SELECT * FROM [SalesLT].[claims]"
    sales = pd.read_sql(sql_sales,cnxn)
    claims = pd.read_sql(sql_claims, cnxn)
    sales['Date'] = pd.to_datetime(sales['Date'])
    claims['Purchased_on'] = pd.to_datetime(claims['Purchased_on'])
    claims['Date'] = pd.to_datetime(claims['Date'])
    return sales, claims

def select_sales(sales, start, stop, product):
    sales = sales[(sales['Date'] >= start) & (sales['Date'] < stop) & (sales['Product']==product)]
    return sales

def get_monthly_claims(claims, start, stop, product):
    claims = claims[(claims['Purchased_on'] >= start) & (claims['Purchased_on'] <= stop) & (claims['Claimed_Product']==product)]
    return claims

def get_months(start, stop):
  return pd.date_range(start, stop, freq='MS').tolist()

def get_survival_curve_month(start, stop, claims, sales):
    months = get_months(start, stop)
    empty_df = pd.DataFrame()
    total_sales = 0
    for m in months:
        temp_df = claims[claims['Purchased_on'] == m]
        try:
            total_sales = total_sales + int(sales[sales.Date == m].groupby(by='Date').sum()['Sales'])
        except Exception as e: 
            continue
        temp_df = temp_df.groupby('Date').count()
        temp_df = temp_df.iloc[:, 0:1]
        empty_df = pd.concat([empty_df, temp_df])
    empty_df = empty_df.sort_index()
    months_df = pd.DataFrame(index=get_months(start, empty_df.index[-1])).reset_index()
    months_df['Date'] = months_df['index']
    months_df = months_df.drop('index', axis=1)
    empty_df = empty_df.reset_index().groupby('Date').sum()
    new_df = pd.merge(months_df, empty_df, how='outer', on=['Date', 'Date'])
    new_df['Claimed_Product'] = new_df['Claimed_Product'].fillna(0)
    new_df['Total_Claims'] = new_df['Claimed_Product'].cumsum()
    new_df['Survival_Count'] = total_sales - new_df['Total_Claims']
    new_df['Survival_Rate'] = 1 - (new_df['Total_Claims'] / int(total_sales))
    return new_df

#Main part of the web app
if start<stop:
    with st.spinner('Request is being processed..'):
        start_time = time.time()
        sales, claims = get_data()
        sales_a = select_sales(sales, start, stop, product=product_a)
        claims_a = get_monthly_claims(claims, start, stop, product=product_a)
        sales_b = select_sales(sales, start, stop, product=product_b)
        claims_b = get_monthly_claims(claims, start, stop, product=product_b)
        df_a = get_survival_curve_month(start, stop, claims_a, sales_a)
        df_b = get_survival_curve_month(start, stop, claims_a, sales_b)
        fig, ax = plt.subplots()
        ax.plot(df_a.Survival_Rate, label=f"Product {product_a}")
        ax.plot(df_b.Survival_Rate, label=f"Product {product_b}")
        fig.legend()
        st.pyplot(fig)
        st.success("--- %s seconds ---" % (round(time.time() - start_time,2)))
else:
    st.error('Error! Start date has to be earlier than the stop date! Please try again.')


