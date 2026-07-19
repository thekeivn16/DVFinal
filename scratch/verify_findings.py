import pandas as pd
import numpy as np
import ast
import os

# Configuration
DATA_PATH = 'dataset/careerviet_all_jobs.csv'
INDUSTRIES_PATH = 'dataset/careerviet_industries.csv'

def parse_industries(val):
    try:
        if isinstance(val, str):
            ids = ast.literal_eval(val)
            if isinstance(ids, list) and len(ids) > 0:
                return ids[0]
    except:
        pass
    return np.nan

def clean_exp(val):
    try:
        return float(val)
    except:
        return np.nan

def run_verification():
    print("--- 1. LOADING DATA ---")
    df = pd.read_csv(DATA_PATH)
    industries_df = pd.read_csv(INDUSTRIES_PATH)
    
    # Preprocessing
    df['from_salary'] = pd.to_numeric(df['job_from_salary'], errors='coerce')
    df['is_premium'] = df['job_premium_icon_item'].fillna(0).astype(int)
    df['is_urgent'] = df['job_is_urgent_job'].fillna(0).astype(int)
    df['exp'] = df['job_experience'].apply(clean_exp)
    
    # Industry Mapping
    df['industry_id'] = df['top_industries'].apply(parse_industries)
    df = df.merge(industries_df[['industry_id', 'industry_name_en']], on='industry_id', how='left')
    
    print(f"Total jobs: {len(df)}")
    
    print("\n--- 2. VERIFYING 50M CEILING ---")
    exact_50m = df[df['from_salary'] == 50_000_000]
    near_50m = df[(df['from_salary'] >= 45_000_000) & (df['from_salary'] <= 55_000_000)]
    print(f"Jobs at exactly 50M: {len(exact_50m)}")
    print(f"Jobs between 45M-55M: {len(near_50m)}")
    if len(exact_50m) > 0:
        print(f"Average experience for 50M roles: {exact_50m['exp'].mean():.2f} years")

    print("\n--- 3. VERIFYING EXPERIENCE-SALARY PARADOX ---")
    paradox_jobs = df[(df['exp'] >= 15) & (df['from_salary'] >= 20_000_000) & (df['from_salary'] <= 30_000_000)]
    high_exp_total = df[df['exp'] >= 15]
    print(f"Jobs with 15+ years exp: {len(high_exp_total)}")
    print(f"Jobs with 15+ years exp AND 20M-30M salary: {len(paradox_jobs)}")
    if len(high_exp_total) > 0:
        print(f"Percentage of high-exp roles in 'low' salary bracket: {len(paradox_jobs)/len(high_exp_total)*100:.2f}%")

    print("\n--- 4. INDUSTRY STRATEGY COMPARISON ---")
    target_industries = ['Sales / Business Development', 'Finance / Investment', 'IT - Software', 'Banking']
    stats = []
    for ind in target_industries:
        sub = df[df['industry_name_en'] == ind]
        if len(sub) > 0:
            stats.append({
                'Industry': ind,
                'Median Salary': sub['from_salary'].median(),
                'Urgency Rate': sub['is_urgent'].mean(),
                'Premium Rate': sub['is_premium'].mean(),
                'Avg Exp': sub['exp'].mean()
            })
    
    stats_df = pd.DataFrame(stats)
    print(stats_df.to_string(index=False))

    print("\n--- 5. SALARY PLATEAU ANALYSIS ---")
    df['exp_bucket'] = pd.cut(df['exp'], bins=[0, 2, 5, 10, 15, 30], labels=['0-2', '2-5', '5-10', '10-15', '15+'])
    plateau = df.groupby('exp_bucket', observed=True)['from_salary'].median().reset_index()
    print(plateau.to_string(index=False))

if __name__ == "__main__":
    run_verification()
