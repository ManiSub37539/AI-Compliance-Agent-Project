from datetime import datetime

from agents.analyzer import analyze
from agents.bottleneck_agent import run_bottleneck_agent
from agents.recommendation_agent import refine_recommendations
from config import DATA_PATH, MODE, MODEL
from utils.data_loader import load_data
from utils.memory import save_run


def main() -> None:
    df = load_data(DATA_PATH)
    analysis = analyze(df)

    print("ANALYSIS RESULTS:")
    print(analysis)

    bottlenecks = run_bottleneck_agent(analysis)
    print("\nBOTTLENECKS:")
    print(bottlenecks)

    recommendations = refine_recommendations(analysis, bottlenecks)
    print("\nRECOMMENDATIONS:")
    print(recommendations)

    save_run(
        {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mode": MODE,
            "model": MODEL,
            "analysis": analysis,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
        }
    )


if __name__ == "__main__":
    main()
