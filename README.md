# Recipe Helper

A personal tool that takes a recipe URL and reformats it to just ingredients and directions. Features:

- Strips away ads, comments, and blog content — just the recipe
- Ingredient amounts are annotated inline in the directions (e.g. "add the eggs [2 eggs]")
- Sliders on each ingredient let you scale the entire recipe proportionally

> [!NOTE]
> This is a toy/experimental project. You're welcome to fork the repo or make suggestions in the issue
> tracker but I am not maintaining it as an open source project and will be entirely self-centered in 
> any changes I make.

## Stack

- **Frontend:** Vue 3 + Vite
- **Backend:** Python FastAPI + [recipe-scrapers](https://github.com/hhursev/recipe-scrapers)

## Local Development

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 2. Start the frontend

In a separate terminal, from the project root:

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173/recipehelper/`. The Vite dev server proxies `/api` requests to the backend automatically.

### 3. Run backend tests

```bash
cd backend
pytest -v
```

## Deployment

### Backend

Deploy the `backend/` folder to [Render](https://render.com) or [Railway](https://railway.app) (both have free tiers):

- **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
- No environment variables required

### Frontend

1. Set your deployed backend URL in a `.env.production` file in the project root:
   ```
   VITE_API_URL=https://your-backend.onrender.com
   ```

2. Build and deploy to GitHub Pages:
   ```bash
   npm run build
   npm run deploy
   ```

   This runs `gh-pages -d dist`, which pushes the `dist/` folder to the `gh-pages` branch.
   In your GitHub repo settings, set Pages to serve from the `gh-pages` branch.

> **Note:** The `base` in `vite.config.js` is set to `/recipehelper/` to match the GitHub repo name. If your repo is named differently, update that value.

## Compatibility

Works with most food blogs and independent recipe sites that use [schema.org/Recipe](https://schema.org/Recipe) structured data. Large commercial sites (AllRecipes, NYT Cooking, etc.) may block server-side requests with a 403.
