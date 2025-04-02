# Setup Instructions

## Prerequisites

- Node.js 18+ 
- Python 3.9+
- Redis Server
- Supabase Account

## Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/insightflow.git
cd insightflow
```

2. Backend Setup:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your Supabase credentials
```

3. Frontend Setup:
```bash
# From project root
npm install
npm run dev
```

## Environment Variables

### Backend (.env)
```env
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

## Running the Application

1. Start Redis Server:
```bash
redis-server
```

2. Start Backend Worker:
```bash
cd backend
arq backend.worker.WorkerSettings
```

3. Start Backend API:
```bash
cd backend
uvicorn main:app --reload
```

4. Start Frontend:
```bash
npm run dev
```

Visit http://localhost:3000 to access the application.
