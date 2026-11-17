#!/bin/sh
# Fill in the domain and repo, and copy AGENTS.md to setup.md. Output: site/dist (what Vercel serves).
#   DOMAIN=name.newyorkai.org REPO=derek-larson14/farfield sh site/build.sh
set -eu
cd "$(dirname "$0")"
: "${DOMAIN:=farfield.newyorkai.org}" "${REPO:=derek-larson14/farfield}"
rm -rf dist && mkdir -p dist/logos
sed -e "s|__DOMAIN__|$DOMAIN|g" -e "s|__REPO__|$REPO|g" index.html > dist/index.html
cp install.sh dist/install.sh   # served byte for byte as it is in the repo, so people can check it
# install.md is what the setup prompt points at; setup.md stays for links that already went out.
sed -e "s|farfield.newyorkai.org|$DOMAIN|g" -e "s|github.com/derek-larson14/farfield|github.com/$REPO|g" -e "s|](CONTRIBUTING.md)|](https://github.com/$REPO/blob/main/CONTRIBUTING.md)|g" ../AGENTS.md > dist/install.md
cp dist/install.md dist/setup.md
python3 package.py .. dist "https://$DOMAIN"
python3 ../tools/sources_md.py --check --html dist/sources.html   # /sources, from the same catalog
cp logos/* dist/logos/
cp social-card.jpg dist/social-card.jpg
cp favicon.svg apple-touch-icon.png dist/
echo "built dist/ for https://$DOMAIN ($REPO)"
