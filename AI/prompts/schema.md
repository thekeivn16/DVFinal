# Schema dữ liệu

Hệ thống có **6 DataFrame** được nạp sẵn vào môi trường thực thi. Tất cả đều lấy từ bộ dữ liệu tuyển dụng CareerViet (~23,500 tin tuyển dụng, 69 ngành nghề).

---

## 1. `df` - Bảng chính (không explode)

**File gốc:** `careerviet_all_jobs_renamed.csv`  
**Kích thước:** 23,536 dòng x 17 cột

| Cột | Kiểu | Mô tả | Ghi chú |
|-----|------|-------|---------|
| `mã công việc` | object | Mã định danh duy nhất cho mỗi tin tuyển dụng | |
| `tên công việc` | object | Tiêu đề của tin tuyển dụng | |
| `mã công ty` | object | Mã định danh công ty | 265 giá trị null |
| `tên công ty` | object | Tên đầy đủ của công ty | |
| `đơn vị tiền tệ` | object | Đơn vị tiền tệ (vnd/usd) | |
| `địa điểm` | object | Danh sách địa điểm tuyển dụng | **JSON string**, ví dụ: `'["Hồ Chí Minh", "Đà Nẵng"]'` |
| `khẩn cấp` | int64 | Tin tuyển dụng khẩn cấp (1) hoặc không (0) | |
| `lương cạnh tranh` | int64 | Đánh dấu "lương cạnh tranh" (1/0) | |
| `công ty yêu thích` | int64 | Đánh dấu công ty được yêu thích (1/0) | |
| `hạn nộp` | object | Hạn cuối nộp hồ sơ | ISO datetime string |
| `ngày cập nhật` | object | Ngày cập nhật tin | ISO datetime string |
| `kinh nghiệm từ (năm)` | float64 | Số năm kinh nghiệm tối thiểu | 4,482 giá trị null |
| `kinh nghiệm đến (năm)` | float64 | Số năm kinh nghiệm tối đa | 7,964 giá trị null |
| `phúc lợi` | object | Danh sách phúc lợi | **JSON string**, ví dụ: `'["Chế độ bảo hiểm", "Du Lịch"]'` |
| `ngành` | object | Danh sách mã ngành nghề | **JSON string** chứa ID, ví dụ: `'["51", "9", "4"]'` - cần map với `df_industries` |
| `lương từ` | float64 | Mức lương tối thiểu (VNĐ) | 12,273 giá trị null (lương cạnh tranh) |
| `lương đến` | float64 | Mức lương tối đa (VNĐ) | 12,273 giá trị null |

> **Lưu ý quan trọng:** Các cột `địa điểm`, `phúc lợi`, `ngành` trong bảng `df` là **JSON string**. Nếu muốn phân tích chi tiết (ví dụ: đếm tin theo từng tỉnh), hãy dùng các bảng **exploded** bên dưới thay vì tự parse JSON.

---

## 2. `df_dia_diem` - Exploded theo địa điểm

**File gốc:** `exploded_địa điểm.csv`  
**Kích thước:** 27,449 dòng x 17 cột  
**Mô tả:** Mỗi dòng = 1 công việc x 1 địa điểm. Cột `địa điểm` chứa **tên tỉnh/thành phố đơn lẻ** (không phải JSON).

Ví dụ giá trị cột `địa điểm`: `Hồ Chí Minh`, `Hà Nội`, `Đà Nẵng`, `Bình Dương`...

**Dùng khi:** phân tích theo vùng miền, đếm tin tuyển dụng theo tỉnh/thành phố, so sánh lương giữa các khu vực.

---

## 3. `df_nganh` - Exploded theo ngành nghề

**File gốc:** `exploded_ngành.csv`  
**Kích thước:** 53,994 dòng x 17 cột  
**Mô tả:** Mỗi dòng = 1 công việc x 1 ngành. Cột `ngành` chứa **tên ngành tiếng Việt** (đã map từ ID qua bảng `df_industries`).

Ví dụ giá trị cột `ngành`: `Bán hàng / Kinh doanh`, `Xây dựng`, `Kế toán / Kiểm toán`...

**Dùng khi:** phân tích theo ngành nghề, top ngành tuyển dụng nhiều, so sánh lương giữa các ngành.

---

## 4. `df_phuc_loi` - Exploded theo phúc lợi

**File gốc:** `exploded_phúc lợi.csv`  
**Kích thước:** 208,689 dòng x 17 cột  
**Mô tả:** Mỗi dòng = 1 công việc x 1 phúc lợi. Cột `phúc lợi` chứa **tên phúc lợi đơn lẻ**.

Ví dụ giá trị cột `phúc lợi`: `Chế độ bảo hiểm`, `Đào tạo`, `Chế độ thưởng`, `Tăng lương`, `Du Lịch`...

**Dùng khi:** thống kê phúc lợi phổ biến, so sánh phúc lợi giữa các ngành hoặc khu vực.

---

## 5. `df_industries` - Bảng tra cứu ngành nghề

**File gốc:** `careerviet_industries.csv`  
**Kích thước:** 69 dòng x 3 cột

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `industry_id` | int64 | Mã ngành (dùng để map với cột `ngành` trong bảng `df`) |
| `industry_name_en` | object | Tên ngành tiếng Anh |
| `industry_name_vn` | object | Tên ngành tiếng Việt |

**Dùng khi:** Cần map mã ngành từ bảng `df` sang tên ngành đầy đủ. Tuy nhiên, bảng `df_nganh` đã map sẵn - nên ưu tiên dùng `df_nganh` cho phân tích theo ngành.

---

## 6. `df_dia_diem_nganh` - Exploded theo địa điểm và ngành nghề

**File gốc:** `exploded_all_combined.csv`  
**Kích thước:** 62,048 dòng x 17 cột  
**Mô tả:** Mỗi dòng = 1 công việc x 1 địa điểm x 1 ngành. Cột `địa điểm` chứa **tên tỉnh/thành phố đơn lẻ** (không phải JSON). Cột `ngành` chứa **tên ngành tiếng Việt** (đã map từ ID qua bảng `df_industries`).

Ví dụ giá trị cột `địa điểm`: `Hồ Chí Minh`, `Hà Nội`, `Đà Nẵng`, `Bình Dương`...

Ví dụ giá trị cột `ngành`: `Bán hàng / Kinh doanh`, `Xây dựng`, `Kế toán / Kiểm toán`...

**Dùng khi:** phân tích những yêu cầu cần rõ ràng mỗi quan hệ giữa ngành và địa điểm riêng biệt.
## Chọn đúng bảng dữ liệu

| Mục đích phân tích | Bảng nên dùng |
|---------------------|---------------|
| Tổng quan, đếm số tin | `df` |
| Phân tích theo tỉnh/thành phố | `df_dia_diem` |
| Phân tích theo ngành nghề | `df_nganh` |
| Phân tích phúc lợi | `df_phuc_loi` |
| Map mã ngành sang tên | `df_industries` |
| Phân tích lương | `df` (hoặc kết hợp với bảng exploded) |
| Phân tích kinh nghiệm | `df` |
| Phân tích theo địa điểm và ngành nghề |`df_dia_diem_nganh` |

## Lưu ý xử lý thời gian (Quan trọng)

Các cột thời gian (`hạn nộp`, `ngày cập nhật`) trong dataset có **nhiều định dạng khác nhau** có thể bị lỗi, nên cẩn thận.
