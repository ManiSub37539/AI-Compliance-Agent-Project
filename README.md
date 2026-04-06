# AI-Compliance-Agent-Project

## What It Does
- Reviews prompts and outputs and flags risk before potential damage happens.
- Checks prompts before they are sent to analysis for safety concerns (for example, sensitive info), appropriateness, assumptions, data accuracy, and hallucination risk.
- Provides suggestions to improve prompt structure and quality.

## What It Does Not Do
- Provide legal advice. The assistant should explicitly direct users to professional services when needed.
- Use strong language. The agent is intended to assist, not replace professional services.

## Operation Bot (Restaurant Data)

This is a beginner-friendly agent workflow project that reads restaurant sales data, finds bottlenecks, and gives suggestions.

### Features
- Finds busy and slow hours.
- Compares revenue by sales channel.
- Flags hours with lots of orders but weak revenue.
- Saves each run to a JSON history file.
- Supports local mode and OpenAI mode.

### Files
- `main.py` - runs the full workflow.
- `config.py` - reads `.env` settings.
- `data/sample_data.csv` - sample dataset.
- `agents/analyzer.py` - metrics and grouping.
- `agents/bottleneck_agent.py` - bottleneck summary generation.
- `agents/recommendation_agent.py` - recommendation generation.
- `utils/data_loader.py` - CSV validation and parsing.
- `utils/memory.py` - run history writer.
- `prompts/system_prompt.txt` - system prompt for OpenAI mode.
- `memory/history.json` - saved outputs from previous runs.

### Run
1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env`.
4. Run:

```bash
python main.py
```

### Modes
Local mode:

```env
MODE=local
```

OpenAI mode:

```env
MODE=openai
OPENAI_API_KEY=your_key_here
MODEL=gpt-5
```

### Required CSV Columns
- `timestamp`
- `orders`
- `revenue`
- `channel`

### Template Credit
Originally based on a Boot.dev lesson template, then adapted for this restaurant bottleneck use case.
