# Ví dụ phân tích (Few-shot)

Dưới đây là các ví dụ minh họa nội dung từng trường trong phản hồi. Hãy tuân theo phong cách này khi trả lời người dùng.

---

## Ví dụ 1: Top 10 ngành tuyển dụng nhiều nhất

**Câu hỏi:** "Ngành nào tuyển dụng nhiều nhất?"

**thinking:**
1. Câu hỏi liên quan đến ngành nghề -> dùng bảng `df_nganh` (đã explode sẵn, mỗi dòng = 1 công việc × 1 ngành).
2. Đếm số lượng tin tuyển dụng theo cột `ngành` bằng `value_counts()`.
3. Lấy top 10 và vẽ biểu đồ cột ngang (barh) để tên ngành dễ đọc hơn so với cột đứng.

**explanation:**
Để phân tích ngành nghề tuyển dụng nhiều nhất, chúng ta sẽ thực hiện các bước sau:

1. **Đếm số tin tuyển dụng theo ngành:** Nhóm dữ liệu theo cột `ngành` trong bảng `df_nganh` và đếm số lượng tin tại mỗi ngành bằng `value_counts()`.
2. **Lấy top 10 ngành:** Sắp xếp kết quả giảm dần và chỉ giữ lại 10 ngành dẫn đầu bằng `head(10)`.
3. **Trực quan hóa:** Vẽ biểu đồ cột ngang (horizontal bar chart) để dễ đọc tên ngành dài.

Code này dùng `value_counts()` trên cột `ngành` của `df_nganh` để đếm số tin tuyển dụng theo từng ngành, rồi lấy 10 ngành cao nhất. Biểu đồ cột ngang được vẽ bằng matplotlib. Kết quả cuối cùng được lưu trong biến `result`.

**code:**
# Đếm số tin tuyển dụng theo ngành từ bảng df_nganh (đã explode sẵn)
top_nganh = df_nganh['ngành'].value_counts().head(10)

# Vẽ biểu đồ cột ngang để dễ đọc tên ngành
fig, ax = plt.subplots(figsize=(10, 6))
top_nganh.sort_values().plot(kind='barh', ax=ax, color='steelblue')
ax.set_xlabel('Số lượng tin tuyển dụng')
ax.set_ylabel('Ngành nghề')
ax.set_title('Top 10 ngành nghề tuyển dụng nhiều nhất trên CareerViet')
plt.tight_layout()

# Chuyển kết quả thành bảng DataFrame để dễ xem
result = top_nganh.reset_index()
result.columns = ['Ngành nghề', 'Số lượng tin']
result

---

## Ví dụ 2: Mức lương trung bình theo khu vực

**Câu hỏi:** "So sánh lương giữa Hà Nội và Hồ Chí Minh"

**thinking:**
1. Cần phân tích theo địa điểm -> dùng `df_dia_diem` (đã explode, mỗi dòng = 1 công việc × 1 địa điểm).
2. Lọc chỉ 2 thành phố "Hà Nội" và "Hồ Chí Minh" bằng `isin()`.
3. Cần loại bỏ các dòng null ở cột `lương từ` / `lương đến` vì ~12,000 tin không có thông tin lương.
4. Tính lương trung bình = (lương từ + lương đến) / 2 cho mỗi tin, rồi dùng `groupby()` để so sánh giữa 2 thành phố.

**explanation:**
Để so sánh lương giữa Hà Nội và Hồ Chí Minh, chúng ta sẽ thực hiện các bước sau:

1. **Lọc dữ liệu:** Từ bảng `df_dia_diem`, lọc ra chỉ các tin tuyển dụng tại 2 thành phố, đồng thời loại bỏ những tin không có thông tin lương.
2. **Tính lương trung bình mỗi tin:** Tạo cột mới `lương trung bình` bằng cách lấy trung bình cộng của `lương từ` và `lương đến`.
3. **So sánh theo nhóm:** Dùng `groupby('địa điểm')` để tính lương trung bình, trung vị, và đếm số tin có lương ở mỗi thành phố.
4. **Trực quan hóa:** Vẽ biểu đồ cột so sánh lương trung bình giữa 2 thành phố.

Code này lọc bảng `df_dia_diem` theo 2 thành phố bằng `isin()` kết hợp `notna()`. Sau đó tạo cột `lương trung bình` và dùng `groupby().agg()` để tính mean, median, count cho mỗi thành phố.

**code:**
# Lọc 2 thành phố và loại bỏ dòng không có thông tin lương
cities = ['Hà Nội', 'Hồ Chí Minh']
df_filter = df_dia_diem[
    (df_dia_diem['địa điểm'].isin(cities)) &
    (df_dia_diem['lương từ'].notna())
].copy()

# Tính lương trung bình = (lương từ + lương đến) / 2
df_filter['lương trung bình'] = (df_filter['lương từ'] + df_filter['lương đến']) / 2

# Nhóm theo thành phố và tính các chỉ số thống kê
result = df_filter.groupby('địa điểm')['lương trung bình'].agg(['mean', 'median', 'count']).reset_index()
result.columns = ['Thành phố', 'Lương TB (VNĐ)', 'Lương trung vị (VNĐ)', 'Số tin có lương']

# Vẽ biểu đồ so sánh lương trung bình
fig, ax = plt.subplots(figsize=(8, 5))
result.plot(kind='bar', x='Thành phố', y='Lương TB (VNĐ)', ax=ax, color=['#e74c3c', '#3498db'], legend=False)
ax.set_ylabel('VNĐ')
ax.set_title('So sánh lương trung bình: Hà Nội vs Hồ Chí Minh')
ax.tick_params(axis='x', rotation=0)
plt.tight_layout()

result

---

## Ví dụ 3: Phúc lợi phổ biến nhất

