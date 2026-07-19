import pandas as pd
import numpy as np

df = pd.read_csv('dataset/exploded_ngành.csv')

# Filter for Finance/Investment
finance_df = df[df['ngành'] == 'Tài chính / Đầu tư'].copy()

print(f"Total rows for 'Tài chính / Đầu tư': {len(finance_df)}")

# Check 'lương cạnh tranh' distribution
print("\n'lương cạnh tranh' distribution:")
print(finance_df['lương cạnh tranh'].value_counts())

# Check 'khẩn cấp' distribution
print("\n'khẩn cấp' distribution:")
print(finance_df['khẩn cấp'].value_counts())

# Check salary ranges where provided
# Note: 'lương từ' and 'lương đến' might be in millions or absolute values.
# Usually 'vnd' unit.
provided_salary = finance_df[finance_df['lương từ'].notna() | finance_df['lương đến'].notna()].copy()
print(f"\nRows with provided salary: {len(provided_salary)}")

if not provided_salary.empty:
    print("\nSalary statistics (where provided):")
    print(provided_salary[['lương từ', 'lương đến']].describe())
    
    # Check for high salaries (> 50M)
    # Assuming values are in millions or need to be checked.
    # If values are like 50000000, then it's absolute.
    high_salary = provided_salary[(provided_salary['lương từ'] >= 50) | (provided_salary['lương đến'] >= 50)]
    print(f"\nRows with salary >= 50M: {len(high_salary)}")
    if len(high_salary) > 0:
        print(high_salary[['tên công việc', 'lương từ', 'lương đến', 'khẩn cấp', 'lương cạnh tranh']].head(10))

# Check 'Premium' vs 'Thường' logic
# If 'lương cạnh tranh' is -1 and 1, maybe 1 is Premium?
# The user says "Elite" strategy = High Salary + Low Urgency.
# And "Premium ở đây được dùng để khẳng định uy tín".
# Let's see if jobs with high salary are marked as 'lương cạnh tranh'? 
# Usually if they have a salary, they are NOT 'lương cạnh tranh'.
# But maybe 'lương cạnh tranh' in this dataset means 'Premium' listing?

# Let's check the relationship between salary and 'lương cạnh tranh'
print("\nRelationship between salary provided and 'lương cạnh tranh':")
print(pd.crosstab(finance_df['lương cạnh tranh'], finance_df['lương từ'].isna(), rownames=['lương cạnh tranh'], colnames=['salary_is_nan']))
