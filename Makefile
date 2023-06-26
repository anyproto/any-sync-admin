.DEFAULT_GOAL := start
.PHONY: build

start:
	docker-compose up --force-recreate --build --remove-orphans --detach
stop:
	docker-compose stop
clean:
	docker system prune --all --force
pull:
	docker-compose pull
cleanTmp:
	rm -rf tmp/
restart: stop start
update: stop pull start
upgrade: stop clean start

# for building rpm and deb packages via fpm
build:
	./build.sh
buildClean:
	rm -rf build/
