import pandas as pd
import plotly.express as px
import ast
import numpy as np
import os

# Create output directory
output_dir = 'analysis_plots'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load data
df = pd.read_csv('dataset/careerviet_all_jobs.csv')
industries_df = pd.read_csv('dataset/careerviet_industries.csv')

# --- Preprocessing ---
df['is_premium'] = df['job_premium_icon_item'].fillna(0).astype(int)
df['is_urgent'] = df['job_is_urgent_job'].fillna(0).astype(int)
df['premium_label'] = df['is_premium'].map({1: 'Premium', 0: 'Non-Premium'})
df['urgent_label'] = df['is_urgent'].map({1: 'Urgent', 0: 'Not Urgent'})

# Clean Salary
df['salary'] = pd.to_numeric(df['job_from_salary'], errors='coerce')

# Clean Experience
def clean_exp(val):
    try:
        return float(val)
    except:
        return np.nan
df['exp_num'] = df['job_experience'].apply(clean_exp)

# Industry Mapping
def parse_industries(val):
    try:
        if isinstance(val, str):
            ids = ast.literal_eval(val)
            if isinstance(ids, list) and len(ids) > 0:
                return ids[0]
    except:
        pass
    return np.nan

df['main_industry_id'] = df['top_industries'].apply(parse_industries)
df = df.merge(industries_df[['industry_id', 'industry_name_en']], left_on='main_industry_id', right_on='industry_id', how='left')

# Drop NaNs for the multi-dim plot
plot_df = df.dropna(subset=['salary', 'exp_num', 'industry_name_en']).copy()

# Cap outliers for better visualization
cap_sal = plot_df['salary'].quantile(0.99)
cap_exp = plot_df['exp_num'].quantile(0.99)
plot_df['salary_capped'] = plot_df['salary'].clip(upper=cap_sal)
plot_df['exp_capped'] = plot_df['exp_num'].clip(upper=cap_exp)

# --- 4D Interactive Plot (X, Y, Color, Facet) ---
fig = px.scatter(
    plot_df,
    x="salary_capped",
    y="exp_capped",
    color="premium_label",
    facet_col="urgent_label",
    hover_data=['job_title', 'industry_name_en', 'emp_name'],
    color_discrete_map={'Premium': '#f39c12', 'Non-Premium': '#3498db'},
    labels={
        "salary_capped": "Min Salary (VND)",
        "exp_capped": "Years of Experience",
        "premium_label": "Job Type",
        "urgent_label": "Urgency"
    },
    title="4D Analysis: Salary vs Experience vs Premium vs Urgency",
    template="plotly_white",
    opacity=0.6
)

# Save as HTML for interactivity
html_path = os.path.join(output_dir, 'interactive_strategy_map.html')
fig.write_html(html_path)

# --- Summary Statistics for Evaluation ---
print("--- Correlation Matrix (Numeric Dimensions) ---")
corr = plot_df[['salary', 'exp_num', 'is_premium', 'is_urgent']].corr()
print(corr)

print("\n--- Strategy Grouping (Medians) ---")
summary = plot_df.groupby(['urgent_label', 'premium_label']).agg(
    median_salary=('salary', 'median'),
    median_exp=('exp_num', 'median'),
    count=('job_id', 'count')
).reset_index()
print(summary)

print(f"\nInteractive plot saved to: {html_path}")
