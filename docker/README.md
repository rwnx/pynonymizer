These files can build pynonymizer + client image for each database type. 

run this script from the root of the repo:

```sh
# pynonymizer.__version__ = 2.2.1
./docker/get_build.py                                                                                                        
# docker build -f docker/pynonymizer.Dockerfile . -t rwnxt/pynonymizer:latest -t rwnxt/pynonymizer:2 -t rwnxt/pynonymizer:2.2 -t rwnxt/pynonymizer:2.2.1
# docker push rwnxt/pynonymizer:latest
# docker push rwnxt/pynonymizer:2
# docker push rwnxt/pynonymizer:2.2
# docker push rwnxt/pynonymizer:2.2.1

# pre, post, and dev releases will not be tagged with latest / etc
# pynonymizer.__version__ = 2.2.1-rc.1
./docker/get_build.py                                                                                                        
# docker build -f docker/pynonymizer.Dockerfile . -t rwnxt/pynonymizer:2.2.1-rc.1
# docker push rwnxt/pynonymizer:2.2.1-rc.1
```