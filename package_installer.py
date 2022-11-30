def installed(packages):
    _installed = False
    def install_packages(*packages):
        print('working')
        global _installed
        _installed = False
        if not _installed:
            import os
            import sys
            import time
            _started = time.time()
            os.system("mkdir -p /tmp/packages")
            _packages = " ".join(f"'{p}'" for p in packages)
            print("INSTALLED:")
            os.system(
                f"{sys.executable} -m pip freeze --no-cache-dir")
            print("INSTALLING:")
            os.system(
                f"{sys.executable} -m pip install "
                f"--no-cache-dir --target /tmp/packages "
                f"--only-binary :all: --no-color "
                f"--no-warn-script-location {_packages}")
            sys.path.insert(0, "/tmp/packages")
            _installed = True
            _ended = time.time()
            print(f"package installation took: {_ended - _started:.2f} sec")
        
    install_packages(packages)
