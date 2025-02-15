## Running the Application

The application consists of two components that need to be run separately:

### 1. FastAPI Backend
```bash
# From project root
python run.py
# Or alternatively:
uvicorn app.main:app --reload --port 8000
```
The backend API will be available at `http://localhost:8000`

### 2. Streamlit Frontend
```bash
# In a separate terminal, from project root
streamlit run app/frontend/app.py
```
The frontend will be available at `http://localhost:8501`

### Accessing the Application

1. First ensure both services are running:
   - Backend should show: "Uvicorn running on http://0.0.0.0:8000"
   - Frontend should automatically open in your browser at http://localhost:8501

2. Login with default admin credentials:
   - Username: admin
   - Password: admin123!(change this in production)

3. API documentation is available at:
   - Swagger UI: `http://localhost:8000/api/v1/docs`
   - ReDoc: `http://localhost:8000/api/v1/redoc`

### Checking Services

1. Backend Health Check:
```bash
curl http://localhost:8000/api/v1/
# Should return: {"status":"online","message":"Tech RAG API is running","version":"1.0.0"}
```

2. Frontend:
- The Streamlit interface should automatically open in your default browser
- If not, manually navigate to `http://localhost:8501`
