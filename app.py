import json, pandas as pd, streamlit as st
st.set_page_config(page_title="Petromart Consumer Price Dashboard", page_icon="🥤", layout="wide")
COL = {'PEPSI':'#2563eb','COKE':'#dc2626','COLA NEXT':'#0891b2','GOURMET':'#ea580c','PAKOLA':'#16a34a'}
ORDER = json.load(open('companies.json'))          # PEPSI, COKE, COLA NEXT, GOURMET, PAKOLA
BO = [b for v in ORDER.values() for b in v]

@st.cache_data
def load():
    return pd.read_csv('data.csv')
D = load()

tabcss = ''.join(f'.stTabs [data-baseweb="tab"]:nth-child({i+1})[aria-selected="true"]{{background:{COL[c]} !important}}' for i, c in enumerate(ORDER))
st.markdown("""<style>
.block-container{padding-top:1rem;max-width:1200px}
.hero{background:linear-gradient(120deg,#0f2a5f,#6d28d9 60%,#db2777);color:#fff;padding:26px 28px;border-radius:16px;margin-bottom:14px}
.hero h1{margin:0;font-size:28px;color:#fff}.hero p{margin:4px 0 0;opacity:.85}
.kpi{background:rgba(127,127,127,.10);border-radius:14px;padding:14px 16px;text-align:center}
.kpi b{display:block;font-size:28px}.kpi span{font-size:12px;opacity:.7;text-transform:uppercase;letter-spacing:.05em}
/* nav bar */
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#14213d;padding:8px;border-radius:14px;flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{height:auto;color:#fff !important;border-radius:10px;padding:9px 20px;font-weight:700;background:rgba(255,255,255,.08)}
.stTabs [data-baseweb="tab"] p{color:#fff !important;font-size:15px;font-weight:700}
.stTabs [data-baseweb="tab"]:hover{background:rgba(255,255,255,.2)}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
.stTabs [data-baseweb="tab-panel"]{padding-top:14px}
.sec{border-radius:12px 12px 0 0;color:#fff;padding:12px 18px;display:flex;justify-content:space-between;font-size:20px;font-weight:700}
.sec small{font-weight:400;opacity:.9;font-size:12px;align-self:center}
.tw{overflow-x:auto;border:1px solid rgba(127,127,127,.25);border-top:0;border-radius:0 0 12px 12px}
table.t{width:100%;border-collapse:collapse;font-size:14px}
table.t th{background:#14213d;color:#fff;text-align:left;padding:9px 12px;font-size:12px;text-transform:uppercase}
table.t td{padding:8px 12px;border-bottom:1px solid rgba(127,127,127,.2)}
table.t tr.o td{background:rgba(127,127,127,.08)}
td.b{font-weight:700;vertical-align:top;border-right:1px solid rgba(127,127,127,.2)}
td.n{text-align:right}.bar{display:block;height:6px;border-radius:4px;margin-top:3px}
""" + tabcss + "</style>", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🥤 Petromart Consumer Price Dashboard</h1><p>Consumer Price (CP) by company → brand → SKU · prices in PKR · survey export 9 Oct 2026</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("Filters")
    cities = st.multiselect("City", sorted(D.City.unique()), default=sorted(D.City.unique()))
    st.caption("CP = average shelf price across stores that stocked the SKU. Common = most frequent price.")
F = D[D.City.isin(cities)]
if F.empty:
    st.warning("No data for this selection."); st.stop()

def kpis(items):
    for c, (v, l) in zip(st.columns(len(items)), items):
        c.markdown(f'<div class="kpi"><b>{v}</b><span>{l}</span></div>', unsafe_allow_html=True)

tabs = st.tabs([f"🥤 {c}" if c == 'PEPSI' else c for c in ORDER] + ["🗂️ Data"])

for tab, co in zip(tabs, ORDER):
    with tab:
        g = F[F.Company == co]
        col = COL[co]
        if g.empty:
            st.info("No prices for this company in the selected cities."); continue
        s = g.groupby(['Brand', 'SKU'])['CP'].agg(avg='mean', mn='min', mx='max', n='count',
              common=lambda x: x.mode().iloc[0]).reset_index()
        s['o'] = s.Brand.map(BO.index); s = s.sort_values(['o', 'SKU']).reset_index(drop=True)
        kpis([(g['Store Id'].nunique(), 'Stores'), (s.Brand.nunique(), 'Brands'), (len(s), 'SKUs priced'),
              (f"Rs {g.CP.mean():,.0f}", 'Avg CP'), (f"{len(g):,}", 'Price points')])
        st.write("")
        top = s.avg.max(); rows = []; alt = -1
        for b, grp in s.groupby('o', sort=True):
            alt += 1
            for j, (_, r) in enumerate(grp.iterrows()):
                cell = f'<td class="b" rowspan="{len(grp)}" style="color:{col}">{r.Brand}</td>' if j == 0 else ''
                rows.append(f'<tr class="{"o" if alt % 2 else ""}">{cell}<td>{r.SKU}</td>'
                  f'<td style="font-weight:700;min-width:150px">Rs {r.avg:,.0f}<i class="bar" style="width:{r.avg/top*100:.0f}%;background:{col}"></i></td>'
                  f'<td class="n">Rs {r.common:,.0f}</td><td class="n">{r.mn:,.0f}–{r.mx:,.0f}</td><td class="n">{r.n}</td></tr>')
        st.markdown(f'<div class="sec" style="background:linear-gradient(90deg,{col},{col}bb)">{co}<small>Brand · SKU · Consumer Price</small></div>'
          f'<div class="tw"><table class="t"><tr><th>Brand</th><th>SKU</th><th>Consumer Price (avg)</th><th>Common</th><th>Min–Max</th><th>Stores</th></tr>{"".join(rows)}</table></div>', unsafe_allow_html=True)
        if co == 'GOURMET':
            st.caption("Buzz Up, Cola One and Ice-Cream Soda are grouped under Gourmet. SKUs with no recorded prices are left out.")

with tabs[-1]:
    st.subheader("Survey data (one row per store × SKU price)")
    q = st.text_input("Search brand / SKU / store")
    V = F if not q else F[F.apply(lambda r: q.lower() in ' '.join(map(str, r.values)).lower(), axis=1)]
    try:
        st.dataframe(V, hide_index=True, height=520, width='stretch')
    except TypeError:                       # older Streamlit versions
        st.dataframe(V, hide_index=True, height=520, use_container_width=True)
    st.download_button("⬇️ Download filtered data (CSV)", V.to_csv(index=False).encode(), "petromart_cp_data.csv", "text/csv")
