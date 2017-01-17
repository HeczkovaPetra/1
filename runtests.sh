#!/bin/bash

while getopts ":vtrsc" opt; do
  case $opt in
    v)
      v=1
      ;;
    t)
      t=1
      ;;
    r)
      r=1
      ;;
    s)
      s=1
      ;;
    c)
      c=1
      ;;
    \?) #pro neplatne parametry
      printf "Usage: ./runtests.sh [-vtrsc] TEST_DIR [regex]

    -v  validate tree
    -t  run tests
    -r  report results
    -s  synchronize expected results
    -c  clear generated files

    It is mandatory to supply at least one option.\n"
      exit 2
      ;;
  esac
done

shift $(($OPTIND - 1))

REGEX=$2
TEST_DIR=`echo $1 | sed 's/^.\///'`

if [ -z "$REGEX" ]; then
   REGEX=$TEST_DIR
fi

# Kontrola jestli stromy adresaru existuji
find $TEST_DIR > /dev/null 2> /dev/null || exit 1
#find $REGEX > /dev/null 2> /dev/null || exit 1 

if [ $TEST_DIR = '/dev/null' ]; then
   exit 1
fi

EC=0

IFS="
"

# OPERACE -t -r
# 6. Pro dvojice souborů X-{expected,captured} je jejich rozdil (ziskany prikazem diff -up) zapsan do odpovidajiciho souboru X-delta, pro X z mnoziny {stdout,stderr,status}.
# 7. Na standardni chybovy vystup je zapsano \"$TEST: $RESULT\\n\", kde: $TEST je cesta adresare obsahujici cmd-given relativni k TEST_DIR (v kanonickem tvaru bez prefixu ./). $RESULT je OK, pokud jsou soubory {stdout,stderr,status}-delta prazdne; v opacnem pripade FAILED.
# 8. Navratovy kod je nastaveny na 0, pokud je vysledkem vsech testů OK.
# 9. Pokud je standardni chybovy vystup pripojen na terminal, jsou retezce OK vypisovany zelene a retezce FAILED vypisovany cervene.


function differ {
   res_all=0
   for st in stdout stderr status; do
      diff -up "$st-expected" "$st-captured" > "$st-delta" 2> /dev/null || { res_all=1 ; break 
}
      if [ -s "$st-delta" ]; then
         res_all=1
      fi
   done
# kontroluje pripojeni na terminal
   tty -s
   if [ $? -eq 0 ]; then
      if [ $res_all -eq 1 ]; then
         RESULT="[1;31mFAILED[0m" # cervena
         EC=1
      else
         RESULT="[1;32mOK[0m" # zelena
      fi
   else
      if [ $res_all -eq 1 ]; then
         RESULT="FAILED"
         EC=1
      else
         RESULT="OK"
      fi
   fi
}

if [ $v ]; then

# Pokud je v nekterem adresari aspon jeden adresar, tak jsou v nem jenom adresare a zadne jine soubory.

   for dir in `ls -R -l $TEST_DIR | grep $TEST_DIR | grep -E $REGEX | sed 's/:*$//'`; do
   if [ `ls -l $dir | cut -c1,1 | tr '\n' 'a' | grep -c '\-ad\|da-'` -ne 0  ]; then
      EC=1 ; echo "$0: directories and other files are mixed in $dir" >&2
   fi
   done


# V kazdem adresari, ve kterem nejsou adresare, existuje soubor cmd-given a uzivatel ma opravneni jej spoustet.

   for i in `find $TEST_DIR -name 'cmd-given' | grep -E $REGEX`; do
      test -x $i
      if [ $? != 0 ]; then
         EC=1 ; echo "$0: cmd-given is not executable." >&2
      fi
   done

# Vsechny soubory stdin-given v danem stromu jsou uzivateli pristupne pro cteni, pokud existuji.

   for i in `find $TEST_DIR -name 'stdin-given' | grep -E $REGEX`; do
      test -r $i
      if [ $? != 0 ]; then
         EC=1 ; echo "$0: stdin-given is not readable." >&2
      fi
   done

# Ve stromu nejsou žádné symbolické odkazy a žádné vícenásobné pevné odkazy.

   if [ `ls -l -R $TEST_DIR | grep -c "^l"` -ne 0 ]; then
      EC=1 ; echo "$0: there are symbolic links in $TEST_DIR" >&2
   fi

# Vsechny soubory {stdout,stderr,status}-{expected,captured,delta} v danem stromu jsou uzivateli pristupne pro zapis, pokud existuji.

   reg="\(status\|stdout\|stderr\)-\(expected\|captured\|delta\)"
   all=`ls -l -R $TEST_DIR | grep -E $REGEX | grep -c $reg`
   wr=`ls -l -R $TEST_DIR | grep -E $REGEX | grep $reg | grep -c "w"`
   if [ $all -ne $wr ]; then
      EC=1 ; echo "$0: {stdout,stderr,status}-{expected,captured,delta} are not writeable" >&2
   fi

