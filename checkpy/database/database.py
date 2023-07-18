import tinydb
import os
import time
import contextlib
from checkpy.entities.path import Path, CHECKPYPATH

_DBPATH = CHECKPYPATH + "database" + "db.json"

@contextlib.contextmanager
def database():
	if not _DBPATH.exists():
		with open(str(_DBPATH), 'w') as f:
			pass
	try:
		db = tinydb.TinyDB(str(_DBPATH))
		yield db
	finally:
		db.close()

@contextlib.contextmanager
def githubTable():
	with database() as db:
		yield db.table("github")

@contextlib.contextmanager
def localTable():
	with database() as db:
		yield db.table("local")

def clean():
	with database() as db:
		db.drop_tables()

def forEachTestsPath():
	for path in forEachGithubPath():
		yield path

	for path in forEachLocalPath():
		yield path

def forEachUserAndRepo():
	with githubTable() as table:
		for username, repoName in [(entry["user"], entry["repo"]) for entry in table.all()]:
			yield username, repoName

def forEachGithubPath():
	with githubTable() as table:
		for entry in table.all():
			yield Path(entry["path"])

def forEachLocalPath():
	with localTable() as table:
		for entry in table.all():
			yield Path(entry["path"])

def isKnownGithub(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		return table.contains((query.user == username) & (query.repo == repoName))

def addToGithubTable(username, repoName, releaseId, releaseTag):
	if not isKnownGithub(username, repoName):
		path = str(CHECKPYPATH + "tests" + repoName)

		with githubTable() as table:
			table.insert({
				"user" 			: username,
				"repo" 			: repoName,
				"path"          : path,
				"release" 		: releaseId,
				"tag" 			: releaseTag,
				"timestamp" 	: time.time()
			})

def addToLocalTable(localPath):
	query = tinydb.Query()
	with localTable() as table:
		if not table.search(query.path == str(localPath)):
			table.insert({
				"path" : str(localPath)
			})

def updateGithubTable(username, repoName, releaseId, releaseTag):
	query = tinydb.Query()
	path = str(CHECKPYPATH + "tests" + repoName)
	with githubTable() as table:
		table.update({
			"user" 			: username,
			"repo" 			: repoName,
			"path"          : path,
			"release" 		: releaseId,
			"tag" 			: releaseTag,
			"timestamp" 	: time.time()
		}, query.user == username and query.repo == repoName)

def timestampGithub(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		return table.search(query.user == username and query.repo == repoName)[0]["timestamp"]

def setTimestampGithub(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		table.update(
			{"timestamp" : time.time()},
			query.user == username and query.repo == repoName
		)

def githubPath(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		return Path(table.search(query.user == username and query.repo == repoName)[0]["path"])

def releaseId(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		return table.search(query.user == username and query.repo == repoName)[0]["release"]

def releaseTag(username, repoName):
	query = tinydb.Query()
	with githubTable() as table:
		return table.search(query.user == username and query.repo == repoName)[0]["tag"]
