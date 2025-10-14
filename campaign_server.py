import asyncio
import csv
import io
from typing import List, Optional

# top-level imports and app setup
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from langgraph_make_call import make_travel_planning_call
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# Allow Next.js dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

campaign_state = {
    "total": 0,
    "pending": [],  # type: List[str]
    "in_progress": None,  # type: Optional[str]
    "completed": [],  # type: List[str]
    "failed": [],  # type: List[str]
    "running": False,
}


def normalize_phone(n: str) -> str:
    n = n.strip()
    if not n:
        return n
    return n if n.startswith("+") else "+" + n


def extract_phone_numbers(file_bytes: bytes) -> List[str]:
    text = file_bytes.decode("utf-8", errors="ignore")
    stream = io.StringIO(text)

    # Try DictReader for header-based CSV first
    stream.seek(0)
    dr = csv.DictReader(stream)
    numbers: List[str] = []

    if dr.fieldnames:
        candidates = [fn for fn in dr.fieldnames if fn and fn.lower() in {"phone", "phone_number", "phone number", "number"}]
        if candidates:
            col = candidates[0]
            for row in dr:
                val = (row.get(col) or "").strip()
                if val:
                    numbers.append(normalize_phone(val))
    
    # Fallback: treat first column as phone if header not found
    if not numbers:
        stream.seek(0)
        rr = csv.reader(stream)
        for i, row in enumerate(rr):
            if not row:
                continue
            # Skip header-like first row if it contains non-digit content
            if i == 0 and any(ch.isalpha() for ch in ",".join(row)):
                continue
            numbers.append(normalize_phone(row[0]))

    # Filter out empties and deduplicate while preserving order
    seen = set()
    result: List[str] = []
    for n in numbers:
        if n and n not in seen:
            seen.add(n)
            result.append(n)
    return result


async def run_campaign(numbers: List[str]):
    campaign_state["running"] = True
    campaign_state["pending"] = numbers.copy()
    campaign_state["total"] = len(numbers)
    campaign_state["completed"] = []
    campaign_state["failed"] = []

    for n in numbers:
        campaign_state["in_progress"] = n
        try:
            # Initiate outbound call via LiveKit to this number
            await make_travel_planning_call(n)
            campaign_state["completed"].append(n)
        except Exception:
            campaign_state["failed"].append(n)
        finally:
            # Remove from pending
            if campaign_state["pending"] and campaign_state["pending"][0] == n:
                campaign_state["pending"].pop(0)
            # Small delay between calls to avoid rapid-fire dialing
            await asyncio.sleep(3)
    campaign_state["in_progress"] = None
    campaign_state["running"] = False


# index() route
@app.get("/", response_class=FileResponse)
async def index():
    return FileResponse("frontend/index.html")


@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")
    content = await file.read()
    numbers = extract_phone_numbers(content)
    if not numbers:
        raise HTTPException(status_code=400, detail="No phone numbers found in CSV")

    # Run sequential campaign in background
    asyncio.create_task(run_campaign(numbers))
    return JSONResponse({"message": "Campaign started", "total": len(numbers)})


@app.get("/status")
async def status():
    return JSONResponse(campaign_state)


# Mount static assets under /frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("campaign_server:app", host="127.0.0.1", port=8000, reload=True)