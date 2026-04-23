# Operation Bot Presentation (4 Slides)

## Slide 1 - Project Goal + Input

Operation Bot turns restaurant CSV data into practical operations decisions.

Problem it solves:
- Finds bottleneck hours and weak channels
- Detects high-volume but low-revenue windows
- Gives clear staffing/scheduling/menu actions

CSV input contract:
- timestamp, orders, revenue, channel

Validation in utils/data_loader.py:
- Missing columns, bad timestamps, or bad numbers stop the run with errors

---

## Slide 2 - How the App Operates (End-to-End)

Pipeline in main.py:
1. Load + validate CSV
2. Analyze patterns in agents/analyzer.py
3. Generate bottleneck summary in agents/bottleneck_agent.py
4. Generate recommendations in agents/recommendation_agent.py
5. Save run output to memory/history.json via utils/memory.py

Modes from config.py:
- local (rule-based text)
- openai (model-generated text)

---

## Slide 3 - What the Code Produces

Analysis outputs:
- Peak/slow hours
- Busiest/slowest days
- Channel revenue performance
- Seasonality trends
- Volume vs revenue mismatch windows

How results are used:
- Bottleneck agent summarizes risk areas
- Recommendation agent turns those signals into priority actions

Each run is stored with timestamp, mode, analysis, bottlenecks, and recommendations.

---

## Slide 4 - Real Example + Demo Flow

Recent run example:
- Peak hours: 18, 11, 21
- Slow hours: 8, 14
- Strongest channel: delivery
- Weakest channel: takeout
- Mismatch hours: 8, 14, 18

Top actions generated:
1. Add staffing during peak windows
2. Move breaks/training to slow windows
3. Use bundles in mismatch windows to increase ticket size

Live demo steps:
1. Show sample CSV
2. Run python main.py
3. Show analysis, bottlenecks, recommendations
4. Open memory/history.json to show saved run history
