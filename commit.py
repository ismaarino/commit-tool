#·······················#
#	GIT Commit Maker	#
#·······················#
VERSION = "1.0"

def import_or_install(package):
	try:
		return __import__(package)
	except ImportError:
		os.system('pip install ' + package)
		return __import__(package)

import sys, signal, subprocess, os, re, time, math
from datetime import date
colorama = import_or_install("colorama")
from colorama import Fore, Back, Style

#···································································#

BRANCH_NAME_DIVIDER = "/"
MAX_DIFF_LENGTH = 15000
GIT_DIFF_SKIP_LINES = 4
FETCH_REMOTES = True
MAIN_BRANCH_NAME = "master"
OPS = ["fix", "feat", "perf", "refactor", "docs", "style", "test"]

#···································································#

def logo():
	print("  _____                          _ _   \n" +
	" / ____|                        (_) |  \n" +
	"| |     ___  _ __ ___  _ __ ___  _| |_ \n" +
	"| |    / _ \\| '_ ` _ \\| '_ ` _ \\| | __|\n" +
	"| |___| (_) | | | | | | | | | | | | |_ \n" +
	" \\_____\\___/|_| |_| |_|_| |_| |_|_|\\__|\n" +
	"                       v" + VERSION + " by ismael")

def c(t, color):
	return color + t + Style.RESET_ALL

def printLoading(n):
	states = ["|","/","-","\\"]
	print(states[n % 4] + "\b", end="")

def checkIfYes(i):
	return i == "" or i == "y"

def run(cmd):
	out = subprocess.getoutput(cmd)
	return out

def handler(signum, frame):
	print("\n" + c("Aborted by user", Back.RED))
	subprocess.check_output("git reset")
	print("Resetted changes on project.")
	exit(0)

def myBranch():
	return str(run("git rev-parse --abbrev-ref HEAD")).strip()

def repositoryInfo():
	files_at_main = str(run("git ls-tree -r " + MAIN_BRANCH_NAME + " --name-only")).split("\n")
	print("This repository has " + c(str(len(files_at_main)), Fore.YELLOW + Style.BRIGHT) + " files at " + c(MAIN_BRANCH_NAME, Style.BRIGHT + Fore.MAGENTA))
	exts = []
	exts_n = []
	for i in range(0, len(files_at_main)):
		splitted = files_at_main[i].split(".")
		if len(splitted) > 1 and len(splitted[-1]) > 0 and "./" not in files_at_main[i] and files_at_main[i][0] != "." and "/" not in splitted[-1] :
			ext = splitted[-1]
			if ext not in exts :
				n = 0
				for j in range(i, len(files_at_main)) :
					ext2 = files_at_main[j].split(".")[-1]
					if ext2 == ext :
						n += 1
				j = 0
				inserted = False
				while j < len(exts_n) and not inserted :
					if n > exts_n[j] :
						exts_n.insert(j, n)
						exts.insert(j, ext)
						inserted = True
					j += 1
				if len(exts_n) == 0 or not inserted:
					exts_n.append(n)
					exts.append(ext)

	colors = [Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE]
	used_colors = []
	for i in range(0, len(exts)) :
		hsum = 0
		for j in range(0, len(exts[i])) :
			hsum += ord(exts[i][j])
		color_code = -1
		while color_code in used_colors or color_code == -1 :
			color_code = hsum % len(colors)
			hsum += 1
		used_colors.append(color_code)
		if len(used_colors) == len(colors) :
			used_colors.clear()
		color = colors[color_code]
		print(c(exts[i], color + Fore.BLACK), end="")
		width = exts_n[i] - len(exts[i])
		if width < 0 :
			width = 0
		for j in range(0, width) :
			print(c(" ", color), end="")
		print(" ", end="")
	print("\n")

