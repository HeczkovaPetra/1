#!/usr/bin/php
<?php
#XQR:xheczk04

$napoveda = "------------------------------------------------------------------------------
./src/xqr.php
===
--help                 - Show help
--input=filename.ext   - Input file with xml
--output=filename.ext  - Output file with xml
--query='query'        - Query under xml - can not be used with -qf attribute
--qf=filename.ext      - Filename with query under xml
-n                     - Xml will be generated without XML header
-r=element             - Name of root element
------------------------------------------------------------------------------
";

// pomocne promenne
$q = 0; $qf = 0; $n = 0; $root = 1; 
$out = -100; $vstup = -100;

/**
 * Zpracovani parametru a kontrola neslucitelnych parametru, 
 * array slice - parametry zacinaji od $argv[1] 
 */ 
foreach (array_slice($argv,1) as $arg) {
	$a = explode("=", $arg);

	if ("--help" == $arg) {
		if($argc == 2){
			Echo $napoveda;
			exit(0);
		} else { exit(1); }
	}
	elseif ("--input"  == $a[0]) {
		if((!is_file($a[1])) || (!file_exists($a[1]))) {exit(2);}
		$vstup = file_get_contents($a[1]);
	}
	elseif ("--output" == $a[0]) {
		if (!($out = fopen($a[1], 'w'))) {
			exit(3);
		}
	}
	elseif ("--query" == $a[0]) {
		$dotaz = $a[1];
		$q = 1;
	}
	elseif ("--qf" == $a[0]) {
		if((!is_file($a[1])) || (!file_exists($a[1]))) {exit(2);}
		$dotaz  = file_get_contents($a[1]);
		$qf = 1;
	}
	elseif ("-n" == $arg) {
		$n = 1;
	}
	elseif ("--root" == $a[0]) {
		$root = $a[1];
	}
	else { // jiny neplatny parametr
		exit(1);
	}
	// query a qf nelze kombinovat
	if($q == 1 && $qf == 1){
		file_put_contents('php://stderr', "./src/xqr.php wrong combination of parameters -qf and -q\n");
		exit(1);
	}
}

/**
 * Zastupuje fci main, zpracovava vstup a vystup, pokud nejsou v souboru,
 * vytvari SimpleXMLIterator, pracuje s parametry -n a --root,
 * osetruje kdyz se LIMIT rovna 0, vola fci search_array  
 */ 
if($out < 0){
	$out = fopen('php://stdout','w');
}
if($vstup < 0){
	$vstup = file_get_contents("php://stdin");
}

$limit = 0;
$dotaz = query_to_array($dotaz);
$sxi = new SimpleXmlIterator($vstup);

if(!array_key_exists('LIMIT', $dotaz) || $dotaz['LIMIT'] >= 1){
	if($n != 1){
		fprintf($out, "<?xml version=\"1.0\" encoding=\"utf-8\"?>");
	}
	if($root != 1){
		fprintf($out, "<%s>", $root);
	}
	search_array($sxi, $dotaz['FROM'], $dotaz, "from");
	if($root != 1){
		fprintf($out, "</%s>", $root);
	}
	fprintf($out, "\n");
} else {
	if($n != 1){
		fprintf($out, "<?xml version=\"1.0\" encoding=\"utf-8\"?>");
	}
	if($root != 1){
        	fprintf($out, "<%s/>\n", $root);
	}
}

/**
 * Rekurzivne prohledava pole, pouzije se aby nasla oblast FROM a pak zavola
 * samu sebe, aby nasla SELECT, vola fci where_check, pokud dotaz obsahuje 
 * podminku, nakonci je vypis pomoci asXML() 
 * @sxi je SimpleXMLIterator object
 * @needle2 je element, ktery vyhledavame
 * @qu je zadany dotaz
 * @str je pomocny string urcuje, co hledame, nabyva hodnot "from" nebo "select"   
 */ 
function search_array($sxi, $needle2, $qu, $str){

global $limit; global $out;
// neco.atr rozdelime do pole
$needle = explode('.', $needle2);

foreach($sxi as $key => $value){

	// pro pripady FROM lib.my
  // existuje .my a neexistuje pozadovany atribut $torf bude false
	$torf = true;
	if(array_key_exists(1,$needle) && !isset($value->attributes()->$needle[1])){
		$torf = false;
	}

	// LIMIT 
	if(array_key_exists('LIMIT',$qu ) && $limit >= $qu['LIMIT']){
		return true;
	}

	if($torf && ($key === $needle[0] || empty($needle[0])) || search_array($value, $needle2,  $qu, $str)!==false){
		// FROM cast
		if($str == "from"){
			search_array($value, $qu['SELECT'], $qu, "select");
			// pokud hledame v ROOT tak pokracujeme
			if(!empty($needle[0])){
				return true;
			}
			if(empty($needle[0]) && array_key_exists(1,$needle)){return false;}
		// SELECT cast
		} else { // $str == "select"
      // volame where_check, pokud v dotazu existuje podminka
			if(array_key_exists('WHERE', $qu) && where_check($qu, $value) == false){
        continue;
			}
			$limit++;
      // vypis nalezeneho elementu
			fprintf($out, $value->asXML());
		}
	}
	

} // end foreach
return false;
} // end function

