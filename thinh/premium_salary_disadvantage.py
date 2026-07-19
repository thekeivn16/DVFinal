import pandas as pd
import numpy as np

def find_premium_salary_disadvantage():
    print("Loading datasets...")
    exploded_df = pd.read_csv('dataset/exploded_ngành.csv')
    original_df = pd.read_csv('dataset/careerviet_updated_jobs.csv', usecols=['job_id', 'job_premium_icon_item'])
    
    print("Merging data...")
    df = pd.merge(exploded_df, original_df, left_on='mã công việc', right_on='job_id', how='left')
    
    # Filter for 'Gấp' (Urgent) and disclosed salary
    # No experience constraint this time
    urgent_df = df[(df['khẩn cấp'] == 1) & (df['lương cạnh tranh'] == -1)].copy()
    
    urgent_df['avg_salary'] = (urgent_df['lương từ'] + urgent_df['lương đến']) / 2
    
    # Group by ngành and Premium status
    grouped = urgent_df.groupby(['ngành', 'job_premium_icon_item'])['avg_salary'].mean().unstack()
    
    # Rename columns
    grouped.columns = ['Thường & Gấp', 'Premium & Gấp']
    
    # Drop rows where either is NaN
    results = grouped.dropna()
    
    # Find where Premium < Thường
    disadvantage = results[results['Premium & Gấp'] < results['Thường & Gấp']].copy()
    disadvantage['Diff'] = disadvantage['Premium & Gấp'] - disadvantage['Thường & Gấp']
    disadvantage['Diff %'] = (disadvantage['Diff'] / disadvantage['Thường & Gấp']) * 100
    
    # Add counts
    counts = urgent_df.groupby(['ngành', 'job_premium_icon_item']).size().unstack()
    counts.columns = ['Count Thường', 'Count Premium']
    final_results = pd.concat([disadvantage, counts], axis=1, join='inner')
    
    print("\n--- Ngành where Premium & Gấp average salary is LOWER than Thường & Gấp ---")
    if final_results.empty:
        print("None found.")
    else:
        # Sort by the most negative difference
        print(final_results.sort_values(by='Diff', ascending=True))
        
    # Save to CSV
    output_path = 'thinh/premium_salary_disadvantage.csv'
    final_results.to_csv(output_path)
    print(f"\nFull results saved to: {output_path}")

if __name__ == "__main__":
    find_premium_salary_disadvantage()
