# RetailPulse --- AI-Powered Customer Analytics & Demand Forecasting Platform

RetailPulse is an end-to-end retail analytics and machine-learning
project built with Python and Streamlit. It turns historical retail
transactions into customer, sales, churn, demand-forecasting, and
inventory-planning insights through an interactive seven-page dashboard.

**Live dashboard:**
https://retailpulse-ai-customer-analytics.streamlit.app

**GitHub repository:**
https://github.com/Ams1421/RetailPulse-AI-Customer-Analytics

> **Important data note:** The processed CSV files required by the deployed
> dashboard are included in the repository. The original Excel workbook,
> local backups, and trained model files are not included. To reproduce the
> full analysis from source, download the workbook from the official UCI page
> and run the project scripts.

------------------------------------------------------------------------

## Contents

-   [Project overview](#project-overview)
-   [Dataset used](#dataset-used)
-   [Data preparation and project-created
    features](#data-preparation-and-project-created-features)
-   [Dashboard pages](#dashboard-pages)
-   [Technology stack](#technology-stack)
-   [Repository structure](#repository-structure)
-   [Requirements](#requirements)
-   [Download and run the project](#download-and-run-the-project)
-   [Data files required by the
    dashboard](#data-files-required-by-the-dashboard)
-   [Reproducing the analysis](#reproducing-the-analysis)
-   [Data quality and modelling
    limitations](#data-quality-and-modelling-limitations)
-   [GitHub and deployment notes](#github-and-deployment-notes)
-   [Credits](#credits)

## Project overview

RetailPulse is designed to help explore questions such as:

-   Which customer groups have different purchasing patterns?
-   How much historical sales activity is recorded over time?
-   Which customers were labelled as churned in the historical modelling
    experiment?
-   How do simple demand-forecasting baselines compare?
-   What replenishment quantities are suggested under stated inventory
    assumptions?

The project combines exploratory data analysis, customer segmentation,
churn classification, product-level demand forecasting, and
assumption-based inventory planning. The dashboard presents the
resulting outputs in charts, KPI cards, tables, filters, and CSV
downloads.

This is a portfolio and learning project, not a live retail operating
system.

## Dataset used

The source dataset is **Online Retail II**, published by the UCI Machine
Learning Repository:

-   **Official dataset page:**
    https://archive.ics.uci.edu/dataset/502/online+retail+ii
-   **Format:** Excel workbook
-   **Worksheets:** `Year 2009-2010` and `Year 2010-2011`
-   **Historical period represented:** December 2009 to December 2011
-   **Approximate original size:** 1.07 million transaction rows across
    the two worksheets

The original transaction fields include invoice, stock code, product
description, quantity, invoice date, unit price, customer ID, and
country. The data represents historical transactions; it is not live or
current retail activity.

Please obtain the source workbook from the official UCI page and follow
its dataset terms. The workbook is not included in this Git repository.

## Data preparation and project-created features

The source workbook was combined and processed by the project's data
scripts. The recorded cleaning and analysis outputs reported the
following:

  Processing item                                       Recorded result
  --------------------------------------------------- -----------------
  Original transaction rows                                   1,067,371
  Exact duplicate rows removed                                   34,335
  Rows after duplicate removal                                1,033,036
  Rows used for standard sales analysis                       1,007,913
  Unique customers in the standard sales subset                   5,878
  Unique products in the standard sales subset                    4,916
  Countries in the standard sales subset                             43
  Invoice count in the standard sales subset                     40,077
  Standard sales revenue reported by the EDA script       20,476,260.45

These are recorded outputs from the project's processing run. Revenue is
shown in the dataset's monetary units; the project should not imply that
it is a live or independently audited financial figure.

### Cleaning and derived transaction fields

The cleaned transaction dataset adds or standardizes fields used by
later steps, including:

-   Standardized names for invoice, customer, product, date, quantity,
    price, revenue, and country fields.
-   `line_revenue`, calculated for each transaction line.
-   `is_cancellation_invoice`, a flag for cancellation invoices.
-   `is_return`, a flag for return/negative-quantity rows.
-   `is_negative_price` and `is_zero_price`, flags for price-quality
    checks.
-   `has_customer_id`, indicating whether a customer ID is present.

The project recorded cancellation invoices, negative quantities,
negative prices, zero-price rows, missing customer IDs, and missing
product descriptions during cleaning. These conditions are flagged or
handled by the relevant scripts; they should not be assumed to represent
ordinary positive sales.

### Customer features added by this project

The customer feature table includes standard behavioural fields such as
first/last purchase, invoice count, total items, total spend, average
order value, distinct products, recency, and customer lifetime.

Five project-created columns with the `RP_` prefix were also added:

  -----------------------------------------------------------------------
  Feature                             Purpose
  ----------------------------------- -----------------------------------
  `RP_Purchase_Season`                Groups purchase activity by season.

  `RP_Purchase_Recency_Band`          Groups customers by recency bands.

  `RP_Customer_Value_Band`            Groups customers into value bands
                                      based on project rules.

  `RP_Product_Diversity_Band`         Groups customers by product
                                      diversity.

  `RP_Customer_Loyalty_Index`         A heuristic activity score from 0
                                      to 100. It is not a validated
                                      loyalty metric.
  -----------------------------------------------------------------------

These `RP_` features are derived from the source transaction data using
project-defined rules. They are not original columns supplied by UCI,
and they should be described as engineered features rather than
independent customer information.

### Customer segmentation

The project builds an RFM-style table with recency, frequency, monetary
values, R/F/M scores, and K-Means cluster labels. The recorded run
segmented 5,878 customers into four clusters. Cluster numbers are
arbitrary identifiers; a higher cluster number does not automatically
mean a better customer.

### Churn modelling

The churn experiment uses a defined historical feature window and a
later observation window to label customer activity. In the recorded
run, 2,960 customers were labelled, split into 2,220 training customers
and 740 held-out test customers. A Logistic Regression example achieved
approximately 0.779 ROC-AUC on that held-out test set. Other models and
metrics may be recorded in the generated report.

These are historical experimental results, not a guarantee of future
churn prediction performance.

### Demand forecasting and inventory planning

Demand forecasting evaluates simple product-level baselines and records
metrics such as MAE and RMSE. Inventory planning uses forecast outputs
and explicit assumptions, including lead time, safety stock, and assumed
stock on hand, to calculate reorder points and suggested replenishment
units.

The source data does not provide verified live inventory-on-hand values.
Inventory recommendations are therefore planning demonstrations, not
actual purchase orders.

## Dashboard pages

The Streamlit application contains seven pages:

1.  **Executive Overview** --- KPI cards, monthly revenue trend, top
    products by revenue, top countries by revenue, customer cluster
    distribution, and forecast evaluation.
2.  **Customer Segmentation** --- cluster counts and shares, cluster
    profiles, customer-level RFM records, filters, behaviour scatter
    plots, and project-created customer features.
3.  **Churn Analysis** --- historical churn report, test-set class
    balance, actual-versus-predicted comparison, predicted probability
    distribution, and downloadable predictions.
4.  **Demand Forecasting** --- baseline MAE/RMSE comparisons,
    product-level forecast chart, forecast summary metrics, and
    downloadable results.
5.  **Inventory Planning** --- planning-status summaries, replenishment
    metrics, suggested restocks, assumptions, and downloadable
    recommendations.
6.  **Model Evaluation** --- forecasting comparison charts, churn
    confusion-matrix view, and model evaluation report.
7.  **About & Data Notes** --- project capabilities, report
    availability, dataset source, and limitations.

Some dashboard panels display a helpful message if their corresponding
data or report file is missing.

## Technology stack

-   **Language:** Python
-   **Dashboard:** Streamlit
-   **Data processing:** Pandas, NumPy
-   **Visualisation:** Plotly
-   **Machine learning:** Scikit-learn
-   **Data files:** CSV and compressed CSV (`.csv.gz`), with the
    original source in Excel (`.xlsx`)
-   **Testing:** pytest
-   **Version control:** Git and GitHub

The repository's `requirements.txt` records the package versions used
for this project. It includes more packages than the dashboard alone may
need because it captures the broader project environment.

## Repository structure

The main project structure is:

``` text
RetailPulse/
├── app/
│   ├── app.py
│   └── assets/
│       ├── retailpulse_logo.png
│       └── retailpulse_app_icon.png
├── configs/
├── data/                         # Ignored by Git; prepare locally
├── docs/
├── models/                       # Trained model files are ignored by Git
├── notebooks/
├── reports/
│   ├── eda_summary.txt
│   ├── customer_cluster_summary.csv
│   ├── churn_model_report.txt
│   ├── demand_forecasting_summary.txt
│   ├── inventory_planning_summary.txt
│   └── model_evaluation_summary.txt
├── src/
│   ├── data/
│   ├── features/
│   ├── models/
│   └── forecasting/
├── tests/
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

The exact set of files in `reports/`, `src/`, and `tests/` may change as
the project evolves. The processed CSV outputs needed by the live dashboard
are committed; the original source workbook and trained model files are not.

## Requirements

-   Git
-   Python compatible with the package versions in `requirements.txt`
-   Windows PowerShell, macOS Terminal, or a Linux shell
-   The source workbook and processed output files described below

Because pinned scientific Python package versions can differ in
compatibility across Python versions and operating systems, use a Python
version compatible with the packages in `requirements.txt`. If
installation fails, check the error and the supported Python versions
for the specific package rather than randomly upgrading all
dependencies.

## Download and run the project

### 1. Clone the repository

``` bash
git clone https://github.com/Ams1421/RetailPulse-AI-Customer-Analytics.git
cd RetailPulse-AI-Customer-Analytics
```

### 2. Create and activate a virtual environment

**Windows PowerShell:**

``` powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the environment policy guidance for
your machine or activate the environment through your IDE. Do not run
project commands outside the environment unintentionally.

**macOS/Linux:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Obtain the source dataset

1.  Open the [official UCI Online Retail II
    page](https://archive.ics.uci.edu/dataset/502/online+retail+ii).
2.  Download the Excel workbook.
3.  Place it at the location expected by the data preparation scripts.
    In the original development setup, the file was named
    `online_retail_II.xlsx` under `data/`.
4.  Create the `data` directory if it does not exist.

**Note:** The repository ignores `data/*`, so downloading or generating
data locally does not add it to Git automatically.

### 5. Generate the processed data

The dashboard reads precomputed CSV outputs; it does not run the full
modelling pipeline automatically when it starts. The source scripts are
in `src/`. Review the scripts and their current input/output paths, then
run the data preparation and modelling scripts in their intended order.

The project scripts used during development included:

``` text
src/data/inspect_dataset.py
src/data/clean_dataset.py
src/data/eda_analysis.py
src/models/customer_segmentation.py
src/features/build_features.py
src/models/churn_prediction.py
src/forecasting/demand_forecasting.py
```

Inventory-planning output must also be generated for the Inventory
Planning page. To see the exact available scripts in your checkout, run:

**Windows PowerShell:**

``` powershell
Get-ChildItem src -Recurse -File -Filter *.py | Select-Object FullName
```

Run each script using the active virtual environment and follow any
paths or arguments defined in that script. The pipeline may take time
because the source workbook contains over one million transaction rows.

### 6. Confirm dashboard data files exist

At minimum, the current dashboard expects these files under `data/`:

``` text
customer_features.csv
customer_rfm_segments.csv
churn_test_predictions.csv
forecast_evaluation.csv
demand_forecasts.csv
inventory_recommendations.csv
daily_product_sales.csv
retail_transactions_cleaned.csv.gz
```

The `customer_cluster_summary.csv` file is read from `reports/` by the
current dashboard code. The app also uses text reports in `reports/`,
including `eda_summary.txt`, `churn_model_report.txt`,
`demand_forecasting_summary.txt`, `inventory_planning_summary.txt`, and
`model_evaluation_summary.txt`.

If a required data file is missing, its chart or table may show a
message or an incomplete view.

### 7. Start Streamlit

From the repository root:

``` powershell
python -m streamlit run app/app.py
```

Open the local URL printed in the terminal, usually:

``` text
http://localhost:8501
```

Stop the local server with `Ctrl + C`.

### 8. Run the tests

From the repository root:

``` powershell
python -m pytest -q
```

Tests cover the functionality included in the current test suite.
Passing tests does not prove every dashboard page or every model has
been independently validated, so also inspect the seven pages in the
browser.

## Data files required by the dashboard

  ----------------------------------------------------------------------------
  File                                     Used for
  ---------------------------------------- -----------------------------------
  `daily_product_sales.csv`                Monthly revenue and product sales
                                           charts.

  `retail_transactions_cleaned.csv.gz`     Country-level revenue aggregation.

  `customer_features.csv`                  Customer KPIs and engineered
                                           customer features.

  `customer_rfm_segments.csv`              Customer cluster visualisations and
                                           RFM table.

  `churn_test_predictions.csv`             Churn class distribution,
                                           prediction comparison, and
                                           probability charts.

  `forecast_evaluation.csv`                MAE/RMSE comparisons.

  `demand_forecasts.csv`                   Product-level demand forecast
                                           visualisations.

  `inventory_recommendations.csv`          Replenishment and inventory
                                           planning.

  `reports/customer_cluster_summary.csv`   Cluster profile summary.

  Other report files in `reports/`         Narrative summaries and model
                                           evaluation information.
  ----------------------------------------------------------------------------

The original workbook `online_retail_II.xlsx` is needed to reproduce the
pipeline from source, but it is not needed merely to open the dashboard
if all required processed outputs and reports are already present.

## Reproducing the analysis

For reproducibility:

1.  Start from the official UCI source workbook.
2.  Run the project's inspection and cleaning scripts.
3.  Run EDA and feature engineering.
4.  Generate customer segmentation and churn prediction outputs.
5.  Generate demand forecasts and evaluation results.
6.  Generate inventory recommendations.
7.  Run the dashboard and tests.
8.  Keep the generated reports with the outputs so the dashboard's
    explanations and metrics correspond to the same run.

Use the generated summaries and script outputs as the record of a
particular run. If the source data or scripts change, rerun the pipeline
and re-check the dashboard metrics.

## Data quality and modelling limitations

-   The data is historical and should not be interpreted as current
    market demand.
-   Some transactions have missing customer IDs or descriptions,
    cancellation invoices, returns, negative prices, or zero prices.
-   The cleaning and modelling scripts use different eligibility rules
    for different analyses; row counts can therefore differ between
    reports and datasets.
-   Cluster IDs are arbitrary. Interpret clusters using their profile
    metrics rather than their numeric labels alone.
-   Churn labels depend on the feature and observation windows chosen in
    the experiment.
-   Forecasting metrics are dependent on the products, time range, test
    window, and baseline methods used.
-   Inventory results rely on assumed stock levels and
    lead-time/safety-stock rules, not a live inventory-management
    system.
-   `RP_Customer_Loyalty_Index` is a heuristic project feature and has
    not been validated as a measure of loyalty.
-   Predictions and recommendations are educational estimates, not
    guaranteed outcomes or automated business decisions.

## GitHub and deployment notes

-   **Repository:**
    https://github.com/Ams1421/RetailPulse-AI-Customer-Analytics
-   The `.gitignore` excludes data files by default, trained model files
    under `models/*`, local backups, and temporary files. The eight processed
    CSV files required by the current dashboard are explicitly tracked in Git.
-   Do not commit secrets, `.env` files, large local backups, or the original
    Excel workbook.
-   The live Streamlit Community Cloud dashboard is available at:
    https://retailpulse-ai-customer-analytics.streamlit.app
-   When updating data outputs, verify that the required files are present
    in the repository and that the deployed app has completed its redeployment.

## Credits

-   **Dataset:** UCI Machine Learning Repository, Online Retail II ---
    https://archive.ics.uci.edu/dataset/502/online+retail+ii
-   **Project:** RetailPulse --- AI-Powered Customer Analytics & Demand
    Forecasting Platform
-   **Repository:**
    https://github.com/Ams1421/RetailPulse-AI-Customer-Analytics

------------------------------------------------------------------------

*RetailPulse is a learning and portfolio project. Review the source
code, data-processing rules, reports, and limitations before using its
outputs for business decisions.*