# Vsechny soubory status-{expected,captured} obsahuji pouze cele cislo zapsane v desitkove soustave nasledovane znakem konce radku (0x0A).

   h1=0 ; h2=0
   for line in `find $TEST_DIR -name "status-expected" -o -name "status-captured" | grep -E $REGEX `; do
      if [ `cat $line | grep -c "^[0-9]$"` -ne 0 ]; then
         h1=1
      fi
   done
   if [ $h1 -eq 1 ]; then
      EC=1 ; echo "$0: $line do not include integer" >&2
   fi

# Ve stromu jsou pouze adresare adresarů a vyse vyjmenovane soubory (a zadne jine).

# muze to obsahovat stdin-given?
   for dir in `ls -R -l $TEST_DIR | grep $TEST_DIR | grep -E $REGEX | sed 's/:*$//'`; do
   if [ `ls -l $dir | grep "^-" | grep -vc "cmd\|status\|expected\|captured\|delta\|stdin\|stdout\|stderr\|status"` -ne 0  ]; then
      h2=1
   fi
   done

   if [ $h2 -eq 1 ]; then
      EC=1 ; echo "$0: other files in $TEST_DIR" >&2
   fi

fi

if [ $t ]; then

# Pro adresare z daneho stromu, ve kterych se nachazi soubor cmd-given, proved:

   for file in `find $TEST_DIR -name "cmd-given" | grep -E $REGEX`; do

# 1. Aktualni adresar je nastaven na prave zpracovavany adresar.

      file_path=`echo ${file//\/cmd-given} | sed 's/^.\///'`
      cd $file_path || { EC=2 ; break 
} 

# 2. Soubor cmd-given z aktualniho adresare je spusten.
# 3. Na standardni vstup je spustenemu souboru predam obsah souboru stdin-given z aktualniho adresare, pokud soubor existuje. Pokud soubor stdin-given neexistuje, je na vstup presmerovan soubor /dev/null.
# 4. Standardni vystup a standardni chybovy vystup produkovane spustenym programem jsou zapisovany do souborů {stdout,stderr}-captured v aktualnim adresari.
# 5. Navratovy kod spusteneho souboru je zapsan do souboru status-captured v aktualnim adresari.

      if [ `ls | grep "stdin-given"` ]; then
         ./cmd-given < stdin-given > stdout-captured  2> stderr-captured |echo $? > status-captured
      else
         ./cmd-given < /dev/null > stdout-captured 2> stderr-captured |echo $? > status-captured
      fi

      differ
      echo "${file_path/\.\/}: $RESULT" >&2

# Ukonceni cyklu

      out_path=`echo $file_path | tr -sc '[\/]' 'a'`
      cd `echo ${out_path//a/..}` || { EC=2 ; break
}
   done

fi

if [ $r ]; then

# Viz operace -t, ale body 1 az 5 jsou vynechany a pro vypis vysledků se misto standardniho chyboveho vystupu pouziva standardni vystup (pri tisku i pri detekci terminalu).

   for file in `find $TEST_DIR -name "cmd-given" | grep -E $REGEX`; do
      file_path=`echo ${file//\/cmd-given}`
      cd $file_path || { EC=2 ; break 
}

      differ
      echo "${file_path/\.\/}: $RESULT"

      out_path=`echo $file_path | tr -sc '[\/]' 'a'`
      cd `echo ${out_path//a/..}` || { EC=2 ; break 
}
   done 
fi

if [ $s ]; then

#  Vsechny soubory {stdout,stderr,status}-captured v danem stromu prejmenuje na odpovidajici soubory {stdout,stderr,status}-expected.
# Pokud soubory {stdout,stderr,status}-expected jiz existuji, jsou prepsany.

   for file in `find $TEST_DIR -name "stdout-captured" -o -name "stderr-captured" -o -name "status-captured" | grep -E $REGEX`; do
      mv "$file" "${file%-captured}-expected" || { EC=2 ;
echo "$0: files cannot be renamed" >&2 
}
   done

fi

if [ $c ]; then

# Smaze vsechny soubory {stdout,stderr,status}-{captured,delta} v danem stromu podle daneho filtru.

   reg="\(stdout\|stderr\|status\)-\(captured\|delta\)"
   for file in `ls -R $TEST_DIR | grep $reg | grep -E $REGEX`; do
      rm -f `find $TEST_DIR -name $file` || { EC=2 ;
echo "$0: files cannot be removed" >&2 
}
   done

fi

unset $IFS

exit $EC

