"""from agents.agent1 import run_agent1
from agents.agent2 import run_agent2
from agents.agent3 import run_agent3
from agents.agent4 import run_agent4
import os

DATA_PATH = r"C:\Users\HP\Desktop\ESG-Monitoring-System\Dataset\Manufacturing_ESG_Financial_Data.csv"
OUTPUT_DIR = r"C:\Users\HP\Desktop\ESG-Monitoring-System\outputs"

def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    run_agent1(DATA_PATH, os.path.join(OUTPUT_DIR, "ESG1_Output.csv"))
    run_agent2(os.path.join(OUTPUT_DIR, "ESG1_Output.csv"), os.path.join(OUTPUT_DIR, "ESG2_Output.csv"))
    run_agent3(os.path.join(OUTPUT_DIR, "ESG2_Output.csv"), os.path.join(OUTPUT_DIR, "ESG3_Output.csv"))
    run_agent4(os.path.join(OUTPUT_DIR, "ESG3_Output.csv"), os.path.join(OUTPUT_DIR, "ESG4_Output.csv"))

    print("Full ESG Multi-Agent Pipeline ")

if __name__ == "__main__":
    run_pipeline()
"""