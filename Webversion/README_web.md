## 🌐 Web version (HTML / CSS / JavaScript)

Alongside the **Python** version, this project now has a **browser-based version** — an interactive RC column P–M interaction diagram (ACI 318) where you drag a factored demand onto the chart to check adequacy. No install, runs on any device.

**▶ Live demo:** https://bhattaraipawan.github.io/Interaction-Diagram/

The web app is three plain files in this repo: `index.html`, `style.css`, `script.js`.
To run it locally, just open `index.html` in a browser (or serve the folder with `python -m http.server` for clean relative paths).

<details>
<summary><b>Publish the live demo (GitHub Pages)</b></summary>

1. Commit `index.html`, `style.css` and `script.js` to this repo (the repo root, or a `docs/` folder if you'd rather keep the web files separate from the Python code).
2. **Settings → Pages → Build and deployment → Source:** *Deploy from a branch*.
3. Choose `main` and **`/ (root)`** (or **`/docs`** if you used that folder), then **Save**.
4. The demo goes live at the URL above in about a minute.
</details>
