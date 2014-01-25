import os,subprocess,sys

####### Installing dependencies

here = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))

with open(os.path.join(here,"dependencies.sh"),"wt") as erase: pass

def run(*commands):
    with open(os.path.join(here,"dependencies.sh"),"at") as out:
        for command in commands:
            if hasattr(command,"__call__"):
                commands = command
                for command in commands():
                    out.write(command+"\n")
            else:
                out.write(command+"\n")
    raise SystemExit("Please examine, then run dependencies.sh as root (in "+here+")")

def Import(module,*otherwise):
    try: return __import__(module)
    except ImportError: pass
    else: return
    run(*otherwise)
    return __import__(module)

def git(where):
    def go():
        name = where.rsplit('/',1)[-1]
        os.chdir(here)
        if os.path.exists(name):
            os.chdir(name)
            subprocess.check_call(["git","pull"])
        else:
            subprocess.call(["git","clone",where,name])
        os.chdir(name)
        if os.path.exists('autogen.sh'):
            subprocess.check_call(["sh","autogen.sh",'--help'])
        elif os.path.exists('configure.ac'):
            subprocess.check_call(['autoreconf'])
        if os.path.exists('configure'):
            subprocess.check_call(["sh","configure"])
        if os.path.exists('Makefile'):
            subprocess.check_call(["make","-j8"])
            return ("cd "+os.path.abspath("."),
                  "make install")
        else:
            subprocess.check_call(['python','setup.py','build'])
            return ("cd "+os.path.abspath('.'),
                    "python setup.py install")
    return go
