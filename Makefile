build:
	docker build -t twister2/init:v1 .

it:
	docker run -i -t twister2/init:v1 /bin/bash

mkdir:
	docker run -it -v "$(pwd)":/src twister2/init bash
