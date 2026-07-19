import pandas as pd
import numpy as np

def find_premium_salary_advantage():
    print("Loading datasets...")
    # Exploded industries dataset
    exploded_df = pd.read_csv('dataset/exploded_ngành.csv')
    
    # Original dataset to get the Premium flag
    # 'job_premium_icon_item' is the Premium flag
    # 'job_id' is 'mã công việc'
    original_df = pd.read_csv('dataset/careerviet_updated_jobs.csv', usecols=['job_id', 'job_premium_icon_item'])
    
    # Merge to get Premium flag into exploded dataset
    print("Merging data...")
    df = pd.merge(exploded_df, original_df, left_on='mã công việc', right_on='job_id', how='left')
    
    # Filter for 'Gấp' (Urgent) jobs only
    # khẩn cấp == 1
    urgent_df = df[df['khẩn cấp'] == 1].copy()
    
    # Filter for rows with disclosed salaries only (lương cạnh tranh == -1)
    # Average salary is (lương từ + lương đến) / 2
    urgent_df = urgent_df[urgent_df['lương cạnh tranh'] == -1].copy()
    urgent_df['avg_salary'] = (urgent_df['lương từ'] + urgent_df['lương đến']) / 2
    
    # Group by ngành and Premium status
    # job_premium_icon_item: 1 = Premium, 0 = Thường
    grouped = urgent_df.groupby(['ngành', 'job_premium_icon_item'])['avg_salary'].mean().unstack()
    
    # Rename columns for clarity
    grouped.columns = ['Thường & Gấp', 'Premium & Gấp']
    
    # Drop rows where either is NaN (to compare properly)
    results = grouped.dropna()
    
    # Find where Premium > Thường
    advantage = results[results['Premium & Gấp'] > results['Thường & Gấp']].copy()
    advantage['Diff'] = advantage['Premium & Gấp'] - advantage['Thường & Gấp']
    advantage['Diff %'] = (advantage['Diff'] / advantage['Thường & Gấp']) * 100
    
    print("\n--- Ngành where Premium & Gấp average salary is HIGHER than Thường & Gấp ---")
    if advantage.empty:
        print("None found.")
    else:
        # Sort by the magnitude of the advantage
        print(advantage.sort_values(by='Diff', ascending=False))
        
    # Save to CSV for the user
    output_path = 'thinh/premium_salary_advantage.csv'
    advantage.to_csv(output_path)
    print(f"\nFull results saved to: {output_path}")

if __name__ == "__main__":
    find_premium_salary_advantage()
