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
df = pd.read_csv('dataset/careerviet_all_jobs.csv')
industries_df = pd.read_csv('dataset/careerviet_industries.csv')

# --- Preprocessing ---
df['is_premium'] = df['job_premium_icon_item'].fillna(0).astype(int)
df['is_urgent'] = df['job_is_urgent_job'].fillna(0).astype(int)

# Categorize Salary Type
df['salary_type'] = np.where(df['job_salary_string'] == 'Competition', 'Competitive (Thỏa thuận)', 'Numeric (Có con số)')

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

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams['font.size'] = 11

# --- Plot 1: Premium Rate by Salary Type ---
plt.figure(figsize=(8, 6))
sns.barplot(data=df, x='salary_type', y='is_premium', palette='muted')
plt.title('Premium Feature Usage Rate: Numeric vs Competitive', fontsize=14)
plt.ylabel('Premium Rate (%)')
plt.xlabel('Salary Visibility')
plt.savefig(os.path.join(output_dir, 'comp_premium_rate.png'), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 2: Industry Transparency ---
industry_trans = df.groupby('industry_name_en')['salary_type'].value_counts(normalize=True).unstack().fillna(0)
# Sort by % of Competitive roles
industry_trans = industry_trans.sort_values('Competitive (Thỏa thuận)', ascending=False).head(20)

plt.figure(figsize=(12, 8))
industry_trans.plot(kind='barh', stacked=True, color=['#e67e22', '#3498db'], ax=plt.gca())
plt.title('Industry Preference: Numeric vs Competitive Salaries', fontsize=14)
plt.xlabel('Proportion')
plt.ylabel('Industry')
plt.legend(title='Salary Type', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'comp_industry_stacked.png'), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 3: Experience Proxy ---
# Map experience to numeric
def clean_exp(val):
    try:
        return float(val)
    except:
        return np.nan
df['exp_num'] = df['job_experience'].apply(clean_exp)

plt.figure(figsize=(10, 6))
sns.violinplot(data=df.dropna(subset=['exp_num']), x='salary_type', y='exp_num', palette='Set2', split=True)
plt.title('Required Experience: Numeric vs Competitive Roles', fontsize=14)
plt.ylabel('Years of Experience')
plt.xlabel('Salary Visibility')
plt.savefig(os.path.join(output_dir, 'comp_experience_dist.png'), dpi=300, bbox_inches='tight')
plt.close()

# --- Plot 4: Urgency Rate ---
plt.figure(figsize=(8, 6))
sns.barplot(data=df, x='salary_type', y='is_urgent', palette='magma')
plt.title('Urgency Rate: Numeric vs Competitive Salaries', fontsize=14)
plt.ylabel('Urgency Rate (%)')
plt.xlabel('Salary Visibility')
plt.savefig(os.path.join(output_dir, 'comp_urgency_rate.png'), dpi=300, bbox_inches='tight')
plt.close()

print("Competitive Salary analysis plots saved to analysis_plots/")
