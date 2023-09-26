rm -rf ./dist
rm requirements.txt

poetry build
poetry export --format requirements.txt --output requirements.txt --without-hashes
docker build .