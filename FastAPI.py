from fastapi import FastAPI, Query, Response
import requests
import io
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

# Menggunakan backend non-interaktif untuk Matplotlib
plt.switch_backend('Agg')

app = FastAPI()

# Fungsi untuk mendapatkan token
def get_token():
    url = "http://34.101.242.121:3000/api/v1/auth/login"
    data = {"username": "admin", "password": "admin123"}
    response = requests.post(url, json=data)
    if response.status_code == 200:
        response_json = response.json()
        if response_json.get("success"):
            return response_json["data"]  # Token berada di "data"
        else:
            raise Exception(f"Login failed: {response_json.get('message')}")
    else:
        raise Exception(f"Failed to get token. Status Code: {response.status_code}, Response: {response.text}")

# Fungsi untuk mengambil data dari API
def fetch_data_with_token(month: int, year: int):
    token = get_token()  # Ambil token secara otomatis
    headers = {"Authorization": f"Bearer {token}"}
    url = f"http://34.101.242.121:3000/api/v1/waste-records/month/{month}/year/{year}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()["data"]
        if len(data) == 0:  # Cek apakah data kosong
            raise Exception("No data available for the specified month and year")
        return data
    else:
        raise Exception(f"Failed to fetch data. Status Code: {response.status_code}, Response: {response.text}")

# Endpoint untuk mengambil data
@app.get("/fetch-data/")
def fetch_data(month: int = Query(...), year: int = Query(...)):
    try:
        data = fetch_data_with_token(month, year)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi bar chart
@app.get("/visualize-bar-chart/")
def visualize_bar_chart(month: int = Query(...), year: int = Query(...)):
    try:
        data = fetch_data_with_token(month, year)
        cleaned_data = [
            {
                "departement_name": item["departement"]["departement_name"],
                "total_weight": item["total_weight"]
            }
            for item in data if item["departement"] is not None
        ]
        df = pd.DataFrame(cleaned_data)
        plt.figure(figsize=(14, 6))
        sns.barplot(
            data=df,
            x="departement_name",
            y="total_weight",
            palette="cubehelix",
            edgecolor="black"
        )
        plt.title(f"Total Berat Sampah per Departemen ({month}/{year})", fontsize=18, weight='bold', color='darkblue')
        plt.xlabel("Departemen", fontsize=14, weight='bold')
        plt.ylabel("Berat Sampah (kg)", fontsize=14, weight='bold')
        plt.xticks(rotation=45, fontsize=12, ha='right', weight='bold')
        plt.yticks(fontsize=12, weight='bold')

        for index, row in df.iterrows():
            plt.text(index, row.total_weight + 2, f"{row.total_weight} kg", ha='center', fontsize=10, color='black', weight='bold')

        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi pie chart
@app.get("/visualize-pie-chart/")
def visualize_pie_chart(month: int = Query(...), year: int = Query(...)):
    try:
        data = fetch_data_with_token(month, year)
        cleaned_data = [
            {
                "departement_name": item["departement"]["departement_name"],
                "total_weight": item["total_weight"]
            }
            for item in data if item["departement"] is not None
        ]
        df = pd.DataFrame(cleaned_data)
        labels = df["departement_name"]
        sizes = df["total_weight"]
        percentages = [f"{size / sizes.sum() * 100:.1f}%" for size in sizes]
        plt.figure(figsize=(14, 8))
        wedges, texts = plt.pie(
            sizes,
            startangle=140,
            colors=plt.cm.Set3.colors,
            wedgeprops={'edgecolor': 'black'},
        )
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.3, y * 1.1),
                ha='center',
                va='center',
                fontsize=10,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )
        legend_labels = [f"{label} ({percentage})" for label, percentage in zip(labels, percentages)]
        plt.legend(
            wedges,
            legend_labels,
            title="Departemen dan Persentase",
            loc="upper left",
            bbox_to_anchor=(1.05, 1),
            fontsize=10,
            ncol=1
        )
        plt.title(f"Distribusi Sampah per Departemen ({month}/{year})", fontsize=16, weight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}

# Endpoint untuk visualisasi pie chart berdasarkan jenis sampah
@app.get("/visualize-pie-chart-categories/")
def visualize_pie_chart_categories(month: int = Query(...), year: int = Query(...)):
    try:
        data = fetch_data_with_token(month, year)
        categories_data = []
        for item in data:
            for category in item.get("categories", []):
                if category.get("category"):
                    categories_data.append({
                        "category_name": category["category"]["category_name"],
                        "total_weight": category["total_weight"]
                    })
        if not categories_data:
            raise Exception("No category data available for the specified month and year")
        df = pd.DataFrame(categories_data)
        grouped_df = df.groupby("category_name")["total_weight"].sum().reset_index()
        labels = grouped_df["category_name"]
        sizes = grouped_df["total_weight"]
        percentages = [f"{size / sizes.sum() * 100:.1f}%" for size in sizes]
        plt.figure(figsize=(14, 8))
        wedges, texts = plt.pie(
            sizes,
            startangle=140,
            colors=plt.cm.Set3.colors,
            wedgeprops={'edgecolor': 'black'},
        )
        for i, wedge in enumerate(wedges):
            angle = (wedge.theta2 - wedge.theta1) / 2 + wedge.theta1
            x = np.cos(np.radians(angle))
            y = np.sin(np.radians(angle))
            plt.annotate(
                labels[i],
                xy=(x, y),
                xytext=(x * 1.3, y * 1.1),
                ha='center',
                va='center',
                fontsize=10,
                weight='bold',
                arrowprops=dict(arrowstyle="-", color="black")
            )
        legend_labels = [f"{label} ({percentage})" for label, percentage in zip(labels, percentages)]
        plt.legend(
            wedges,
            legend_labels,
            title="Jenis Sampah dan Persentase",
            loc="center left",
            bbox_to_anchor=(1.1, 0.2),
            fontsize=10,
            ncol=1
        )
        plt.title(f"Distribusi Jenis Sampah ({month}/{year})", fontsize=16, weight='bold')
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return Response(content=buf.getvalue(), media_type="image/png")
    except Exception as e:
        return {"success": False, "error": str(e)}
