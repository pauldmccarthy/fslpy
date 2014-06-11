((python-mode . ((project-venv-name . "pyfsl-env")))

 ; make our bodgy wx widgets installation work nicely with emacs
 (nil . ((eval . (setenv "DYLD_LIBRARY_PATH" "/Users/paulmc/optlib/wx3.0.0/usr/local/lib/"))))
 (nil . ((eval . (setenv "PYTHONPATH" "/Users/paulmc/optlib/wx3.0.0/lib/python2.7/site-packages:/Users/paulmc/optlib/wx3.0.0/lib/python2.7/site-packages/wx-3.0-osx_carbon"))))
 (nil . ((eval . (setenv "PYTHONHOME" "/Users/paulmc/.virtualenvs/pyfsl-env")))))
