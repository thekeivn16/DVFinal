import pandas as pd
import re
import numpy as np
import json
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor, as_completed

# File đầu vào và đầu ra
INPUT_CSV = 'dataset/careerviet_all_jobs.csv'
OUTPUT_CSV = 'dataset/careerviet_updated_jobs.csv'

# Biểu thức chính quy (Regex) để tìm con số sau chữ '-c' và trước '-vi.html'
pattern = re.compile(r'-c(\d+)-vi\.html')

# Số luồng chạy song song (Bạn có thể tăng giảm tùy vào cấu hình máy)
MAX_WORKERS = 8 

def process_chunk(chunk_df):
    """Hàm chạy trong mỗi luồng: Nhận một phần của DataFrame và cào dữ liệu"""
    results = []
    
    # Mỗi luồng sẽ khởi động 1 browser riêng để đảm bảo an toàn (Thread-safe)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        for index, row in chunk_df.iterrows():
            link = row['job_link']
            
            if pd.isna(link):
                # Lưu mảng rỗng nếu link bị null
                results.append((index, json.dumps([])))
                continue
                
            link = str(link).replace("https://careerviet.vn/en", "https://careerviet.vn/vi")
            print(f"Đang xử lý: {link}")
            
            extracted_numbers = set()
            page = context.new_page() # Mở tab mới

            def handle_response(response):
                if "careerviet.vn/viec-lam/" in response.url and "_rsc=" in response.url:
                    match = pattern.search(response.url)
                    if match:
                        number = match.group(1)
                        extracted_numbers.add(number)

            page.on("response", handle_response)

            try:
                page.goto(link, wait_until="networkidle", timeout=30000)
            except Exception as e:
                print(f"Lỗi khi truy cập trang {link}: {e}")
            finally:
                page.remove_listener("response", handle_response)
                page.close() # Đóng tab sau khi xong để giải phóng RAM

            numbers_list = list(extracted_numbers)
            print(f"-> Đã tìm thấy: {numbers_list}")
            
            # Chuyển list thành chuỗi định dạng JSON để khi lưu CSV sẽ có dạng ["1", "2"]
            results.append((index, json.dumps(numbers_list)))
            
        browser.close()
        
    return results

def crawl_category_numbers():
    # 1. Đọc dữ liệu từ file CSV
    try:
        df = pd.read_csv(INPUT_CSV)
    except Exception as e:
        print(f"Lỗi khi đọc file CSV: {e}")
        return

    # Giới hạn 10 dòng để test như code cũ (Xóa dòng này nếu muốn chạy toàn bộ file)
    # df = df.head(10).copy()

    # Tạo sẵn cột industries (giữ nguyên các cột còn lại)
    df['industries'] = None

    # 2. Chia DataFrame thành các phần nhỏ (chunks) để chia cho các luồng
    chunks = [df.iloc[i::MAX_WORKERS].copy() for i in range(MAX_WORKERS)]
    # Lọc bỏ các chunk rỗng (nếu số luồng > số dòng dữ liệu)
    chunks = [chunk for chunk in chunks if not chunk.empty]
    all_results = []

    print(f"\nBắt đầu chạy song song với {MAX_WORKERS} luồng...")
    
    # Khởi tạo ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit các chunks vào pool
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        
        # Thu thập kết quả khi các luồng hoàn thành
        for future in as_completed(futures):
            all_results.extend(future.result())

    # Cập nhật dữ liệu mới vào DataFrame dựa trên index gốc
    for index, industries_array_str in all_results:
        df.at[index, 'industries'] = industries_array_str

    # 3. Xuất kết quả ra file CSV mới (giữ nguyên toàn bộ cột cũ)
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"\nĐã hoàn thành! Kết quả được lưu tại: {OUTPUT_CSV}")

if __name__ == "__main__":
    crawl_category_numbers()