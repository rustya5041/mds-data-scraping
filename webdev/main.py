import io
import base64
import math
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import matplotlib.pyplot as plt
import numpy as np

plt.style.use('seaborn')

app = FastAPI()
templates = Jinja2Templates(directory='templates')
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root(request: Request) -> None:
    """
    This function returns the index.html page
    """
    return templates.TemplateResponse("index.html", 
                                      {"request" : request})

@app.get("/solve")
async def solve(a:int, b:int, c:int) -> dict:
    """
    This function returns the roots of a quadratic equation
    params: a, b, c - coefficients of the quadratic equation
    returns: a dictionary with the roots of the quadratic equation
    """
    if b**2 - 4*a*c < 0:
        return {"roots" : []}
    elif b**2 - 4*a*c == 0:
        return {"roots" : [-b/(2*a)]}
    else:
        return {"roots" : sorted([(-b + math.sqrt(b**2 - 4*a*c))/(2*a), (-b - math.sqrt(b**2 - 4*a*c))/(2*a)])}

@app.post("/plot")
async def plot(request:Request, a:str = Form(...), b:str = Form(...), c:str = Form(...)):
    """
    This function returns the plot of a quadratic equation
    params: a, b, c - coefficients of the quadratic equation
    returns: a plot of the quadratic equation
    """
    a = int(a)
    b = int(b)
    c = int(c)

    roots = await solve(a, b, c)

    fig = plt.figure()
    x = np.linspace(-10, 10, 100)
    y = a*x**2 + b*x + c
    plt.plot(x, y)
    plt.grid()
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Parabola of the quadratic equation')
    plt.axhline(y=0, color='k')
    plt.axvline(x=0, color='k')
    plt.savefig('plot.png')
    
    img = io.BytesIO()
    fig.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()

    return templates.TemplateResponse("plot.html",
                                        {"request" : request, 'a': a, 'b': b, 'c': c,
                                        "roots" : roots['roots'],
                                        "picture" : plot_url})