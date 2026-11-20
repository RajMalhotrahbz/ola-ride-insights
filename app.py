import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title='OLA Ride Insights', page_icon='🚕', layout='wide', initial_sidebar_state='expanded')

NAVY = '#0B1220'; BLUE = '#3B82F6'; CYAN = '#06B6D4'; GREEN = '#10B981'; ORANGE = '#F59E0B'; RED = '#EF4444'

@st.cache_data(show_spinner='Loading OLA bookings...')
def load_data():
    path = Path(__file__).parent / 'OLA_Cleaned_Data.csv'
    df = pd.read_csv(path)
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    for col in ['booking_value','ride_distance','hour','minute','is_successful','is_customer_cancelled','is_driver_cancelled','is_driver_not_found','successful_revenue']:
        if col in df.columns: df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

df = load_data()

# Sidebar controls
st.sidebar.markdown('## 🔎 Dashboard Filters')
min_date = df['datetime'].min().date(); max_date = df['datetime'].max().date()
date_range = st.sidebar.date_input('Date range', value=(min_date, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date
vehicle_options = sorted(df['vehicle_type'].dropna().unique().tolist())
selected_vehicles = st.sidebar.multiselect('Vehicle type', vehicle_options, default=vehicle_options)
status_options = sorted(df['booking_status'].dropna().unique().tolist())
selected_statuses = st.sidebar.multiselect('Booking status', status_options, default=status_options)
payment_options = sorted(df['payment_method'].dropna().unique().tolist())
selected_payments = st.sidebar.multiselect('Payment method', payment_options, default=payment_options)

mask = df['datetime'].dt.date.between(start_date, end_date)
mask &= df['vehicle_type'].isin(selected_vehicles)
mask &= df['booking_status'].isin(selected_statuses)
mask &= df['payment_method'].isin(selected_payments)
f = df.loc[mask].copy()
success = f[f['booking_status'].eq('Success')].copy()

# Helpers
def fmt_money(x): return f'₹{x:,.0f}'
def pct(n, d): return (n / d * 100) if d else 0

st.markdown(f"""<div style='background:linear-gradient(110deg,{NAVY},#172A48);padding:24px 28px;border-radius:18px;color:white;margin-bottom:16px'>
<h1 style='margin:0;color:white;font-size:32px'>🚕 OLA Ride Insights</h1>
<p style='margin:8px 0 0;color:#CBD5E1'>Ride-sharing operations · Revenue · Customer experience · Cancellation intelligence</p></div>""", unsafe_allow_html=True)
st.caption(f"Filtered view: {len(f):,} bookings | {start_date:%d %b %Y} to {end_date:%d %b %Y}")

# KPI row based on filtered data
n_bookings = len(f); n_success = len(success); total_rev = success['successful_revenue'].sum(); avg_value = success['booking_value'].mean() if n_success else 0
success_rate = pct(n_success, n_bookings)
customer_cancels = int(f['is_customer_cancelled'].fillna(0).sum())
driver_cancels = int(f['is_driver_cancelled'].fillna(0).sum())
dnf = int(f['is_driver_not_found'].fillna(0).sum())
unsuccessful_rate = pct(n_bookings-n_success, n_bookings)
kpis = st.columns(6)
for col, label, value, helptext in zip(kpis,
    ['Bookings','Successful rides','Success rate','Successful revenue','Avg. booking value','Unsuccessful rate'],
    [f'{n_bookings:,}',f'{n_success:,}',f'{success_rate:.1f}%',fmt_money(total_rev),fmt_money(avg_value),f'{unsuccessful_rate:.1f}%'],
    ['Bookings in the current filters','Completed rides in the current filters','Successful rides divided by all filtered bookings','Revenue from successful rides only','Mean booking value for successful rides','Includes customer/driver cancellations and driver-not-found']):
    col.metric(label, value, help=helptext)

# Main tab layout
tabs = st.tabs(['📊 Overview','🚘 Vehicle Analysis','💰 Revenue','❌ Cancellation','⭐ Ratings & Experience','🗺️ Locations','📋 Data Explorer'])

with tabs[0]:
    st.subheader('Overall booking performance')
    c1,c2 = st.columns([1.45,1])
    with c1:
        daily = f.groupby(f['datetime'].dt.date).size().reset_index(name='Bookings')
        daily.columns=['Date','Bookings']
        fig = px.line(daily, x='Date', y='Bookings', markers=True, title='Booking volume by date')
        fig.update_layout(height=350, margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        status = f['booking_status'].value_counts().reset_index(); status.columns=['Status','Bookings']
        fig = px.pie(status, names='Status', values='Bookings', hole=.55, title='Booking status breakdown')
        fig.update_layout(height=350, margin=dict(l=10,r=10,t=45,b=10))
        st.plotly_chart(fig, use_container_width=True)
    c3,c4 = st.columns(2)
    with c3:
        hourly = f.groupby('hour').size().reset_index(name='Bookings')
        fig = px.bar(hourly, x='hour', y='Bookings', title='Bookings by hour', labels={'hour':'Hour of day'})
        fig.update_layout(height=330, xaxis=dict(dtick=1))
        st.plotly_chart(fig, use_container_width=True)
    with c4:
        weekday_order=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        wd = f.groupby('day_name').size().reindex(weekday_order).fillna(0).reset_index(name='Bookings')
        fig = px.bar(wd, x='day_name', y='Bookings', title='Bookings by weekday', labels={'day_name':'Weekday'})
        fig.update_layout(height=330)
        st.plotly_chart(fig, use_container_width=True)
    st.info('Business question: What demand patterns should operations and driver supply teams plan around? Use the hour and date filters to identify high-volume periods.')

with tabs[1]:
    st.subheader('Vehicle type performance')
    vehicle = f.groupby('vehicle_type').agg(Bookings=('booking_id','count')).reset_index()
    vehicle_success = success.groupby('vehicle_type').agg(Successful_Rides=('booking_id','count'),Total_Distance=('ride_distance','sum'),Avg_Distance=('ride_distance','mean'),Avg_Customer_Rating=('customer_rating','mean'),Avg_Driver_Rating=('driver_ratings','mean')).reset_index()
    vehicle = vehicle.merge(vehicle_success, on='vehicle_type', how='left').fillna(0)
    c1,c2 = st.columns(2)
    with c1:
        fig=px.bar(vehicle.sort_values('Total_Distance',ascending=False),x='vehicle_type',y='Total_Distance',title='Total successful ride distance by vehicle',labels={'vehicle_type':'Vehicle type','Total_Distance':'Distance (km)'})
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=px.bar(vehicle.sort_values('Avg_Distance',ascending=False),x='vehicle_type',y='Avg_Distance',title='Average ride distance by vehicle',labels={'vehicle_type':'Vehicle type','Avg_Distance':'Average distance (km)'})
        st.plotly_chart(fig,use_container_width=True)
    c3,c4=st.columns(2)
    with c3:
        fig=px.bar(vehicle.sort_values('Bookings',ascending=False),x='vehicle_type',y='Bookings',title='Bookings by vehicle type')
        st.plotly_chart(fig,use_container_width=True)
    with c4:
        fig=px.bar(vehicle,x='vehicle_type',y='Avg_Customer_Rating',title='Average customer rating by vehicle',labels={'vehicle_type':'Vehicle type','Avg_Customer_Rating':'Customer rating'})
        st.plotly_chart(fig,use_container_width=True)
    st.dataframe(vehicle.round(2),use_container_width=True,hide_index=True)

with tabs[2]:
    st.subheader('Revenue and payment behavior')
    c1,c2=st.columns(2)
    with c1:
        pay=success.groupby('payment_method',dropna=False)['successful_revenue'].sum().reset_index()
        pay['payment_method']=pay['payment_method'].fillna('Not recorded')
        fig=px.bar(pay.sort_values('successful_revenue',ascending=False),x='payment_method',y='successful_revenue',title='Revenue by payment method',labels={'payment_method':'Payment method','successful_revenue':'Revenue (₹)'})
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        cust=success.groupby('customer_id').agg(Rides=('booking_id','count'),Booking_Value=('booking_value','sum')).reset_index().nlargest(5,'Booking_Value')
        fig=px.bar(cust,x='customer_id',y='Booking_Value',title='Top 5 customers by successful booking value',labels={'customer_id':'Customer ID','Booking_Value':'Booking value (₹)'})
        st.plotly_chart(fig,use_container_width=True)
    rev_daily=success.groupby(success['datetime'].dt.date)['successful_revenue'].sum().reset_index()
    rev_daily.columns=['Date','Revenue']
    fig=px.line(rev_daily,x='Date',y='Revenue',markers=True,title='Successful revenue by date')
    st.plotly_chart(fig,use_container_width=True)
    dist=success.groupby(success['datetime'].dt.date)['ride_distance'].sum().reset_index(); dist.columns=['Date','Ride Distance (km)']
    fig=px.bar(dist,x='Date',y='Ride Distance (km)',title='Successful ride distance per day')
    st.plotly_chart(fig,use_container_width=True)

with tabs[3]:
    st.subheader('Cancellation and unsuccessful booking analysis')
    c1,c2,c3=st.columns(3)
    c1.metric('Customer cancellations',f'{customer_cancels:,}',f'{pct(customer_cancels,n_bookings):.1f}% of filtered bookings')
    c2.metric('Driver cancellations',f'{driver_cancels:,}',f'{pct(driver_cancels,n_bookings):.1f}% of filtered bookings')
    c3.metric('Driver not found',f'{dnf:,}',f'{pct(dnf,n_bookings):.1f}% of filtered bookings')
    c4,c5=st.columns(2)
    with c4:
        cust_reasons=f[f['is_customer_cancelled'].eq(1)]['canceled_rides_by_customer'].value_counts().reset_index(); cust_reasons.columns=['Reason','Count']
        if not cust_reasons.empty:
            fig=px.bar(cust_reasons,x='Count',y='Reason',orientation='h',title='Customer cancellation reasons')
            st.plotly_chart(fig,use_container_width=True)
        else: st.info('No customer cancellations in this filter selection.')
    with c5:
        driver_reasons=f[f['is_driver_cancelled'].eq(1)]['canceled_rides_by_driver'].value_counts().reset_index(); driver_reasons.columns=['Reason','Count']
        if not driver_reasons.empty:
            fig=px.bar(driver_reasons,x='Count',y='Reason',orientation='h',title='Driver cancellation reasons')
            st.plotly_chart(fig,use_container_width=True)
        else: st.info('No driver cancellations in this filter selection.')
    incomplete=f[f['incomplete_rides'].eq('Yes')]['incomplete_rides_reason'].value_counts().reset_index(); incomplete.columns=['Reason','Count']
    if not incomplete.empty:
        fig=px.bar(incomplete,x='Reason',y='Count',title='Incomplete rides: reasons')
        st.plotly_chart(fig,use_container_width=True)
    st.warning('Interpretation: cancellation and driver-not-found rates are operational indicators. Review the reason categories and time patterns before proposing staffing or policy changes.')

with tabs[4]:
    st.subheader('Ratings and customer experience')
    c1,c2=st.columns(2)
    avg_dr=success['driver_ratings'].mean() if not success.empty else 0
    avg_cr=success['customer_rating'].mean() if not success.empty else 0
    c1.metric('Average driver rating',f'{avg_dr:.2f}/5' if pd.notna(avg_dr) else 'N/A')
    c2.metric('Average customer rating',f'{avg_cr:.2f}/5' if pd.notna(avg_cr) else 'N/A')
    c3,c4=st.columns(2)
    with c3:
        if success['driver_ratings'].dropna().size:
            fig=px.hist(success,x='driver_ratings',nbins=20,title='Driver rating distribution')
            st.plotly_chart(fig,use_container_width=True)
    with c4:
        if success['customer_rating'].dropna().size:
            fig=px.hist(success,x='customer_rating',nbins=20,title='Customer rating distribution')
            st.plotly_chart(fig,use_container_width=True)
    ratingveh=success.groupby('vehicle_type')[['driver_ratings','customer_rating']].mean().reset_index()
    fig=px.bar(ratingveh,x='vehicle_type',y=['driver_ratings','customer_rating'],barmode='group',title='Customer vs driver ratings by vehicle',labels={'vehicle_type':'Vehicle type','value':'Rating','variable':'Rating type'})
    st.plotly_chart(fig,use_container_width=True)
    corr=success[['driver_ratings','customer_rating']].corr().iloc[0,1]
    st.metric('Customer rating vs driver rating correlation',f'{corr:.3f}',help='Pearson correlation on successful rides with both ratings available')
    st.caption('Rating fields may be missing for non-successful rides; the app calculates averages from available successful-ride rating records.')

with tabs[5]:
    st.subheader('Pickup and drop-off locations')
    c1,c2=st.columns(2)
    with c1:
        pick=f['pickup_location'].value_counts().head(15).reset_index(); pick.columns=['Pickup location','Bookings']
        fig=px.bar(pick,x='Bookings',y='Pickup location',orientation='h',title='Top pickup locations (booking volume)')
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        drop=f['drop_location'].value_counts().head(15).reset_index(); drop.columns=['Drop location','Bookings']
        fig=px.bar(drop,x='Bookings',y='Drop location',orientation='h',title='Top drop locations (booking volume)')
        st.plotly_chart(fig,use_container_width=True)
    pairs=f.groupby(['pickup_location','drop_location']).size().reset_index(name='Bookings').nlargest(15,'Bookings')
    st.markdown('**Most frequent pickup → drop routes**')
    st.dataframe(pairs,use_container_width=True,hide_index=True)

with tabs[6]:
    st.subheader('Filtered bookings data')
    st.write('Explore records using the sidebar filters. Export the filtered view below.')
    st.dataframe(f, use_container_width=True, height=460)
    csv_data=f.to_csv(index=False).encode('utf-8')
    st.download_button('⬇️ Download filtered CSV',data=csv_data,file_name='ola_filtered_bookings.csv',mime='text/csv')

st.divider()
st.caption('OLA Ride Insights · Portfolio analytics project · Dataset period: July 2024')
