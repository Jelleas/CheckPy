import unittest
import os
import shutil
from checkpy.entities.path import Path
import checkpy.entities.exception as exception

class TestPathFileName(unittest.TestCase):
    def test_name(self):
        path = Path("foo.txt")
        self.assertEqual(path.fileName, "foo.txt")

    def test_nestedName(self):
        path = Path("/foo/bar/baz.txt")
        self.assertEqual(path.fileName, "baz.txt")

    def test_extraSlash(self):
        path = Path("/foo/bar/baz.txt/")
        self.assertEqual(path.fileName, "baz.txt")

class TestPathFolderName(unittest.TestCase):
    def test_name(self):
        path = Path("/foo/bar/baz.txt")
        self.assertEqual(path.folderName, "bar")

    def test_extraSlash(self):
        path = Path("/foo/bar/baz.txt/")
        self.assertEqual(path.folderName, "bar")

class TestPathContainingFolder(unittest.TestCase):
    def test_empty(self):
        path = Path("")
        self.assertEqual(str(path.containingFolder()), ".")

    def test_file(self):
        path = Path("/foo/bar/baz.txt")
        self.assertEqual(str(path.containingFolder()), os.path.normpath("/foo/bar"))

    def test_folder(self):
        path = Path("/foo/bar/baz/")
        self.assertEqual(str(path.containingFolder()), os.path.normpath("/foo/bar"))

class TestPathIsPythonFile(unittest.TestCase):
    def test_noPythonFile(self):
        path = Path("/foo/bar/baz.txt")
        self.assertFalse(path.isPythonFile())

    def test_pythonFile(self):
        path = Path("/foo/bar/baz.py")
        self.assertTrue(path.isPythonFile())

    def test_folder(self):
        path = Path("/foo/bar/baz/")
        self.assertFalse(path.isPythonFile())

        path = Path("/foo/bar/baz")
        self.assertFalse(path.isPythonFile())

class TestPathExists(unittest.TestCase):
    def setUp(self):
        self.fileName = "dummy.py"
        with open(self.fileName, "w") as f:
            pass

    def tearDown(self):
        os.remove(self.fileName)

    def test_doesNotExist(self):
        path = Path("foo/bar/baz.py")
        self.assertFalse(path.exists())

    def test_exists(self):
        path = Path("dummy.py")
        self.assertTrue(path.isPythonFile())

class TestPathWalk(unittest.TestCase):
    def setUp(self):
        self.dirName = "dummy"
        os.mkdir(self.dirName)

    def tearDown(self):
        if os.path.exists(self.dirName):
            shutil.rmtree(self.dirName)

    def test_oneDir(self):
        paths = []
        for path, subdirs, files in Path(self.dirName).walk():
            paths.append(path)
        self.assertTrue(len(paths) == 1)
        self.assertEqual(str(paths[0]), self.dirName)

    def test_oneDirOneFile(self):
        fileName = "dummy.py"
        with open(os.path.join(self.dirName, fileName), "w") as f:
            pass
        ps = []
        fs = []
        for path, subdirs, files in Path(self.dirName).walk():
            ps.append(path)
            fs.extend(files)
        self.assertTrue(len(ps) == 1)
        self.assertEqual(str(ps[0]), self.dirName)
        self.assertTrue(len(fs) == 1)
        self.assertEqual(str(fs[0]), fileName)

    def test_nestedDirs(self):
        otherDir = os.path.join(self.dirName, "dummy2")
        os.mkdir(otherDir)
        fileName = "dummy.py"
        with open(os.path.join(self.dirName, fileName), "w") as f:
            pass
        ps = []
        fs = []
        for path, subdirs, files in Path(self.dirName).walk():
            ps.append(path)
            fs.extend(files)
        self.assertTrue(len(ps) == 2)
        self.assertEqual(str(ps[0]), self.dirName)
        self.assertEqual(str(ps[1]), otherDir)
        self.assertTrue(len(fs) == 1)
        self.assertEqual(str(fs[0]), fileName)

class TestPathCopyTo(unittest.TestCase):
    def setUp(self):
        self.fileName = "dummy.txt"
        self.content = "foo"
        with open(self.fileName, "w") as f:
            f.write(self.content)
        self.target = "dummy.py"

    def tearDown(self):
        os.remove(self.fileName)
        if os.path.exists(self.target):
            os.remove(self.target)

    def test_noFile(self):
        fileName = "idonotexist.py"
        path = Path(fileName)
        with self.assertRaises(IOError):
            path.copyTo(".")
        self.assertFalse(os.path.exists(fileName))

    def test_file(self):
        path = Path(self.fileName)
        path.copyTo(self.target)
        self.assertTrue(os.path.exists(self.fileName))
        self.assertTrue(os.path.exists(self.target))

