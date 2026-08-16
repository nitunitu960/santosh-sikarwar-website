# How to Publish santoshsikarwar.in

## Step 1 — Create the GitHub repository
1. Go to https://github.com/new
2. Repository name: `santosh-sikarwar-website`
3. Choose **Public**
4. Do NOT add README, .gitignore, or license (already present locally)
5. Click **Create repository**

## Step 2 — Push your code
Run these in the project folder (replace YOUR-USERNAME):

```powershell
git remote add origin https://github.com/YOUR-USERNAME/santosh-sikarwar-website.git
git push -u origin main
```

## Step 3 — Turn on GitHub Pages
1. In the repo, go to **Settings > Pages**
2. Under "Build and deployment" > Source, choose **Deploy from a branch**
3. Branch: **main**, folder: **/ (root)**, then **Save**
4. Under "Custom domain", enter: `santoshsikarwar.in` and Save
5. Check **Enforce HTTPS** (may take a few minutes to become available)

## Step 4 — Point GoDaddy DNS to GitHub
In GoDaddy: My Products > santoshsikarwar.in > DNS > Manage DNS.

Add these records (delete existing conflicting A/CNAME records first):

A records (host = @) pointing to GitHub Pages IPs:
```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

CNAME record for www:
```
Type: CNAME
Name: www
Value: YOUR-USERNAME.github.io
```

DNS can take 10 minutes to 48 hours to propagate. Once done,
https://santoshsikarwar.in will show your site.

## Updating the site later
Edit files, then:
```powershell
git add .
git commit -m "Update content"
git push
```