/**
 * Fce kontroluje WHERE polozku a vybira vhodne, vraci true nebo false,
 * vola fci where_check2, 
 * pokryva 3 pripady, WHERE elem, WHERE .atr, WHERE elem.atr 
 * @dotaz je zadany dotaz
 * @arr je element  
 */ 
function where_check($dotaz, $arr){

$d = explode('.',$dotaz['WHERE']);
// WHERE price
if(strpos($dotaz['WHERE'],'.') === false){
	foreach($arr as $k => $v) {
		if($k == $dotaz['WHERE']) {
			return where_check2($dotaz, $v);
		}
	}

} else {
	// WHERE .id
	if(empty($d[0])){
		foreach($arr->attributes() as $k => $v) {
			if($k == $d[1]){
				return where_check2($dotaz, $v);
			}
		}
	// WHERE neco.id
	} else {
		foreach($arr as $k => $v){
			foreach($v->attributes() as $k2 => $v2){
				if($k == $d[0] && $k2 == $d[1]){
					return where_check2($dotaz, $v2);
				}
			}
		}	
	}
}
return false;
} // end funcion

/**
 * Fce volana fci where_check, vraci true nebo false,
 * pokryva 2 pripady, WHERE ... [<|>|=] number, WHERE ... CONTAINS "string", 
 * parametry stejne jako u fce where_check 
 */ 
function where_check2($dotaz, $v){
	if(array_key_exists('SIG', $dotaz)){
        	if ($dotaz['SIG'] == ">" && $v > $dotaz['NUM']) {
                	return true;
                } elseif ($dotaz['SIG'] == "<" && $v < $dotaz['NUM']) {
                        return true;
                } elseif ($dotaz['SIG'] == "=" && $v == $dotaz['NUM']) {
                        return true;
                }
        }
        // CONTAINS
        if(array_key_exists('CONTAINS', $dotaz) && strpos($v,$dotaz['CONTAINS']) !== false){
                        return true;
        }
} // end funcion

/**
 * Fce upravuje dotaz do asociativniho pole a kontroluje syntax a semnatiku
 * @dotaz je zadany dotaz 
 */ 
function query_to_array($dotaz){
	$dotaz = explode(" ", trim($dotaz));
	$qu = array();
	$arrlength = count($dotaz);

	for($x = 0; $x < $arrlength; $x = $x+2){
		$y = $x+1;
		$qu[$dotaz[$x]] = $dotaz[$y];
	}
	// vynechano z ceho SELECT
	if($qu['FROM'] == "WHERE" || $qu['FROM'] == "LIMIT"){
		$qu['LIMIT'] = 0;
	}
	if($qu['FROM'] == "ROOT"){
		$qu['FROM'] = "";
	}
	// kdyz mame WHERE musi nasledovat CONTAINS nebo [<|>|=]
	if (array_key_exists('WHERE', $qu)) {
		if (array_key_exists('CONTAINS', $qu)) {
			// po CONTAINS musi nasledovat "string"
			if (strpos($qu['CONTAINS'], '"') === false) {
				file_put_contents('php://stderr', "Error in WHERE condition: string literal is expected.\n");
				exit(80);
			}
			// odstranuju "" z retezce
			$qu['CONTAINS'] = trim($qu['CONTAINS'], '"');
		} elseif (array_key_exists('>', $qu) || array_key_exists('<', $qu) || array_key_exists('=', $qu)) {
			next($qu);next($qu);$next = next($qu);
			$qu['NUM'] = current($qu);
			$qu['SIG'] = key($qu);
			// po [<|>|=] musi nasledovat cislo
			if (!ctype_digit($qu['NUM'])) {
				file_put_contents('php://stderr', "Error in WHERE condition: number is expected.\n");
				exit(80);
			}
		} else {
			file_put_contents('php://stderr', "Error in WHERE condition: CONTAINS or < or > or = is expected.\n");
			exit(80);
		}
	}
	return $qu;
} // end function

?>
