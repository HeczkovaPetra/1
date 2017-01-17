# BIF proj - xheczk04

import sys
from operator import itemgetter, attrgetter, methodcaller

tab_name = ["Coding genes","protein_coding","miRNA","TR_D_gene","Summary","CDS","Coding transcripts","Summary"]
tab_cnt  = ["Count"    ,0,0,0,0,0,0,0,0,0]
tab_size = ["Size [bp]",0,0,0,0,0,0,0,0,0]
tab_cov = ["G.cov. [%]",0,0,0,0,0,0,0,0,0]

chrom_lens = [248956422, 242193529, 198295559, 190214555, 181538259, 170805979, 159345973, 145138636, 138394717, 133797422, 135086622, 133275309, 114364328, 107043718, 101991189, 90338345, 83257441, 80373285, 58617616, 64444167, 46709983, 50818468, 156040895, 57227415]


def parse(filename):
	cr = 0
	reslist, exonlist = [], []
	res = (0,0,0,0,0)

	with open(filename) as f :
		for line in f :

			# preskocim zacatek
			if "#" in line :
				continue

			# pro chromozomy 1-22, X, Y
			llist = line.split()
			cr = llist[0]

			if cr == 'X' : cr = 22
			elif cr == 'Y' : cr = 23 
			elif cr.isdigit() : cr = int(cr) - 1
			else : continue

			# gene_id
			gid = llist[9][1:-2] # uvozovky a strednik

			# delka genu
			start = int(llist[3])
			end = int(llist[4])

			# gene_biotype (stejny pro geny se stejnym id)
			s = line[line.index("gene_biotype")+14:]
			gbt = s[:s.index("\"")]

			for k in range(len(tab_name)) :
				if tab_name[k] == gbt :
					res = (cr,gid,k,start,end)
					reslist.append(res)
					if "protein_coding" == gbt :
						if "transcript" == llist[2] :
							k = tab_name.index("Coding transcripts")
							res = (cr,gid,k,start,end)
							exonlist.append(res)
						if "CDS" == llist[2] :
							k = tab_name.index("CDS")
							res = (cr,gid,k,start,end)
							exonlist.append(res)
					break
	f.close()
	return reslist, exonlist

def stat(rlist):
	suma_cnt, suma_size, suma_cov = 0, 0, 0
	const = 100/float(sum(chrom_lens))

	for i in rlist :
		tab_cnt[i[2]] += 1
		tab_size[i[2]] += i[4]-i[3]+1
		tab_cov[i[2]] += (i[4]-i[3]+1)*const

	for k in range(len(tab_name)) :
		if not tab_cnt[k] == "Count" :
			suma_cnt  = suma_cnt  + tab_cnt[k]
			suma_size = suma_size + tab_size[k]
			suma_cov = suma_cov + tab_cov[k]
		if tab_name[k] == "Summary" :
			tab_cnt[k]  = suma_cnt 
			tab_size[k] = suma_size
			tab_cov[k] = suma_cov
			suma_cnt, suma_size, suma_cov = 0, 0, 0

	# zapis do souboru
	f = open("output.csv", "w")
	for k in range(len(tab_name)) :
		f.write(tab_name[k]+";"
			+str(tab_cnt[k])+";"
			+str(tab_size[k])+";"
			+str(tab_cov[k])+"\n")
		if tab_name[k] == "Summary" :
			f.write("\n")
	f.close()

def red_len(a,b):
	# vybiram nejvetsi moznou delku genu
	if a[1] == b[1]:
		return (a[0], a[1], a[2], min(a[3],b[3]), max(a[4],b[4]))
	resl.append(a)
	return b

def red_cov(a,b):
	# stejny chromozom
	if a[0] == b[0] :
		# kompletni prekryv
		if a[4] > b[4] :
			x = (b[0], b[1], b[2], 1, 0)
			resl2.append(x)
			return a			
		# castecny prekryv
		elif a[4] > b[3] :
			x = (b[0], b[1], b[2], a[4]+1, b[4])
			resl2.append(a)
			return x
		else :
			resl2.append(a)
			return b
	# jiny chromozom nebo bez prekryvu
	else :
		resl2.append(a)
	return b
	
def main():
	# nekontroluju parametr, predpokladam ze bude zadany korektne
	filename = "Homo_sapiens.GRCh38.84.gtf"
	#filename = sys.argv[1]
	global resl, resl2
	resl, resl2 = [], []

	reslist, exonlist = parse(filename)
	resl.append(reduce(red_len, reslist))

	resl = sorted(resl, key=itemgetter(0,3,4))
	resl2.append(reduce(red_cov,resl))

	exonlist = sorted(exonlist, key=itemgetter(0,3,4))
	resl2.append(reduce(red_cov,exonlist))

	stat(resl2)

if __name__ == "__main__":
	main()


