import test as t
import lib
import assertlib

@t.test(0)
def allEvenNumbersInOutput(test):
	def testMethod():
		result = lib.outputOf(_fileName)
		evenNumbers = set(range(4, 1001, 2))
		for line in result.split("\n"):
			if line == "\n":
				continue
			evenNumbers -= set(lib.getPositiveIntegersFromString(line))
		testResult = len(evenNumbers) == 0
		return testResult, result
	test.test = testMethod

	test.description = lambda : "all even numbers occur in output"

@t.test(1)
def allCalculationsCorrect(test):
	def testMethod():
		result = lib.outputOf(_fileName)
		for line in result.split("\n"):
			if line.strip() == "":
				continue
			numbers = lib.getPositiveIntegersFromString(line)
			if not any(sum(numbers) / 2 == n for n in numbers):
				return False, "calculcation \"%s\" is incorrect" %line
		return True, ""
	test.test = testMethod

	test.description = lambda : "calculations on each line are correct"
	test.fail = lambda info : str(info)

@t.test(2)
def allCalculationsContainTwoPrimes(test):
	def testMethod():
		primes = set([2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601, 607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691, 701, 709, 719, 727, 733, 739, 743, 751, 757, 761, 769, 773, 787, 797, 809, 811, 821, 823, 827, 829, 839, 853, 857, 859, 863, 877, 881, 883, 887, 907, 911, 919, 929, 937, 941, 947, 953, 967, 971, 977, 983, 991, 997])
		result = lib.outputOf(_fileName)
		for line in result.split("\n"):
			if line.strip() == "":
				continue
			numbers = lib.getPositiveIntegersFromString(line)
			if sum(1 for n in numbers if n in primes) != 2:
				return False, "calculation \"%s\" does not contain exactly two prime numbers" %line
		return True, ""
	test.test = testMethod

	test.description = lambda : "calculations on each line contain exactly two primes"
	test.fail = lambda info : str(info) 