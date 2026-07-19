import pandas as pd

df = pd.read_csv('dataset/exploded_ngành.csv')
finance_df = df[df['ngành'] == 'Tài chính / Đầu tư'].copy()

# Rows with provided salary (lương cạnh tranh == -1)
provided_salary = finance_df[finance_df['lương cạnh tranh'] == -1].copy()

print(f"Finance jobs with provided salary: {len(provided_salary)}")
print("\nSalary statistics:")
print(provided_salary[['lương từ', 'lương đến']].describe())

# Check khẩn cấp for high salary (> 30M and > 50M)
provided_salary['is_high_30'] = provided_salary['lương từ'] >= 30
provided_salary['is_high_50'] = provided_salary['lương từ'] >= 50

print("\nUrgency (khẩn cấp) for High Salary jobs (>30M):")
print(provided_salary[provided_salary['is_high_30']]['khẩn cấp'].value_counts(normalize=True))

print("\nUrgency (khẩn cấp) for Very High Salary jobs (>50M):")
print(provided_salary[provided_salary['is_high_50']]['khẩn cấp'].value_counts(normalize=True))

# Check the maximum values
print("\nTop 10 salaries in Finance:")
print(provided_salary.sort_values(by='lương từ', ascending=False)[['tên công việc', 'lương từ', 'lương đến', 'khẩn cấp']].head(10))
