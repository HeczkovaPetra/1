#!/usr/bin/python
# -*- coding: utf-8 -*-
#CST:xheczk04

import sys, getopt, os, re

# fce, ktera pocita statistickou informaci
# data - text ze souboru, param - zadany parametr z prikazove radky
# param2 - true pokud je rozsireni, p - true pokud je parametr p
# nosub - true pokud je zadan parametr nosub
# patt - pokud zadan parametr w obsahuje vzorec, jinak prazdny
def find_some(data, param, param2, p, nosub, patt):
	counter = 0; m = []
	# seznam klicovych slov jazyka C
	klist = ['auto','break','case','char','const','continue','default','do','double','else','enum','extern','float','for','goto','if','int','long','register','return','short','signed','sizeof','static','struct','switch','typedef','union','unsigned','void','volatile','while','inline']
	# seznam jednoduchych operatoru
	olist = ['>>=','<<=','\+\+','--','==','!=','>=','<=','->','>>','<<','>','<','&&','\|\|','&','\|','\+=','-=','\*=','/=','%=','&=','\|=','\^=','\^','\+','-','/','%','!','~','=']

	# zpracovani backslash
	data = re.sub(r'\\\n', '@@', data)
	# vyhledavani vzorce (i v komentech atd.)
	if param == "w":
		# pripady kdy -w= (prazdny)
		if not patt:
			couter = len(re.findall('\s', data))
		else:
			counter = data.count(patt)
	# odstraneni a pocitani komentare + rozsireni com
	data2 = re.sub('/@{0,2}/.*?\n', '', data)
	data2 = re.sub('/@{0,2}\*.*?\*@{0,2}/', '',data2, flags=re.DOTALL)
	if param == "c":
		counter = len(data) - len(data2)
	# odstraneni retezce, makra
	short = re.sub('^#.*$', '', data2, flags=re.MULTILINE)
	short = re.sub('[\"|\'].*[\"|\']', '', short)
	short = re.sub('@@', '', short)
	# pocitani a odstraneni operatory
	if param == "o":
		# situace .foo
		counter += len(re.findall('[ |,|;]\.[a-zA-Z]', short)) 
		# situace * num, *( num, * (num
		counter += len(re.findall('\*\s*\(*\s*[a-zA-Z0-9]', short))
		# situace int *t, int (*t
		counter -= len(re.findall('(^|}|,|;|char|short|int|float|long|double|const)\s*\(*\s*\*{1,2}', short, flags=re.MULTILINE))
	# situace cislo s +-eE a hexa cisla
	short = re.sub('[0-9\.]+(e|E)(-|\+)?[0-9a-zA-Z]+','', short)
	short = re.sub('0(x|X)[0-9\+-\.a-zA-Z]+','', short)

	# pocitani klicovych slov
	for i in olist:
		if param == "o":
			i2 = re.sub(r'\\', '', i)
			counter += short.count(i2)
		short = re.sub(i, ' ', short)
	short = re.sub('\*',' ', short)
	# rozsireni IND
	if param == "o" and param2:
		counter += len(re.findall('\[.*?\]', short, flags=re.DOTALL))
		counter -= len(re.findall('(char|short|int|float|long|double|const)\s*[a-z\s\*A-Z]*\s*\[.*?\]', short))
		counter -= len(re.findall('(char|short|int|float|long|double|const)\s*[a-z\s\*A-Z]*\s*\[.*?\];', short))

	# klicova slova
	for i in klist:
		reg =  i + "[\s|{|\(|\)|,|$|;]"
		if param == "k":
			counter += len(re.findall(reg, short, flags=re.MULTILINE))
		short = re.sub(reg, ' ', short)
	# identifikatory
	short = re.sub('[;|\(|\)|"|\'|\{|\}|\[|\]|\,]', ' ', short)
	short = re.sub('\.', ' ', short)
	if param == "i":
		n = short.split()
		rex = re.compile('[:|\?|0-9]')
		n = [x for x in n if not rex.match(x)]
		counter = len(n)
	return counter
	

# fce, ktera jenom vypise na standartni chybovy vystup
# i - chybovy kod
def ending(i):
	err_list = [
		"Error: unknown parameter.\n",
		"Error: incompatible parameters.\n",
		"Error: wrong input.\n",
		"Error: wrong output.\n",
		"Unknown error.\n"
	]
	print(err_list[i], file=sys.stderr)
	if i == 0: i += 1
	sys.exit(i)