**Câu hỏi:** "Phúc lợi nào phổ biến nhất?"

**thinking:**
1. Câu hỏi về phúc lợi -> dùng bảng `df_phuc_loi` (đã explode sẵn, mỗi dòng = 1 công việc × 1 phúc lợi).
2. Đếm tần suất xuất hiện từng loại phúc lợi bằng `value_counts()`, cần `dropna()` trước vì có thể có null.
3. Vẽ biểu đồ top 10 phúc lợi dạng cột ngang.

**explanation:**
Để tìm ra phúc lợi phổ biến nhất trên CareerViet, chúng ta sẽ thực hiện các bước sau:

1. **Loại bỏ giá trị null:** Dùng `dropna()` trên cột `phúc lợi` của bảng `df_phuc_loi`.
2. **Đếm tần suất:** Sử dụng `value_counts()` để đếm số lần xuất hiện của từng loại phúc lợi.
3. **Lấy top 10:** Chỉ giữ lại 10 phúc lợi phổ biến nhất bằng `head(10)`.
4. **Trực quan hóa:** Vẽ biểu đồ cột ngang để dễ so sánh.

Code này đếm tần suất xuất hiện từng loại phúc lợi trong bảng `df_phuc_loi` (~208,000 dòng). Kết quả được chuyển thành DataFrame `result`.

**code:**
# Đếm tần suất phúc lợi, loại bỏ giá trị null trước khi đếm
top_pl = df_phuc_loi['phúc lợi'].dropna().value_counts().head(10)

# Vẽ biểu đồ cột ngang để so sánh top 10 phúc lợi
fig, ax = plt.subplots(figsize=(10, 6))
top_pl.sort_values().plot(kind='barh', ax=ax, color='#27ae60')
ax.set_xlabel('Số lượng tin tuyển dụng')
ax.set_title('Top 10 phúc lợi phổ biến nhất')
plt.tight_layout()

# Chuyển kết quả thành bảng DataFrame
result = top_pl.reset_index()
result.columns = ['Phúc lợi', 'Số lượng']
result

---

## Ví dụ 4: Phân tích kinh nghiệm yêu cầu

**Câu hỏi:** "Phân bố kinh nghiệm yêu cầu"

**thinking:**
1. Kinh nghiệm nằm ở bảng chính `df` (không cần bảng exploded vì không liên quan đến địa điểm/ngành/phúc lợi).
2. Cột `kinh nghiệm từ (năm)` có ~4,500 giá trị null -> cần dùng `notna()` để lọc bỏ trước khi phân tích.
3. Vẽ histogram để thể hiện phân bố - dùng 20 bins để phân chia đủ chi tiết.

**explanation:**
Để phân tích phân bố kinh nghiệm yêu cầu của nhà tuyển dụng, chúng ta sẽ:

1. **Lọc dữ liệu:** Từ bảng chính `df`, lọc ra những tin tuyển dụng có thông tin kinh nghiệm (cột `kinh nghiệm từ (năm)` không phải null).
2. **Vẽ histogram:** Sử dụng `ax.hist()` với 20 bins để thể hiện phân bố số năm kinh nghiệm tối thiểu.

Code này lọc bảng `df` chỉ giữ lại những dòng có cột `kinh nghiệm từ (năm)` khác null bằng `notna()`. Histogram được vẽ với 20 cột (bins).

**code:**
# Lọc dữ liệu có thông tin kinh nghiệm từ bảng chính df
df_exp = df[df['kinh nghiệm từ (năm)'].notna()].copy()
print(f"Có {len(df_exp)}/{len(df)} tin tuyển dụng có yêu cầu kinh nghiệm")

# Vẽ histogram phân bố kinh nghiệm tối thiểu
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(df_exp['kinh nghiệm từ (năm)'], bins=20, color='#8e44ad', edgecolor='white', alpha=0.8)
ax.set_xlabel('Số năm kinh nghiệm tối thiểu')
ax.set_ylabel('Số lượng tin tuyển dụng')
ax.set_title('Phân bố kinh nghiệm yêu cầu')
plt.tight_layout()

---

## Ví dụ 5: Sửa lỗi code

**Câu hỏi:** "Code bị lỗi: KeyError: 'salary_from'"

**thinking:**
1. Lỗi `KeyError: 'salary_from'` nghĩa là tên cột `salary_from` không tồn tại trong DataFrame.
2. Dữ liệu đã được đổi tên sang tiếng Việt -> cột lương bây giờ là `lương từ` và `lương đến` (không còn là `salary_from`, `salary_to`).
3. Cần sửa tất cả các tên cột tiếng Anh thành tên cột tiếng Việt tương ứng.

**explanation:**
Lỗi xảy ra do tên cột đã được đổi sang tiếng Việt trong bộ dữ liệu. Cụ thể:

- `salary_from` -> `lương từ`
- `salary_to` -> `lương đến`

Code đã được sửa, thay thế tên cột tiếng Anh bằng tên cột tiếng Việt. Code này lọc bảng `df` chỉ giữ các dòng có cột `lương từ` khác null, tạo cột `lương trung bình`, và sắp xếp giảm dần lấy top 10.

**code:**
# Lọc các tin có thông tin lương (cột đã đổi tên sang tiếng Việt)
df_salary = df[df['lương từ'].notna()].copy()

# Tính lương trung bình từ 2 cột lương từ và lương đến
df_salary['lương trung bình'] = (df_salary['lương từ'] + df_salary['lương đến']) / 2

# Sắp xếp giảm dần theo lương và lấy top 10 công việc lương cao nhất
result = df_salary[['tên công việc', 'tên công ty', 'lương trung bình']].sort_values('lương trung bình', ascending=False).head(10)
result
