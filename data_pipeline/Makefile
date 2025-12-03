.PHONY: build run dev logs clean env

IMAGE_NAME := nada-data-pipeline
CONTAINER_NAME := nada-data-pipeline-container

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run --name $(CONTAINER_NAME) \
		--env-file .env \
		-v $(PWD)/logs:/app/logs \
		-v $(PWD)/data:/app/data \
		$(IMAGE_NAME)

dev:
	python3 scripts/collect_youtube.py

logs:
	tail -f logs/youtube_pipeline.log

clean:
	docker stop $(CONTAINER_NAME) 2>/dev/null || true
	docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker rmi $(IMAGE_NAME) 2>/dev/null || true
