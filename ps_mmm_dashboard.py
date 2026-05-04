import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import snowflake.connector
import os

st.set_page_config(page_title="Subscription MMM Dashboard", layout="wide")
st.title("Subscriber Growth — Marketing Mix Model")
st.caption("Built with Cortex Code | OLS Regression with Adstock Decay (λ=0.7)")

MODEL_COEFFICIENTS = {
    "META": 0.006716,
    "TIKTOK": -0.018241,
    "YOUTUBE": 0.008473,
    "SEM": 0.017966,
    "DV360": 0.044294,
    "REDDIT": -0.043105,
    "SNAP": -0.089642,
    "X": -0.062939,
    "HULU_CTV": 0.014185,
    "ROKU_CTV": 0.006917,
    "TWITCH": -0.027708,
}

P_VALUES = {
    "META": 0.3652,
    "TIKTOK": 0.0283,
    "YOUTUBE": 0.1111,
    "SEM": 0.0585,
    "DV360": 0.0101,
    "REDDIT": 0.0860,
    "SNAP": 0.0118,
    "X": 0.0103,
    "HULU_CTV": 0.0008,
    "ROKU_CTV": 0.0934,
    "TWITCH": 0.0181,
}

CURRENT_SPEND_MM = {
    "META": 34.43,
    "TIKTOK": 26.58,
    "YOUTUBE": 42.25,
    "SEM": 21.90,
    "DV360": 14.71,
    "REDDIT": 9.73,
    "SNAP": 7.37,
    "X": 8.54,
    "HULU_CTV": 54.43,
    "ROKU_CTV": 46.13,
    "TWITCH": 18.24,
}

MODEL_STATS = {"r_squared": 0.5043, "adj_r_squared": 0.4526, "f_stat": 9.76, "f_pvalue": 0.000000}
OTHER_COEFFICIENTS = {"OWNED_SOCIAL_ENGAGEMENT": 0.001530, "IS_WEEKEND": 1108.68, "WEB_SIGNUPS": 0.4848, "CONSTANT": 103.59}

contributions = {}
for ch, coef in MODEL_COEFFICIENTS.items():
    contributions[ch] = abs(coef * CURRENT_SPEND_MM[ch] * 1e6 / 181 * 3.33)
total_c = sum(contributions.values())
contributions_pct = {k: v / total_c * 100 for k, v in contributions.items()}

col1, col2, col3 = st.columns(3)
col1.metric("R-squared", f"{MODEL_STATS['r_squared']:.3f}")
col2.metric("F-statistic", f"{MODEL_STATS['f_stat']:.1f}")
col3.metric("Significant Channels (p<0.05)", "6 of 11")

st.divider()

tab1, tab2, tab3 = st.tabs(["Channel Contribution", "Model Coefficients", "Budget Optimizer"])

with tab1:
    st.subheader("Channel Contribution to Subscriber Growth")
    sorted_contrib = sorted(contributions_pct.items(), key=lambda x: -x[1])
    channels = [c[0] for c in sorted_contrib]
    pcts = [c[1] for c in sorted_contrib]
    colors = ['#29B5E8' if MODEL_COEFFICIENTS[ch] > 0 else '#f87171' for ch in channels]

    fig = go.Figure(go.Bar(
        x=pcts, y=channels, orientation='h',
        marker_color=colors,
        text=[f"{p:.1f}%" for p in pcts],
        textposition='outside'
    ))
    fig.update_layout(
        height=450, xaxis_title="% Contribution to Explained Variance",
        yaxis=dict(autorange="reversed"),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#f0f0f5'),
        margin=dict(l=100, r=40, t=20, b=40)
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Blue = positive effect on subscriber growth | Red = negative (spend here correlates with LOWER growth)")

with tab2:
    st.subheader("OLS Regression Coefficients")
    coef_df = pd.DataFrame([
        {"Channel": ch, "Coefficient": coef, "p-value": P_VALUES[ch],
         "Significant": "YES" if P_VALUES[ch] < 0.05 else "no",
         "Direction": "+" if coef > 0 else "-"}
        for ch, coef in MODEL_COEFFICIENTS.items()
    ]).sort_values("p-value")

    st.dataframe(
        coef_df.style.apply(
            lambda row: ['background-color: #1a3a2a' if row['Significant'] == 'YES' else 'background-color: #3a1a1a'] * len(row),
            axis=1
        ),
        use_container_width=True, hide_index=True
    )
    st.markdown("""
    **Interpretation**: Each coefficient represents the change in daily net subscriber adds
    per $1 increase in adstock-transformed channel spend.
    - **Hulu CTV (+0.014)**: Every $1K in Hulu spend → ~14 additional net subs (strongest positive signal)
    - **DV360 (+0.044)**: Programmatic display is efficient for subscriber acquisition
    - **Snap/X/Twitch (negative)**: Spend on these channels correlates with LOWER growth — possible audience mismatch or saturation
    """)

with tab3:
    st.subheader("Budget Optimizer")
    st.markdown("Adjust channel allocation and see predicted impact on subscriber growth.")

    new_spend = {}
    cols = st.columns(3)
    for i, (ch, current) in enumerate(CURRENT_SPEND_MM.items()):
        with cols[i % 3]:
            new_spend[ch] = st.slider(
                f"{ch} ($M/6mo)", min_value=0.0, max_value=current * 2.5,
                value=current, step=0.5, key=ch
            )

    baseline_predicted = sum(MODEL_COEFFICIENTS[ch] * CURRENT_SPEND_MM[ch] * 1e6 / 181 for ch in MODEL_COEFFICIENTS)
    new_predicted = sum(MODEL_COEFFICIENTS[ch] * new_spend[ch] * 1e6 / 181 for ch in MODEL_COEFFICIENTS)
    daily_lift = new_predicted - baseline_predicted
    period_lift = daily_lift * 181

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Daily Predicted Lift", f"{daily_lift:+,.0f} net subs/day")
    c2.metric("6-Month Predicted Lift", f"{period_lift:+,.0f} total net subs")
    budget_change = sum(new_spend.values()) - sum(CURRENT_SPEND_MM.values())
    c3.metric("Budget Change", f"${budget_change:+,.1f}M")

    if period_lift > 0:
        st.success(f"This reallocation would add an estimated **{period_lift:,.0f}** additional subscribers over 6 months.")
    elif period_lift < 0:
        st.warning(f"This reallocation would reduce subscriber growth by an estimated **{abs(period_lift):,.0f}** over 6 months.")
    else:
        st.info("No change from baseline.")
