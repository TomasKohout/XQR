from __future__ import print_function
import getopt
import sys
from pathlib import Path
from xml.dom import minidom


EPARAMS = 1
EINPUT  = 2
EOUTPUT = 3
EOUTFORM= 4
EPARSE  = 80
KEY_ELEMS = ("SELECT", "FROM", "WHERE", "LIMIT", "NOT", "CONTAINS", "=", ">", "<")

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def errhandle(err):
    if (err == EPARAMS):
        eprint("Spatne parametry")
        sys.exit(EPARAMS)
    elif (err == EINPUT):
        eprint("Nezadan vstupni soubor")
        sys.exit(EINPUT)
    elif (err == EOUTPUT):
        eprint("Nezadan vystupni soubor nebo neco podobneho")
        sys.exit(EOUTPUT)
    elif (err == EOUTFORM):
        eprint("Spatny format vystupniho souboru")
        sys.exit(EOUTFORM)
    elif (err == EPARSE):
        eprint("Chyba v zapisu dotazu")
        sys.exit(EPARSE)


def usage():
    if len(sys.argv) == 2:
        print("help")
    else:
        errhandle(EPARAMS)


def getWord(str):
    ret = ""
    cut = 0
    for i, c in enumerate(str):
        if not c.isspace():
            ret += c
            for s in KEY_ELEMS:
                if ret == s:
                    cut = len(ret)
                    str = str[cut:]
                    if str.startswith(" "):
                        str = str[1:]
                    if ret == str:
                        str == ""
                    return ret, str
        else:
            cut = len(ret)
            str = str[cut:]
            if str.startswith(" "):
                str = str[1:]
            break
    if ret == str:
        str = ""
    return ret, str


def parse(query):
    word, query = getWord(query)
    element = None
    table   = None
    notCount = 0
    condElem = None
    relOper  = None
    literal  = None
    if (word == "SELECT"):
        element, query = getWord(query)
        if element in KEY_ELEMS:
            errhandle(EPARSE)
        word, query = getWord(query)
        if word == "FROM":

            if not query:
                return element, table, notCount, condElem, relOper, literal
            table, query = getWord(query)

            if not query or query.isspace():
                return element, table, notCount, condElem, relOper, literal

            if table == "WHERE":
                word = table
                table = ""
            else:
                if not query: #WHERE EMPTY
                    return element, table, notCount, condElem, relOper, literal

                word, query = getWord(query)

            if (word == "WHERE"):
                if not query:
                    errhandle(EPARSE)
                word, query = getWord(query)
                if word == "NOT":
                    while (word == "NOT"):
                        if query:
                            word, query = getWord(query)
                            notCount += 1
                        else:
                            errhandle(EPARSE)
                condElem = word
                if query:
                    word, query = getWord(query)
                else:
                    errhandle(EPARSE)
                relOper = word
                if query:
                    word, query = getWord(query)
                else:
                    errhandle(EPARSE)
                literal = word
            else:
                errhandle(EPARSE)
        else:
            errhandle(EPARSE)
    else:
        errhandle(EPARSE)
    return element,table, notCount, condElem, relOper, literal


def getParams():
    try:
        opts, args = getopt.getopt(sys.argv[1:],  "ho:i:q:n::r::",["help", "output=", "input=", "query=", "qf=", "n", "root="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    output = None
    input  = None
    query  = None
    queryFlag = False
    qf     = None
    qfFlag     = False
    n      = False
    root   = None

    for o, a in opts:
        if o in ("-o","--output"):
            output = a #TODO err handle if not folder
            if not(output):
                errhandle(EPARAMS)
        elif o in ("-i", "--input"):
            input = a
            pathCheck = Path(input)
            if not(input) or (not pathCheck.is_file()):
                errhandle(EPARAMS)
        elif o in ("-h", "--help"):
            usage()
        elif o in ("-q", "--query"):
            query = a
            if not (query):
                errhandle(EPARAMS)

            if query.startswith('\'') and query.endswith('\''):
                query = query[1:-1]

            if "'" in query:
                errhandle(EPARAMS)
            queryFlag = True
        elif o in ("--qf"):
            qf = a
            if not (qf):
                errhandle(EPARAMS)
            qfFlag = True
        elif o in ("-n"):
            if not (a):
                errhandle(EPARAMS)

            n = True
        elif o in ("-r", "--root"):
            root = a
        else:
            assert False, "neznamy parametr"

    if not (queryFlag or qfFlag):
        errhandle(EPARAMS)

    return output, input, query, queryFlag, qf, qfFlag, n, root


def iteroverit(root, input, element, table, notCount, condElem, relOper, literal):
    if not root[0]:
        return 0

    for child in root:
        print([child])


    #iteroverit(root[0], input, element, table, notCount, condElem, relOper, literal)


def main():
    output = None
    input = None
    query = None
    queryFlag = False
    qf = None
    qfFlag = False
    n = False
    root = None

    output, input, query, queryFlag, qf, qfFlag, n, root = getParams()

    element = None
    table = None
    notCount = 0
    condElem = None
    relOper = None
    literal = None
    if query and (qfFlag is False):
        element, table, notCount, condElem, relOper, literal = parse(query)
    elif qfFlag and (queryFlag is False):
        myFile = Path(qf)
        if myFile.is_file():
            file = open(myFile, "r")
            query = file.read()
            element, table, notCount, condElem, relOper, literal = parse(query)
        else:
            errhandle(EINPUT)
    else:
        errhandle(EPARAMS)

    notCount = notCount % 2 # zjisti, jestli negovat nebo ne

    #print("%s %s %d %s %s %s" % (element, table, notCount, condElem, relOper, literal))
    if not table:
        print("Prazdny dokument nebo hlavicka")
    tree = minidom.parse(input)
    xmlroot = [tree.documentElement]

    xml = iteroverit(xmlroot, input, element, table, notCount, condElem, relOper, literal)


if __name__ == "__main__":
    main()