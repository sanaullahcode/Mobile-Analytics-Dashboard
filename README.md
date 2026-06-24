# 📱 Mobile Price Predictor

A Streamlit web app that predicts mobile phone prices (in PKR) using a Random Forest model trained on a 2025 mobile specs dataset. Includes user login/registration, an analytics dashboard, and a price prediction tool — all backed by a local SQLite database.

## Features
- 🔐 User authentication (login/register) with SQLite-backed accounts
- 📊 Interactive analytics dashboard (brand, year, processor, screen size distributions)
- 🔮 ML-based price predictor (Random Forest Regressor)
- 🕘 Per-user prediction history
- 🛠️ Admin panel (basic)

## Tech Stack
- [Streamlit](https://streamlit.io/) – UI
- [scikit-learn](https://scikit-learn.org/) – ML model
- [Plotly](https://plotly.com/python/) – charts
- SQLite – storage

## Project Structure
```
.
├── mobiles_app.py        # Main Streamlit app (entry point)
├── database.py           # SQLite database manager (users, predictions, activity)
├── prediction_model.py   # Data cleaning + Random Forest training/prediction logic
├── Mobiles_Dataset__2025_.csv  # Source dataset
├── requirements.txt
└── README.md
```

> Note: `mobile_analytics.db` and `*.pkl` model files are **not** committed to this repo — they're created automatically the first time you run the app / train the model.

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the app
```bash
streamlit run mobiles_app.py
```

⚠️ **Change these default passwords before deploying publicly** — they're meant for local testing only.

### 5. Train the model
Inside the app, go to the **Price Predictor** tab and click **"🚀 Train Prediction Model"**. This reads `Mobiles_Dataset__2025_.csv`, trains a Random Forest model, and saves it as `mobile_price_model.pkl` for future predictions.

## License
This project is for educational/demo purposes.
