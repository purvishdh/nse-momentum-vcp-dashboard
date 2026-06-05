---
title: NSE Momentum VCP Dashboard
emoji: 📈
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# NSE Momentum VCP Dashboard

Live NSE-backed momentum trading dashboard built on the VCP (Volatility Contraction Pattern) strategy by Mark Minervini.

## Features
- Live Volume Gainers from NSE
- Most Active Equities Screener
- Sector Rotation Chart
- 52-Week High/Low Watchlist
- VCP Entry / Exit Rules
- Position Allocation Matrix

## How to run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