def updateAllRemotes(my_branch):
	print("fetching remotes...",end="")
	remotes = str(run("git branch -r")).strip().split("\n")
	for i in range(0, len(remotes)) :
		remote = remotes[i].strip()
		if ">" not in remote and remote != my_branch :
			printLoading(i)
			try :
				subprocess.check_output("git checkout --track " + remote, stderr=subprocess.STDOUT)
				subprocess.check_output("git pull", stderr=subprocess.STDOUT)
				subprocess.check_output("git checkout " + my_branch, stderr=subprocess.STDOUT)
			except :
				pass
	if my_branch != myBranch() :
		subprocess.check_output("git checkout " + my_branch, stderr=subprocess.STDOUT)
	print("OK")

def alertIfNotChangelog(tostage_files) :
	has_changelog = False
	i = 0
	while not has_changelog and i < len(tostage_files) :
		if "changelog" in tostage_files[i].lower() :
			has_changelog = True
		i += 1
	if not has_changelog :
		print(c("[WARNING] You didn't update Changelog", Style.BRIGHT + Fore.YELLOW))

def stageFile(filename, fileop, y):
	if fileop == "M" and y:
		diff = str(run("git diff \"" + filename +"\"")).strip()
		diff_lines = diff.split("\n")
		if len(diff) > MAX_DIFF_LENGTH :
			diff = diff[0:300] + "..."
			print(c("This file is too large, the view is trimmed", Style.BRIGHT))
		elif len(diff_lines) >= GIT_DIFF_SKIP_LINES :
			for j in range(0, len(diff_lines[GIT_DIFF_SKIP_LINES])) :
				print(c("·", Style.BRIGHT + Fore.BLUE), end="")
			print(" ")
			for j in range(GIT_DIFF_SKIP_LINES, len(diff_lines)) :
				if diff_lines[j][0] == "+" :
					print(Style.BRIGHT + Fore.GREEN, end="")
				elif diff_lines[j][0] == "-" : 
					print(Style.BRIGHT + Fore.RED, end="")
				if "No newline at end of file" not in diff_lines[j] :
					print(diff_lines[j])
				print(Style.RESET_ALL, end="")
			for k in range(0, len(diff_lines[len(diff_lines) - 1])) :
				print(c("·", Style.BRIGHT + Fore.BLUE), end="")
			print("")
	stage = y or checkIfYes(input("\nStage changes of " + c(filename, Style.BRIGHT + Fore.MAGENTA) + " ([enter]/n)? "))
	if stage :
		run("git add \"" + filename + "\"")
		print(" " + c("Staged " + filename, Style.BRIGHT + Fore.GREEN))
	else :
		print(" " + filename + "was not staged.")

#···································································#

signal.signal(signal.SIGINT, handler)

colorama.init()

args = sys.argv
	
branch = myBranch()

if FETCH_REMOTES :
	updateAllRemotes(branch)

# repositoryInfo()

tostage_files_output = str(run("git status --porcelain"))
tostage_files = tostage_files_output.strip().split("\n")

do_commit = len(tostage_files) > 1 or (len(tostage_files) == 1 and len(tostage_files[0]) > 0)

