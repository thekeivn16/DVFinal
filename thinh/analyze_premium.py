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

# 1. Clean Salary columns (handle missing and Competition)
# job_salary_string can be "Competition"
# job_from_salary and job_to_salary might be NaN
jobs_df['job_from_salary'] = pd.to_numeric(jobs_df['job_from_salary'], errors='coerce')
jobs_df['job_to_salary'] = pd.to_numeric(jobs_df['job_to_salary'], errors='coerce')

# Calculate median salary for jobs that have salary info
jobs_df['median_salary'] = (jobs_df['job_from_salary'] + jobs_df['job_to_salary']) / 2

# 2. Premium and Urgent status
jobs_df['is_premium'] = jobs_df['job_premium_icon_item'].fillna(0).astype(int)
jobs_df['is_urgent'] = jobs_df['job_is_urgent_job'].fillna(0).astype(int)
jobs_df['premium_label'] = jobs_df['is_premium'].map({1: 'Premium', 0: 'Non-Premium'})

# 3. Industry Mapping
def parse_industries(val):
    try:
        if isinstance(val, str):
            ids = ast.literal_eval(val)
            if isinstance(ids, list) and len(ids) > 0:
                return ids[0] # Take the first industry for simplicity
    except:
        pass
    return np.nan

jobs_df['main_industry_id'] = jobs_df['top_industries'].apply(parse_industries)
# Join with industry names
jobs_df = jobs_df.merge(industries_df[['industry_id', 'industry_name_en']], left_on='main_industry_id', right_on='industry_id', how='left')

# --- Visualization ---

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.size'] = 12

# Fig 1: Boxplot Salary
plt.figure(figsize=(10, 6))
# Filter out rows without salary for the boxplot
salary_data = jobs_df.dropna(subset=['job_from_salary'])
sns.boxplot(x='premium_label', y='job_from_salary', data=salary_data, palette='viridis')
plt.title('Salary Distribution (Min): Premium vs Non-Premium', fontsize=15)
plt.ylabel('Min Salary (VND)')
plt.xlabel('Job Type')
plt.savefig(os.path.join(output_dir, 'salary_boxplot.png'))
plt.close()

# Fig 2: Scatter Salary vs Urgent (Premium Color)
plt.figure(figsize=(10, 6))
# Adding a small jitter to urgent (which is 0/1) to see density if needed, but scatter usually uses discrete for one axis here
# However, the prompt asks for Salary vs Urgent. Since Urgent is binary, we can use a stripplot or jittered scatter.
sns.stripplot(x='is_urgent', y='job_from_salary', hue='premium_label', data=salary_data, alpha=0.5, jitter=True)
plt.title('Min Salary vs Urgency (Colored by Premium Status)', fontsize=15)
plt.ylabel('Min Salary (VND)')
plt.xlabel('Urgent Status (0: No, 1: Yes)')
plt.savefig(os.path.join(output_dir, 'salary_vs_urgent_scatter.png'))
plt.close()

# Fig 3: Stacked Bar Premium Rate by Industry
# Calculate premium rate per industry
industry_stats = jobs_df.groupby('industry_name_en').agg(
    total_jobs=('is_premium', 'count'),
    premium_jobs=('is_premium', 'sum')
).reset_index()

industry_stats['premium_rate'] = industry_stats['premium_jobs'] / industry_stats['total_jobs']
industry_stats['non_premium_rate'] = 1 - industry_stats['premium_rate']

# Sort by premium rate for better visualization
industry_stats = industry_stats.sort_values('premium_rate', ascending=False).head(15) # Top 15 industries

plt.figure(figsize=(12, 8))
industry_stats.set_index('industry_name_en')[['premium_rate', 'non_premium_rate']].plot(kind='barh', stacked=True, color=['#f39c12', '#3498db'], ax=plt.gca())
plt.title('Premium Job Rate by Top 15 Industries', fontsize=15)
plt.xlabel('Proportion')
plt.ylabel('Industry')
plt.legend(['Premium', 'Non-Premium'], bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'premium_rate_industry.png'))
plt.close()

print("Visualizations saved to artifacts directory.")
