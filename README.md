# Retail Store Sales Analysis

A Streamlit dashboard for retail sales analysis with executive overview, sales trends, product/category analysis, customer and payment analysis (when supported by the CSV columns), EDA, data quality, data explorer, downloads, and project information.

## Run locally
```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Upload `app.py`, `requirements.txt`, and this README to the root of a GitHub repository. In Streamlit Community Cloud, choose `app.py` as the main file.

## Expected columns
The app recognizes common variants of sales columns, including `Quantity`, `Price Per Unit`, `Total Spent`, date, category, item/product, customer and payment method. Missing optional dimensions are handled with an explanatory message.
