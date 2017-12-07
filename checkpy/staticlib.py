from checkpy import caches
import redbaron

def source(fileName):
	with open(fileName) as f:
		return f.read()

@caches.cache()
def fullSyntaxTree(fileName):
	return fstFromSource(source(fileName))

@caches.cache()
def fstFromSource(source):
	return redbaron.RedBaron(source)

@caches.cache()
def functionCode(functionName, fileName):
	definitions = [d for d in fullSyntaxTree(fileName).find_all("def") if d.name == functionName]
	if definitions:
		return definitions[0]
	return None

def functionLOC(functionName, fileName):
	code = functionCode(functionName, fileName)
	ignoreNodes = []
	ignoreNodeTypes = [redbaron.EndlNode, redbaron.StringNode]
	for node in code.value:
		if any(isinstance(node, t) for t in ignoreNodeTypes):
			ignoreNodes.append(node)

	for ignoreNode in ignoreNodes:
		code.value.remove(ignoreNode)

	return len(code.value) + 1