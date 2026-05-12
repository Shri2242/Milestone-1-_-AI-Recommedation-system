# Deploying the Streamlit App (Phase 8)

This document provides instructions on how to run the AI Restaurant Recommender locally using Streamlit and how to deploy it for free to the Streamlit Community Cloud.

## Running Locally

1. **Install Dependencies**
   Ensure your virtual environment is active, then install the required packages (Streamlit is included in `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```

2. **Set Environment Variables**
   Ensure your `.env` file exists in the root directory with your Groq API key:
   ```env
   GROQ_API_KEY="your_groq_api_key_here"
   ```

3. **Run the App**
   Start the Streamlit development server:
   ```bash
   streamlit run streamlit_app.py
   ```

4. **Access the App**
   Open your browser and navigate to `http://localhost:8501`.

---

## Deploying to Streamlit Community Cloud

Streamlit Community Cloud is the fastest way to share your application. It links directly to your GitHub repository and automatically redeploys when you push changes.

### Step 1: Push to GitHub
Make sure your latest code (including `streamlit_app.py` and `requirements.txt`) is pushed to your `main` branch on GitHub.

### Step 2: Connect to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click the **New App** button.
3. Fill in the details:
   - **Repository**: Select `Shri2242/Milestone-1-_-AI-Recommedation-system`
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`

### Step 3: Add API Secrets
Because your GitHub repository is public (or you don't want to commit the `.env` file), you must securely add your Groq API key to Streamlit's servers.

1. On the deployment configuration screen, click **Advanced settings...**
2. In the **Secrets** text box, enter your API key using TOML format:
   ```toml
   GROQ_API_KEY = "your_actual_groq_api_key_here"
   ```
3. Click **Save**.

### Step 4: Deploy
Click the **Deploy!** button. 

Streamlit will provision a server, install your dependencies from `requirements.txt`, and start the app. Once finished, your app will be live and accessible via a public URL!
