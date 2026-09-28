import shutil


def apply(workdir):
    shutil.rmtree(workdir / "tmp")
    shutil.rmtree(workdir / ".cache")
