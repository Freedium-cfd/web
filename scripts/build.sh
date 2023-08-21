#!/bin/bash
pip install nuitka==1.7
sudo apt install patchelf ccache -y
sudo /usr/sbin/update-ccache-symlinks
export PATH="/usr/lib/ccache:$PATH"

python3 -m nuitka --standalone --nofollow-import-to=pytest --python-flag=nosite,-O,isolated --plugin-enable=anti-bloat,implicit-imports,data-files,pylint-warnings --warn-implicit-exceptions --warn-unusual-code --prefer-source-code --static-libpython=yes --include-package=uvicorn.workers --verbose --show-modules --show-memory --show-progress --show-scons server  # --low-memory

mkdir server.dist/server
cp -r server/templates server.dist/server/

mkdir -p server.dist/tld/res/
cp -r ~/venv/lib/python3.9/site-packages/tld/res/ server.dist/tld/res/
