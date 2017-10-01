test:
	python -m unittest discover -p 'test_*.py' -v

run:
	time python examples.py

deploy_viv:
	tar -czf ~/slackline.tar.gz __init__.py results config core logs tests data examples.py Makefile cythons

clenow:
	python gui_controller.py

install:
	cython cythons/functions.pyx
	cd cythons && gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -I/usr/include/python2.7 -o functions.so functions.c

clean:
	rm cythons/functions.c cythons/functions.so

post:
	cd core && python postprocessor.py

pencil_post:
	cd core && python pencil_post.py

zip:
	tar -czf slackline.tar.gz *
