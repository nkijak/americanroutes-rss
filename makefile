IMAGE?=registry.kinnack.com/americanroutes
TAG?=latest
BIN?=

init:
	pip install pipenv
	pipenv install

target/rss.xml: src/crawler/feed.py src/crawler/parser.py
	mkdir -p target
	${BIN}python src/crawler/feed.py

clean:
	rm -q target/rss.xml

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

docker-restart:
	sudo service docker restart

docker-config:
	sudo mv ci/daemon.json /etc/docker/daemon.json

ci-config: docker-config docker-restart


.PHONY: serve deploy docker-push docker-build restart-app
