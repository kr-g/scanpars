"""
(c) 2022 K. Goger - https://github.com/kr-g/

license:
    free for non-commercial use
"""

import platform
import sys
import os
import importlib
import re
import json
import subprocess

import setuptools

#


def check_changelog():
    _regex = re.compile(r".*version.*\-.*\?\?\?", re.MULTILINE | re.IGNORECASE)
    with open("CHANGELOG.md") as f:
        tx = f.read()
        if re.search(_regex, tx):
            print("!!!\n" * 5, file=sys.stderr)
            print("check changelog", file=sys.stderr)
            print()
            print("!!!\n" * 5, file=sys.stderr)
            return True


def get_changelog_headers(showmax=3):
    _regex = re.compile(
        r"^.*version[ ]*([\w.]*)[ -]*(.*)$", re.MULTILINE | re.IGNORECASE
    )
    with open("CHANGELOG.md") as f:
        tx = f.read()
        for m in re.finditer(_regex, tx):
            yield m.group(1), m.group(2)
            showmax -= 1
            if showmax <= 0:
                return


#


def find_versions(fnam, version="VERSION"):
    with open(fnam) as f:
        cont = f.read()
    regex = f"^(?=[^#]).*({version})[ ]*=[ ]*((?P<qou>[\"'])(.*)(?P=qou))$"
    match = re.finditer(regex, cont, re.MULTILINE | re.IGNORECASE)
    if match is None:
        raise Exception(f"version with spec={version} not found")
    for m in match:
        fuls = m.group(2)
        qou = m.group(3)
        version = m.group(4)
        yield version, fuls, qou


def find_version(fnam, version="VERSION"):
    return next(find_versions(fnam, version))[0]


def find_projectname():
    cwd = os.getcwd()
    name = os.path.basename(cwd)
    return name


def load_requirements():
    with open("requirements.txt") as f:
        lines = f.readlines()
        lines = map(lambda x: x.strip(), lines)
        lines = filter(lambda x: len(x) > 0, lines)
        lines = filter(lambda x: x[0] != "#", lines)
        return list(lines)


def do_mod_import(projectname=None, fnam="__main__"):
    if projectname is None:
        projectname = find_projectname()
    mod = importlib.import_module(f"{projectname}.{fnam}")
    return mod


def do_const_import(projectname=None):
    mod = do_mod_import(projectname, "const")
    return mod


def do_main_import(projectname=None):
    mod = do_mod_import(projectname, "__main__")
    return mod


def get_scripts(projectname):
    console_scripts = []
    gui_scripts = []

    try:
        mod = do_main_import(projectname)
        if "main_func" in dir(mod):
            console_scripts = [
                f"{projectname} = {projectname}.__main__:main_func",
            ]
        if "gui_func" in dir(mod):
            gui_scripts = [
                f"{projectname}-ui = {projectname}.__main__:gui_func",
            ]
    except:
        print("no scripts found", file=sys.stderr)

    entry_points = {
        "console_scripts": console_scripts,
        "gui_scripts": gui_scripts,
    }

    return entry_points


def find_packages(exclude=None):
    if exclude is None:
        exclude = [
            "tests",
            "tests.*",
            "docs",
        ]
    return setuptools.find_packages(exclude=exclude)


#


def load_base_settings():
    with open("setup.json") as f:
        return json.load(f)


def project_settings(projectname=None, fnam="const.py", version="VERSION"):

    pyver = platform.python_version_tuple()[:2]
    pyversion = ".".join(pyver)
    python_requires = f">={pyversion}"

    if projectname is None:
        projectname = find_projectname()

    file = os.path.join(projectname, fnam)
    version = find_version(file, version)

    install_requires = load_requirements()

    entry_points = get_scripts(projectname)

    packages = find_packages()

    rc = {
        "projectname": projectname,
        "pyver": pyver,
        "pyversion": pyversion,
        "file": file,
        "setuptoolsversion": setuptools.__version__,
        "version": version,
        "setup": {
            "name": projectname,
            "version": version,
            "python_requires": python_requires,
            "install_requires": install_requires,
            "entry_points": entry_points,
            "packages": packages,
        },
    }

    return rc


#
# https://setuptools.pypa.io/en/latest/userguide/declarative_config.html
#


def elements_iter(adict, keypath=[]):
    """deep elements iterator"""
    _iter = lambda x: x.items()
    if type(adict) == list:
        _iter = enumerate

    for k, v in _iter(adict):
        keypath = [*keypath, k]

        if type(v) in [list, dict]:
            yield from elements_iter(v, keypath)
            continue

        def setr(nv):
            adict[k] = nv

        yield keypath, v, setr


def replace_settings(project_settings, base_settings):
    """replace base setting generics from project settings"""
    base_settings = dict(base_settings)
    # not the most effective way ...
    for k, v in project_settings.items():
        for kk, vv, setr in elements_iter(base_settings):
            if type(vv) != str:
                continue
            r = "{" + k + "}"
            if vv.find(r) >= 0:
                setr(vv.replace(r, v))

    return base_settings


def build_setup_settings(proj_settings, base_settings):
    base_settings = replace_settings(proj_settings, base_settings)
    settings = dict(proj_settings["setup"])
    settings.update(base_settings)
    return settings


#


