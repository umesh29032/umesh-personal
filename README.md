#######################################
# STEP 1: Setup SSH config for 2 accounts
#######################################

# Open SSH config file (create if not exists)
nano ~/.ssh/config

# Paste below content in the file:
# (This part is manually added, not via script)
#
# Host github.com-personal
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/id_rsa_personal
#
# Host github.com-company
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/id_ed25519
#
# Save and exit: Ctrl + O, Enter, Ctrl + X

#######################################
# STEP 2: Add SSH keys to GitHub accounts
#######################################

# Show personal public key (copy this to personal GitHub -> SSH keys)
cat ~/.ssh/id_rsa_personal.pub

# Show company public key (copy this to company GitHub -> SSH keys)
cat ~/.ssh/id_ed25519.pub

#######################################
# STEP 3: Personal repo setup (DSA)
#######################################

# Go to personal project folder
cd ~/umesh-personal

# Initialize git repo
git init

# Set personal Git identity for this repo only
git config user.name "Umesh Personal"
git config user.email "umesh.personal@example.com"

# Add sample file if DSA folder is empty
mkdir -p DSA
echo "// sample DSA code" > DSA/sample.cpp

# Stage and commit changes
git add .
git commit -m "Initial commit - add DSA folder"

# Rename branch to main
git branch -M main

# Add personal remote via SSH (using SSH host alias)
git remote add origin git@github.com-personal:umesh29032/umesh-personal.git

# Push to personal GitHub repo
git push -u origin main

#######################################
# STEP 4: Company repo setup (example)
#######################################

# Go to company project folder
cd ~/company-project

# Initialize git repo
git init

# Set company Git identity for this repo only
git config user.name "Umesh Company"
git config user.email "umesh@company.com"

# Add files (assuming you already have some)
git add .
git commit -m "Initial commit - company project"

# Rename branch to main
git branch -M main

# Add company remote via SSH (using SSH host alias)
git remote add origin git@github.com-company:company-org/company-repo.git

# Push to company GitHub repo
git push -u origin main

