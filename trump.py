import random
import monopoly

def throw():
	return random.randint(1,6) + random.randint(1,6)

def possession(board):
	d = {}
	for i in range(len(board.values)):
		if board.values[i] > 0:
			d[board.names[i]] = False
	return d

if __name__ == "__main__":
	board = monopoly.Board()
	piece = monopoly.Piece()
	nTrials = 1000
	nThrows = 0

	for i in range(nTrials):
		d = possession(board)
		while not all(d.values()): 
			piece.move(throw())
			name = board.names[piece.location]
			if name in d and not d[name]:
				d[name] = True

			nThrows += 1

	print(nThrows // nTrials)