# funkce, ktera vypisuje formatovany vystup
# names - seznam jmen souboru, counts - vysledky fce find_some(),
# param_p - true pokud je p zadan, 
# out - kam se vysledek vypise, soubor nebo standartni vystup
def display(names, counts, param_p, out):
	max_n = len("CELKEM:"); max_c = 0; sum = 0
	names2 = []
	#pocitani sumy hodnot pro "CELKEM"
	for i in counts:
		sum += i
		# hledani nejdelsi polozky
		if len(str(i)) > max_c: max_c = len(str(i))
	counts.append(sum)
	for i in names:
		# jenom nazev souboru
		if param_p:
			(filepath, i) = os.path.split(i)
		# cela cesta
		else:
			i = os.path.join(os.path.expanduser("~"), i)
		names2.append(i)
		# hledani nejdelsi polozky
		if len(i) > max_n: max_n = len(i)
	# pridani polozky posledni polozky do seznamu jmen
	names2.append("CELKEM:")

	if out: # out je soubor
		try:
			out = open(out, "w")
		except IOError:
			ending(3)
	else: # out je prazdny, tzn. zapis na standartni vystup
		out = sys.stdout

	# zapis
	for i,j in zip(names2, counts):
		# pocitani mezer
		s1 = max_n - len(i)
		s2 = max_c - len(str(j))
		print(i + " "*s1 + " " + " "*s2 + str(j), end = '\n', file = out)

# fce main, obsahuje getopts pro zpracovani parametru, kontroly chyb,
# prochazi slozku a vybira soubory, pokud je potreba,
# vola fci find_some() a display()
def main():
	try:
		# zpracovani prikazove radky
		opts, args = getopt.getopt(sys.argv[1:],"sw:koicp",["help","output=","input=","nosubdir"])
	except getopt.GetoptError as err:
		ending(0)
	# pomocne promenne
	# koiwc: true - muzu prijmout parametr a nastavit na False
	koiwc = True; param2 = False;
	param = ""; param_p = False; nosub = False; patt = ""
	inputt = ""; output = ""

	for o, a in opts:
		if o == "--help":
			# help nesmi byt kombinovan s jinymi parametry
			if len(opts) > 1: ending(1)
			print("Skript pro analyzu zdrojovych souboru jazyka C podle standardu ISO C99, ktery ve stanovenem formatu vypise statistiky komentaru, klicovych slov, operatoru a retezcu. \n\n\
Tento skript bude pracovat s temito parametry:    \n\
--input=fileordir zadany vstupni soubor nebo adresar se zdrojovym kodem v jazyce C\n\
--nosubdir prohledavani bude provadeno pouze v zadanem adresari, ale uz ne v jeho podadresarich \n\
--output=filename zadany textovy vystupni soubor\n\
-k vypise pocet vsech vyskytu klicovych slov (vyskytujicich se mimo poznamky a retezce)\n\
-o vypise pocet vyskytu jednoduchych operatoru\n\
-i vypise pocet vyskytu identifikatoru – nezahrnuje klicova slova\n\
-w=pattern vyhleda presny textovy retezec pattern ve vsech zdrojovych kodech,je case-sensitive.\n\
-c vypise celkovy pocet znaku komentaru vcetne uvozujicich znaku komentaru (//, /* a */)\n\
-p v kombinaci s predchozimi (az na --help) zpusobi, ze soubory se budou vypisovat bez cesty k souboru (tedy pouze samotna jmena souboru\n\
")
			sys.exit(0)
		elif o == "-s":
			param2 = True
		elif o == "-k":
			koiwc = False if koiwc else ending(1)
			param = "k"
		elif o == "-o":
			koiwc = False if koiwc else ending(1)
			param = "o"
		elif o == "-i":
			koiwc = False if koiwc else ending(1)
			param = "i"
		elif o in "-w":
			koiwc = False if koiwc else ending(1)
			param = "w"
			if a.find('='): ending(0)
			else: patt = a[1:]
		elif o == "-c":
			koiwc = False if koiwc else ending(1)
			param = "c"
		elif o == "-p":
			param_p = True
		elif o in "--output":
			output = a
		elif o in "--input":
			inputt = a
			# soubor existuje
			if not os.path.exists(a): ending(2)
		elif o in "--nosubdir":
			nosub = True
		else:
			ending(0)
	# je zadan --nosubdir a zaroven je jako input soubor
	if nosub and os.path.isfile(inputt):
		ending(1)

	names = []; counts = []
	# neni zadano, hledani v aktualni slozce
	if not inputt:
		inputt = os.getcwd()
	# je zadan soubor pres --input=file.c
	if os.path.isfile(inputt):
		names.append(inputt)
		try: f = open(inputt, 'r')
		except IOError: ending(2)
		counts.append(find_some(f.read(), param, param2, param_p, nosub, patt))
	# je zadana slozka pres --input=dir/
	else:
		for dirname, dirnames, filenames in os.walk(inputt):
			for filename in filenames:
				n = re.split('\.',filename)
				# vyber jenom C souboru
				if n[1] == 'c' or n[1] == 'h':
					inp = os.path.join(dirname, filename)
					names.append(inp)
					try: f = open(inp, 'r')
					except IOError: ending(2)
					counts.append(find_some(f.read(), param, param2, param_p, nosub, patt))
			# zadan --nosubdir neprohledavaji se slozky
			if nosub:
				break;
	# fce delajici vypis
	display(names, counts, param_p, output)

if __name__ == "__main__":
	main()


