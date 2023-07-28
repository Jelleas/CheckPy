import tinydb
from tinydb.table import Table
import time
import contextlib
import checkpy
import pathlib
from typing import Generator, Iterable, Tuple

_DBPATH = checkpy.CHECKPYPATH / "database" / "db.json"

@contextlib.contextmanager
def database() -> Generator[tinydb.TinyDB, None, None]:
    _DBPATH.touch()
    try:
        db = tinydb.TinyDB(str(_DBPATH))
        yield db
    finally:
        db.close()

@contextlib.contextmanager
def githubTable()-> Generator[Table, None, None]:
    with database() as db:
        yield db.table("github")

@contextlib.contextmanager
def localTable() -> Generator[Table, None, None]:
    with database() as db:
        yield db.table("local")

def clean():
    with database() as db:
        db.drop_tables()

def forEachTestsPath() -> Iterable[pathlib.Path]:
    for path in forEachGithubPath():
        yield path

    for path in forEachLocalPath():
        yield path

def forEachUserAndRepo() -> Iterable[Tuple[str, str]]:
    with githubTable() as table:
        return [(entry["user"], entry["repo"]) for entry in table.all()]

def forEachGithubPath() -> Iterable[pathlib.Path]:
    with githubTable() as table:
        for entry in table.all():
            yield pathlib.Path(entry["path"])

def forEachLocalPath() -> Iterable[pathlib.Path]:
    with localTable() as table:
        for entry in table.all():
            yield pathlib.Path(entry["path"])

def isKnownGithub(username: str, repoName: str) -> bool:
    query = tinydb.Query()
    with githubTable() as table:
        return table.contains((query.user == username) & (query.repo == repoName))

def addToGithubTable(username: str, repoName: str, releaseId: str, releaseTag: str):
    if not isKnownGithub(username, repoName):
        path = str(checkpy.CHECKPYPATH / "tests" / repoName)

        with githubTable() as table:
            table.insert({
                "user" 			: username,
                "repo" 			: repoName,
                "path"          : path,
                "release" 		: releaseId,
                "tag" 			: releaseTag,
                "timestamp" 	: time.time()
            })

def addToLocalTable(localPath: pathlib.Path):
    query = tinydb.Query()
    with localTable() as table:
        if not table.search(query.path == str(localPath)):
            table.insert({
                "path" : str(localPath)
            })

def updateGithubTable(username: str, repoName: str, releaseId: str, releaseTag: str):
    query = tinydb.Query()
    path = str(checkpy.CHECKPYPATH / "tests" / repoName)
    with githubTable() as table:
        table.update({
            "user" 			: username,
            "repo" 			: repoName,
            "path"          : path,
            "release" 		: releaseId,
            "tag" 			: releaseTag,
            "timestamp" 	: time.time()
        }, query.user == username and query.repo == repoName)

def timestampGithub(username: str, repoName: str) -> float:
    query = tinydb.Query()
    with githubTable() as table:
        return table.search(query.user == username and query.repo == repoName)[0]["timestamp"]

def setTimestampGithub(username: str, repoName: str):
    query = tinydb.Query()
    with githubTable() as table:
        table.update(
            {"timestamp" : time.time()},
            query.user == username and query.repo == repoName
        )

def githubPath(username: str, repoName: str) -> pathlib.Path:
    query = tinydb.Query()
    with githubTable() as table:
        return pathlib.Path(table.search(query.user == username and query.repo == repoName)[0]["path"])

def releaseId(username: str, repoName: str) -> str:
    query = tinydb.Query()
    with githubTable() as table:
        return table.search(query.user == username and query.repo == repoName)[0]["release"]

def releaseTag(username: str, repoName: str) -> str:
    query = tinydb.Query()
    with githubTable() as table:
        return table.search(query.user == username and query.repo == repoName)[0]["tag"]
