# OLA Ride Insights — Streamlit App

Interactive analytics application for the OLA Ride Insights portfolio project, using the cleaned dataset supplied by the project author.

## Run locally

1. Install Python 3.10+.
2. Open this folder in a terminal.
3. Create/activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
5. Launch:

   ```bash
   streamlit run app.py
   ```

Streamlit will print a local URL (typically http://localhost:8501).

## Included sections
- Overview: KPI cards, daily bookings, status mix, hourly demand and weekday volume
- Vehicle analysis: booking volume, distance totals/averages and ratings by vehicle type
- Revenue: payment-method revenue, top customers, daily revenue and ride-distance trends
- Cancellation: customer/driver reasons, driver-not-found and incomplete ride reasons
- Ratings: rating distributions, averages and rating correlation
- Locations: top pickup/drop locations and frequent routes
- Data explorer: filter and download the selected records

## Data
The included `OLA_Cleaned_Data.csv` is the provided cleaned dataset (103,024 rows, July 2024). The app filters by date, vehicle type, booking status and payment method. Revenue KPIs use successful rides only.


## Deployment (Streamlit Community Cloud)
1. Push this folder to a GitHub repository (include `app.py`, `requirements.txt`, `README.md`, and the CSV).
2. On Streamlit Community Cloud, create a new app and connect your repository.
3. Set the main file path to `app.py`.
4. Deploy. Keep the dataset in the repo for the simple version, or move it to external storage if repository size constraints become an issue.
