"""Public, free Streamlit demo. Start: streamlit run deploy/app.py."""
from datetime import datetime, timezone
import time
import pandas as pd
import requests
import streamlit as st
from prices import fetch_books, fetch_amazon, csv_export

st.set_page_config(page_title='Price Tracker · Portfolio Demo', page_icon='↘', layout='wide')
st.markdown('''<style>
.stApp{background:#f7f5ef;color:#152f2a} .block-container{max-width:1120px;padding-top:3rem}
h1{font-family:Georgia,serif!important;font-weight:500!important;font-size:clamp(2.8rem,6vw,4.7rem)!important;letter-spacing:-.045em;line-height:1.05!important}
h2,h3{color:#183e34!important} [data-testid="stMetric"]{padding:1.2rem;border:1px solid #d7ddd1;border-radius:12px;background:#fffdf8}
.eyebrow{font-size:.8rem;letter-spacing:.14em;color:#3b6559;font-weight:700} a{color:#17674e}
button:focus-visible,a:focus-visible{outline:3px solid #a75e18!important;outline-offset:3px}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>''', unsafe_allow_html=True)
st.markdown('<p class="eyebrow">PRICE TRACKER / PYTHON PORTFOLIO</p>', unsafe_allow_html=True)
st.title('A price. A source.\nA record you can keep.')
st.write('Fetch product prices, compare observations, and export a dated CSV. No account or API key needed.')
st.caption('The reliable live demo reads Books to Scrape, a sandbox catalogue. Its prices are GBP test-store data—not Amazon offers. Amazon fetching is optional and may be blocked.')


@st.cache_data(ttl=600, show_spinner=False, max_entries=1)
def books():
    return fetch_books()


@st.cache_data(ttl=600, show_spinner=False, max_entries=30)
def amazon(value):
    return fetch_amazon(value)


if 'observations' not in st.session_state:
    st.session_state.observations = []
source = st.radio('Choose a source', ['Live sandbox catalogue', 'Amazon.com product'], horizontal=True)
records = []
if source == 'Live sandbox catalogue':
    st.subheader('Explore the live sandbox')
    try:
        with st.spinner('Reading the source catalogue…'):
            records = books()
    except (ValueError, requests.RequestException):
        st.warning('The sandbox source is unavailable right now. Try again later. No sample prices have been substituted.')
else:
    st.subheader('Check an Amazon product')
    st.info('Amazon may return a robot check or hide a price. A failed fetch is reported explicitly; the app does not bypass access controls or substitute prices.')
    with st.form('amazon'):
        value = st.text_input('Amazon.com URL or ASIN', max_chars=500, placeholder='https://www.amazon.com/dp/…')
        submitted = st.form_submit_button('Fetch current page price')
    if submitted:
        if time.time() - st.session_state.get('last_amazon', 0) < 15:
            st.warning('Please wait 15 seconds between product requests.')
        else:
            st.session_state.last_amazon = time.time()
            try:
                with st.spinner('Checking the product page…'):
                    st.session_state.amazon_record = amazon(value)
            except (ValueError, requests.RequestException) as error:
                st.session_state.pop('amazon_record', None)
                st.error(str(error) if isinstance(error, ValueError) else 'Product source unavailable. No price was recorded.')
    records = [st.session_state.amazon_record] if 'amazon_record' in st.session_state else []

if records:
    a,b,c = st.columns(3)
    a.metric('Products returned', len(records))
    b.metric('Currency', records[0]['currency'])
    c.metric('Latest source check (UTC)', records[0]['observed_at'][11:16])
    selected = st.selectbox('Choose a product to track', range(len(records)), format_func=lambda i: records[i]['title'])
    product = records[selected]
    with st.container(border=True):
        st.subheader(product['title'])
        st.write(f"**{product['currency']} {product['price']:,.2f}**")
        st.link_button('Open original source ↗', product['url'])
        st.caption(f"Observed {product['observed_at']} · {product['source']} · Responses may be cached for ten minutes.")
        if st.button('Save this observation', type='primary'):
            key = (product['url'], product['observed_at'])
            if key not in {(r['url'], r['observed_at']) for r in st.session_state.observations}:
                st.session_state.observations.append(product.copy())
                st.success('Saved to this browser session. Export the CSV to keep it.')
            else:
                st.info('This exact source observation is already saved.')

st.subheader('Your observation log')
st.caption('Session-only storage. Reloading, closing the session, or restarting the app may clear it. Download the CSV to retain your records. No background monitoring or email alerts are claimed.')
history = st.session_state.observations
if history:
    st.dataframe(pd.DataFrame(history), hide_index=True, use_container_width=True)
    st.download_button('Download observations (.csv)', csv_export(history), file_name='price-observations.csv', mime='text/csv')
    if product_rows := [r for r in history if records and r['url'] == product['url']]:
        if len(product_rows) > 1:
            first,last = product_rows[0]['price'], product_rows[-1]['price']
            st.metric('Change across your saved observations', f"{last-first:+.2f} {product_rows[-1]['currency']}")
else:
    st.write('Select a product above and save an observation to start your log.')
st.divider()
st.markdown('[Source code](https://github.com/spattoor/Amazon-Price-Tracker) · [Sandbox data source](https://books.toscrape.com/)')
