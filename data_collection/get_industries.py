import requests
import csv

def fetch_and_save_industries():
    url = "https://internal-api.careerviet.vn/api/v1/cs/jsk/industries/public"

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
        "x-lang": "vi"
    }

    try:
        # Gửi GET request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Kiểm tra xem request có thành công không (status code 200)

        # Chuyển đổi response thành JSON
        json_data = response.json()

        # Kiểm tra xem API có trả về success = true không
        if json_data.get("success"):
            data_list = json_data.get("data", [])

            if not data_list:
                print("Không có dữ liệu trong phần 'data'.")
                return

            # Tên file CSV đầu ra
            csv_filename = "dataset/careerviet_industry.csv"

            # Lấy danh sách các cột từ keys của object đầu tiên trong mảng
            fieldnames = ["industry_id", "industry_name_en", "industry_name_vn"]

            # Mở file và ghi dữ liệu (Sử dụng encoding='utf-8-sig' để Excel không bị lỗi font tiếng Việt)
            with open(csv_filename, mode='w', encoding='utf-8-sig', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                
                # Ghi dòng tiêu đề
                writer.writeheader()
                
                # Ghi toàn bộ dữ liệu
                writer.writerows(data_list)

            print(f"Đã lưu thành công {len(data_list)} bản ghi vào file '{csv_filename}'.")

        else:
            print("API trả về thất bại:", json_data.get("message"))

    except requests.exceptions.RequestException as e:
        print("Có lỗi xảy ra khi gọi API:", e)
    except Exception as e:
        print("Có lỗi xảy ra:", e)

if __name__ == "__main__":
    fetch_and_save_industries()