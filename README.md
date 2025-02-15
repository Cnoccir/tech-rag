# Technical Document Knowledge Assistant

A Streamlit-based Knowledge Assistant that serves as an authenticated, searchable, and interactive document repository for technical PDFs. The assistant integrates retrieval-augmented generation (RAG) and AI-driven workflows to enhance user experience.

## Features

- Cross-site authentication
- Document repository with search and filtering
- AI-powered PDF chat with multi-document reasoning
- Admin panel for document management
- Enhanced PDF viewer with dynamic search
- Vector-based retrieval and hybrid search

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with the following variables:
```
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/tech_rag

# Authentication
SECRET_KEY=your_secret_key

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
AWS_BUCKET_NAME=your_bucket_name

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=your_pinecone_index_name
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Run the application:
```bash
streamlit run app/main.py
```

## Running the Application

### Streamlit Frontend
To run the Streamlit frontend:
```bash
streamlit run app/frontend/Home.py
```

### FastAPI Backend
To run the FastAPI backend:
```bash
uvicorn app.main:app --reload
```

The backend will be available at `http://127.0.0.1:8000` and the frontend at `http://localhost:8501`.

## Database Migrations

### Creating a New Migration
To create a new migration:
```bash
alembic revision --autogenerate -m "Migration message"
```

### Applying Migrations
To apply the migrations to the database:
```bash
alembic upgrade head
```

Ensure PostgreSQL is running and the database URL is correctly configured in your `.env` file.

## Project Structure

```
tech_rag/
├── app/
│   ├── auth/           # Authentication modules
│   ├── chat/           # Chat and RAG components
│   ├── database/       # Database models and utilities
│   ├── document/       # Document processing and management
│   ├── static/         # Static files
│   └── main.py         # Main Streamlit application
├── scripts/            # Utility scripts
├── tests/             # Test files
├── .env               # Environment variables
├── README.md
└── requirements.txt
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
