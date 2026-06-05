import requests
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title='NSE Momentum VCP Dashboard', layout='wide')
st.title('🚀 NSE Momentum Trading Dashboard - VCP')
st.caption('Live NSE-backed dashboard | VCP Strategy | Volume | Entry/Exit | Allocation | Sector Rotation')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'application/json, text/plain, */*',
    'Referer': 'https://www.nseindia.com/'
}

session = requests.Session()
session.headers.update(HEADERS)

@st.cache_data(ttl=300)
def get_json(url):
    try:
        session.get('https://www.nseindia.com', timeout=10)
        r = session.get(url, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

@st.cache_data(ttl=300)
def load_volume_gainers():
    data = get_json('https://www.nseindia.com/api/volume-gainers?csv=false')
    return pd.DataFrame(data.get('data', data if isinstance(data, list) else []))

@st.cache_data(ttl=300)
def load_most_active():
    data = get_json('https://www.nseindia.com/api/most-active-equities?index=equities')
    return pd.DataFrame(data.get('data', data if isinstance(data, list) else []))

@st.cache_data(ttl=300)
def load_52w():
    data = get_json('https://www.nseindia.com/api/live-analysis-52week-high-low?index=equities')
    return pd.DataFrame(data.get('data', data if isinstance(data, list) else []))

@st.cache_data(ttl=300)
def load_indices():
    data = get_json('https://www.nseindia.com/api/allIndices')
    return pd.DataFrame(data.get('data', data if isinstance(data, list) else []))

def to_num(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

vg = load_volume_gainers()
ma = load_most_active()
hi52 = load_52w()
idx = load_indices()

col1, col2, col3, col4 = st.columns(4)
col1.metric('📈 Volume Gainers', len(vg))
col2.metric('🔥 Most Active', len(ma))
col3.metric('🏔 52W Feed Rows', len(hi52))
col4.metric('🏦 Index Rows', len(idx))

with st.sidebar:
    st.header('⚙️ Filters')
    st.markdown('---')
    min_vol_ratio = st.slider('Min Volume Ratio', 1.0, 10.0, 1.5, 0.1)
    min_chg = st.slider('Min Price Change %', -10.0, 20.0, 1.0, 0.5)
    max_risk = st.slider('Max Allocation % per Trade', 0.5, 10.0, 2.0, 0.5)
    sector_pick = st.text_input('Sector / Index Contains', 'NIFTY')
    st.markdown('---')
    st.markdown('**VCP Rules**')
    st.markdown('- 3-4 tight contractions')
    st.markdown('- Volume dries up in base')
    st.markdown('- Breakout on volume expansion')
    st.markdown('- Stop below last low')

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    '📊 VCP Screener', '📦 Volume', '🎯 Entry/Exit', '🔄 Sector Rotation', '💰 Allocation', '📋 52W High/Low'
])

with tab1:
    st.subheader('VCP Momentum Candidates')
    if not ma.empty:
        m = to_num(ma.copy(), ['lastPrice', 'pChange', 'totalTradedVolume'])
        if 'pChange' in m.columns:
            m = m[m['pChange'] >= min_chg]
        st.dataframe(m.head(25), use_container_width=True)
        if 'pChange' in m.columns and not m.empty:
            fig = px.bar(m.head(15), x='symbol' if 'symbol' in m.columns else m.columns[0],
                         y='pChange', title='Top Momentum Stocks', color='pChange',
                         color_continuous_scale='RdYlGn')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info('NSE momentum data not available right now. Refresh in a few minutes.')

with tab2:
    st.subheader('Live Volume Gainers')
    if not vg.empty:
        df = to_num(vg.copy(), ['totalTradedVolume', 'quantityTraded', 'lastPrice', 'change', 'pChange'])
        if 'pChange' in df.columns:
            df = df[df['pChange'] >= min_chg]
        if {'totalTradedVolume', 'quantityTraded'}.issubset(df.columns):
            df['vol_ratio'] = df['totalTradedVolume'] / df['quantityTraded'].replace(0, pd.NA)
            df = df[df['vol_ratio'].fillna(0) >= min_vol_ratio]
        if 'pChange' in df.columns:
            df = df.sort_values('pChange', ascending=False)
        st.dataframe(df.head(25), use_container_width=True)
        if 'totalTradedVolume' in df.columns and 'symbol' in df.columns and not df.empty:
            fig2 = px.bar(df.head(15), x='symbol', y='totalTradedVolume',
                          title='Top Volume Stocks', color='pChange',
                          color_continuous_scale='Blues')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning('Live volume-gainer data unavailable right now.')

with tab3:
    st.subheader('Entry / Exit Rules (VCP)')
    st.markdown("""
    ### Entry Checklist
    - Stock is in a clear uptrend (above 50, 150, 200 SMA)
    - VCP pattern shows 3-4 contractions with declining volume
    - Price is within 5-10% of 52-week high
    - Breakout candle has at least 1.5x average volume
    - RSI between 50-70 (momentum zone)

    ### Exit Rules (Mark Minervini Method)
    - **Initial Stop:** Place below the last contraction low immediately on entry
    - **Profit Target 1:** Take 25-30% off at 20-25% gain
    - **Trailing Stop:** Use 10-week moving average as a trailing stop
    - **Hard Exit:** If stock falls more than 7-8% from buy point, exit immediately
    - **Time Stop:** If stock does not move in 3 weeks, exit and redeploy capital
    """)

with tab4:
    st.subheader('Sector Rotation')
    if not idx.empty and 'index' in idx.columns:
        s = idx[idx['index'].astype(str).str.contains(sector_pick, case=False, na=False)].copy()
        s = to_num(s, ['last', 'change', 'pChange'])
        if not s.empty and 'pChange' in s.columns:
            s = s.sort_values('pChange', ascending=False)
            st.dataframe(s[['index', 'last', 'change', 'pChange']].head(25), use_container_width=True)
            fig3 = px.bar(s.head(15), x='index', y='pChange',
                          title='Sector Strength (% Change)', color='pChange',
                          color_continuous_scale='RdYlGn')
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info('No matching sector rows.')
    else:
        st.info('Sector/index feed unavailable right now.')

with tab5:
    st.subheader('Position Allocation Matrix')
    st.markdown(f'Capital assumed for sizing: based on **{max_risk}% max risk per trade**')
    if not vg.empty and 'pChange' in vg.columns:
        alloc = to_num(vg.copy(), ['pChange', 'lastPrice'])
        alloc['score'] = alloc['pChange'].rank(pct=True)
        alloc['allocation_%'] = (alloc['score'] * max_risk).round(2)
        alloc['risk_per_10L'] = (alloc['allocation_%'] / 100 * 1000000).round(0)
        cols = [c for c in ['symbol', 'series', 'lastPrice', 'pChange', 'allocation_%', 'risk_per_10L'] if c in alloc.columns]
        st.dataframe(alloc[cols].sort_values('allocation_%', ascending=False).head(20), use_container_width=True)
    else:
        st.info('Allocation data not available right now.')

with tab6:
    st.subheader('52 Week High / Low Watchlist')
    if not hi52.empty:
        st.dataframe(hi52.head(30), use_container_width=True)
    else:
        st.info('52-week feed not available right now.')

st.markdown('---')
st.caption('Data refreshes every 5 minutes. Built for NSE momentum traders using VCP strategy by Mark Minervini.')
