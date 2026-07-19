import pandas as pd

df = pd.read_csv('dataset/careerviet_all_jobs.csv')

def analyze_selection(industry_pattern):
    # Filter for industry
    # Note: in original CSV, 'industries' is a string list or similar.
    ind_df = df[df['industries'].str.contains(industry_pattern, na=False)].copy()
    
    # Filter for 'Premium & Không gấp'
    # Premium = job_premium_icon_item == 1
    # Không gấp = job_is_urgent_job == 0
    premium_df = ind_df[(ind_df['job_premium_icon_item'] == 1) & (ind_df['job_is_urgent_job'] == 0)]
    
    print(f"\n--- {industry_pattern} ---")
    print(f"Total Premium & Không gấp: {len(premium_df)}")
    print("Salary Type (job_competition) distribution for this selection:")
    # -1 = Provided, 1 = Competitive
    print(premium_df['job_competition'].value_counts())

analyze_selection("Tài chính / Đầu tư")
analyze_selection("Bán hàng / Kinh doanh")
analyze_selection("Ngân hàng")
