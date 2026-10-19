
# Multimodal Pepper AI Decision Support System

An AI-powered mobile-based system for **black pepper crop analysis, quality assessment, and market decision support**.

This project integrates **computer vision, machine learning, and time-series forecasting** to help farmers detect crop issues, evaluate pepper quality, and make informed selling decisions.

---

## 🚀 Features

- 🔍 **Pest Detection**
  - Detect pests on pepper plants using image-based AI models

- 🍃 **Leaf Disease Detection & Severity Analysis**
  - Identify diseases and estimate infection severity

- 🫛 **Berry Disease Detection**
  - Detect diseases affecting pepper berries and provide safe remediation advice

- 📊 **Berry Grading & Quality Scoring**
  - Analyze berry size, color, and texture to determine export quality

- 📈 **Price Forecasting**
  - Predict short-term market prices using historical data

- 💡 **Decision Support**
  - Recommend actions:
    - Sell now
    - Wait for better price
    - Process locally

- 📱 **Mobile Application**
  - Farmers can capture images and receive real-time insights

---

## 🧠 System Architecture

```

Mobile App (Flutter)
↓
FastAPI Backend
↓
AI Models (PyTorch + OpenCV)
↓
Firebase / Cloud Storage

```

The system processes images captured from the field and combines AI predictions with market data to generate actionable insights.

---

## 🏗️ Project Structure

```

multimodal-pepper-ai-decision-support/

├── backend/        # FastAPI backend services
├── mobile/         # Flutter mobile application
├── ml/             # Machine learning models
├── data/           # Datasets (raw, processed)
├── notebooks/      # Experiments & EDA
├── docs/           # Documentation
├── scripts/        # Utility scripts
└── README.md

```

---

## ⚙️ Tech Stack

### 🔹 Backend
- FastAPI
- Python

### 🔹 Machine Learning
- PyTorch
- OpenCV
- Scikit-learn
- Time-series models (ARIMA / LSTM / Prophet)

### 🔹 Mobile
- Flutter

### 🔹 Cloud & Storage
- Firebase

---

## 📊 Workflow

1. Capture image via mobile app  
2. Upload to backend API  
3. Preprocess image (OpenCV)  
4. Run AI models (classification / detection / segmentation)  
5. Compute quality score  
6. Predict market price  
7. Generate recommendation  
8. Return results to mobile app  

---

## 📁 Data Pipeline

- Raw data collection (field visits)
- Image preprocessing & augmentation
- Feature extraction
- Model training & evaluation
- Inference via API

---

## ✅ Berry Grading & Export Price Forecasting (IT22079268)

This component focuses on berry quality grading, export price forecasting, and decision support. It is based on the responsibilities defined in the project proposal and implemented across the backend, ML pipeline, and mobile app.

### Current Authoritative Workflow

The current research workflow uses V3 YOLO11 berry grading with the frozen
Phase 3 follow-up model, the selected Phase 5 grade-specific forecasting
specification and saved forecast records, the Phase 6 decision engine, and the
Phase 7 backend ONNX integration used by Flutter. Older MobileNetV2, V1, and V2
files are retained as historical evidence or backend fallback artifacts; they
must not be mistaken for the selected V3 research workflow.

See [Repository Inventory](docs/guides/repository_inventory.md) for the active,
historical, generated, ignored-local, and protected artifact boundaries.

### Key Implementation Areas

- backend/app/api/routes/grading_forecast.py (API endpoints)
- backend/app/services/grading_forecast/ (grading, forecasting, recommendations, Firebase storage)
- ml/grading_forecast/ (training, evaluation, inference, and model artifacts)
- data/raw/market_prices and data/raw/berry_images (source datasets)
- data/processed/grading_forecast (cleaned data, splits, and summaries)
- mobile/lib/features/grading_forecast/ (UI screens + API client)

### Progress Checklist (WBS Tasks)

- [x] T1 Dataset collection (berry images + market prices)
- [x] T2 Dataset cleaning and preparation
- [x] T3 Image preprocessing (OpenCV-based)
- [x] T4 Feature extraction (visual quality features)
- [x] T5 Berry grading model development (MobileNetV2 + ONNX export)
- [x] T6 Export price forecasting model development (RandomForest + baselines)
- [x] T7 Backend API development and integration
- [x] T8 Mobile dashboard development
- [ ] T9 Database integration (configure Firebase credentials and verify live writes)
- [ ] T10 System testing and evaluation (full end-to-end + field validation)

---

## 👥 Team

- Member 1 – Pest Detection  
- Member 2 – Leaf Disease Detection  
- Member 3 – Berry Disease Detection  
- Member 4 – Berry Grading & Price Forecasting  

---

## 📌 Future Improvements

- Improve model accuracy with larger datasets  
- Real-time inference optimization  
- Offline mode for mobile app  
- Advanced forecasting models  
- Integration with agricultural advisory systems  

---

## 📄 License

This project is for academic and research purposes.

---

## ⭐ Acknowledgements

- Agricultural experts and pepper farmers  
- Academic supervisor and research guidance  
- Open-source ML and development communities  
