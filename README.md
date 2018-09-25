# RUN Twister2 Using Docker

## Building image

```
	make build
```

## Run Docker Interactively

```bash
	make it
```

## Within the container

```bash
	source /app/bashes/profile.bash 
	source /app/bashes/ompi.bash 
	make build #build twister2
	bazel build --config=ubuntu //scripts/package:tarpkgs_no_mpi
	su - twister2
	cd /app/sandbox/github/local/twister2
	source /app/bashes/ompi.bash 
	source /app/bashes/profile.bash 
	./twister2-dist/bin/twister2 submit nodesmpi jar twister2-dist/examples/libexamples-java.jar edu.iu.dsc.tws.examples.internal.task.batch.GatherBatchTask
```



