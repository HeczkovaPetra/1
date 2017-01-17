#!/usr/bin/python

# Projekt ISJ
# xheczk04@stud.fit.vutbr.cz
# duben 2012

import urllib2
import sys
import re
import getopt, sys
        
class DownFile:
	def __init__(self, url, lang):
		self.lang = lang
		self.url = urllib2.urlopen(url).read()
		self.name = url.split('/')[-1].strip(self.lang).replace('-', '+')

	def get_name(self):
		movieName = self.name
		return movieName

	def down(self):
		"download titulku z konkretni stranky"
		find = re.search('/en/subtitleserve/file/[0-9]*', self.url)
		url2 = "".join(['http://www.opensubtitles.org', find.group(0)])
		webFile = urllib2.urlopen(url2)
		locFile = open(url2.split('/')[-1], 'w')
		locFile.write(webFile.read())
		webFile.close()
		locFile.close()
		return url2.split('/')[-1]

	def count(self):
		"spocita cd"
		find = re.findall('/en/subtitleserve/file/[0-9]*', self.url)
		return len(find)

	def get_url(self, cd, lang2):
		"vyhleda nove titulky"
		urlNew = 'http://www.opensubtitles.org/en/search/sublanguageid-'
		urlNew = "".join([urlNew, lang2, 'moviename-', self.name])
		urlNew = "".join([urlNew, '/subsumcd-', str(cd)])
		return urlNew

	def get_list(self, language, someName):
		"ziska seznam stranek s novymi titulky"
		list = re.findall('en/subtitles/[0-9]*', self.url)
		i = 0 ; stru = "".join([someName, language]).replace('+', '-')
		for item in list:
			list[i] = "/".join(['http://www.opensubtitles.org', item, stru])
		return list

class Title:
	def __init__(self):
		self.anglickeTitulky = []
		self.ceskeTitulky = []

	def dictr(self, string):
		"stringy na cas"
		allTitles = re.findall("\d*\r\n\d{2}\:\d{2}\:\d{2},\d{3} --> \d{2}\:\d{2}\:\d{2},\d{3}\r\n.*?\r\n.*?\r\n", string)
                subtitles = []
		for line in allTitles:
#			# star
			line1 = re.search("\d{2}\:\d{2}\:\d{2},\d{3} --> \d{2}\:\d{2}\:\d{2},\d{3}", line).group()
			hours = line1.split(':')[0]
			mint = line1.split(':')[1]
			sec = line1.split(':')[2].split(',')[0]
			msec = line1.split(':')[2].split(',')[1].split(' --> ')[0]
			startTime = float(hours) * 3600 + float(mint) * 60 + float(sec) + float(msec) / 1000
			# end
			line2 = line1.split(' --> ')[1]
			hours = line2.split(':')[0]
			mint = line2.split(':')[1]
			sec = line2.split(':')[2].split(',')[0]
			msec = line2.split(':')[2].split(',')[1]
			endTime = float(hours) * 3600 + float(mint) * 60 + float(sec) + float(msec) / 1000
			# data
			compiled = re.compile("\d{2}\:\d{2}\:\d{2},\d{3} --> \d{2}\:\d{2}\:\d{2},\d{3}\r\n(.*?\r\n.*?)\r\n", re.DOTALL)
			data = compiled.findall(line)[0].replace('\r\n', ' ')
			subtitles.append([{'start':startTime, 'end':endTime, 'data':data}])
		return subtitles

	def matching(self, CZtitle, ENtitle):
		timeEN, timeCZ = 0, 0
		qmrk = re.compile('.*\?.*',re.DOTALL)
		for line in CZtitle:
			if qmrk.match(line[0]['data']):
				timeCZ = line[0]['start']
				break
		for line in ENtitle:
			if qmrk.match(line[0]['data']):
				timeEN = line[0]['start']
				break
		move = timeCZ - timeEN
		return move

	def speak(self, CZtitle, ENtitle, f):
		move = self.matching(CZtitle, ENtitle)
		err = 1.0
		speaches = []
		for lncz in titleCZ:
			en = []	
			time1 = lncz[0]['start'] - move + err
			time2 = lncz[0]['start'] - move - err
			for lnen in titleEN:
				if (lnen[0]['start'] > time2 and lnen[0]['start'] < time1):
					en.append(lnen[0]['data'])
			sp = ''.join(en)
			speaches.append(sp+'	'+lncz[0]['data'])
			del en
		for i in speaches:
			f.write(i)
			f.write('\n')
		return speaches


