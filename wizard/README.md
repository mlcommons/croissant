# Croissant Wizard

Start locally:

```bash
pip install -r requirements.txt
streamlit run st_app.py
```

Launch the end-to-end tests locally (after you started the application):

```bash
nvm use default  # We recommend managing NPM using NVM
npm install
npm run cypress:open  # Opens the Cypress application
npm run cypress:run  # Runs e2e tests in background
```

You can debug the tests in Github Actions because failed screenshots are uploaded as artifacts.
