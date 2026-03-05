# FMCG Intelligence Platform

AI-enabled market intelligence platform for wholesale FMCG operations in Lebanon. Monitors commodity prices, assesses supply chain risks, and provides actionable business insights using Claude AI.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   React Dashboard                        │
│   Dashboard │ Commodities │ Supply Chain │ AI Insights   │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API
┌──────────────────────┴──────────────────────────────────┐
│                  FastAPI Backend                         │
├─────────────────────────────────────────────────────────┤
│  Market Data    │ Supply Chain │  AI Engine  │  Sync     │
│  - Commodity    │ - Risk       │  - Claude   │  - ERP    │
│    Tracker      │   Analyzer   │    Analysis │  - POS    │
│  - Price        │ - Alt        │  - Daily    │           │
│    Forecaster   │   Sourcing   │    Briefing │           │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis (Cache)  │  Background Scheduler   │
└─────────────────────────────────────────────────────────┘
```

## Key Features

- **Commodity Price Tracking**: Monitors rice, wheat, oils, sugar, diesel, and dairy prices with data from World Bank and FAO APIs
- **Price Forecasting**: Prophet-based time series forecasting with statistical fallback for price predictions
- **Supply Chain Risk Analysis**: Scores suppliers on geopolitical, logistics, financial, and currency risk factors
- **ERP/POS Integration**: Syncs product catalog, inventory levels, and sales data from existing systems
- **AI-Powered Insights**: Uses Claude to generate daily briefings, pricing recommendations, and sourcing strategies
- **Alert System**: Automated alerts for price spikes, supply disruptions, margin erosion, and low inventory
- **Lebanon-Specific**: Accounts for LBP volatility, Beirut/Tripoli port risks, and regional geopolitical factors

## Tracked Commodities

| Commodity | Category | Key Sourcing Regions |
|-----------|----------|---------------------|
| Rice (Long Grain) | Grain | India, Pakistan, Thailand |
| Wheat | Grain | Turkey, Ukraine, Russia |
| Sunflower Oil | Oil | Ukraine, Turkey, Argentina |
| Soybean Oil | Oil | Argentina, Brazil, USA |
| Palm Oil | Oil | Malaysia, Indonesia |
| Sugar (Raw) | Sugar | Brazil, India, Thailand |
| Diesel | Fuel | Saudi Arabia, Iraq |
| Brent Crude | Fuel | Global benchmark |
| Powdered Milk | Dairy | New Zealand, Netherlands |

## Quick Start

### Using Docker Compose

```bash
cp .env.example .env
# Edit .env with your API keys (ANTHROPIC_API_KEY required for AI features)

docker compose up -d

# Run database migrations
docker compose exec backend alembic upgrade head

# Seed sample data
docker compose exec backend python -m backend.seed_data
```

### Local Development

```bash
# Backend
pip install -e ".[dev]"
cp .env.example .env
uvicorn backend.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/dashboard/summary` | GET | Dashboard KPIs |
| `/api/dashboard/alerts` | GET | Active alerts |
| `/api/commodities/` | GET | List commodities |
| `/api/commodities/prices/latest` | GET | Latest prices |
| `/api/commodities/{id}/forecast` | GET | Price forecast |
| `/api/suppliers/` | GET | List suppliers |
| `/api/suppliers/{id}/assess-risk` | POST | Run risk assessment |
| `/api/suppliers/supply-chain/overview` | GET | Supply chain status |
| `/api/intelligence/insights` | GET | AI-generated insights |
| `/api/intelligence/daily-briefing` | POST | Generate daily briefing |
| `/api/intelligence/analyze-market` | POST | Run market analysis |
| `/api/sync/erp/products` | POST | Sync ERP products |
| `/api/sync/pos/sales` | POST | Sync POS sales |

### Running Tests

```bash
pytest tests/ -v
```

## Configuration

Key environment variables (see `.env.example`):

- `DATABASE_URL` - PostgreSQL connection string
- `ANTHROPIC_API_KEY` - Required for AI-powered insights
- `ERP_BASE_URL` / `ERP_API_KEY` - ERP system integration
- `POS_BASE_URL` / `POS_API_KEY` - POS system integration
- `LBP_EXCHANGE_RATE` - Current USD/LBP rate