#url0 = 'http://www.opensubtitles.org/en/subtitles/3258272/the-mist-cs' 

lang1 = 'cs'
lang2 = 'en'
lang3 = 'eng/'
cd = 0
IDM = 0

help = "Program pro stahovani a casovou synchronizaci titulku\n\
Autor:	 xheczk04, Heczkova Petra\n\
Predmet: ISJ, 2012\n\n\
Napoveda:\n\
-h nebo --help	vypise tuto napovedu\n\
--id		napr. --id=42 >> najde film s IMDB cislem 42\n\
--cd		napr. --cd=2 >> hleda titulky podle poctu cd\n\
--lang		napr. --lang=en,slo >> z anglictiny do slovenstiny\n\
		pokud nebude zadano tak --lang=cs,en\n\
		cs - cesky, en - anglicky\n\
parametry id, cd a lang lze kombinovat"

try:
	opts, args = getopt.getopt(sys.argv[1:], "hcil:", ["help", "lang=", "cd=", "id="])
except getopt.GetoptError:
	print help
        sys.exit(1)

for a in args:
	url0 = a
for o, a in opts:
	if o in ("--lang"):
		lang1 = a.split(',')[0]
		lang2 = a.split(',')[1]
		if lang2 == 'en':
			lang3 = 'eng/'
			lang4 = 'cze/'
		elif lang2 == 'cs':
			lang3 = 'cze/'
			lang4 = 'eng/'
		else:
			lang3 = "".join([lang2, "/"])
			print "untested language ... but I can try\n\
tested: cs and en"
	elif o in ("-h", "--help"):
		print help
	elif o in ("--cd"):
		cd = a
	elif o in ("--id"):
		IDM = a
		if IDM <= 0:
			print "Cislo filmu nemuze byt zaporne!"
			sys.exit(1)
		url1 = 'http://www.opensubtitles.org/en/search/sublanguageid-'
		url1 = "".join([url1, lang4, 'idmovie-', IDM])
		if  cd > 0:
			url0 = "".join([url1, '/subsumcd-', str(cd)])
		url1 = urllib2.urlopen(url1).read()
		url1 = re.search('en/subtitles/[0-9]*/[a-z0-9-]*">', url1)
		url1 =  url1.group().strip("\">")
		url0 = "".join(['http://www.opensubtitles.org/', url1])
	else:
		print help

cz = DownFile(url0, lang1)
movieName = cz.get_name()
nameCZ = cz.down()
urlNew = cz.get_url(cz.count(), lang3)

if IDM > 0:
	urlNew = urlNew.replace(lang2, '')

try:
	listEN = DownFile(urlNew, lang2).get_list(lang2, movieName)
	nameEN = DownFile("".join(["http://www.opensubtitles.org/", listEN[1]]), lang2).down()

except:
	print "Nepodarilo se najit film s takovym nazvem. "
	sys.exit(1)

# prace se soubory nameEn a nameCZ
fcz = file(nameCZ, 'r') ; fen = file(nameEN, 'r')
fout = file('vyhodnoceni.txt', 'w')

titleCZ = Title().dictr(fcz.read())
titleEN = Title().dictr(fen.read())
speaches = Title().speak(titleCZ, titleEN, fout)

fcz.close() ; fen.close() ; fout.close()

