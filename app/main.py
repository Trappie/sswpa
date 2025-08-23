from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Steinway Society of Western Pennsylvania")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/mission", response_class=HTMLResponse)
async def mission(request: Request):
    return templates.TemplateResponse("mission.html", {"request": request})

@app.get("/programs", response_class=HTMLResponse)
async def programs(request: Request):
    return templates.TemplateResponse("programs.html", {"request": request})

@app.get("/board", response_class=HTMLResponse)
async def board(request: Request):
    return templates.TemplateResponse("board.html", {"request": request})

@app.get("/tickets", response_class=HTMLResponse)
async def tickets(request: Request):
    return templates.TemplateResponse("tickets.html", {"request": request})

@app.get("/young-artists/about", response_class=HTMLResponse)
async def young_artists_about(request: Request):
    return templates.TemplateResponse("young-artists-about.html", {"request": request})

@app.get("/young-artists/audition", response_class=HTMLResponse)
async def young_artists_audition(request: Request):
    return templates.TemplateResponse("young-artists-audition.html", {"request": request})

@app.get("/young-artists/heinz-hall", response_class=HTMLResponse)
async def young_artists_heinz_hall(request: Request):
    return templates.TemplateResponse("young-artists-heinz-hall.html", {"request": request})

@app.get("/young-artists/honors", response_class=HTMLResponse)
async def young_artists_honors(request: Request):
    return templates.TemplateResponse("young-artists-honors.html", {"request": request})

@app.get("/membership", response_class=HTMLResponse)
async def membership(request: Request):
    return templates.TemplateResponse("membership.html", {"request": request})

@app.get("/support", response_class=HTMLResponse)
async def support(request: Request):
    return templates.TemplateResponse("support.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/health")
async def health_check():
    return {"status": "healthy"}