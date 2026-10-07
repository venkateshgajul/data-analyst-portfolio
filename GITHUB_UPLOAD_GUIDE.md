# How to put this portfolio on GitHub (step by step)

Time needed: about 20 minutes. Pick **one** of the three methods in Part B.

## Part A - Prepare (5 min)
1. Unzip `data-analyst-portfolio.zip`. You should see `README.md`, `requirements.txt`, `LICENSE`, `.gitignore` and two project folders.
2. Open `README.md` and `LICENSE` and replace every `<YOUR NAME>`, `<city>`, `<your-handle>`, `<your-email>`.
3. (Recommended) Build the Power BI dashboards using `powerbi/DASHBOARD_BUILD_GUIDE.md` and save the `.pbix` files in each `powerbi/` folder. Export 2-3 dashboard screenshots to each project's `images/` folder and add them near the top of that project's README:
   `![Dashboard](images/dashboard_page1.png)`
4. Optional test run: `pip install -r requirements.txt` then run the commands in the main README to confirm everything works on your machine.

## Part B - Upload
### Method 1 - GitHub Desktop (easiest, recommended)
1. Create a free account at github.com (use a professional username, e.g. `firstname-lastname` or `firstnamedata`).
2. Install **GitHub Desktop** (desktop.github.com) and sign in.
3. `File > Add local repository` > choose the unzipped folder. If it says "not a Git repository", click **create a repository here**.
4. Name: `data-analyst-portfolio`. Description: *SQL, Python, Excel and Power BI projects: retail profitability and telecom churn*.
5. In the left panel you will see all files. Type a summary such as `Add retail and churn analytics projects` and click **Commit to main**.
6. Click **Publish repository**. Keep "Keep this code private" **unchecked** (recruiters must be able to see it). Done.

### Method 2 - Git command line
Install Git (git-scm.com), then open a terminal inside the unzipped folder:
```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"     # same email as your GitHub account

git init
git add .
git commit -m "Add retail sales and telecom churn analytics projects"
git branch -M main
```
On github.com click **+ > New repository**, name it `data-analyst-portfolio`, choose **Public**, and **do NOT tick** "Add a README / .gitignore / license" (the repo already has them). Copy the URL shown, then:
```bash
git remote add origin https://github.com/<your-username>/data-analyst-portfolio.git
git push -u origin main
```
A browser window will ask you to sign in the first time (Git Credential Manager). If you are asked for a password in the terminal, use a **Personal Access Token** (GitHub > Settings > Developer settings > Tokens), not your account password.

### Method 3 - Browser drag-and-drop (no software)
1. github.com > **+ > New repository** > name `data-analyst-portfolio` > Public > tick "Add a README file" > Create.
2. **Add file > Upload files**. GitHub accepts up to **100 files per upload**, so upload **one project folder at a time** (drag the *contents* so that folders are preserved), commit, then repeat for the second project and the top-level files.
3. Overwrite the auto-generated `README.md` with the one from the zip.
Note: the browser cannot upload empty folders, and `.gitignore`/hidden files may need to be added individually.

## Part C - Make the repository look professional (10 min)
- **About box** (gear icon, top right of repo): write a one-line description and add **topics**: `data-analysis`, `sql`, `python`, `power-bi`, `excel`, `data-analytics`, `churn-prediction`, `portfolio`.
- **Pin** the repository on your profile (Profile > Customize your pins).
- Make sure the README renders images (the `images/` folder uploaded) and that the first screen of each README shows the headline result.
- Create a **profile README**: new public repo named exactly like your username with a README that lists your skills and links to this portfolio.
- Copy the repo URL into your **resume header, LinkedIn Featured section and email signature**.
- If you publish a Power BI report with "Publish to web" (safe here because data is synthetic), put the link at the top of that project's README.

## Part D - Final checklist
- [ ] Repo is **Public** and opens in a private/incognito browser window
- [ ] No personal data or credentials anywhere (`git grep -i password`)
- [ ] README has your name, no `<placeholders>` left
- [ ] Screenshots visible; `.pbix` files added if built (each is a few MB, fine for GitHub)
- [ ] Each project README states the data is synthetic
- [ ] Links in resume work

## Common problems
| Problem | Fix |
|---|---|
| `git push` rejected, "fetch first" | You created the GitHub repo with a README. Run `git pull origin main --rebase` then `git push` |
| `remote origin already exists` | `git remote set-url origin <URL>` |
| Images do not show in README | Check the file names/case match exactly (`images/02_discount_vs_margin.png`) and the files were committed |
| `.db` files missing | Intentional - they are in `.gitignore` and are rebuilt by `python/run_pipeline.py` |
