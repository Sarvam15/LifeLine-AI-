# 🚑 LifeLine-AI

### 🎥 Watch the Demo Video
[![Watch the Demo](https://img.shields.io/badge/YouTube-Watch%20Demo%20Video-red?style=for-the-badge&logo=youtube)](PASTE_YOUR_YOUTUBE_OR_DRIVE_VIDEO_LINK_HERE)

*Click the badge above to watch our full demonstration video walk-through!*

---

## 📝 Project Overview
**A responsive, AI-powered emergency dispatch dashboard built using Python and Streamlit.** This platform translates complex backend dispatching logic into an interactive web interface. The system features a mobile-optimized three-tier selection layout (Public, Private, and AI-Priority "Fastest" service), integrated light/dark UI themes, a simulated live countdown timer with random ambulance matching probabilities, and automated patient-condition chat routing. It also integrates real-world geographic visualization using interactive Folium map displays driven by live road-routing server APIs (OSRM).

---

## 🛠️ Project Timeline & Development Architecture

This repository tracks the complete evolution of LifeLine-AI from an initial algorithmic terminal layout to a fully functional, deployment-ready web application:

* **Version 1: The Terminal Prototype (Built with Gemini)**
    * [View Initial Backend Code](./prototype-1/main.py)
    * *Core Logic:* A pure Python terminal-based simulation mapping out the mathematical tracking backend and the automated public service escalation fail-safe.
* **Version 2: The Operational Web App Dashboard (Built on Replit)**
    * [View Operational App Code](./prototype-2%20(current%20version)/app.py) | [Launch Live Application Deployment]((https://life-line-aid--sarvamishra1501.replit.app/))
    * *Core Logic:* The complete interactive web system running on a custom Streamlit layout. It features interactive dashboard selection tiles, live road-mapped visual tracking canvas components, random driver/hospital matching logic matrices, and a direct emergency triage patient-to-hospital chat interface.

---

## 🚀 Future Roadmap (Version 3 — In Active Development)

Version 3 transitions LifeLine-AI from an interactive monitoring hub into an active urban automation network. The core focus is eliminating traffic delays during the "golden hour" via **Automated Green Corridor Technology** and predictive crowd clearance.

### 🟢 Smart Green Corridor Framework
* **V2I (Vehicle-to-Infrastructure) Handshake:** Moving away from manual police coordination, ambulances will stream high-precision telemetry data to a centralized municipal routing cloud.
* **Predictive Signal Preemption:** Integrating live traffic control APIs to predict the ambulance's intersection arrival times, dynamically changing upcoming red lights to green to clear the intersection safely before the vehicle reaches it.
* **AI-Powered Edge Vision:** Incorporating quantized deep learning vision models on existing municipal CCTV feeds to monitor real-time vehicle density, executing priority overrides while minimizing disruption to surrounding urban traffic flow.

### 🚗 Dynamic Traffic Redistribution & Pre-Alerts
* **Predictive Congestion Routing:** Instead of just finding the fastest path, the AI routing engine will actively communicate with municipal traffic platforms to dynamically redistribute surrounding traffic. By altering recommended navigation paths for everyday commuters nearby, the system prevents bottlenecking along the ambulance's active route.
* **Geofenced Commuter Alerts:** Utilizing geofencing APIs to push real-time audio and visual alerts directly to drivers already on the ambulance's upcoming path (via integrated navigation apps or digital roadside signage). This warns commuters to smoothly clear the fast lane *before* the ambulance is close enough to be heard, preventing panicked last-second lane switches and gridlock.

### 🩺 Advanced Biometric Integration
* **Pre-Screener Triage:** Integrating real-time health data (such as heart rate and blood oxygen levels) directly from patient smartwatches into the hospital triage chat module. This allows ER trauma teams to review live patient metrics and prep specific surgical equipment minutes before the ambulance physically reaches the bay.
