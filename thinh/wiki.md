# CareerViet Data Visualization Project - Wiki

This document serves as a knowledge base for analyzing the CareerViet dataset, specifically focusing on the relationship between job features and recruitment strategy.

## 📌 Key Decisions & Core Logic

### 1. Data Mapping & Columns
*   **Target Variable**: Use `job_premium_icon_item` (Binary: 1 for Premium, 0 for Basic) to distinguish paid feature usage.
*   **Urgency Proxy**: Use `job_is_urgent_job`. This identifies jobs that need a "boost" due to immediate hiring needs.
*   **Salary Metrics**: 
    *   **Plotting Variable**: Use `job_from_salary`
    *   *Note*: While `median_salary` can be calculated, `job_from_salary` is used to visualize the most common starting points.
    *   Jobs marked as "Competition" (Lương thỏa thuận) will have null numeric values; these should be excluded from financial plots.
*   **Industry Mapping**: **ALWAYS** use `top_industries`. 
    *   *Note*: The columns `industries` and `premium_industries` are empty (`[]`) in this dataset.

### 2. Strategic Analysis Framework (The 3 Cases)
To determine if Premium is a "Competitive Advantage" or a "Compensation Tool":
*   **Case A (Boost)**: Premium + Low Salary + High Urgency. (Employers are pushing hard-to-fill roles).
*   **Case B (Elite)**: Premium + High Salary + Low Urgency. (Employers are competing for top talent).
*   **Case C (Baseline)**: No statistical difference between Premium and Non-Premium distributions.

---

## 🛠 Commonly Used Snippets (Python/Pandas)

### Parsing `top_industries`
Since industry IDs are stored as strings of lists (e.g., `"[51]"`), they must be parsed:
```python
import ast
df['industry_id'] = df['top_industries'].apply(lambda x: ast.literal_eval(x)[0] if x != '[]' else None)
```

### Joining with Industry Names
```python
industries = pd.read_csv('dataset/careerviet_industries.csv')
df = df.merge(industries[['industry_id', 'industry_name_en']], on='industry_id', how='left')
```

---

## ⚠️ Common Mistakes & Gotchas

### 1. Using the `industries` Column

### 2. Overlooking Outliers
The salary distribution can have extreme outliers (e.g., high-level executive roles). Consider using **Median** rather than **Mean** for industry comparisons to avoid skewing.

---

## 📊 Dashboard Design Best Practices
*   **Interaction**: Enable cross-filtering so that clicking an industry (e.g., IT) immediately updates the Salary vs. Urgency scatter plot.
