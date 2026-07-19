import pandas as pd

df = pd.read_csv('dataset/exploded_ngành.csv')
ngành_list = [
    "An Ninh / Bảo Vệ", "An toàn lao động", "Bán hàng / Kinh doanh",
    "Bán Hàng Kỹ Thuật", "Bán lẻ / Bán sỉ", "Bảo hiểm",
    "Bảo trì / Sửa chữa", "Bất động sản", "Biên phiên dịch"
]

report = df[df['ngành'].isin(ngành_list)].groupby(['ngành', 'lương cạnh tranh']).size().unstack().fillna(0)
print(report)
