import requests
import pandas as pd
import json
import time
import os

CSV_FILENAME = "dataset/careerviet_all_jobs.csv"

def save_jobs_incremental(jobs_list):
    """Hàm lưu nối dữ liệu vào CSV và tự động xử lý trường hợp có cột mới."""
    if not jobs_list:
        return

    df_new = pd.DataFrame(jobs_list)

    if not os.path.exists(CSV_FILENAME):
        # Lần đầu tiên: tạo file và ghi header
        df_new.to_csv(CSV_FILENAME, index=False, encoding="utf-8-sig")
    else:
        # Đọc dòng đầu tiên (header) của file CSV hiện tại
        existing_cols = pd.read_csv(CSV_FILENAME, nrows=0).columns.tolist()
        
        # Kiểm tra xem có cột nào mới toanh xuất hiện không
        new_cols = [col for col in df_new.columns if col not in existing_cols]
        
        if new_cols:
            print(f"  [!] Phát hiện trường dữ liệu mới {new_cols}. Đang cập nhật lại header cho file CSV...")
            # Nếu có cột mới, bắt buộc đọc file cũ lên, nối data (để lấy đủ header) và lưu lại
            # low_memory=False để tránh warning khi Pandas đoán kiểu dữ liệu
            df_old = pd.read_csv(CSV_FILENAME, low_memory=False, encoding="utf-8-sig")
            df_combined = pd.concat([df_old, df_new], ignore_index=True)
            df_combined.to_csv(CSV_FILENAME, index=False, encoding="utf-8-sig")
        else:
            # Nếu không có cột mới: Ép DataFrame mới phải có thứ tự cột y hệt file CSV hiện hành
            # Các cột df_new bị thiếu sẽ tự động được gán NaN
            df_new = df_new.reindex(columns=existing_cols)
            # Append cực nhanh, không gây tốn RAM
            df_new.to_csv(CSV_FILENAME, mode='a', header=False, index=False, encoding="utf-8-sig")

def fetch_jobs_by_industries():
    # 1. Đọc danh sách industry từ file CSV đã tạo trước đó
    try:
        industries_df = pd.read_csv("dataset/careerviet_industries.csv", encoding="utf-8-sig")
        if "industry_id" not in industries_df.columns:
            print("File careerviet_industries.csv không có cột 'industry_id'.")
            return
        industry_ids = industries_df["industry_id"].dropna().astype(int).tolist()
    except FileNotFoundError:
        print("Không tìm thấy file")
        return

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "origin": "https://careerviet.vn",
        "priority": "u=1, i",
        "referer": "https://careerviet.vn/",
        "sec-ch-ua": '"Microsoft Edge";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36 Edg/147.0.0.0",
    }

    print(f"Bắt đầu quét dữ liệu cho {len(industry_ids)} ngành nghề (Lưu nối tiếp từng trang)...\n")

    for industry_id in industry_ids:
        page = 1
        page_count = 1 # Khởi tạo mặc định để lọt vào vòng lặp
        
        while page <= page_count:
            url = f"https://internal-api.careerviet.vn/api/v1/js/jsk/jobs/public?industry={industry_id}&limit=50&page={page}"
            
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                json_data = response.json()
                
                if json_data.get("success"):
                    jobs_data = json_data.get("data", [])
                    
                    if not jobs_data:
                        break # Trang rỗng thì thoát sớm

                    processed_jobs = []
                    # Xử lý các object/list phức tạp thành chuỗi JSON để Pandas xử lý an toàn
                    for job in jobs_data:
                        processed_job = {}
                        for key, value in job.items():
                            if isinstance(value, (list, dict)):
                                processed_job[key] = json.dumps(value, ensure_ascii=False)
                            else:
                                processed_job[key] = value
                        processed_jobs.append(processed_job)
                    
                    # Gọi hàm lưu nối tiếp vào CSV để giải phóng RAM ngay
                    save_jobs_incremental(processed_jobs)
                    
                    # Cập nhật số trang cần chạy tiếp
                    metadata = json_data.get("metadata", {})
                    page_count = metadata.get("pageCount", 1)
                    
                    print(f"Ngành {industry_id: <4} - Trang {page}/{page_count} - Đã lưu {len(processed_jobs)} jobs.")
                    
                else:
                    print(f"API trả về thất bại cho ngành {industry_id}, trang {page}")
                    break
                
            except requests.exceptions.RequestException as e:
                print(f"Lỗi kết nối ở ngành {industry_id}, trang {page}: {e}")
                break 
            
            page += 1
            # Nghỉ 0.5s giữa các request để server không chặn IP
            time.sleep(0.2)

    print("Quét xong! Đang dọn dẹp các jobs bị trùng lặp...")
    # Do 1 job có thể thuộc nhiều industry, bước cuối ta làm sạch file CSV
    if os.path.exists(CSV_FILENAME):
        df_final = pd.read_csv(CSV_FILENAME, low_memory=False, encoding="utf-8-sig")
        initial_len = len(df_final)
        
        if "job_id" in df_final.columns:
            df_final.drop_duplicates(subset=["job_id"], keep="first", inplace=True)
            df_final.to_csv(CSV_FILENAME, index=False, encoding="utf-8-sig")
            
        print(f"Hoàn thành! Đã loại bỏ {initial_len - len(df_final)} jobs trùng. Tổng số jobs lưu trữ: {len(df_final)}.")
    else:
        print("Không có file nào được tạo.")

if __name__ == "__main__":
    fetch_jobs_by_industries()