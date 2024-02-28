IMAGE?=registry.kinnack.com/americanroutes
TAG?=latest
BIN?=

init:
	pip install pipenv
	pipenv install

target/rss.xml: src/crawler/feed.py src/crawler/parser.py
	${BIN}python src/crawler/feed.py

serve: target/rss.xml
	cd target && ${BIN}python -m http.server

docker-build: target/rss.xml
	docker build -t ${IMAGE}:${TAG} .

docker-run:
	docker run --rm -p 8080:80 ${IMAGE}:${TAG}

docker-push: docker-build
	docker push ${IMAGE}:${TAG}

restart-app:
	kubectl delete pods -l app=americanroutes-feed

get-feed:
	curl -v http://kinnack.ddns.net/rss.xml

deploy: docker-push restart-app

.PHONY: serve deploy docker-push docker-build restart-app
