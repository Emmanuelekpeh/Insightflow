# System Architecture

## High-Level Overview

```mermaid
graph TD
    Client[Next.js Frontend] --> API[FastAPI Backend]
    API --> Supabase[(Supabase DB)]
    API --> Redis[(Redis Queue)]
    Redis --> Worker[Arq Worker]
    Worker --> Supabase
```

## Component Structure

### Frontend Components

