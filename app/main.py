import os
import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.configs.settings import STATIC_DIR
from app.routers import articles, stories, results


# Create FastAPI app
app = FastAPI(title="Article ReAngle")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(articles.router)
app.include_router(stories.router)
app.include_router(results.router)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    try:
        index_path = os.path.join(STATIC_DIR, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Article ReAngle</h1><p>Frontend files not found. Please check the file path.</p>",
            status_code=404,
        )


if __name__ == "__main__":
    uvicorn.run(app, host="=127.0.0.1", port="8000", reload=True)
