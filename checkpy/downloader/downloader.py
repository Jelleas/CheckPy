import requests
import zipfile as zf
import os
import io
import pathlib
import shutil
import time

from typing import Dict, Optional, Set, Union

from checkpy import database
from checkpy import printer
from checkpy.entities import exception

user: Optional[str] = None
personal_access_token: Optional[str] = None

def set_gh_auth(username: str, pat: str):
    global user, personal_access_token
    user = username
    personal_access_token = pat

def download(githubLink: str):
    if githubLink.endswith("/"):
        githubLink = githubLink[:-1]

    if "/" not in githubLink:
        printer.displayError(f"{githubLink} is not a valid download location")
        return

    username = githubLink.split("/")[-2].lower()
    repoName = githubLink.split("/")[-1].lower()

    try:
        _syncRelease(username, repoName)
        _download(username, repoName)
    except exception.DownloadError as e:
        printer.displayError(str(e))

def register(localLink: Union[str, pathlib.Path]):
    path = pathlib.Path(localLink)

    if not path.exists():
        printer.displayError("{} does not exist")
        return

    database.addToLocalTable(path)

def update():
    for username, repoName in database.forEachUserAndRepo():
        try:
            _syncRelease(username, repoName)
            _download(username, repoName)
        except exception.DownloadError as e:
            printer.displayError(str(e))

def list():
    for username, repoName in database.forEachUserAndRepo():
        printer.displayCustom(f"Github: {repoName} from {username}")
    for path in database.forEachLocalPath():
        printer.displayCustom(f"Local:  {path}")

def clean():
    for path in database.forEachGithubPath():
        shutil.rmtree(str(path), ignore_errors=True)
    database.clean()
    printer.displayCustom("Removed all tests")
    return

def updateSilently():
    for username, repoName in database.forEachUserAndRepo():
        # only attempt update if 300 sec have passed
        if time.time() - database.timestampGithub(username, repoName) < 300:
            continue

        database.setTimestampGithub(username, repoName)
        try:
            if _newReleaseAvailable(username, repoName):
                _download(username, repoName)
        except exception.DownloadError as e:
            pass

def _newReleaseAvailable(githubUserName: str, githubRepoName: str) -> bool:
    # unknown/new download
    if not database.isKnownGithub(githubUserName, githubRepoName):
        return True
    releaseJson = _getReleaseJson(githubUserName, githubRepoName)

    # new release id found
    if releaseJson["id"] != database.releaseId(githubUserName, githubRepoName):
        database.updateGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
        return True

    # no new release found
    return False

def _syncRelease(githubUserName: str, githubRepoName: str):
    releaseJson = _getReleaseJson(githubUserName, githubRepoName)

    if database.isKnownGithub(githubUserName, githubRepoName):
        database.updateGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])
    else:
        database.addToGithubTable(githubUserName, githubRepoName, releaseJson["id"], releaseJson["tag_name"])


def _getReleaseJson(githubUserName: str, githubRepoName: str) -> Dict:
    """
    This performs one api call, beware of rate limit!!!
    Returns a dictionary representing the json returned by github
    In case of an error, raises an exception.DownloadError
    """
    apiReleaseLink = f"https://api.github.com/repos/{githubUserName}/{githubRepoName}/releases/latest"

    global user
    global personal_access_token
    try:
        if user and personal_access_token:
            r = requests.get(apiReleaseLink, auth=(user, personal_access_token))
        else:
            r = requests.get(apiReleaseLink)
    except requests.exceptions.ConnectionError as e:
        raise exception.DownloadError(message="Oh no! It seems like there is no internet connection available?!")

    # exceeded rate limit,
    if r.status_code == 403:
        raise exception.DownloadError(message=f"Tried finding new releases from {githubUserName}/{githubRepoName} but exceeded the rate limit, try again within an hour!")

    # no releases found or page not found
    if r.status_code == 404:
        raise exception.DownloadError(message=f"Failed to check for new tests from {githubUserName}/{githubRepoName} because: no releases found (404)")

    # random error
    if not r.ok:
        raise exception.DownloadError(message=f"Failed to sync releases from {githubUserName}/{githubRepoName} because: {r.reason}")

    return r.json()

# download tests for githubUserName and githubRepoName from what is known in downloadlocations.json
# use _syncRelease() to force an update in downloadLocations.json
def _download(githubUserName: str, githubRepoName: str):
    githubLink = f"https://github.com/{githubUserName}/{githubRepoName}"
    zipLink = githubLink + f"/archive/{database.releaseTag(githubUserName, githubRepoName)}.zip"

    try:
        r = requests.get(zipLink)
    except requests.exceptions.ConnectionError as e:
        raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

    if not r.ok:
        raise exception.DownloadError(message = f"Failed to download {githubLink} because: {r.reason}")

    f = io.BytesIO(r.content)

    with zf.ZipFile(f) as z:
        destPath = database.githubPath(githubUserName, githubRepoName)

        existingTests: Set[pathlib.Path] = set()
        for path, subdirs, files in os.walk(destPath):
            for fil in files:
                existingTests.add((pathlib.Path(path) / fil).relative_to(destPath))

        newTests: Set[pathlib.Path] = set()
        for name in z.namelist():
            if name.endswith(".py"):
                newTests.add(pathlib.Path(pathlib.Path(name).as_posix().split("tests/")[1]))

        for filePath in [fp for fp in existingTests - newTests if fp]:
            printer.displayRemoved(str(filePath))

        for filePath in [fp for fp in newTests - existingTests if fp.suffix == ".py"]:
            printer.displayAdded(str(filePath))

        for filePath in existingTests - newTests:
            (destPath / filePath).unlink() # remove file

        _extractTests(z, destPath)

    printer.displayCustom(f"Finished downloading: {githubLink}")

def _extractTests(zipfile: zf.ZipFile, destPath: pathlib.Path):
    if not destPath.exists():
        os.makedirs(str(destPath))

    for path in [pathlib.Path(name) for name in zipfile.namelist()]:
        _extractTest(zipfile, path, destPath)

def _extractTest(zipfile: zf.ZipFile, path: pathlib.Path, destPath: pathlib.Path):
    if not "tests/" in path.as_posix():
        return

    subfolderPath = pathlib.Path(path.as_posix().split("tests/")[1])
    filePath = destPath / subfolderPath

    if path.suffix == ".py":
        _extractFile(zipfile, path, filePath)
    elif subfolderPath and not filePath.exists():
        os.makedirs(str(filePath))

def _extractFile(zipfile: zf.ZipFile, path: pathlib.Path, filePath: pathlib.Path):
    zipPathString = path.as_posix()
    if filePath.is_file():
        with zipfile.open(zipPathString) as new, open(str(filePath), "r") as existing:
            # read file, decode, strip trailing whitespace, remove carrier return
            newText = ''.join(new.read().decode('utf-8').strip().splitlines())
            existingText = ''.join(existing.read().strip().splitlines())
            if newText != existingText:
                printer.displayUpdate(str(path))

    with zipfile.open(zipPathString) as source, open(str(filePath), "wb+") as target:
        shutil.copyfileobj(source, target)