class TestPathPathFromFolder(unittest.TestCase):
    def test_empty(self):
        path = Path("")
        with self.assertRaises(exception.PathError):
            path.pathFromFolder("idonotexist")

    def test_folderNotInpath(self):
        path = Path("/foo/bar/baz")
        with self.assertRaises(exception.PathError):
            path.pathFromFolder("quux")

    def test_folderInpath(self):
        path = Path("/foo/bar/baz")
        self.assertEqual(str(path.pathFromFolder("bar")), "baz")
        self.assertEqual(str(path.pathFromFolder("foo")), os.path.normpath("bar/baz"))

class TestPathAdd(unittest.TestCase):
    def test_string(self):
        path = Path("foo/bar")
        self.assertEqual(str(path + "baz"), os.path.normpath("foo/bar/baz"))
        with self.assertRaises(exception.PathError):
            path + "/baz"

        path = Path("foo/bar/")
        self.assertEqual(str(path + "baz"), os.path.normpath("foo/bar/baz"))
        with self.assertRaises(exception.PathError):
            path + "/baz"

    def test_path(self):
        path = Path("foo/bar")
        self.assertEqual(str(path + Path("baz")), os.path.normpath("foo/bar/baz"))
        with self.assertRaises(exception.PathError):
            path + Path("/baz")

        path = Path("foo/bar/")
        self.assertEqual(str(path + Path("baz")), os.path.normpath("foo/bar/baz"))
        with self.assertRaises(exception.PathError):
            path + Path("/baz")

    def test_unsupportedType(self):
        path = Path("foo/bar")
        with self.assertRaises(exception.PathError):
            path + 1

class TestPathSub(unittest.TestCase):
    def test_empty(self):
        path = Path("")
        self.assertEqual(str(path - ""), ".")
        self.assertEqual(str(path - Path("")), ".")

        path = Path("foo/bar/baz")
        self.assertEqual(str(path - ""), os.path.normpath("foo/bar/baz"))
        self.assertEqual(str(path - Path("")), os.path.normpath("foo/bar/baz"))

        path = Path("./foo/bar/baz")
        self.assertEqual(str(path - ""), os.path.normpath("foo/bar/baz"))
        self.assertEqual(str(path - Path("")), os.path.normpath("foo/bar/baz"))

        path = Path("/foo/bar/baz")
        with self.assertRaises(exception.PathError):
            path - ""
        with self.assertRaises(exception.PathError):
            path - Path("")

    def test_string(self):
        path = Path("foo/bar/baz")
        self.assertEqual(str(path - "foo/bar"), "baz")
        with self.assertRaises(exception.PathError):
            path - "/foo/bar"

        path = Path("/foo/bar/baz")
        with self.assertRaises(exception.PathError):
            path - "foo/bar"
        self.assertEqual(str(path - "/foo/bar"), "baz")

    def test_path(self):
        path = Path("foo/bar/baz")
        self.assertEqual(str(path - Path("foo/bar")), "baz")
        with self.assertRaises(exception.PathError):
            path - "/foo/bar"

        path = Path("/foo/bar/baz")
        with self.assertRaises(exception.PathError):
            path - Path("foo/bar")
        self.assertEqual(str(path - Path("/foo/bar")), "baz")

class TestPathIter(unittest.TestCase):
    def test_empty(self):
        path = Path("")
        self.assertEqual(list(path), ["."])

    def test_root(self):
        path = Path("/")
        self.assertEqual(list(path), [os.path.sep])

    def test_path(self):
        path = Path("foo/bar/baz")
        self.assertEqual(list(path), ["foo", "bar", "baz"])

class TestPathContains(unittest.TestCase):
    def test_root(self):
        path = Path("/")
        self.assertTrue(os.path.normpath("/") in path)
        self.assertFalse("." in path)

    def test_current(self):
        path = Path(".")
        self.assertTrue("." in path)
        self.assertFalse("/" in path)

        path = Path("")
        self.assertTrue("." in path)
        self.assertFalse("/" in path)

    def test_localPath(self):
        path = Path("foo/bar/baz")
        for d in ["foo", "bar", "baz"]:
            self.assertTrue(d in path)

    def test_absPath(self):
        path = Path("/foo/bar/baz")
        self.assertTrue(os.path.normpath("/") in path)
        for d in ["foo", "bar", "baz"]:
            self.assertTrue(d in path)

class TestPathLen(unittest.TestCase):
    def test_root(self):
        path = Path("/")
        self.assertEqual(len(path), 1)

    def test_current(self):
        path = Path(".")
        self.assertEqual(len(path), 1)

    def test_localPath(self):
        path = Path("foo/bar/baz")
        self.assertEqual(len(path), 3)
        path = Path("foo/bar/baz/")
        self.assertEqual(len(path), 3)

    def test_absPath(self):
        path = Path("/foo/bar/baz")
        self.assertEqual(len(path), 4)

        path = Path("/foo/bar/baz/")
        self.assertEqual(len(path), 4)


if __name__ == '__main__':
    unittest.main()
