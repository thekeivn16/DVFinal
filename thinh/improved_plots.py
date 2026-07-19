import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import ast
import numpy as np
import os

# Create output directory
output_dir = 'analysis_plots'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# Load data
jobs_df = pd.read_csv('dataset/careerviet_all_jobs.csv')
industries_df = pd.read_csv('dataset/careerviet_industries.csv')

# --- Preprocessing ---

# 1. Clean Salary columns
jobs_df['job_from_salary'] = pd.to_numeric(jobs_df['job_from_salary'], errors='coerce')
jobs_df['job_to_salary'] = pd.to_numeric(jobs_df['job_to_salary'], errors='coerce')
jobs_df['median_salary'] = (jobs_df['job_from_salary'] + jobs_df['job_to_salary']) / 2

# 2. Premium and Urgent status
jobs_df['is_premium'] = jobs_df['job_premium_icon_item'].fillna(0).astype(int)
jobs_df['is_urgent'] = jobs_df['job_is_urgent_job'].fillna(0).astype(int)
jobs_df['premium_label'] = jobs_df['is_premium'].map({1: 'Premium', 0: 'Non-Premium'})
jobs_df['urgent_label'] = jobs_df['is_urgent'].map({1: 'Urgent', 0: 'Not Urgent'})

# 3. Industry Mapping
def parse_industries(val):
    try:
        if isinstance(val, str):
            ids = ast.literal_eval(val)
            if isinstance(ids, list) and len(ids) > 0:
                return ids[0]
    except:
        pass
    return np.nan

jobs_df['main_industry_id'] = jobs_df['top_industries'].apply(parse_industries)
jobs_df = jobs_df.merge(industries_df[['industry_id', 'industry_name_en']], left_on='main_industry_id', right_on='industry_id', how='left')

# 4. Outlier Handling for plotting
salary_data = jobs_df.dropna(subset=['job_from_salary']).copy()
# Cap at 99th percentile to see the distribution better
cap_value = salary_data['job_from_salary'].quantile(0.99)
salary_data['job_from_salary_capped'] = salary_data['job_from_salary'].clip(upper=cap_value)

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.size'] = 11

# --- Plot 1: Split Violin Plot ---
plt.figure(figsize=(10, 6))
sns.violinplot(
    data=salary_data, 
    x='urgent_label', 
    y='job_from_salary_capped', 
    hue='premium_label', 
    split=True, 
    palette={'Premium': '#f39c12', 'Non-Premium': '#3498db'},
    inner='quart'
)
plt.title('Salary Distribution: Premium vs Non-Premium by Urgency', fontsize=14)
plt.ylabel('Min Salary (VND, capped at 99th percentile)')
plt.xlabel('Urgent Status')
plt.savefig(os.path.join(output_dir, 'suggested_split_violin.png'), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 2: 2D Density Heatmap ---
# We focus on Premium jobs to see where they "live"
premium_only = salary_data[salary_data['is_premium'] == 1]
plt.figure(figsize=(10, 7))
# Using histplot as a heatmap
sns.histplot(
    data=salary_data,
    x='is_urgent',
    y='job_from_salary_capped',
    hue='premium_label',
    bins=[2, 20], # 2 bins for binary X, 20 for continuous Y
    pthresh=.05,
    pmax=.9,
    cmap='YlGnBu'
)
plt.title('Job Density Heatmap: Salary vs Urgency', fontsize=14)
plt.xticks([0, 1], ['Not Urgent', 'Urgent'])
plt.ylabel('Min Salary (VND)')
plt.savefig(os.path.join(output_dir, 'suggested_density_heatmap.png'), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 3: Aggregated Industry Bubble Chart ---
industry_agg = jobs_df.groupby('industry_name_en').agg(
    total_jobs=('is_premium', 'count'),
    premium_rate=('is_premium', 'mean'),
    urgent_rate=('is_urgent', 'mean'),
    median_salary=('job_from_salary', 'median')
).reset_index()

# Filter for industries with enough data points
industry_agg = industry_agg[industry_agg['total_jobs'] > 50].sort_values('premium_rate', ascending=False)

plt.figure(figsize=(12, 8))
scatter = plt.scatter(
    x=industry_agg['median_salary'],
    y=industry_agg['urgent_rate'],
    s=industry_agg['total_jobs'] * 0.5, # Size by job count
    c=industry_agg['premium_rate'], # Color by premium rate
    cmap='plasma',
    alpha=0.7,
    edgecolors='w'
)
plt.colorbar(scatter, label='Premium Feature Usage Rate')

# Add labels to top points
for i, row in industry_agg.head(10).iterrows():
    plt.annotate(row['industry_name_en'], (row['median_salary'], row['urgent_rate']), fontsize=9, alpha=0.8)

plt.title('Industry Strategy Map: Median Salary vs Urgency Rate', fontsize=14)
plt.xlabel('Median Starting Salary (VND)')
plt.ylabel('Urgent Job Rate')
plt.grid(True, linestyle='--', alpha=0.6)
plt.savefig(os.path.join(output_dir, 'suggested_industry_bubble.png'), dpi=300, bbox_inches='tight')
plt.close()

print("New suggested plots saved to analysis_plots/")
