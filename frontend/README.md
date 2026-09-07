# Frontend

The frontend is a React 19 single-page interface built by Vite 7 and styled with Tailwind CSS. [`src/App.jsx`](src/App.jsx) owns navigation, model selection, current-session history, and background AI-insight requests.

## Main flow

[`src/pages/UploadPage.jsx`](src/pages/UploadPage.jsx) accepts a PDF, allows edits to the three extracted REF sections, and starts either MIL or Gemma inference through [`src/services/api.js`](src/services/api.js). API jobs are submitted once and polled every 10 seconds until completion or failure.

After MIL completes, `App.jsx` starts AI-insight generation independently. Navigation remains available while those insights are being polled. MIL and Gemma execution disable the main fieldset until their request finishes.

[`src/pages/InferenceHistoryPage.jsx`](src/pages/InferenceHistoryPage.jsx) displays MIL and Gemma results held in React state. This history is not loaded from the backend and disappears on refresh. AI-insight polling is owned by `App.jsx`, so switching between Upload and Inference History does not cancel it; requests are aborted only when `App` unmounts.

## Results and exports

- [`src/components/InferenceResults.jsx`](src/components/InferenceResults.jsx) renders MIL overview, AI insights, attention heatmap, features, and entities.
- [`src/components/GemmaResults.jsx`](src/components/GemmaResults.jsx) renders the Gemma GPA, diagnostic comments, title, and measured request duration.
- [`src/services/exportAnalysisPdf.js`](src/services/exportAnalysisPdf.js) exports MIL analysis and the currently available AI insight state.
- [`src/services/exportGemmaPdf.js`](src/services/exportGemmaPdf.js) exports the Gemma title, model, GPA, duration, and comments.

## Commands

Install dependencies once:

```bash
npm install
```

Available scripts:

```bash
npm run dev
npm run lint
npm run build
npm run preview
```

[`src/services/api.js`](src/services/api.js) uses relative `/api` URLs. [`vite.config.js`](vite.config.js) contains a commented proxy example but does not currently enable a development proxy.
