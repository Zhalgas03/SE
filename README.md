# Trip DVisor — AI Travel Planner

Trip DVisor is an **AI-powered travel planning platform** that turns your preferences into a structured itinerary, lets you collaborate with friends, and supports premium features like weekly AI trip ideas. Built with a modern, modular stack for security, performance, and scalability.

---

## ✨ Features

- **Conversational AI planner**: interactive chat that collects trip preferences step-by-step and generates a structured, day-by-day itinerary (overview, highlights, daily plan, return trip).
- **PDF export**: save trips offline in a formatted PDF.
- **Collaboration & voting**: create polls for itineraries, vote as guest or logged user, weighted votes for registered users.
- **Authentication & security**:
  - Email/password with CAPTCHA
  - GitHub OAuth and Google OAuth
  - Two-factor authentication (2FA) via email codes
  - Password reset and account management
- **Premium plan**:
  - Stripe checkout & webhook integration
  - Weekly AI trip suggestions for subscribers
  - Dark/light themes for premium dashboard
- **Admin dashboard**: manage users, trips, votes.
- **External integrations**:
  - **Amadeus** — flights & transport
  - **Hotelbeds** — accommodation
  - **Google Maps** — interactive maps in itinerary
  - **Perplexity API** — AI route generation
  - **Travelpayouts** — budget estimation

---

## 🧱 Tech stack

- **Frontend:** React (SPA) with Framer Motion, Mapbox, Stripe, jsPDF/html2canvas
- **Backend:** Flask (Python) with Blueprints, JWT auth, Flask-Dance (OAuth)
- **Database:** PostgreSQL
- **Integrations:** Stripe, Amadeus, Hotelbeds, Perplexity, Google Maps
- **Hosting:** Railway (backend + DB), Vercel/Netlify (frontend)

---

## 📸 Screenshots

![Planner Chat](screenshots/planner_chat.png)
![Trip Overview](screenshots/trip_overview.png)
![Admin Panel](screenshots/admin_panel.png)
![Stripe Checkout](screenshots/stripe_checkout.png)

---

## 🚀 Getting started (local)

### Prerequisites
- Python 3.10+
- Node.js LTS
- PostgreSQL

### Backend

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r ../requirements.txt

# create backend/.env (see example below)
python app.py
