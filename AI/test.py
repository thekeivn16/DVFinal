import pandas as pd
import matplotlib.pyplot as plt

df_dia_diem_nganh = pd.read_csv("../dataset/exploded_all_combined.csv", encoding="utf-8-sig")
df = pd.read_csv("../dataset/careerviet_all_jobs_renamed.csv", encoding="utf-8-sig")

# Kết hợp bảng df_nganh với df_dia_diem_nganh để có thông tin lương và ngành nghề
merged_df = df_dia_diem_nganh.merge(df[['mã công việc', 'tên công việc', 'lương từ', 'lương đến']], how='left', on='mã công việc')
print(merged_df.head())

# Tạo cột lương trung bình từ lương từ và lương đến
merged_df['lương trung bình'] = (merged_df['lương từ'] + merged_df['lương đến']) / 2

# Nhóm theo ngành và tính lương trung bình
average_salary_by_industry = merged_df.groupby('ngành')['lương trung bình'].mean().sort_values(ascending=False).head(10)

# Vẽ biểu đồ cột về lương trung bình của top 10 ngành
fig, ax = plt.subplots(figsize=(10, 6))
average_salary_by_industry.plot(kind='bar', ax=ax, color='steelblue')
ax.set_xlabel('Ngành nghề')
ax.set_ylabel('Lương trung bình (VNĐ)')
ax.set_title('Top 10 ngành nghề có lương trung bình cao nhất')
plt.tight_layout()

# Chuyển kết quả thành DataFrame để xem dễ dàng
result = average_salary_by_industry.reset_index()
result.columns = ['Ngành nghề', 'Lương trung bình (VNĐ)']