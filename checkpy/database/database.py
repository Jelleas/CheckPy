import tinydb
import os
import time
from checkpy.entities.path import Path, CHECKPYPATH

_DBPATH = CHECKPYPATH + "database" + "db.json"

def database():
	if not _DBPATH.exists():
		with open(str(_DBPATH), 'w') as f:
			pass
	return tinydb.TinyDB(str(_DBPATH))

def githubTable():
	return database().table("github")

def localTable():
	return database().table("local")

def clean():
	database().drop_tables()

def forEachTestsPath():
	for path in forEachGithubPath():
		yield path

	for path in forEachLocalPath():
		yield path

def forEachUserAndRepo():
	for username, repoName in ((entry["user"], entry["repo"]) for entry in githubTable().all()):
		yield username, repoName

def forEachGithubPath():
	for entry in githubTable().all():
		yield Path(entry["path"])

def forEachLocalPath():
	for entry in localTable().all():
		yield Path(entry["path"])

def isKnownGithub(username, repoName):
	query = tinydb.Query()
	return githubTable().contains((query.user == username) & (query.repo == repoName))

def addToGithubTable(username, repoName, releaseId, releaseTag):
	if not isKnownGithub(username, repoName):
		path = str(CHECKPYPATH + "tests" + repoName)

		githubTable().insert({
			"user" 			: username,
			"repo" 			: repoName,
			"path"          : path,
			"release" 		: releaseId,
			"tag" 			: releaseTag,
			"timestamp" 	: time.time()
		})

def addToLocalTable(localPath):
	query = tinydb.Query()
	table = localTable()

	if not table.search(query.path == str(localPath)):
		table.insert({
			"path" : str(localPath)
		})

def updateGithubTable(username, repoName, releaseId, releaseTag):
	query = tinydb.Query()
	path = str(CHECKPYPATH + "tests" + repoName)
	githubTable().update({
		"user" 			: username,
		"repo" 			: repoName,
		"path"          : path,
		"release" 		: releaseId,
		"tag" 			: releaseTag,
		"timestamp" 	: time.time()
	}, query.user == username and query.repo == repoName)

def timestampGithub(username, repoName):
	query = tinydb.Query()
	return githubTable().search(query.user == username and query.repo == repoName)[0]["timestamp"]

def setTimestampGithub(username, repoName):
	query = tinydb.Query()
	githubTable().update(\
		{
			"timestamp" : time.time()
		}, query.user == username and query.repo == repoName)

def githubPath(username, repoName):
	query = tinydb.Query()
	return Path(githubTable().search(query.user == username and query.repo == repoName)[0]["path"])

def releaseId(username, repoName):
	query = tinydb.Query()
	return githubTable().search(query.user == username and query.repo == repoName)[0]["release"]

def releaseTag(username, repoName):
	query = tinydb.Query()
	return githubTable().search(query.user == username and query.repo == repoName)[0]["tag"]
