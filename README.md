# RetailPulse - AI-Powered Customer Analytics & Demand Forecasting

RetailPulse is a retail analytics platform that combines customer segmentation, churn prediction, demand forecasting, and inventory planning to support data-driven retail decisions.

## Project Overview

RetailPulse uses historical retail transaction data to generate customer insights, evaluate churn prediction models, forecast product demand, and produce inventory replenishment recommendations.

## Features

- **Executive Overview:** Key retail metrics and business insights.
- **Customer Segmentation:** RFM features and K-Means customer clustering.
- **Churn Analysis:** Customer churn classification and evaluation.
- **Demand Forecasting:** Product-level forecasts using baseline forecasting methods.
- **Inventory Planning:** Estimated reorder points, safety stock, and replenishment quantities.
- **Model Evaluation:** Summary of model performance and evaluation results.
- **Data Notes:** Dataset information, methodology, assumptions, and limitations.

## Technology Stack

- Python
- Pandas and NumPy
- Scikit-learn
- Streamlit
- Plotly
- Matplotlib and Seaborn
- Git and GitHub

## Dataset

The project uses the **Online Retail II** dataset from the UCI Machine Learning Repository.

Dataset page: https://archive.ics.uci.edu/dataset/502/online+retail+ii

The original workbook is not committed to this repository. Download it from the dataset source and place it at:

`data/raw/online_retail_II.xlsx`

## Project Structure

```text
RetailPulse/
â”œâ”€â”€ app/
â”‚   â””â”€â”€ app.py
â”œâ”€â”€ configs/
â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ raw/
â”‚   â””â”€â”€ processed/
â”œâ”€â”€ docs/
â”œâ”€â”€ models/
â”œâ”€â”€ reports/
â”‚   â””â”€â”€ figures/
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ data/
â”‚   â”œâ”€â”€ features/
â”‚   â”œâ”€â”€ forecasting/
â”‚   â”œâ”€â”€ inventory/
â”‚   â””â”€â”€ models/
â”œâ”€â”€ tests/
â”œâ”€â”€ requirements.txt
â””â”€â”€ README.md
```

## Local Setup

Create and activate a virtual environment from the project root.

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run the Dashboard

From the project root:

```powershell
python -m streamlit run app/app.py
```

Streamlit will display the local address for the dashboard in the terminal.

## Run Tests

```powershell
python -m pytest .\tests -v
```

## Generate the Analytics Outputs

Run the processing scripts in the following order after obtaining the original dataset:

1. `src/data/inspect_dataset.py`
2. `src/data/clean_dataset.py`
3. `src/data/eda_analysis.py`
4. `src/features/build_features.py`
5. `src/models/customer_segmentation.py`
6. `src/models/churn_prediction.py`
7. `src/forecasting/demand_forecasting.py`
8. `src/inventory/inventory_optimization.py`
9. `src/models/evaluate_models.py`

Generated datasets and trained models are excluded from Git to avoid committing large data files and binary artifacts.

## Important Limitations

- Churn results represent a historical holdout evaluation and are not a guarantee of future customer behavior.
- Demand forecasting uses baseline methods and is limited by the available historical transaction data.
- Inventory recommendations use assumed stock coverage and supplier lead time because actual stock-on-hand and supplier records are unavailable.
- Forecasts and recommendations are analytical estimates, not confirmed purchasing instructions.
- Dataset revenue values should be interpreted in the context of the original dataset; a currency unit is not assumed here.

## Current Test Coverage

The current automated test suite covers daily-series preparation, the minimum selling-day threshold, inventory calculation formulas, separate product calculations, negative forecast rejection, and missing required columns.

## Repository

GitHub: https://github.com/Ams1421/RetailPulse-AI-Customer-Analytics
