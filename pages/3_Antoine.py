import streamlit as st
import plotly.graph_objects as go

st.markdown("### 📊 Indicateurs Stratégiques — Antoine")

k1, k2, k3 = st.columns(3)
k1.metric("Pertes évitées", "312 000 €", delta="+14 alertes")
k2.metric("Taux Disponibilité (OEE)", "96.4 %", delta="+2.1 %")
k3.metric("ROI Prescriptive", "7.6 x")

st.markdown("---")
st.markdown("#### 🔮 Plan de renouvellement matériel")
mode_invest = st.selectbox("Scénario budgétaire :", ["Conserver la pompe P-17", "Remplacer par AlphaFlow-18"])

fig_cap = go.Figure()
if "Conserver" in mode_invest:
    fig_cap.add_trace(go.Scatter(x=['Actuel', 'Année +1', 'Année +2'], y=[12000, 29000, 55000], name="Opex", line=dict(color='#f59e0b')))
else:
    fig_cap.add_trace(go.Scatter(x=['Actuel', 'Année +1', 'Année +2'], y=[80000, 82000, 84000], name="Capex", line=dict(color='#10b981')))
st.plotly_chart(fig_cap, use_container_width=True)
