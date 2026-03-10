#!/bin/bash

# 1. Colors for clarity
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}--- Syncing AI Contractors (James & Jules) ---${NC}"

# 2. Ensure we are on main
git checkout main

# 3. Pull Backend from James (Ultra)
echo -e "${GREEN}Merging James (Ultra) - Backend...${NC}"
git merge james_dev --no-edit

# 4. Pull Frontend from Jules (Pro)
echo -e "${GREEN}Merging Jules (Pro) - Frontend...${NC}"
git merge jules_dev --no-edit

# 5. Summary
echo -e "${BLUE}--- Stage 1 Update Complete ---${NC}"
git status
