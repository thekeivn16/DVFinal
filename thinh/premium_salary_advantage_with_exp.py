import pandas as pd
import numpy as np

def find_premium_salary_advantage_with_exp():
    print("Loading datasets...")
    exploded_df = pd.read_csv('dataset/exploded_ngành.csv')
    original_df = pd.read_csv('dataset/careerviet_updated_jobs.csv', usecols=['job_id', 'job_premium_icon_item'])
    
    print("Merging data...")
    df = pd.merge(exploded_df, original_df, left_on='mã công việc', right_on='job_id', how='left')
    
    # Filter for:
    # 1. 'Gấp' (Urgent) jobs (khẩn cấp == 1)
    # 2. Disclosed salaries (lương cạnh tranh == -1)
    # 3. MUST HAVE EXPERIENCE (kinh nghiệm từ (năm) is not null)
    print("Filtering data (Urgent + Disclosed Salary + Has Experience)...")
    valid_df = df[
        (df['khẩn cấp'] == 1) & 
        (df['lương cạnh tranh'] == -1) & 
        (df['kinh nghiệm từ (năm)'].notna())
    ].copy()
    
    valid_df['avg_salary'] = (valid_df['lương từ'] + valid_df['lương đến']) / 2
    
    # Group by ngành and Premium status (1 = Premium, 0 = Thường)
    grouped = valid_df.groupby(['ngành', 'job_premium_icon_item'])['avg_salary'].mean().unstack()
    
    # Rename columns
    grouped.columns = ['Thường & Gấp', 'Premium & Gấp']
    
    # Drop rows where either is NaN
    results = grouped.dropna()
    
    # Find where Premium > Thường
    advantage = results[results['Premium & Gấp'] > results['Thường & Gấp']].copy()
    advantage['Diff'] = advantage['Premium & Gấp'] - advantage['Thường & Gấp']
    advantage['Diff %'] = (advantage['Diff'] / advantage['Thường & Gấp']) * 100
    
    # Add count of jobs to see sample size
    counts = valid_df.groupby(['ngành', 'job_premium_icon_item']).size().unstack()
    counts.columns = ['Count Thường', 'Count Premium']
    final_results = pd.concat([advantage, counts], axis=1, join='inner')
    
    print("\n--- Ngành where Premium & Gấp (with Experience) avg salary is HIGHER ---")
    if final_results.empty:
        print("None found.")
    else:
        print(final_results.sort_values(by='Diff', ascending=False))
        
    # Save to CSV
    output_path = 'thinh/premium_salary_advantage_with_exp.csv'
    final_results.to_csv(output_path)
    print(f"\nFull results saved to: {output_path}")

if __name__ == "__main__":
    find_premium_salary_advantage_with_exp()