class AutoDoc(object):
    """create markdown of cmd-line"""

    def __init__(self, cmd_tool=None, extreadme="_"):
        self.rst()

        if cmd_tool is None:
            cmd_tool = find_projectname()

        self.cmd_tool = cmd_tool
        self.extreadme = extreadme

    def doc(self):
        return self._doc

    def rst(self):
        self._doc = ""

    def pr(self, *args):
        d = ""
        for s in args:
            self._doc += d
            self._doc += s
            d = "\t"
        self._doc += "\n"

    def create(self, create_index=False):

        self.rst()

        self.pr("")
        self.pr(f"# all `{self.cmd_tool}` cmd-line options")
        self.pr("")

        args = ["python3", "-m", self.cmd_tool, "-h"]
        rc = subprocess.run(args, capture_output=True)
        if rc.returncode:
            raise Exception(rc)

        s = rc.stdout.decode()

        _regex = r"{(.*)}"
        matches = re.finditer(_regex, s, re.MULTILINE)

        scancmd = [""]

        for m in matches:
            scancmd.extend(m.group(1).split(","))

        print("found", scancmd)

        if create_index:
            self.pr("index:")

            fnam = self.build_fnam()

            for idx, cmd in enumerate(scancmd):
                if idx > 0:
                    cmd_ = "-".join([self.cmd_tool, cmd]).strip()
                else:
                    cmd_ = self.cmd_tool
                # this works only with github
                self.pr(f"  - [{cmd_}](./{fnam}#{cmd_})")

            self.pr()

        for idx, cmd in enumerate(scancmd):

            args = ["python3", "-m", self.cmd_tool, cmd, "-h"]
            args = list(filter(lambda x: len(x), args))
            rc = subprocess.run(args, capture_output=True)

            if rc.returncode:
                raise Exception(rc)

            cmd = " ".join(args[2:-1])
            cmd_ = cmd.replace(" ", "_").replace("-", "")

            self.pr("")
            self.pr(f"## {cmd}")
            self.pr("")
            self.pr(f"run `{cmd} -h` for help")
            self.pr("")
            lines = rc.stdout.decode().splitlines()

            for line in lines:
                self.pr(" " * 4 + line)

            self.pr("")

        return self

    def build_fnam(self):
        return f"README{self.extreadme}CMDLINE.md"

    def write(self):
        with open(self.build_fnam(), "w") as f:
            f.write(self._doc)

    def create_autodoc(self):
        self.create()
        self.write()


#

"""
this uses an already "maintained" requirements.txt files
and bumps the version numbers from currently installed
packages.
"""


class Package(object):
    def __init__(self, spec):
        if spec.startswith("-e"):
            self.editable = True
            self.package = spec[spec.find("#egg=") + 5 :]
            self.version = None
        else:
            self.editable = False
            self.package = spec[: spec.find("==")]
            self.version = spec[spec.find("==") + 2 :]

    def __repr__(self):
        return (
            self.__class__.__name__
            + f"( {self.package}, {self.version}, {self.editable} )"
        )


def load_installed_versions():
    packs = {}

    proc = subprocess.Popen(
        [
            "pip",
            "freeze",
        ],
        stdout=subprocess.PIPE,
    )

    if proc is None:
        raise Exception("could not start pip")

    while True:
        line = proc.stdout.readline()
        if len(line) == 0:
            break
        line = line.decode().strip()
        print(line)
        p = Package(line)
        packs[p.package] = p

    return packs


def load_requirements_versions_cleared():

    requirements = load_requirements()
    print("loaded", requirements)

    def clr(x):
        p1 = x.find("==")
        p2 = x.find(">=")
        p3 = x.find(">")
        p = max(p1, p2)
        p = max(p, p3)
        if p < 0:
            return x
        return x[:p]

    req_cleared = list(map(lambda x: clr(x), requirements))

    print("cleared", req_cleared)

    return req_cleared


def bump_versions(req_cleared, packs, strong=False):

    if strong:
        cmp = "=="
    else:
        cmp = ">="

    new_req = []
    for p in req_cleared:
        pack = packs[p]
        if pack.version is None:
            new_req.append(f"{pack.package}")
            print(new_req[-1:], "from editable", file=sys.stderr)
        else:
            new_req.append(f"{pack.package}{cmp}{pack.version}")

    print("bumbed", new_req)

    new_requirements = "\n".join(new_req)

    return new_requirements


def save_requirements(new_requirements):
    with open("requirements.txt", "w") as f:
        f.write(new_requirements)


def bump_requirements(strong=False):
    packs = load_installed_versions()
    req_cleared = load_requirements_versions_cleared()
    req_vers = bump_versions(req_cleared, packs, strong=strong)
    save_requirements(req_vers)


#

## todo remove ???
def upgrade_requirements_packages():

    raise Exception("deprecated")

    proc = subprocess.Popen(
        args=[
            "python3",
            "-m",
            "pip",
            "install",
            "-r",
            "requirements.txt",
            "-U",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    while True:
        line = proc.stdout.readline()
        if len(line) == 0:
            break
        print(line.decode().strip())
    proc.wait()
    if proc.returncode == 0:
        return
    return proc.returncode


# use this


def create_autodoc():
    AutoDoc().create_autodoc()


def setup_settings(base_settings=None, proj_settings=None, dump=True):

    if base_settings is None:
        base_settings = load_base_settings()

    if proj_settings is None:
        proj_settings = project_settings()

    settings = build_setup_settings(proj_settings, base_settings)

    if dump:
        print("settings", json.dumps(settings, indent=4))

    return settings


def check_setup(settings, prelude=True):
    version = settings["version"]
    rc = check_changelog()
    first = True
    if not prelude:
        print("last versions found")
        for v, d in get_changelog_headers():
            if first:
                first = False
                if version != v:
                    print("***last version not matching", version, v)
                    rc = True
            print(v, d)
    return rc
