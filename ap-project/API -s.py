# به نام او 

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Load and preprocess data
df = pd.read_csv("myket_app_store.csv")
df = df.dropna()

@app.get("/summary", response_class=HTMLResponse)
async def read_root(request: Request):
    # Generate charts
    charts = generate_charts(df)
    return templates.TemplateResponse("charts.html", {"request": request, "charts": charts})

@app.get("/data", response_class=JSONResponse)
async def get_data():
    # Convert data to JSON serializable format
    data_info = {
        "shape": df.shape,
        "head": df.head().to_dict(),
        "unique_categories": df['category_fa'].nunique(),
        "category_counts": df['category_fa'].value_counts().to_dict(),
        "missing_values": df.isna().sum().to_dict(),
        "duplicated_values": df.duplicated().sum(),
        "description": df.describe().to_dict(),
        "top_10_apps": df.sort_values(by='installs', ascending=False).head(10)[['app_name', 'installs']].to_dict(),
        "mean_rating": df['rating'].mean(),
        "category_installs_average": df.groupby('category_fa')['installs'].mean().astype(int).sort_values(ascending=False).to_dict()
    }
    return data_info

def generate_charts(df):
    charts = {}

    # Top 10 Apps by Installs
    top_10_apps = df.sort_values(by='installs', ascending=False).head(10)
    fig1 = px.bar(top_10_apps, x='app_name', y='installs', title='Top 10 Apps by Installs')
    charts['top_10_apps'] = fig1.to_html(full_html=False)

    # Rating Distribution
    fig2, ax = plt.subplots()
    ax.hist(df['rating'], bins=100)
    ax.set_xlabel('Rating')
    ax.set_ylabel('Frequency')
    ax.set_title('Rating Distribution')
    charts['rating_distribution'] = fig_to_base64(fig2)

    # Total Apps by Category
    categories = df['category_en'].value_counts()
    fig3 = go.Figure(go.Bar(x=categories.values[::-1], y=categories.index[::-1], orientation='h'))
    fig3.update_layout(title="Total Apps by Category", xaxis_title="Number of Apps", yaxis_title="Category")
    charts['total_apps_by_category'] = fig3.to_html(full_html=False)

    # New Total Apps by Category chart
    trace1 = go.Bar(
        x=categories.values[::-1],
        y=categories.index[::-1],
        orientation='h',
        text=categories.values[::-1]
    )
    layout = go.Layout(
        autosize=False,
        width=1000,
        height=1000,
        xaxis=dict(linecolor='black', linewidth=0.5, mirror=True),
        yaxis=dict(linecolor='black', linewidth=1, mirror=True),
        margin=go.layout.Margin(l=100, r=100, b=100, t=100, pad=10)
    )
    fig4 = go.Figure(data=[trace1], layout=layout)
    fig4.update_layout(
        title="Total Apps by Category",
        xaxis_title="Number of Apps",
        yaxis_title="Category",
        title_x=0.5,
        font=dict(family="mirza", size=18, color="black"),
        bargap=0.4
    )
    fig4.update_traces(textposition='outside', marker_color='rgb(19, 68, 160)')
    charts['new_total_apps_by_category'] = fig4.to_html(full_html=False)

    # Category-wise Rating Distribution Analysis
    fig5, ax = plt.subplots()
    for category in df['category_en'].unique():
        category_df = df[df['category_en'] == category]
        ax.hist(category_df['rating'], bins=20, alpha=0.5, label=category)
    ax.set_xlabel('Rating')
    ax.set_ylabel('Frequency')
    ax.set_title('Rating Distribution by Category')
    ax.legend()
    charts['category_rating_distribution'] = fig_to_base64(fig5)

    return charts

def fig_to_base64(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"

