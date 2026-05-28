import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Bonito HVP Pipeline Tool", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F7F4EE; color: #1A1A1A; }
    [data-testid="stSidebar"] { background-color: #EEEBE3; }
    [data-testid="stSidebar"] * { color: #1A1A1A !important; }
    h1, h2, h3, h4, p, li { color: #1A1A1A !important; }
    div[data-testid="stMetricValue"] { color: #1A3A5C !important; font-size: 1.4rem; }
    div[data-testid="stMetricLabel"] { color: #444444 !important; }
    .section-header {
        background-color: #1A3A5C;
        color: white !important;
        padding: 8px 14px;
        border-radius: 4px;
        font-size: 13px;
        font-weight: bold;
        letter-spacing: 1px;
        margin-bottom: 12px;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    blr = pd.read_csv("data/blr csv.csv")
    mum = pd.read_csv("data/mum csv.csv")
    blr["City"] = "Bangalore"
    mum["City"] = "Mumbai"
    df = pd.concat([blr, mum], ignore_index=True)
    df.columns = df.columns.str.strip()

    for col in ["Gross Date", "DCM Date", "CDP Date", "Net Date"]:
        df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

    for col in ["Signup Value", "Net Reported Value"]:
        df[col] = df[col].astype(str).str.replace(",", "").str.strip()
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Has DCM"] = df["DCM Date"].notna().astype(int)
    df["Has CDP"] = df["CDP Date"].notna().astype(int)
    df["Has Net"] = df["Net Date"].notna().astype(int)

    typology_map = {
        "2BHK":"2BHK","3BHK":"3BHK","3.5BHK":"3BHK",
        "4BHK":"4BHK","4.5BHK":"4BHK",
        "5BHK":"5BHK","6BHK":"6BHK","8BHK":"6BHK",
    }
    df["Typology"] = df["Typlogy"].astype(str).str.strip().map(typology_map).fillna(df["Typlogy"].astype(str).str.strip())

    def clean_source(s):
        if pd.isna(s): return "Presales"
        s = str(s).strip().lower()
        if "channel" in s or "cp" in s: return "Channel Partner"
        if "referral" in s or "reference" in s: return "Referral"
        if "digital" in s or "online" in s or "social" in s or "google" in s: return "Digital"
        if "direct" in s or "walk" in s: return "Digital"
        if "developer" in s or "devloper" in s or "tie" in s: return "Developer"
        return "Presales"
    df["Source"] = df["Lead Source"].apply(clean_source)

    def get_quarter(dt):
        if pd.isna(dt): return "Unknown"
        y, m = dt.year, dt.month
        if y == 2025 and m in [4,5,6]: return "Q1"
        if y == 2025 and m in [7,8,9]: return "Q2"
        if y == 2025 and m in [10,11,12]: return "Q3"
        if y == 2026 and m in [1,2,3,4]: return "Q4"
        return "Other"
    df["Quarter"] = df["Gross Date"].apply(get_quarter)

    def sv_band(v):
        if pd.isna(v): return "Unknown"
        v = v / 1e5
        if v <= 20: return "≤20L"
        elif v <= 30: return "21–30L"
        elif v <= 40: return "31–40L"
        elif v <= 50: return "41–50L"
        elif v <= 75: return "51–75L"
        else: return "75L+"
    df["SV Band"] = df["Signup Value"].apply(sv_band)

    return df

df = load_data()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🏠 Bonito HVP Tool")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload updated dataset (CSV)", type="csv")
if uploaded_file:
    new_df = pd.read_csv(uploaded_file)
    new_df.columns = new_df.columns.str.strip()
    for col in ["Gross Date","DCM Date","CDP Date","Net Date"]:
        new_df[col] = pd.to_datetime(new_df[col], dayfirst=True, errors="coerce")
    for col in ["Signup Value","Net Reported Value"]:
        new_df[col] = new_df[col].astype(str).str.replace(",","").str.strip()
        new_df[col] = pd.to_numeric(new_df[col], errors="coerce")
    new_df["Has DCM"] = new_df["DCM Date"].notna().astype(int)
    new_df["Has CDP"] = new_df["CDP Date"].notna().astype(int)
    new_df["Has Net"] = new_df["Net Date"].notna().astype(int)
    df = new_df
    st.sidebar.success("✓ New data loaded")

st.sidebar.markdown("### 🔍 Filters")
all_quarters = ["Q1","Q2","Q3","Q4"]
all_ecs      = sorted(df["EC"].dropna().unique().tolist())
all_types    = ["2BHK","3BHK","4BHK","5BHK","6BHK"]
all_sources  = ["Channel Partner","Digital","Presales","Referral","Developer"]
all_sv_bands = ["≤20L","21–30L","31–40L","41–50L","51–75L","75L+"]

selected_quarters = st.sidebar.multiselect("Quarter", all_quarters, default=all_quarters)
selected_ecs      = st.sidebar.multiselect("Experience Centre", all_ecs, default=all_ecs)
selected_types    = st.sidebar.multiselect("Typology (BHK)", all_types, default=all_types)
selected_sources  = st.sidebar.multiselect("Lead Source", all_sources, default=all_sources)
selected_sv_bands = st.sidebar.multiselect("Signup Value Band", all_sv_bands, default=all_sv_bands)

st.sidebar.markdown("---")
st.sidebar.markdown("### 👤 People Filters")

all_cms = sorted(df["Gross CM"].dropna().unique().tolist()) if "Gross CM" in df.columns else []
selected_cms = st.sidebar.multiselect("Closing Manager", all_cms, default=all_cms) if all_cms else []

all_designers = sorted(df["Designer"].dropna().unique().tolist()) if "Designer" in df.columns else []
selected_designers = st.sidebar.multiselect("Designer", all_designers, default=all_designers) if all_designers else []

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
mask = (
    df["Quarter"].isin(selected_quarters) &
    df["EC"].isin(selected_ecs) &
    df["Typology"].isin(selected_types) &
    df["Source"].isin(selected_sources) &
    df["SV Band"].isin(selected_sv_bands)
)
if all_cms and selected_cms:
    mask = mask & df["Gross CM"].isin(selected_cms)
if all_designers and selected_designers:
    mask = mask & df["Designer"].isin(selected_designers)

filtered = df[mask].copy()

st.sidebar.markdown("---")
st.sidebar.metric("Leads in selection", len(filtered))
st.sidebar.metric("Converted (Net)", int(filtered["Has Net"].sum()))

# ── CORE METRICS ──────────────────────────────────────────────────────────────
g = len(filtered)
d = int(filtered["Has DCM"].sum())
c = int(filtered["Has CDP"].sum())
n = int(filtered["Has Net"].sum())

def pct(num, den):
    if den <= 0: return 0.0
    return max(0.0, min(round(num / den * 100, 1), 100.0))

conv_rate = pct(n, g)
g2d       = pct(d, g)
d2c       = pct(c, d)
c2n       = pct(n, c)
avg_sv    = filtered["Signup Value"].mean() / 1e5 if g > 0 else 0
avg_nv    = filtered[filtered["Has Net"]==1]["Net Reported Value"].mean() / 1e5 if n > 0 else 0
revenue   = filtered[filtered["Has Net"]==1]["Net Reported Value"].sum() / 1e7 if n > 0 else 0

EC_COL   = {"HRBR":"#1A3A5C","HSR":"#1A5C8A","MUM-THN":"#5C1A3A","MUM-ADH":"#083840"}
SRC_COL  = {"Channel Partner":"#1A3A5C","Digital":"#0A7A72","Referral":"#1A8040","Presales":"#C07010","Developer":"#8B1A1A"}
TYPE_COL = {"2BHK":"#1A8040","3BHK":"#0A7A72","4BHK":"#1A3A5C","5BHK":"#C07010","6BHK":"#8B1A1A"}
CHART_BG = dict(
    plot_bgcolor="white",
    paper_bgcolor="#F7F4EE",
    font=dict(color="#1A1A1A", size=12),
    title_font=dict(color="#1A1A1A", size=13),
    legend=dict(font=dict(color="#1A1A1A"), bgcolor="white", bordercolor="#DDDDDD", borderwidth=1),
    hoverlabel=dict(bgcolor="white", font_color="#1A1A1A", font_size=12),
    xaxis=dict(title_font=dict(color="#1A1A1A"), tickfont=dict(color="#1A1A1A")),
    yaxis=dict(title_font=dict(color="#1A1A1A"), tickfont=dict(color="#1A1A1A")),
)

st.markdown("# 🏠 Bonito Designs — HVP Pipeline Intelligence")
st.caption(f"Showing **{g} leads** · All data from Bonito Designs internal dataset")
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — HEADLINE METRICS
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 1 — HEADLINE METRICS</div>', unsafe_allow_html=True)

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total Grosses", g)
c2.metric("Net Conversions", n)
c3.metric("Overall Conv%", f"{conv_rate}%")
c4.metric("Avg Signup Val", f"₹{avg_sv:.1f}L")
c5.metric("Avg Net Value", f"₹{avg_nv:.1f}L")
c6.metric("Revenue", f"₹{revenue:.2f}Cr")

st.markdown("<br>", unsafe_allow_html=True)
c7,c8,c9,c10 = st.columns(4)
c7.metric("Gross→DCM Rate", f"{g2d}%", help=f"{d} of {g} leads")
c8.metric("DCM→CDP Rate", f"{d2c}%", help=f"{c} of {d} leads")
c9.metric("CDP→Net Rate", f"{c2n}%", help=f"{n} of {c} leads")
if "Status" in filtered.columns:
    c10.metric("Still Active", int((filtered["Status"]=="Active").sum()))

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — CONVERSION FUNNEL
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 2 — CONVERSION FUNNEL</div>', unsafe_allow_html=True)

col1, col2 = st.columns([1,2])
with col1:
    fd = pd.DataFrame({
        "Stage":      ["Gross","DCM","CDP","Net"],
        "Count":      [g, d, c, n],
        "% of Gross": ["100%", f"{g2d}%", f"{pct(c,g)}%", f"{conv_rate}%"],
        "Stage Rate": ["—", f"{g2d}%", f"{d2c}%", f"{c2n}%"],
        "Dropped":    ["—", str(g-d), str(d-c), str(c-n)],
        "Drop %":     ["—", f"{pct(g-d,g)}%", f"{pct(d-c,d)}%", f"{pct(c-n,c)}%"],
    })
    st.dataframe(fd, hide_index=True, use_container_width=True)
    st.caption(f"Total leads in selection: {g}")

with col2:
    fig = px.funnel(fd, x="Count", y="Stage",
        color_discrete_sequence=["#1A3A5C","#0A7A72","#C07010","#1A8040"])
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(l=10,r=10,t=20,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — EC PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 3 — EXPERIENCE CENTRE PERFORMANCE</div>', unsafe_allow_html=True)

ec = filtered.groupby("EC").agg(
    Grosses=("Has Net","count"), DCM=("Has DCM","sum"),
    CDP=("Has CDP","sum"), Nets=("Has Net","sum"),
    Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
    Revenue=("Net Reported Value","sum"),
).reset_index()
ec["Conv%"]      = ec.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
ec["G→DCM%"]     = ec.apply(lambda r: pct(r.DCM,  r.Grosses), axis=1)
ec["DCM→CDP%"]   = ec.apply(lambda r: pct(r.CDP,  r.DCM),     axis=1)
ec["CDP→Net%"]   = ec.apply(lambda r: pct(r.Nets, r.CDP),     axis=1)
ec["Avg SV(₹L)"] = (ec["Avg_SV"]/1e5).round(1)
ec["Avg NV(₹L)"] = (ec["Avg_NV"]/1e5).round(1)
ec["Rev(₹Cr)"]   = (ec["Revenue"]/1e7).round(2)
ec["Rev%"]       = ec.apply(lambda r: pct(r.Revenue, ec["Revenue"].sum()), axis=1)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(ec, x="EC", y="Conv%", title="Overall Conv Rate by EC (%)",
        color="EC", color_discrete_map=EC_COL, text="Conv%")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(ec, x="EC", y="Rev(₹Cr)", title="Revenue by EC (₹Cr)",
        color="EC", color_discrete_map=EC_COL, text="Rev(₹Cr)")
    fig.update_traces(texttemplate="₹%{text}Cr", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("**EC Complete Data Table**")
ec_show = ec[["EC","Grosses","DCM","CDP","Nets","G→DCM%","DCM→CDP%","CDP→Net%","Conv%","Avg SV(₹L)","Avg NV(₹L)","Rev(₹Cr)","Rev%"]].copy()
ec_show.columns = ["EC","Gross","DCM","CDP","Net","G→DCM%","DCM→CDP%","CDP→Net%","Overall%","Avg Signup(₹L)","Avg Net Val(₹L)","Revenue(₹Cr)","Rev%"]
st.dataframe(ec_show, hide_index=True, use_container_width=True)
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — TYPOLOGY
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 4 — TYPOLOGY ANALYSIS</div>', unsafe_allow_html=True)

typo_order = ["2BHK","3BHK","4BHK","5BHK","6BHK"]
ty = filtered.groupby("Typology").agg(
    Grosses=("Has Net","count"), Nets=("Has Net","sum"),
    Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
    Revenue=("Net Reported Value","sum"),
).reset_index()
ty = ty[ty["Typology"].isin(typo_order)].copy()
ty["Typology"] = pd.Categorical(ty["Typology"], categories=typo_order, ordered=True)
ty = ty.sort_values("Typology")
ty["Conv%"]      = ty.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
ty["Vol%"]       = ty.apply(lambda r: pct(r.Grosses, ty["Grosses"].sum()), axis=1)
ty["Avg SV(₹L)"] = (ty["Avg_SV"]/1e5).round(1)
ty["Avg NV(₹L)"] = (ty["Avg_NV"]/1e5).round(1)
ty["Rev(₹Cr)"]   = (ty["Revenue"]/1e7).round(2)
ty["Rev%"]       = ty.apply(lambda r: pct(r.Revenue, ty["Revenue"].sum()), axis=1)

col1, col2, col3 = st.columns(3)
with col1:
    fig = px.pie(ty, values="Grosses", names="Typology",
        title=f"Pipeline Volume — {g} leads",
        color="Typology", color_discrete_map=TYPE_COL)
    fig.update_traces(textfont_color="white")
    fig.update_layout(paper_bgcolor="#F7F4EE",
        font=dict(color="#1A1A1A"),
        title_font=dict(color="#1A1A1A"),
        legend=dict(font=dict(color="#1A1A1A"), bgcolor="white"),
        hoverlabel=dict(bgcolor="white", font_color="#1A1A1A"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(ty, x="Typology", y="Conv%", title="Conv Rate by Typology (%)",
        color="Typology", color_discrete_map=TYPE_COL, text="Conv%")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

with col3:
    fig = px.bar(ty, x="Typology", y="Rev(₹Cr)", title="Revenue by Typology (₹Cr)",
        color="Typology", color_discrete_map=TYPE_COL, text="Rev(₹Cr)")
    fig.update_traces(texttemplate="₹%{text}Cr", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("**Typology Complete Data Table**")
ty_show = ty[["Typology","Grosses","Vol%","Nets","Conv%","Avg SV(₹L)","Avg NV(₹L)","Rev(₹Cr)","Rev%"]].copy()
ty_show.columns = ["Typology","Gross","Vol%","Net","Conv%","Avg Signup(₹L)","Avg Net Val(₹L)","Revenue(₹Cr)","Rev%"]
st.dataframe(ty_show, hide_index=True, use_container_width=True)
st.caption("3.5BHK → 3BHK  ·  4.5BHK → 4BHK  ·  8BHK → 6BHK")
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — LEAD SOURCE
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 5 — LEAD SOURCE PERFORMANCE</div>', unsafe_allow_html=True)

src = filtered.groupby("Source").agg(
    Grosses=("Has Net","count"), Nets=("Has Net","sum"),
    Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
    Revenue=("Net Reported Value","sum"),
).reset_index()
src["Conv%"]      = src.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
src["Vol%"]       = src.apply(lambda r: pct(r.Grosses, src["Grosses"].sum()), axis=1)
src["Avg SV(₹L)"] = (src["Avg_SV"]/1e5).round(1)
src["Avg NV(₹L)"] = (src["Avg_NV"]/1e5).round(1)
src["Rev(₹Cr)"]   = (src["Revenue"]/1e7).round(2)
src["Rev%"]       = src.apply(lambda r: pct(r.Revenue, src["Revenue"].sum()), axis=1)

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(src.sort_values("Grosses", ascending=False),
        x="Source", y="Grosses", title="Volume by Source",
        color="Source", color_discrete_map=SRC_COL, text="Grosses")
    fig.update_traces(textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(src.sort_values("Conv%", ascending=False),
        x="Source", y="Conv%", title="Conv Rate by Source (%)",
        color="Source", color_discrete_map=SRC_COL, text="Conv%")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

fig = px.scatter(src, x="Grosses", y="Conv%", size="Nets", color="Source",
    title=f"Volume vs Conv Rate — bubble size = Nets — {g} leads",
    color_discrete_map=SRC_COL,
    hover_data={"Avg SV(₹L)":True,"Avg NV(₹L)":True,"Rev(₹Cr)":True,"Nets":True},
    text="Source")
fig.update_traces(textposition="top center", textfont_color="#1A1A1A")
fig.update_layout(**CHART_BG, margin=dict(t=50))
st.plotly_chart(fig, use_container_width=True)

st.markdown("**Lead Source Complete Data Table**")
src_show = src[["Source","Grosses","Vol%","Nets","Conv%","Avg SV(₹L)","Avg NV(₹L)","Rev(₹Cr)","Rev%"]].copy()
src_show.columns = ["Source","Gross","Vol%","Net","Conv%","Avg Signup(₹L)","Avg Net Val(₹L)","Revenue(₹Cr)","Rev%"]
st.dataframe(src_show, hide_index=True, use_container_width=True)
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — DEAL VALUE DISTRIBUTION
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 6 — DEAL VALUE DISTRIBUTION</div>', unsafe_allow_html=True)

sv_order = ["≤20L","21–30L","31–40L","41–50L","51–75L","75L+"]
sv = filtered.groupby("SV Band").agg(
    Grosses=("Has Net","count"), Nets=("Has Net","sum"),
    Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
).reset_index()
sv["Conv%"]      = sv.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
sv["Avg SV(₹L)"] = (sv["Avg_SV"]/1e5).round(1)
sv["Avg NV(₹L)"] = (sv["Avg_NV"]/1e5).round(1)
sv["SV Band"]    = pd.Categorical(sv["SV Band"], categories=sv_order, ordered=True)
sv = sv.sort_values("SV Band")

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(sv, x="SV Band", y="Grosses",
        title=f"Pipeline Volume by Signup Band — {g} leads",
        color_discrete_sequence=["#1A3A5C"], text="Grosses")
    fig.update_traces(textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(sv, x="SV Band", y="Conv%",
        title=f"Conv Rate by Signup Band (%)",
        color="SV Band",
        color_discrete_sequence=["#1A3A5C","#1A5C8A","#0A7A72","#C07010","#8B4500","#8B1A1A"],
        text="Conv%")
    fig.update_traces(texttemplate="%{text}%", textposition="outside", textfont_color="#1A1A1A")
    fig.update_layout(**CHART_BG, showlegend=False, margin=dict(t=50,b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown("**Signup Value Band Table**")
sv_show = sv[["SV Band","Grosses","Nets","Conv%","Avg SV(₹L)","Avg NV(₹L)"]].copy()
sv_show.columns = ["Signup Band","Gross","Net","Conv%","Avg Signup(₹L)","Avg Net Val(₹L)"]
st.dataframe(sv_show, hide_index=True, use_container_width=True)
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — CLOSING MANAGER PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
if "Gross CM" in filtered.columns:
    st.markdown('<div class="section-header">SECTION 7 — CLOSING MANAGER PERFORMANCE</div>', unsafe_allow_html=True)

    cm = filtered.groupby(["Gross CM","EC"]).agg(
        Grosses=("Has Net","count"), DCM=("Has DCM","sum"),
        CDP=("Has CDP","sum"), Nets=("Has Net","sum"),
        Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
        Revenue=("Net Reported Value","sum"),
    ).reset_index()
    cm = cm[cm["Grosses"] >= 3].copy()
    cm["Conv%"]      = cm.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
    cm["G→DCM%"]     = cm.apply(lambda r: pct(r.DCM,  r.Grosses), axis=1)
    cm["CDP→Net%"]   = cm.apply(lambda r: pct(r.Nets, r.CDP),     axis=1)
    cm["Avg SV(₹L)"] = (cm["Avg_SV"]/1e5).round(1)
    cm["Avg NV(₹L)"] = (cm["Avg_NV"]/1e5).round(1)
    cm["Rev(₹Cr)"]   = (cm["Revenue"]/1e7).round(2)
    cm = cm.sort_values("Conv%", ascending=False)

    st.markdown("**CM Data Table** — CMs with ≥3 Grosses in current selection")
    cm_show = cm[["Gross CM","EC","Grosses","DCM","CDP","Nets","G→DCM%","CDP→Net%","Conv%","Avg SV(₹L)","Avg NV(₹L)","Rev(₹Cr)"]].copy()
    cm_show.columns = ["CM","EC","Gross","DCM","CDP","Net","G→DCM%","CDP→Net%★","Overall%","Avg Signup(₹L)","Avg Net Val(₹L)","Revenue(₹Cr)"]
    st.dataframe(cm_show, hide_index=True, use_container_width=True)
    st.caption("★ CDP→Net% = closing skill — ability to convert a live interested lead")
    st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — DESIGNER PERFORMANCE
# ═════════════════════════════════════════════════════════════════════════════
if "Designer" in filtered.columns:
    st.markdown('<div class="section-header">SECTION 8 — DESIGNER PERFORMANCE</div>', unsafe_allow_html=True)

    des = filtered.groupby(["Designer","EC"]).agg(
        Grosses=("Has Net","count"), Nets=("Has Net","sum"),
        Avg_SV=("Signup Value","mean"), Avg_NV=("Net Reported Value","mean"),
        Revenue=("Net Reported Value","sum"),
    ).reset_index()
    des = des[des["Grosses"] >= 3].copy()
    des["Conv%"]      = des.apply(lambda r: pct(r.Nets, r.Grosses), axis=1)
    des["Avg SV(₹L)"] = (des["Avg_SV"]/1e5).round(1)
    des["Avg NV(₹L)"] = (des["Avg_NV"]/1e5).round(1)
    des["Rev(₹Cr)"]   = (des["Revenue"]/1e7).round(2)
    des = des.sort_values("Conv%", ascending=False)

    st.markdown("**Designer Data Table** — Designers with ≥3 leads in current selection")
    des_show = des[["Designer","EC","Grosses","Nets","Conv%","Avg SV(₹L)","Avg NV(₹L)","Rev(₹Cr)"]].copy()
    des_show.columns = ["Designer","EC","Gross","Net","Conv%","Avg Signup(₹L)","Avg Net Val(₹L)","Revenue(₹Cr)"]
    st.dataframe(des_show, hide_index=True, use_container_width=True)
    st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9 — TIMING INTELLIGENCE
# ═════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">SECTION 9 — TIMING INTELLIGENCE</div>', unsafe_allow_html=True)

tim = filtered.copy()
tim["G→N"] = (tim["Net Date"]  - tim["Gross Date"]).dt.days
tim["G→D"] = (tim["DCM Date"]  - tim["Gross Date"]).dt.days
tim["D→C"] = (tim["CDP Date"]  - tim["DCM Date"]).dt.days
tim["C→N"] = (tim["Net Date"]  - tim["CDP Date"]).dt.days
conv = tim[tim["Has Net"]==1].copy()

col1, col2 = st.columns([2,1])
with col1:
    gn_valid = conv["G→N"].dropna()
    gn_valid = gn_valid[gn_valid >= 0]
    if len(gn_valid) > 0:
        temp = conv[conv["G→N"] >= 0].copy()
        temp["Band"] = pd.cut(temp["G→N"],
            bins=[0,7,14,21,30,60,200],
            labels=["0–7d","8–14d","15–21d","22–30d","31–60d","60d+"])
        bc = temp["Band"].value_counts().sort_index().reset_index()
        bc.columns = ["Days to Close","Count"]
        fig = px.bar(bc, x="Days to Close", y="Count",
            title=f"Gross→Net Days Distribution — {len(gn_valid)} converted leads",
            color_discrete_sequence=["#1A3A5C"], text="Count")
        fig.update_traces(textposition="outside", textfont_color="#1A1A1A")
        fig.update_layout(**CHART_BG, margin=dict(t=50,b=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    gn = conv["G→N"].dropna()
    gn = gn[gn >= 0]
    if len(gn) > 0:
        st.metric("Median G→Net", f"{gn.median():.0f} days")
        st.metric("Mean G→Net", f"{gn.mean():.1f} days")
        st.metric("Convert ≤14 days", f"{pct(len(gn[gn<=14]), len(gn))}%")
        st.metric("Convert ≤21 days", f"{pct(len(gn[gn<=21]), len(gn))}%")

st.markdown("**Stage-by-Stage Timing**")
timing_rows = []
for stage, col in [("Gross→DCM","G→D"),("DCM→CDP","D→C"),("CDP→Net","C→N"),("Gross→Net","G→N")]:
    v = conv[col].dropna()
    v = v[v >= 0]
    if len(v) > 0:
        timing_rows.append({
            "Stage":         stage,
            "Leads":         len(v),
            "Mean (days)":   round(v.mean(), 1),
            "Median (days)": round(v.median(), 1),
            "Min":           int(v.min()),
            "Max":           int(v.max()),
        })
if timing_rows:
    st.dataframe(pd.DataFrame(timing_rows), hide_index=True, use_container_width=True)
    st.caption("Timing calculated only from leads with complete and valid date records")
