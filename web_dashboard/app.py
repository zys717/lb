import os
import json
import glob
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import re

app = FastAPI()

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base paths (relative to this file)
BASE_DIR = Path(__file__).resolve().parent.parent
SCENARIOS_DIR = BASE_DIR / "scenarios"
REPORTS_DIR = BASE_DIR / "reports"
GROUND_TRUTH_DIR = BASE_DIR / "ground_truth"
GUIDELINES_FILE = BASE_DIR / "rag" / "guidelines" / "guidelines.jsonl"

def parse_jsonc(file_path):
    """Simple helper to parse JSONC (JSON with comments)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove single line comments //
    content = re.sub(r'//.*', '', content)
    # Remove multi line comments /* */
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    return json.loads(content)

@app.get("/api/scenarios")
async def list_scenarios():
    """List all scenarios found in the scenarios directory."""
    scenarios = []
    # Walk through scenarios directory to find .jsonc files
    for root, dirs, files in os.walk(SCENARIOS_DIR):
        for file in files:
            if file.endswith(".jsonc") and file.startswith("S"):
                # Extract ID like S001
                match = re.match(r"(S\d+)", file)
                if match:
                    scenario_id = match.group(1)
                    rel_path = os.path.relpath(os.path.join(root, file), SCENARIOS_DIR)
                    
                    # Parse file to get test cases
                    try:
                        full_path = os.path.join(root, file)
                        data = parse_jsonc(full_path)
                        test_cases = []
                        if "test_cases" in data:
                            for tc in data["test_cases"]:
                                test_cases.append({
                                    "id": tc.get("id", tc.get("case_id", "Unknown")),
                                    "name": tc.get("name", ""),
                                    "description": tc.get("description", "")
                                })
                    except:
                        test_cases = []

                    scenarios.append({
                        "id": scenario_id,
                        "filename": file,
                        "path": rel_path,
                        "category": os.path.basename(root),
                        "test_cases": test_cases
                    })
    # Sort by ID
    scenarios.sort(key=lambda x: x["id"])
    return scenarios

@app.get("/api/scenario/{scenario_id}")
async def get_scenario(scenario_id: str):
    """Get details of a specific scenario."""
    # Find the file
    found_file = None
    for root, dirs, files in os.walk(SCENARIOS_DIR):
        for file in files:
            if file.startswith(scenario_id) and file.endswith(".jsonc"):
                found_file = os.path.join(root, file)
                break
        if found_file:
            break
    
    if not found_file:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    try:
        data = parse_jsonc(found_file)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing scenario: {str(e)}")

@app.get("/api/report/{scenario_id}")
async def get_report(scenario_id: str):
    """Get the RAG report for a scenario."""
    # Try to find Sxxx_RAG_REPORT.json
    report_file = REPORTS_DIR / f"{scenario_id}_RAG_REPORT.json"
    
    # Fallback to other naming conventions if needed, or check for LLM_VALIDATION
    if not report_file.exists():
        # Try LLM validation as fallback
        report_file = REPORTS_DIR / f"{scenario_id}_LLM_VALIDATION.json"
        
    if not report_file.exists():
        # Try Rule Baseline
        report_file = REPORTS_DIR / f"{scenario_id}_RULE_BASELINE.json"

    if not report_file.exists():
        raise HTTPException(status_code=404, detail="Report not found")
        
    try:
        with open(report_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading report: {str(e)}")

@app.get("/api/ground_truth/{scenario_id}")
async def get_ground_truth(scenario_id: str):
    """Get the ground truth for a scenario."""
    # Try to find Sxxx_violations.json
    gt_file = GROUND_TRUTH_DIR / f"{scenario_id}_violations.json"
    
    if not gt_file.exists():
        raise HTTPException(status_code=404, detail="Ground truth not found")
        
    try:
        with open(gt_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading ground truth: {str(e)}")

@app.get("/api/regulations")
async def get_regulations():
    """Get all guidelines/regulations."""
    if not GUIDELINES_FILE.exists():
        return []
        
    guidelines = []
    try:
        with open(GUIDELINES_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    guidelines.append(json.loads(line))
        return guidelines
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading guidelines: {str(e)}")

# Serve static files (Frontend)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
