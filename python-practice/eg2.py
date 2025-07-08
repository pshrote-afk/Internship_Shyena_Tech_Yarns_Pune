class WorldState:
	has_iron = False
	has_gold = False
	killed_dragon = False
	visited_overworld = False
	visited_nether = False
	visited_end = False
	exit = False

worldState = WorldState()

def overworld():
	print("You stayed in Overworld")
	print("1. Mine for Iron")
	print("2. Mine for Diamond")
	
	mine = input(">>>")
	if(mine == "1"):
		worldState.has_iron = True
		print("You now have iron.",end="\n(Hint: you should now go mine diamonds)")		
	elif(mine == "2" and worldState.has_iron == True):
		print("You now have 37 diamonds.",end="\n(Hint: you should now go make diamond armour)")		
		worldState.visited_overworld = True
	else:
		print("Go mine iron, before you can get diamonds")

def nether():
	if(worldState.visited_overworld == False):
		print("Complete all tasks of Overworld to enter")			
		return
	print("You went to the Nether")
	print("1. Mine for gold")
	print("2. Mine for netherite")

	mine = int(input(">>>"))
	if(mine == 1):
		worldState.has_gold = True
		print("You now have gold.",end="\n(Hint: you should now go mine netherite)")		
	elif(mine == 2 and worldState.has_gold == True):
		print("You now have 37 netherite.",end="\n(Hint: you should now go make netherite armour)")		
		worldState.visited_nether = True
	else:
		print("Go mine gold, before you can get netherite")
	
def end():
	if(worldState.visited_nether == False):
		print("Complete all tasks of Nether to enter")
		return
	print("You warped to the End")
	print("1. Kill Ender Dragon")
	print("2. Hunt for Elytra")

	mine = int(input(">>>"))
	if(mine == 1):
		worldState.killed_dragon = True
		print("You have courageously slayed the Ender Dragon.",end="\n(Hint: you should now go bring home the Elytra)")		
	elif(mine == 2 and worldState.killed_dragon == True):
		print("You have now defeated the End City.\nYou went and claimed the Elytra",end="\n\n(Endscreen: you went back to Overworld, built a big house, and lived happily ever after with your husband/wife, 7 kids, 18 dogs, and 112 Llamas.)\n\n")
		worldState.visited_end = True
	else:
		print("Go kill the Ender Dragon first, you greedy")
	

while(worldState.exit!=True):

	print("""
	You inside a new MineCraft World:
	1. Stay in Overworld
	2. Go to the Nether
	3. Warp to the End
	4. Exit
	""")

	world = int(input(">>>"))
	if(world == 1):
		overworld()
	
	elif(world == 2):
		nether()

	elif(world == 3):
		end()
	
	elif(world == 4):
		worldState.exit = True

	if((worldState.visited_overworld == True) and (worldState.visited_nether == True) and (worldState.visited_end == True)):
		print("Game completed.")
		break


print("\n\nMineCraft simulator:\nParas Shrote\n\nwww.github.com/pshrote-afk\n\n")