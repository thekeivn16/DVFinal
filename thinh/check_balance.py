import pandas as pd
import os

def check_balance():
    # File path as specified by user
    file_path = 'dataset/exploded_ngành.csv'
    output_dir = 'thinh'
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    print(f"Loading dataset: {file_path}")
    df = pd.read_csv(file_path)
    
    # Identify unique values in 'lương cạnh tranh'
    unique_vals = sorted(df['lương cạnh tranh'].unique())
    print(f"Unique values in 'lương cạnh tranh': {unique_vals}")
    
    # Group by 'ngành' and count occurrences of each 'lương cạnh tranh' value
    balance_df = df.groupby(['ngành', 'lương cạnh tranh']).size().unstack(fill_value=0)
    
    # Check if balanced (count of -1 == count of 1)
    # We'll check if the difference is zero for all rows
    if -1 in balance_df.columns and 1 in balance_df.columns:
        balance_df['Difference'] = balance_df[1] - balance_df[-1]
        balance_df['Is Balanced'] = balance_df['Difference'] == 0
    else:
        balance_df['Is Balanced'] = False
        print("Warning: Dataset does not contain both -1 and 1 values in 'lương cạnh tranh'.")

    # Save the full report to thinh/balance_report.csv
    report_path = os.path.join(output_dir, 'balance_report.csv')
    balance_df.to_csv(report_path)
    print(f"Full report saved to: {report_path}")

    # Summary
    total_nganh = len(balance_df)
    balanced_nganh = balance_df['Is Balanced'].sum()
    
    print(f"\n--- Summary ---")
    print(f"Total 'ngành' categories: {total_nganh}")
    print(f"Balanced 'ngành': {balanced_nganh}")
    print(f"Unbalanced 'ngành': {total_nganh - balanced_nganh}")
    
    if total_nganh == balanced_nganh:
        print("\nConclusion: YES, every ngành is perfectly balanced.")
    else:
        print("\nConclusion: NO, the ngành are not balanced.")
        print("\nMost unbalanced ngành (top 10 by absolute difference):")
        balance_df['Abs_Diff'] = balance_df['Difference'].abs()
        print(balance_df.sort_values(by='Abs_Diff', ascending=False).head(10))

if __name__ == "__main__":
    check_balance()
