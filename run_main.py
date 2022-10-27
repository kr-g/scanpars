import os
from setuputil import do_main_import

cwd = os.path.dirname(__file__)
cwd = "." if len(cwd) == 0 else cwd
os.chdir(cwd)

mod = do_main_import()
mod.main_func()
