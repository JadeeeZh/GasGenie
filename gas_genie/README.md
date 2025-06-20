# Gas Genie

Gas Genie is an AI-powered side-panel that predicts the cheapest safe gas price and auto-suggests "wait vs send" decisions, plus one-click "speed-up" or "cancel" options for transactions.

## Features

- Real-time gas price monitoring from multiple sources
- ML-based gas price predictions
- Smart "wait vs send" recommendations
- Transaction speed-up suggestions
- One-click transaction management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gas-genie.git
cd gas-genie
```

2. Create a virtual environment and activate it:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your API keys:
```bash
cp .env.example .env
# Edit .env with your API keys
```

## Usage

1. Start the Gas Genie agent:
```bash
python -m src.gas_genie.gas_genie
```

2. The agent will be available at `http://localhost:8000`

3. You can interact with the agent through the Sentient Chat interface or programmatically using the API.

## API Endpoints

- `POST /assist`: Main endpoint for gas price predictions and recommendations
- `GET /health`: Health check endpoint

## Deployment

The agent can be deployed on Google Cloud Platform (GCP) following the standard deployment guide for Sentient agents.

## License

MIT License 