if do_commit :

	logo()

	if branch == MAIN_BRANCH_NAME :
		print("\nYour current branch is " + c(branch, Style.BRIGHT + Fore.MAGENTA) + ".")
		change_branch = input("Do you want to create a new one and export your work to it (y/n)? ").strip()
		if checkIfYes(change_branch) :
			new_branch_name = ""
			while len(new_branch_name) == 0 :
				new_branch_name = input("New branch name: ").strip()
			branch = new_branch_name
			print(Fore.BLACK + Back.WHITE)
			os.system("git stash")
			os.system("git checkout -b " + branch)
			os.system("git stash pop")
			print(Style.RESET_ALL, end="")

	# Stage Files
	print(c(" + Stage Files + ", Back.CYAN + Fore.BLACK))
	print("\nFound " + c(str(len(tostage_files)), Fore.YELLOW) + " modified or new file(s):\n" + tostage_files_output + "\n")

	alertIfNotChangelog(tostage_files)

	stage_all = checkIfYes(input("\nStage " + c("all", Style.BRIGHT + Fore.YELLOW) + " files (y/n)? ").strip()) if len(tostage_files) > 1 else False

	for i in range(0, len(tostage_files)) :
		tostage_files[i] = tostage_files[i].strip()
		if len(tostage_files[i]) > 0 :
			file_name = ""

			if "\"" in tostage_files[i] :
				file_name = tostage_files[i].split("\"")[1]
			else :
				file_name = tostage_files[i].split(" ")[1]
			file_op = tostage_files[i][0]
			stageFile(file_name, file_op, stage_all)

	# Build Commit Message
	print("\n" + c(" + Message Text + ", Back.CYAN + Fore.BLACK))

	content = ""

	item = ""
	read_item = ""
	is_item = False

	if BRANCH_NAME_DIVIDER in branch :
		read_item = branch.split(BRANCH_NAME_DIVIDER)[1]
		item = input("\nDetected branch " + c(branch, Back.GREEN) + "\nUse " + c(read_item, Fore.YELLOW) + " as item name? or " + c("override", Fore.BLACK + Back.WHITE) + " it with: ").strip()
		if len(item) == 0:
			item = read_item
			is_item = True
			print("Using default " + c(read_item, Fore.YELLOW) + " as item name")
	else :
		print("\nDetected branch " + c(branch, Back.GREEN) + " but couldn't parse item name from it")
		item = input("Item ID: ").strip()

	if len(item) > 0 :
		content += "#" + item + " "
	else :
		print(c("Ignored", Fore.BLACK + Back.WHITE) + " item name of the commit")

	print("\nOperation types:\n 1. Fix\n 2. Feature\n 3. Perfection\n 4. Refactor\n 5. Documentation\n 6. Code Style\n 7. Test\n [enter] to omit")
	opmode = input("\nOperation: ").strip()

	if len(opmode) > 0 and int(opmode) > 0 and int(opmode) <= len(OPS):
		content += "[" + OPS[int(opmode) - 1] + "] "
	else :
		print("\n" + c("Ignored", Fore.BLACK + Back.WHITE) + " operation of commit")

	description = ""
	while len(description) == 0 :
		description = input("\nDescription: ").strip()

	content += description[0].lower() + description[1:]

	input("Your commit is: [" + c(content, Style.BRIGHT + Fore.GREEN) + "]\nPress enter to apply")

	# Execute Commit
	cmd = "git commit -m \"" + content + "\""

	print(Fore.BLACK + Back.WHITE)
	os.system(cmd)
	print(Style.RESET_ALL)

else :
	print(c("Nothing to commit", Fore.CYAN))


# Merge main branch into current
merge = "n"
if MAIN_BRANCH_NAME != branch :
	print("\n" + c(" + Merge From ", Back.CYAN + Fore.BLACK) + c(MAIN_BRANCH_NAME, Back.CYAN + Fore.MAGENTA) + c(" into ", Back.CYAN + Fore.BLACK) + c(branch, Back.GREEN) + c(" + ", Back.CYAN + Fore.BLACK))

	merge = input("\nMerge from " + MAIN_BRANCH_NAME + " ([enter]/n)? ").strip()
	if checkIfYes(merge) :
		try :
			subprocess.check_output("git pull origin " + MAIN_BRANCH_NAME)
			print(c("Pull of " + MAIN_BRANCH_NAME + " OK",Fore.GREEN))
		except :
			print(c("An error ocurred. Can't pull " + MAIN_BRANCH_NAME + " :(", Fore.RED) + " Using local copy instead.\n")
		os.system("git merge " + MAIN_BRANCH_NAME)
		print(c("Merge of " + MAIN_BRANCH_NAME + " OK",Fore.GREEN))
	else :
		print("Not merging from main branch")

if checkIfYes(merge) or do_commit :
	# Push changes
	print("\n" + c(" + Push To Upstream + ", Back.CYAN + Fore.BLACK))

	push = input("\nPush changes to upstream ([enter]/n)? ").strip()
	if checkIfYes(push) :
		try :
			subprocess.check_output("git push --set-upstream origin " + branch)
			print(c("Push to origin OK",Fore.GREEN))
		except :
			print(c("An error ocurred. Can't push to server :(", Fore.RED))
	else :
		print("Not pushing to upstream")
else :
	print("No need to push any change")

print(c("Done.", Back.GREEN))