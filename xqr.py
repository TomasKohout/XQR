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

def isnumber(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

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
                        str = ""
                    return ret, str
                elif ret[len(ret)-1:] == s:
                    str = str[len(ret)-1:]
                    return ret[:len(ret)-1], str


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
    limit    = None
    if (word == "SELECT"):
        element, query = getWord(query)
        if element in KEY_ELEMS:
            errhandle(EPARSE)
        word, query = getWord(query)
        if word == "FROM":

            if not query:
                return element, table, notCount, condElem, relOper, literal, limit
            table, query = getWord(query)

            if not query or query.isspace():
                return element, table, notCount, condElem, relOper, literal, limit

            if table == "WHERE":
                word = table
                table = ""
            else:
                if not query: #WHERE EMPTY
                    return element, table, notCount, condElem, relOper, literal, limit

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

                if "LIMIT" in query:
                    word, query = getWord(query)
                    if word == "LIMIT":
                        if query:
                            word, query = getWord(query)
                        else:
                            errhandle(EPARSE)

                        if isnumber(word):
                            limit = word
                        else:
                            errhandle(EPARSE)

                    else:
                        errhandle(EPARSE)

            else:
                errhandle(EPARSE)
        else:
            errhandle(EPARSE)
    else:
        errhandle(EPARSE)
    return element,table, notCount, condElem, relOper, literal, limit

#--qf=./STest/test12.qu --input=./STest/test12.in --root=MyCatalog --output=file.xml
def getParams():
    try:
        opts, args = getopt.getopt(sys.argv[1:],  "ho:i:q:n::r::",["help", "output=", "input=", "query=", "qf=", "n", "root="])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(EPARAMS)
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
            checkP = output.rfind('/')
            fold   = output[:checkP+1]
            print(fold)
            checkP = Path(fold)
            if not checkP.is_dir():
                errhandle(EPARAMS)

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
            if not a:
                errhandle(EPARAMS)
            root = a
        else:
            assert False, "neznamy parametr"

    if not (queryFlag or qfFlag):
        errhandle(EPARAMS)

    return output, input, query, queryFlag, qf, qfFlag, n, root


def iteroverit(root, element, table):
    if not root:
        return 0

    xmlroot = None
    tagName = None
    attName = None
    ret     = []

    if table:
        if table[0] == ".":
            tagName = table[1:]
        elif "." in table:
            splitIt = table.split(".")
            if len(splitIt) == 2:
                tagName = splitIt[0]
                attName = splitIt[1]
            else:
                errhandle(EPARSE)
        else:
            tagName = table


    if tagName == "ROOT" and attName == None:
        xmlroot = [root.documentElement]

    elif tagName == None and attName:
        if attName[0] == ".":
            attName = attName[1:]

        tmp = root.getElementsByTagName("*")
        for t in tmp:
            if t.hasAttribute(attName):
                xmlroot = [t]
                break
    elif tagName and tagName != "ROOT" and attName:
        tmp = root.getElementsByTagName(tagName)
        for t in tmp:
            if t.hasAttribute(attName):
                xmlroot = [t]
                break
    elif tagName and tagName != "ROOT" and not attName:
        xmlroot = [root.getElementsByTagName(tagName)[0]]
    else:
        errhandle(EPARSE)

    if  root.documentElement.tagName == element and tagName == "ROOT":
        return [root.documentElement]
    else:
        for x in xmlroot:
            ret.extend(x.getElementsByTagName(element))

    return ret
    #iteroverit(root[0], input, element, table, notCount, condElem, relOper, literal)


def cond(condElem, relOper, literal):
    elem = condElem
    lit  = literal
    if "\"" == lit[0] and "\"" == lit[len(lit)-1]:
        lit = lit[1:]
        lit = lit[:len(lit)-1]

    if isnumber(lit) and relOper == "CONTAINS":
        errhandle(EPARSE)

    if isnumber(elem):
        elem = float(elem)

    if relOper == "CONTAINS":
        if lit in elem:
            return True
        else:
            return False
    elif relOper == "<":
        if isnumber(lit):
            return elem < float(lit)
    elif relOper == ">":
        if isnumber(lit):
            return elem > float(lit)
    elif relOper == "=":
        if isnumber(lit):
            return elem == float(lit)
        elif lit == "True" or lit == "False":
            return elem == lit
    else:
        errhandle(EPARSE)


def where(xml, element, notCount, condElem, relOper, literal):
    ret = []
    if notCount == 0:
        if "." not in condElem: #element
            for tag in xml:
                if tag.tagName == condElem:
                    try:
                        if cond(tag.firstChild.nodeValue,relOper,literal):
                            ret.append(tag)
                            continue
                    except:
                        continue
                for underTag in tag.getElementsByTagName(condElem):
                    try:
                        if cond(underTag.firstChild.nodeValue, relOper, literal):
                            ret.append(tag) #todo is it working?

                        break
                    except:
                        break
        elif condElem[0] == ".": #.att
            for att in xml:
                if att.hasAttribute(condElem[1:]):
                    if cond(att.getAttribute(condElem[1:]),relOper, literal):
                        ret.append(att)
                        continue

                for attforsec in att.getElementsByTagName("*"):
                    if attforsec.hasAttribute(condElem[1:]):
                        if cond(attforsec.getAttribute(condElem[1:]), relOper, literal):
                            ret.append(att)
                            break
        elif "." in condElem: #ele.att
            tmp = condElem.split(".")
            for tag in xml:
                #print(literal, tag.getAttribute(tmp[1]))
                #print(tag.tagName, tag.hasAttribute(tmp[1]), cond(tag.getAttribute(tmp[1]), relOper, literal))
                if tag.tagName == tmp[0] and tag.hasAttribute(tmp[1]) and cond(tag.getAttribute(tmp[1]), relOper, literal):
                   #print(notCount)
                    ret.append(tag)
                    continue
                for underTag in tag.getElementsByTagName(tmp[0]):
                    if underTag.hasAttribute(condElem[1:]) and cond(underTag.getAttribute(tmp[1]), relOper, literal):
                        ret.append(tag)
                        break

    return ret



def main():
    outputF = None
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
    limit = None
    if query and (qfFlag is False):
        element, table, notCount, condElem, relOper, literal, limit = parse(query)
    elif qfFlag and (queryFlag is False):
        myFile = Path(qf)
        if myFile.is_file():
            file = open(myFile, "r")
            query = file.read()
            element, table, notCount, condElem, relOper, literal, limit = parse(query)
        else:
            errhandle(EINPUT)
    else:
        errhandle(EPARAMS)

    notCount = notCount % 2 # zjisti, jestli negovat nebo ne

    #print("%s %s %d %s %s %s" % (element, table, notCount, condElem, relOper, literal))
    if not table:
        print("Prazdny dokument nebo hlavicka")
    tree = minidom.parse(input)

    xml = iteroverit(tree, element, table)

    if condElem:
        xml = where(xml, element, notCount, condElem, relOper, literal)

    if output:
        try:
            outputF = open(output, "w")
        except (OSError, IOError):
            errhandle(EOUTPUT)
        outputF.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
        if root:
            outputF.write("\n<" + root + ">\n")
        for x in xml:
            outputF.write(x.toxml())
        if root:
            outputF.write("\n</" + root + ">")
        outputF.close()
        return 0

    sys.stdout.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>")
    if root:
        sys.stdout.write("\n<" + root + ">\n")
    for e in xml:
        sys.stdout.write(e.toxml())
    if root:
        sys.stdout.write("\n"+"<" + root + "/>")

    return 0

if __name__ == "__main__":
    main()