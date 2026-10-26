# NSDS Dashboard Plus

A Streamlit prototype with five sections:
- Dashboard
- Trend analysis
- Alert center (message generation only; no real delivery)
- Data management (CSV import; session-only)
- Methodology and sources

**Important:** The bundled data are synthetic and must not be presented as real case counts. The app does not send alerts to hospitals.

## Run on Mac
Open Terminal in this folder, then run:
```bash
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```
Open the local URL Streamlit prints (usually http://localhost:8501).

## CSV schema
Required: `disease, year_be, month, cases`
Optional: `month_name_th, data_status, source_url, source_note`
Years are Buddhist Era (e.g., 2567), month is 1-12.
