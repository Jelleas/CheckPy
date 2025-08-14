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
        _syncCommit(username, repoName)
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
            _syncCommit(username, repoName)
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
            if _newCommitAvailable(username, repoName):
                _download(username, repoName)
        except exception.DownloadError:
            pass

def _newCommitAvailable(githubUserName: str, githubRepoName: str) -> bool:
    # unknown/new download
    if not database.isKnownGithub(githubUserName, githubRepoName):
        return True
    commitJson = _getLatestCommitJson(githubUserName, githubRepoName)

    # new commit found
    if commitJson["sha"] != database.commitSha(githubUserName, githubRepoName):
        database.updateGithubTable(
            githubUserName,
            githubRepoName,
            commitJson["commit"]["message"],
            commitJson["sha"],
        )
        return True

    # no new commit found
    return False

def _syncCommit(githubUserName: str, githubRepoName: str):
    commitJson = _getLatestCommitJson(githubUserName, githubRepoName)

    if database.isKnownGithub(githubUserName, githubRepoName):
        database.updateGithubTable(
            githubUserName,
            githubRepoName,
            commitJson["commit"]["message"],
            commitJson["sha"],
        )
    else:
        database.addToGithubTable(
            githubUserName,
            githubRepoName,
            commitJson["commit"]["message"],
            commitJson["sha"],
        )

def _get_with_auth(url: str) -> requests.Response:
    """
    Get a url with authentication if available.
    Returns a requests.Response object.
    """
    global user
    global personal_access_token
    if user and personal_access_token:
        return requests.get(url, auth=(user, personal_access_token))
    else:
        return requests.get(url)

def _getLatestCommitJson(githubUserName: str, githubRepoName: str) -> Dict:
    """
    Get the latest commit from the default branch of the given repository.
    This performs one api call, beware of rate limit!!!
    Returns a dictionary representing the json returned by github
    In case of an error, raises an exception.DownloadError
    """
    apiCommitLink = f"https://api.github.com/repos/{githubUserName}/{githubRepoName}/commits"

    try:
        r = _get_with_auth(apiCommitLink)
    except requests.exceptions.ConnectionError as e:
        raise exception.DownloadError(message="Oh no! It seems like there is no internet connection available?!")

    # exceeded rate limit,
    if r.status_code == 403:
        raise exception.DownloadError(message=f"Tried finding new commits from {githubUserName}/{githubRepoName} but exceeded the rate limit, try again within an hour!")

    # no commits found or page not found
    if r.status_code == 404:
        raise exception.DownloadError(message=f"Failed to check for new commits from {githubUserName}/{githubRepoName} because: no commits found (404)")

    # random error
    if not r.ok:
        raise exception.DownloadError(message=f"Failed to get commits from {githubUserName}/{githubRepoName} because: {r.reason}")

    return r.json()[0]

# download tests for githubUserName and githubRepoName from what is known in db
# use _syncCommit() to force an update in db
def _download(githubUserName: str, githubRepoName: str):
    sha = database.commitSha(githubUserName, githubRepoName)
    zipUrl = f'https://api.github.com/repos/{githubUserName}/{githubRepoName}/zipball/{sha}'

    try:
        r = _get_with_auth(zipUrl)
    except requests.exceptions.ConnectionError as e:
        raise exception.DownloadError(message = "Oh no! It seems like there is no internet connection available?!")

    gitHubUrl = f'https://github.com/{githubUserName}/{githubRepoName}' # just for feedback

    if not r.ok:
        raise exception.DownloadError(message = f"Failed to download {gitHubUrl} because: {r.reason}")

    f = io.BytesIO(r.content)

    with zf.ZipFile(f) as z:
        destPath = database.githubPath(githubUserName, githubRepoName)

        existingFiles: Set[pathlib.Path] = set()
        for path, subdirs, files in os.walk(destPath):
            for fil in files:
                existingFiles.add((pathlib.Path(path) / fil).relative_to(destPath))

        newFiles: Set[pathlib.Path] = set()
        for name in z.namelist():
            if name:
                path: str = pathlib.Path(name).as_posix()
                if "tests/" in path:
                    newFiles.add(pathlib.Path(path.split("tests/")[1]))

        for filePath in [fp for fp in existingFiles - newFiles if fp.suffix == ".py"]:
            printer.displayRemoved(str(filePath))

        for filePath in [fp for fp in newFiles - existingFiles if fp.suffix == ".py"]:
            printer.displayAdded(str(filePath))

        for filePath in existingFiles - newFiles:
            (destPath / filePath).unlink() # remove file

        _extractTests(z, destPath)

    printer.displayCustom(f"Finished downloading: {gitHubUrl}")

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

    if path.suffix:
        _extractFile(zipfile, path, filePath)
    elif subfolderPath and not filePath.exists():
        os.makedirs(str(filePath))

def _extractFile(zipfile: zf.ZipFile, path: pathlib.Path, filePath: pathlib.Path):
    zipPathString = path.as_posix()
    if filePath.is_file():
        with zipfile.open(zipPathString) as new, open(str(filePath), "r") as existing:
            # read file and decode
            try:
                newText = new.read().decode('utf-8')
            except UnicodeDecodeError:
                # Skip any non utf-8 file
                return

            # strip trailing whitespace, remove carrier return
            newText = ''.join(newText.strip().splitlines())
            existingText = ''.join(existing.read().strip().splitlines())
            if newText != existingText:
                printer.displayUpdate(str(path))

    with zipfile.open(zipPathString) as source, open(str(filePath), "wb+") as target:
        shutil.copyfileobj(source, target)
